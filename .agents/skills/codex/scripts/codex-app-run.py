#!/usr/bin/env python3
"""Run one Codex app-server turn over JSON-RPC stdio."""

import argparse
import json
import os
from pathlib import Path
import queue
import re
import signal
import subprocess
import sys
import threading
import time


HANDSHAKE_TIMEOUT_SECONDS = 120
INTERRUPT_GRACE_SECONDS = 10
INTERRUPT_RESPONSE_CODE = -32800


class AppServerFailure(Exception):
    """A bounded, user-safe helper failure."""


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-cmd", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--sandbox", choices=("read-only",))
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--out-last", required=True)
    parser.add_argument("--out-events", required=True)
    parser.add_argument("--state-file", required=True)
    parser.add_argument("--done-file", required=True)
    parser.add_argument("--thread-id")
    args = parser.parse_args()
    if not args.codex_cmd.strip():
        parser.error("--codex-cmd must not be empty")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.model):
        parser.error("--model must match [A-Za-z0-9._-]+")
    if not re.fullmatch(r"[a-z]+", args.effort):
        parser.error("--effort must match [a-z]+")
    if args.thread_id is not None and not args.thread_id:
        parser.error("--thread-id must not be empty")
    return args


def create_private_outputs(args):
    os.umask(0o077)
    cwd = Path(args.cwd).resolve(strict=True)
    if not cwd.is_dir():
        raise AppServerFailure("--cwd must be a directory")
    prompt_path = Path(args.prompt_file)
    prompt = prompt_path.read_text(encoding="utf-8")
    if not prompt.strip():
        raise AppServerFailure("--prompt-file must contain a non-empty prompt")

    out_last = Path(args.out_last)
    out_events = Path(args.out_events)
    for output in (out_last, out_events):
        if not output.parent.is_dir():
            raise AppServerFailure("output parent directory must already exist")
        if output.exists() or output.is_symlink():
            raise AppServerFailure(f"refusing to overwrite an existing output: {output}")

    last_stream = out_last.open("x", encoding="utf-8")
    try:
        events_stream = out_events.open("x", encoding="utf-8")
    except Exception:
        last_stream.close()
        raise
    return cwd, prompt, out_last, last_stream, events_stream


def refusal_for(method):
    if method == "item/commandExecution/requestApproval":
        return {"decision": "decline"}, "declined command execution approval"
    if method == "item/fileChange/requestApproval":
        return {"decision": "decline"}, "declined file change approval"
    if method == "item/tool/requestUserInput":
        return None, "no noninteractive refusal result exists for user input"
    if method == "mcpServer/elicitation/request":
        return {"action": "cancel"}, "cancelled MCP elicitation"
    if method == "item/permissions/requestApproval":
        return {"permissions": {}}, "returned no additional permissions"
    if method == "item/tool/call":
        return {"contentItems": [], "success": False}, "refused dynamic tool call"
    if method == "account/chatgptAuthTokens/refresh":
        return None, "no noninteractive refusal result exists for token refresh"
    if method == "attestation/generate":
        return None, "no noninteractive refusal result exists for attestation"
    if method in ("applyPatchApproval", "execCommandApproval"):
        return {
            "decision": {
                "denied": {
                    "rejection": "Noninteractive runner does not approve requests."
                }
            }
        }, "denied approval request"
    return None, "unsupported server request"


class RunSignals:
    """Record interrupts throughout setup, child execution and finalization."""

    def __init__(self):
        self.number = None
        self.time = None
        self.saved_handlers = {}

    def record(self, received_signal, _frame):
        if self.number is None:
            self.number = received_signal
            self.time = time.monotonic()

    def install(self):
        for signum in (signal.SIGTERM, signal.SIGINT):
            self.saved_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, self.record)

    def restore(self):
        for signum, handler in self.saved_handlers.items():
            signal.signal(signum, handler)


