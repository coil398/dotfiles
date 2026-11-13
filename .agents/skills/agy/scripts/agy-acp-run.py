#!/usr/bin/env python3
"""Run one agy ACP turn for agy-run.py and record its evidence.

The helper starts ``agy acp`` with the target directory as its process cwd,
opens or loads one session, sets the requested model and mode, sends one
prompt, and writes events, the final response, and key=value state.  Permission
requests from agy are always rejected; the caller judges the recorded result.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_TURN_NOT_ENDED = 3
EXIT_PROTOCOL = 4
SETUP_TIMEOUT_SECONDS = 120
SESSION_ID_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
CREDENTIAL_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password|bearer)\S*")


def timestamp_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def safe_value(value) -> str:
    text = str(value)
    text = "".join(" " if ch in "\r\n\t" or ord(ch) < 32 else ch for ch in text)
    text = CREDENTIAL_RE.sub("[redacted]", text)
    if len(text) > 120:
        text = text[:117] + "..."
    return text.replace(" ", "_") if text else '""'


class RunLog:
    """Append fixed events as `<time> run_id=<id> event=<name> key=value`."""

    def __init__(self, path: Path, run_id: str):
        self.path = path
        self.run_id = run_id
        self.available = True

    def event(self, name: str, **fields) -> None:
        if not self.available:
            return
        parts = [timestamp_now(), f"run_id={self.run_id}", f"event={name}"]
        parts.extend(f"{key}={safe_value(value)}" for key, value in fields.items())
        try:
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(" ".join(parts) + "\n")
        except OSError as exc:
            self.available = False
            print(f"agy helper: run.log append failed: {exc}", file=sys.stderr)


class State:
    """Append-only key=value state; later lines override earlier ones."""

    def __init__(self, path: Path):
        self.path = path

    def set(self, **values) -> None:
        with self.path.open("a", encoding="utf-8") as stream:
            for key, value in values.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                text = str(value).replace("\n", " ")
                stream.write(f"{key}={text}\n")


def create_autosync_hold() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    holds_dir = Path(state_home) / "dotfiles-autosync" / "holds"
    holds_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    hold_path = holds_dir / f"agy-acp-run-{os.getpid()}-{time.time_ns()}.hold"
    pending_path = holds_dir / f".{hold_path.name}.pending"
    fd = os.open(pending_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(f"{os.getpid()}\n")
    os.replace(pending_path, hold_path)
    return hold_path


class AcpFailure(Exception):
    pass


class AcpClient:
    def __init__(self, agy_cmd: str, cwd: str, events_path: Path, log: RunLog):
        env = dict(os.environ)
        env.update({"DOTFILES_AUTOSYNC_SKIP": "1", "JEV_HOOKS_MODE": "off"})
        self.proc = subprocess.Popen(
            [agy_cmd, "acp"], cwd=cwd, env=env, text=True, encoding="utf-8",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr,
        )
        self.log = log
        self.events = events_path.open("a", encoding="utf-8")
        self.write_lock = threading.Lock()
        self.pending: dict[int, queue.Queue] = {}
        self.next_id = 0
        self.closed = threading.Event()
        self.prompt_sent = False
        self.chunks: list[str] = []
        self.observed: dict[str, str] = {}
        self.tool_calls: dict[str, str] = {}
        self.permission_requests: list[dict] = []
        self.unknown_requests: list[str] = []
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()

    def _send(self, message: dict) -> None:
        line = json.dumps(message, ensure_ascii=False)
        with self.write_lock:
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()

    def call(self, method: str, params: dict, timeout: float | None):
        with self.write_lock:
            self.next_id += 1
            request_id = self.next_id
            reply: queue.Queue = queue.Queue(maxsize=1)
            self.pending[request_id] = reply
        started = time.monotonic()
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = None if timeout is None else started + timeout
        while True:
            wait = 1.0 if deadline is None else max(0.0, min(1.0, deadline - time.monotonic()))
            try:
                message = reply.get(timeout=wait)
                break
            except queue.Empty:
                if self.closed.is_set() and reply.empty():
                    raise AcpFailure(f"agy acp closed before responding to {method}")
                if deadline is not None and time.monotonic() >= deadline:
                    raise AcpFailure(f"{method} timed out after {timeout}s")
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if "error" in message:
            error = message["error"]
            self.log.event("rpc_error", method=method, code=error.get("code"),
                           message=error.get("message"), elapsed_ms=elapsed_ms)
            raise AcpFailure(f"{method} failed: {error.get('code')} {error.get('message')}")
        self.log.event("rpc_ok", method=method, elapsed_ms=elapsed_ms)
        result = message.get("result")
        if not isinstance(result, dict):
            raise AcpFailure(f"{method} returned a non-object result")
        return result

    def _read_loop(self) -> None:
        try:
            for line in self.proc.stdout:
                self.events.write(line if line.endswith("\n") else line + "\n")
                self.events.flush()
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    print("agy helper: non-JSON line from agy acp", file=sys.stderr)
                    continue
                if not isinstance(message, dict):
                    continue
                if "method" in message and "id" in message:
                    self._answer_request(message)
                elif "method" in message:
                    self._notification(message)
                elif "id" in message:
                    reply = self.pending.pop(message["id"], None)
                    if reply is not None:
                        reply.put(message)
        finally:
            self.closed.set()

    def _answer_request(self, message: dict) -> None:
        method = message.get("method")
        params = message.get("params") or {}
        if method == "session/request_permission":
            tool = params.get("toolCall") or {}
            options = params.get("options") or []
            reject = next((o for o in options if o.get("kind") == "reject_once"), None)
            record = {"tool": tool.get("name") or tool.get("title") or "unknown",
                      "kind": tool.get("kind") or "unknown"}
            self.permission_requests.append(record)
            self.log.event("permission_rejected", tool=record["tool"], kind=record["kind"],
                           reject_option=bool(reject))
            if reject is not None:
                result = {"outcome": {"outcome": "selected", "optionId": reject["optionId"]}}
            else:
                result = {"outcome": {"outcome": "cancelled"}}
            self._send({"jsonrpc": "2.0", "id": message["id"], "result": result})
            return
        self.unknown_requests.append(str(method))
        self.log.event("unknown_request_refused", method=method)
        self._send({"jsonrpc": "2.0", "id": message["id"],
                    "error": {"code": -32601, "message": f"method not supported by runner: {method}"}})

    def _notification(self, message: dict) -> None:
        if message.get("method") != "session/update":
            return
        update = (message.get("params") or {}).get("update") or {}
        kind = update.get("sessionUpdate")
        if kind == "config_option_update":
            options = update.get("configOptions") or []
            for option in options if isinstance(options, list) else []:
                if option.get("id") in ("model", "thought_level", "mode"):
                    self.observed[option["id"]] = str(option.get("currentValue"))
            return
        if not self.prompt_sent:
            return
        if kind == "agent_message_chunk":
            content = update.get("content") or {}
            if content.get("type", "text") == "text":
                self.chunks.append(content.get("text", ""))
        elif kind in ("tool_call", "tool_call_update"):
            call_id = update.get("toolCallId")
            status = update.get("status")
            if call_id and status:
                self.tool_calls[call_id] = status

    def close(self) -> int | None:
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        try:
            return self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            try:
                return self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                return self.proc.wait()
        finally:
            self.reader.join(timeout=5)
            self.events.close()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agy-cmd", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--mode", required=True, choices=("plan", "auto"))
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--final-response", required=True, type=Path)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--run-log", required=True, type=Path)
    parser.add_argument("--helper-done", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--resume-session-id")
    return parser.parse_args(argv)


def run(args, state: State, log: RunLog) -> int:
    prompt = args.prompt_file.read_text(encoding="utf-8")
    client = AcpClient(args.agy_cmd, args.cwd, args.events, log)
    exit_code = EXIT_PROTOCOL
    try:
        init = client.call("initialize", {
            "protocolVersion": 1,
            "clientCapabilities": {},
            "clientInfo": {"name": "agy-run", "version": "1"},
        }, SETUP_TIMEOUT_SECONDS)
        state.set(AGENT_VERSION=(init.get("agentInfo") or {}).get("version", "unavailable"))
        session_params = {"cwd": args.cwd, "mcpServers": []}
        if args.resume_session_id:
            session_params["sessionId"] = args.resume_session_id
            client.call("session/load", session_params, SETUP_TIMEOUT_SECONDS)
            session_id = args.resume_session_id
        else:
            result = client.call("session/new", session_params, SETUP_TIMEOUT_SECONDS)
            session_id = result.get("sessionId")
            if not isinstance(session_id, str) or not SESSION_ID_RE.fullmatch(session_id):
                raise AcpFailure("session/new returned no usable sessionId")
        state.set(SESSION_ID=session_id, SESSION_ACTION="load" if args.resume_session_id else "new")
        log.event("session_ready", session_id=session_id,
                  action="load" if args.resume_session_id else "new")
        client.call("session/set_model", {"sessionId": session_id, "modelId": args.model},
                    SETUP_TIMEOUT_SECONDS)
        client.call("session/set_mode", {"sessionId": session_id, "modeId": args.mode},
                    SETUP_TIMEOUT_SECONDS)
        client.prompt_sent = True
        state.set(TURN_STARTED_AT=timestamp_now())
        log.event("turn_start", session_id=session_id, model=args.model, mode=args.mode)
        result = client.call("session/prompt", {
            "sessionId": session_id,
            "prompt": [{"type": "text", "text": prompt}],
        }, None)
        stop_reason = result.get("stopReason", "unavailable")
        state.set(STOP_REASON=stop_reason, USAGE=result.get("usage") or {})
        exit_code = EXIT_OK if stop_reason == "end_turn" else EXIT_TURN_NOT_ENDED
    except (AcpFailure, OSError) as exc:
        state.set(FAILURE=str(exc))
        log.event("helper_failure", reason=str(exc))
        print(f"agy helper: {exc}", file=sys.stderr)
    finally:
        agy_exit = client.close()
        final_text = "".join(client.chunks)
        args.final_response.write_text(final_text, encoding="utf-8")
        failed = sum(1 for status in client.tool_calls.values() if status == "failed")
        state.set(
            AGY_EXIT=agy_exit,
            OBSERVED_MODEL=client.observed.get("model", "unavailable"),
            OBSERVED_THOUGHT_LEVEL=client.observed.get("thought_level", "unavailable"),
            OBSERVED_MODE=client.observed.get("mode", "unavailable"),
            TOOL_CALL_COUNT=len(client.tool_calls),
            TOOL_CALL_FAILED_COUNT=failed,
            PERMISSION_REJECTED=client.permission_requests,
            UNKNOWN_REQUESTS=client.unknown_requests,
            FINAL_RESPONSE_CHARS=len(final_text),
        )
        log.event("turn_end", exit=exit_code, agy_exit=agy_exit,
                  tool_calls=len(client.tool_calls), tool_failed=failed,
                  permission_rejected=len(client.permission_requests),
                  final_response_chars=len(final_text),
                  observed_model=client.observed.get("model", "unavailable"),
                  observed_thought_level=client.observed.get("thought_level", "unavailable"),
                  observed_mode=client.observed.get("mode", "unavailable"))
    return exit_code


def stop_on_signal(number, _frame):
    for other in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(other, signal.SIG_IGN)
    raise AcpFailure(f"helper received {signal.Signals(number).name}")


def main(argv=None) -> int:
    args = parse_args(argv)
    os.umask(0o077)
    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(number, stop_on_signal)
    log = RunLog(args.run_log, args.run_id)
    state = State(args.state)
    started = time.monotonic()
    state.set(HELPER_STARTED_AT=timestamp_now(), HELPER_PID=os.getpid())
    log.event("helper_start", cwd=args.cwd, model=args.model, mode=args.mode,
              resume=bool(args.resume_session_id))
    hold_path = None
    exit_code = EXIT_PROTOCOL
    try:
        hold_path = create_autosync_hold()
        exit_code = run(args, state, log)
    except (AcpFailure, OSError) as exc:
        state.set(FAILURE=f"helper setup failed: {exc}")
        log.event("helper_failure", reason=str(exc))
        print(f"agy helper: setup failed: {exc}", file=sys.stderr)
    finally:
        if hold_path is not None:
            try:
                os.unlink(hold_path)
            except OSError as exc:
                print(f"agy helper: could not remove autosync hold: {exc}", file=sys.stderr)
        elapsed = round(time.monotonic() - started, 3)
        state.set(HELPER_ENDED_AT=timestamp_now(), HELPER_ELAPSED_SECONDS=elapsed,
                  HELPER_EXIT=exit_code, RUN_LOG_AVAILABLE=log.available)
        log.event("helper_end", exit=exit_code, elapsed_s=elapsed)
        fd = os.open(args.helper_done, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(f"EXIT={exit_code}\n")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