class AppServerClient:
    def __init__(self, args, cwd, prompt, out_last, last_stream, events_stream, signals):
        self.args = args
        self.cwd = cwd
        self.prompt = prompt
        self.out_last = out_last
        self.last_stream = last_stream
        self.events_stream = events_stream
        self.process = None
        self.incoming = queue.Queue()
        self.responses = {}
        self.next_request_id = 1
        self.thread_id = None
        self.thread_event_written = False
        self.turn_id = None
        self.turn_started = False
        self.turn_status = None
        self.final_message = None
        self.signals = signals
        self.interrupt_sent = False
        self.interrupt_response_id = None

    def write_event(self, message):
        self.events_stream.write(json.dumps(message, separators=(",", ":"), ensure_ascii=False))
        self.events_stream.write("\n")
        self.events_stream.flush()

    def send(self, message):
        if self.process is None or self.process.stdin is None:
            raise AppServerFailure("app-server stdin is unavailable")
        try:
            self.process.stdin.write(json.dumps(message, separators=(",", ":"), ensure_ascii=False))
            self.process.stdin.write("\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            raise AppServerFailure("app-server closed its input stream")

    def new_request(self, method, params):
        request_id = self.next_request_id
        self.next_request_id += 1
        self.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        return request_id

    def start(self):
        command = [self.args.codex_cmd, "app-server"]
        try:
            self.process = subprocess.Popen(
                command,
                cwd=str(self.cwd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=None,
                text=True,
                encoding="utf-8",
                bufsize=1,
                env={**os.environ, "DOTFILES_AUTOSYNC_SKIP": "1"},
            )
        except OSError:
            raise AppServerFailure("could not start the configured Codex command")

        def read_server_messages():
            try:
                for line in self.process.stdout:
                    self.incoming.put(line)
            finally:
                self.incoming.put(None)

        threading.Thread(target=read_server_messages, daemon=True).start()

    def request(self, method, params):
        request_id = self.new_request(method, params)
        deadline = time.monotonic() + HANDSHAKE_TIMEOUT_SECONDS
        while request_id not in self.responses:
            self.check_interrupt()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AppServerFailure(f"timed out waiting for {method} response")
            self.receive_one(min(0.25, remaining))
        response = self.responses.pop(request_id)
        if "error" in response:
            code = response.get("error", {}).get("code", "unknown")
            raise AppServerFailure(f"app-server rejected {method} (JSON-RPC error {code})")
        return response.get("result", {})

    def receive_one(self, timeout):
        try:
            line = self.incoming.get(timeout=timeout)
        except queue.Empty:
            return
        if line is None:
            status = self.process.poll()
            raise AppServerFailure(f"app-server exited before completing the turn (status {status})")
        try:
            message = json.loads(line)
        except (json.JSONDecodeError, UnicodeError):
            raise AppServerFailure("app-server emitted an invalid JSON-RPC frame")
        if not isinstance(message, dict):
            raise AppServerFailure("app-server emitted a non-object JSON-RPC frame")

        self.write_event(message)
        if "method" in message:
            self.handle_server_method(message)
        elif "id" in message:
            self.responses[message["id"]] = message
        else:
            raise AppServerFailure("app-server emitted an unrecognized JSON-RPC frame")
        self.check_interrupt()

    def handle_server_method(self, message):
        method = message.get("method")
        params = message.get("params") or {}
        if "id" in message:
            self.refuse_server_request(message, method)
            return
        if method == "thread/started":
            thread = params.get("thread") or {}
            self.set_thread_id(thread.get("id"))
        elif method == "turn/started":
            self.set_thread_id(params.get("threadId"))
            turn = params.get("turn") or {}
            self.set_turn_id(turn.get("id"))
        elif method == "item/completed":
            item = params.get("item") or {}
            self.capture_agent_message(item)
        elif method == "turn/completed":
            self.set_thread_id(params.get("threadId"))
            turn = params.get("turn") or {}
            self.set_turn_id(turn.get("id"))
            self.capture_turn_messages(turn.get("items") or [])
            self.turn_status = turn.get("status")

    def refuse_server_request(self, request, method):
        result, reason = refusal_for(method)
        response = {
            "jsonrpc": "2.0",
            "id": request["id"],
        }
        if result is None:
            error = {
                "code": INTERRUPT_RESPONSE_CODE,
                "message": "Request refused by noninteractive Codex runner.",
            }
            response["error"] = error
            audit = {"type": "server_request_refused", "method": method, "id": request["id"],
                     "error": error}
        else:
            response["result"] = result
            audit = {"type": "server_request_refused", "method": method, "id": request["id"],
                     "result": result}
        self.write_event(audit)
        print(f"app-server request refused: {method}: {reason}", file=sys.stderr, flush=True)
        self.send(response)

    def set_thread_id(self, thread_id):
        if isinstance(thread_id, str) and thread_id:
            self.thread_id = thread_id
            if not self.thread_event_written:
                self.write_event({"type": "thread.started", "thread_id": thread_id})
                self.thread_event_written = True

    def set_turn_id(self, turn_id):
        if isinstance(turn_id, str) and turn_id:
            self.turn_id = turn_id
            self.check_interrupt()

    def capture_agent_message(self, item):
        if item.get("type") != "agentMessage" or not isinstance(item.get("text"), str):
            return
        text = item["text"]
        if item.get("phase") in (None, "final_answer"):
            self.final_message = text

    def capture_turn_messages(self, items):
        for item in items:
            if isinstance(item, dict):
                self.capture_agent_message(item)

    def check_interrupt(self):
        if self.signals.number is None:
            return
        if self.signals.time is not None and time.monotonic() - self.signals.time >= INTERRUPT_GRACE_SECONDS:
            self.terminate_child()
            raise AppServerFailure("interrupted")
        if self.turn_started and self.turn_id and not self.interrupt_sent:
            self.interrupt_response_id = self.new_request(
                "turn/interrupt",
                {"threadId": self.thread_id, "turnId": self.turn_id},
            )
            self.interrupt_sent = True

    def wait_for_turn(self):
        while self.turn_status not in ("completed", "interrupted", "failed"):
            self.check_interrupt()
            self.receive_one(0.25)
        if self.signals.number is not None:
            return 130
        if self.turn_status == "completed":
            return 0
        print(f"app-server turn ended with status {self.turn_status}", file=sys.stderr, flush=True)
        return 1

    def close_child(self):
        if self.process is None:
            return
        try:
            if self.process.stdin and not self.process.stdin.closed:
                self.process.stdin.close()
        except OSError:
            pass
        if self.process.poll() is None:
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.terminate_child()

    def terminate_child(self):
        if self.process is None or self.process.poll() is not None:
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        except OSError:
            pass

    def run(self):
        try:
            if self.signals.number is not None:
                raise AppServerFailure("interrupted")
            self.start()
            if self.signals.number is not None:
                raise AppServerFailure("interrupted")
            self.request("initialize", {
                "clientInfo": {
                    "name": "codex-runner",
                    "title": "Codex runner",
                    "version": "1",
                }
            })
            self.send({"jsonrpc": "2.0", "method": "initialized"})

            thread_params = {
                "cwd": str(self.cwd),
                "model": self.args.model,
                "approvalPolicy": "never",
            }
            if self.args.sandbox is not None:
                thread_params["sandbox"] = self.args.sandbox
            if self.args.thread_id:
                thread_params["threadId"] = self.args.thread_id
                thread_result = self.request("thread/resume", thread_params)
            else:
                thread_result = self.request("thread/start", thread_params)
            thread = thread_result.get("thread") or {}
            self.set_thread_id(thread.get("id") or self.args.thread_id)
            if not self.thread_id:
                raise AppServerFailure("app-server did not return a thread id")
            if self.signals.number is not None:
                raise AppServerFailure("interrupted")

            self.turn_started = True
            turn_result = self.request("turn/start", {
                "threadId": self.thread_id,
                "input": [{"type": "text", "text": self.prompt}],
                "effort": self.args.effort,
            })
            turn = turn_result.get("turn") or {}
            self.set_turn_id(turn.get("id"))
            if not self.turn_id and self.turn_status not in ("completed", "interrupted", "failed"):
                raise AppServerFailure("app-server did not return a turn id")

            status = self.wait_for_turn()
            final_message = self.final_message
            if final_message is not None:
                self.last_stream.write(final_message)
                self.last_stream.flush()
            return status
        except AppServerFailure as exc:
            if str(exc) != "interrupted":
                print(f"app-server helper failed: {exc}", file=sys.stderr, flush=True)
            if self.signals.number is not None:
                self.terminate_child()
                return 130
            self.terminate_child()
            return 1
        except Exception as exc:
            print(f"app-server helper failed: {type(exc).__name__}", file=sys.stderr, flush=True)
            self.terminate_child()
            return 130 if self.signals.number is not None else 1
        finally:
            if self.signals.number is not None and self.process and self.process.poll() is None:
                self.terminate_child()
            else:
                self.close_child()


def main():
    signals = RunSignals()
    signals.install()
    args = None
    last_stream = events_stream = None
    status = 125
    try:
        args = parse_args()
        os.umask(0o077)
        started_epoch = int(time.time())
        done_file = Path(args.done_file)
        if done_file.exists() or done_file.is_symlink():
            raise AppServerFailure(f"refusing to overwrite an existing output: {done_file}")
        cwd = Path(args.cwd).resolve(strict=True)
        if not cwd.is_dir():
            raise AppServerFailure("--cwd must be a directory")
        with Path(args.state_file).open("x", encoding="utf-8") as state_stream:
            state_stream.write(
                f"START_EPOCH={started_epoch}\n"
                f"OBSERVED_CWD={cwd}\n"
                f"REQUESTED_MODEL={args.model}\n"
                f"REQUESTED_EFFORT={args.effort}\n"
                f"REQUESTED_SANDBOX={args.sandbox or 'user-config'}\n"
            )
        status = 2
        cwd, prompt, out_last, last_stream, events_stream = create_private_outputs(args)
        client = AppServerClient(args, cwd, prompt, out_last, last_stream, events_stream, signals)
        status = client.run()
    except (OSError, AppServerFailure) as exc:
        print(f"app-server helper refused to start: {exc}", file=sys.stderr)
    except Exception as exc:
        print(f"app-server helper failed: {type(exc).__name__}", file=sys.stderr)
        status = 1
    finally:
        try:
            for stream in (last_stream, events_stream):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError as exc:
                        print(f"app-server helper could not close output: {exc}", file=sys.stderr)
                        status = 125
            if signals.number is not None:
                status = 130
            if args is not None:
                try:
                    with Path(args.done_file).open("x", encoding="utf-8") as done_stream:
                        done_stream.write(f"EXIT={status}\n")
                except OSError as exc:
                    print(f"app-server helper could not write completion: {exc}", file=sys.stderr)
                    status = 125
        finally:
            signals.restore()
    return status


if __name__ == "__main__":
    raise SystemExit(main())
