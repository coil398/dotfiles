#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONDONTWRITEBYTECODE=1 python3 - "${SCRIPT_DIR}/../.agents/skills/codex/scripts/codex-app-run.py" <<'PY'
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


HELPER = Path(sys.argv[1]).resolve()
sys.argv = [sys.argv[0]]
if not HELPER.is_file():
    print(f"BLOCKED: app-server helper is unavailable: {HELPER}", file=sys.stderr)
    raise SystemExit(2)

FAKE_SERVER = r'''#!/usr/bin/env python3
import json
import os
import sys

mode = os.environ["APP_FAKE_MODE"]
trace_path = os.environ["APP_FAKE_TRACE"]
cwd = os.environ["APP_FAKE_CWD"]
thread_id = "thread-fixture"
turn_id = "turn-fixture"

def trace(message):
    with open(trace_path, "a", encoding="utf-8") as stream:
        stream.write(json.dumps(message, separators=(",", ":")) + "\n")

trace({"type": "argv", "argv": sys.argv[1:]})

def send(message):
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()

def receive():
    line = sys.stdin.readline()
    if not line:
        return None
    message = json.loads(line)
    trace(message)
    return message

def respond(message, result):
    send({"jsonrpc": "2.0", "id": message["id"], "result": result})

def completed(status):
    send({"jsonrpc": "2.0", "method": "item/completed", "params": {
        "threadId": thread_id,
        "turnId": turn_id,
        "completedAtMs": 1,
        "item": {"id": "message-fixture", "type": "agentMessage",
                 "phase": "final_answer", "text": "fixture final answer"}
    }})
    send({"jsonrpc": "2.0", "method": "turn/completed", "params": {
        "threadId": thread_id,
        "turn": {"id": turn_id, "status": status, "items": [
            {"id": "message-fixture", "type": "agentMessage",
             "phase": "final_answer", "text": "fixture final answer"}
        ]}
    }})

while True:
    message = receive()
    if message is None:
        break
    method = message.get("method")
    if method == "initialize":
        respond(message, {
            "codexHome": "/tmp/codex-home-fixture",
            "platformFamily": "unix",
            "platformOs": "macos",
            "userAgent": "codex-cli-fixture",
        })
    elif method == "initialized":
        continue
    elif method in ("thread/start", "thread/resume"):
        respond(message, {
            "approvalPolicy": "never",
            "approvalsReviewer": "user",
            "cwd": cwd,
            "model": "fixture-model",
            "modelProvider": "openai",
            "sandbox": {"type": "readOnly"},
            "thread": {
                "cliVersion": "0.162.1",
                "createdAt": 1,
                "cwd": cwd,
                "ephemeral": False,
                "id": thread_id,
                "modelProvider": "openai",
                "preview": "fixture prompt",
                "projectId": None,
                "sessionId": "session-fixture",
                "source": "appServer",
                "status": {"type": "idle"},
                "turns": [],
                "updatedAt": 1,
            },
        })
    elif method == "turn/start":
        if mode == "interrupt":
            send({"jsonrpc": "2.0", "method": "turn/started", "params": {
                "threadId": thread_id,
                "turn": {"id": turn_id, "status": "inProgress", "items": []}
            }})
        respond(message, {"turn": {"id": turn_id, "status": "inProgress", "items": []}})
        if mode == "interrupt":
            while True:
                incoming = receive()
                if incoming is None:
                    break
                if incoming.get("method") == "turn/interrupt":
                    respond(incoming, {})
                    completed("interrupted")
                    break
            continue
        if mode == "refusal":
            requests = [
                ("item/commandExecution/requestApproval", {"itemId": "item-fixture", "startedAtMs": 1, "threadId": thread_id, "turnId": turn_id}, {"decision": "decline"}),
                ("item/fileChange/requestApproval", {"itemId": "item-fixture", "startedAtMs": 1, "threadId": thread_id, "turnId": turn_id}, {"decision": "decline"}),
                ("item/tool/requestUserInput", {"isBlocking": True, "itemId": "item-fixture", "questions": [], "threadId": thread_id, "turnId": turn_id}, None),
                ("mcpServer/elicitation/request", {"serverName": "fixture-mcp", "threadId": thread_id}, {"action": "cancel"}),
                ("item/permissions/requestApproval", {"cwd": "/tmp", "itemId": "item-fixture", "permissions": {}, "startedAtMs": 1, "threadId": thread_id, "turnId": turn_id}, {"permissions": {}}),
                ("item/tool/call", {"arguments": {}, "callId": "call-fixture", "threadId": thread_id, "tool": "fixture-tool", "turnId": turn_id}, {"contentItems": [], "success": False}),
                ("account/chatgptAuthTokens/refresh", {"reason": "unauthorized"}, None),
                ("attestation/generate", {}, None),
                ("applyPatchApproval", {"callId": "call-fixture", "conversationId": thread_id, "fileChanges": {}}, {"decision": {"denied": {"rejection": "Noninteractive runner does not approve requests."}}}),
                ("execCommandApproval", {"callId": "call-fixture", "command": ["true"], "conversationId": thread_id, "cwd": "/tmp", "parsedCmd": []}, {"decision": {"denied": {"rejection": "Noninteractive runner does not approve requests."}}}),
            ]
            for index, (request_method, request_params, expected) in enumerate(requests, 100):
                send({"jsonrpc": "2.0", "id": index, "method": request_method, "params": request_params})
                answer = receive()
                if expected is None:
                    assert answer is not None and "error" in answer
                    assert answer["error"]["code"] == -32800
                else:
                    assert answer is not None and answer.get("result") == expected
        status = "failed" if mode == "failure" else "completed"
        completed(status)
        continue
    elif method == "turn/interrupt":
        respond(message, {})
        completed("interrupted")
    else:
        raise SystemExit("fake server received an unexpected method")
'''


class CodexAppRunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="codex-app-run-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.prompt = self.base / "prompt.md"
        self.prompt.write_text("fixture prompt\n", encoding="utf-8")
        self.fake = self.base / "fake-codex"
        self.fake.write_text(FAKE_SERVER, encoding="utf-8")
        self.fake.chmod(0o755)
        self.cwd = self.base / "workspace"
        self.cwd.mkdir()
        self.trace = self.base / "fake-server-trace.jsonl"

    def invoke(self, mode, thread_id=None, wait=True, sandbox="read-only"):
        last = self.base / "last.md"
        events = self.base / "events.jsonl"
        env = dict(os.environ, APP_FAKE_MODE=mode, APP_FAKE_TRACE=str(self.trace),
                   APP_FAKE_CWD=str(self.cwd.resolve()))
        command = [
            sys.executable, str(HELPER),
            "--codex-cmd", str(self.fake),
            "--prompt-file", str(self.prompt),
            "--model", "fixture-model",
            "--effort", "medium",
            "--sandbox", sandbox,
            "--cwd", str(self.cwd),
            "--out-last", str(last),
            "--out-events", str(events),
        ]
        if thread_id:
            command.extend(["--thread-id", thread_id])
        process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        if wait:
            stdout, stderr = process.communicate(timeout=15)
            return process.returncode, stdout, stderr, last, events
        return process, last, events

    def traced_messages(self):
        if not self.trace.exists():
            return []
        return [json.loads(line) for line in self.trace.read_text(encoding="utf-8").splitlines()]

    def test_new_thread_writes_final_response_and_jsonl_events(self):
        code, _stdout, stderr, last, events = self.invoke("normal")
        self.assertEqual(code, 0, stderr)
        self.assertEqual(last.read_text(encoding="utf-8"), "fixture final answer")
        sent = self.traced_messages()
        self.assertEqual([m["method"] for m in sent if "method" in m],
                         ["initialize", "initialized", "thread/start", "turn/start"])
        thread_start = next(m for m in sent if m.get("method") == "thread/start")
        self.assertEqual(thread_start["params"], {
            "cwd": str(self.cwd.resolve()), "model": "fixture-model",
            "approvalPolicy": "never", "sandbox": "read-only",
        })
        argv = next(m["argv"] for m in sent if m.get("type") == "argv")
        self.assertEqual(argv, ["app-server"])
        turn_start = next(m for m in sent if m.get("method") == "turn/start")
        self.assertEqual(turn_start["params"]["input"], [{"type": "text", "text": "fixture prompt\n"}])
        self.assertEqual(turn_start["params"]["effort"], "medium")
        lines = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
        self.assertIn({"type": "thread.started", "thread_id": "thread-fixture"}, lines)
        self.assertTrue(any(m.get("method") == "turn/completed" for m in lines))

    def test_resume_uses_thread_resume_with_explicit_settings(self):
        code, _stdout, stderr, _last, _events = self.invoke("normal", thread_id="thread-existing")
        self.assertEqual(code, 0, stderr)
        sent = self.traced_messages()
        self.assertFalse(any(m.get("method") == "thread/start" for m in sent))
        resume = next(m for m in sent if m.get("method") == "thread/resume")
        self.assertEqual(resume["params"], {
            "threadId": "thread-existing", "cwd": str(self.cwd.resolve()),
            "model": "fixture-model", "approvalPolicy": "never", "sandbox": "read-only",
        })

    def test_workspace_write_adds_only_canonical_agents_root(self):
        agents = self.cwd / ".agents"
        agents.mkdir()
        code, _stdout, stderr, _last, _events = self.invoke(
            "normal", sandbox="workspace-write")
        self.assertEqual(code, 0, stderr)
        argv = next(m["argv"] for m in self.traced_messages() if m.get("type") == "argv")
        self.assertEqual(argv, [
            "app-server", "-c",
            f"sandbox_workspace_write.writable_roots=[{json.dumps(str(agents.resolve()))}]",
        ])
        thread_start = next(m for m in self.traced_messages()
                            if m.get("method") == "thread/start")
        self.assertEqual(thread_start["params"]["sandbox"], "workspace-write")

    def test_failed_turn_exits_nonzero(self):
        code, _stdout, stderr, _last, _events = self.invoke("failure")
        self.assertNotEqual(code, 0)
        self.assertIn("failed", stderr)

    def test_server_requests_are_declined_cancelled_or_refused(self):
        code, _stdout, stderr, _last, _events = self.invoke("refusal")
        self.assertEqual(code, 0, stderr)
        answers = [m for m in self.traced_messages() if "id" in m and "method" not in m]
        self.assertEqual(len(answers), 10)
        self.assertTrue(all(("result" in answer) or (answer.get("error", {}).get("code") == -32800)
                            for answer in answers))

    def test_sigterm_requests_turn_interrupt_and_exits_130(self):
        process, _last, events = self.invoke("interrupt", wait=False)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if events.exists() and '"method":"turn/started"' in events.read_text(encoding="utf-8"):
                break
            if process.poll() is not None:
                break
            time.sleep(0.02)
        self.assertIsNone(process.poll(), "helper exited before receiving SIGTERM")
        os.kill(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=14)
        self.assertEqual(process.returncode, 130, stderr or stdout)
        sent = self.traced_messages()
        interrupt = next(m for m in sent if m.get("method") == "turn/interrupt")
        self.assertEqual(interrupt["params"], {
            "threadId": "thread-fixture", "turnId": "turn-fixture",
        })

    def test_detached_shell_forwards_sigterm_to_helper(self):
        last = self.base / "wrapped-last.md"
        events = self.base / "wrapped-events.jsonl"
        env = dict(os.environ, APP_FAKE_MODE="interrupt",
                   APP_FAKE_TRACE=str(self.trace), APP_FAKE_CWD=str(self.cwd))
        helper_args = [
            "--codex-cmd", str(self.fake),
            "--prompt-file", str(self.prompt),
            "--model", "fixture-model",
            "--effort", "medium",
            "--sandbox", "read-only",
            "--cwd", str(self.cwd),
            "--out-last", str(last),
            "--out-events", str(events),
        ]
        wrapper = r'''
helper=$1
shift
python3 "$helper" "$@" &
helper_pid=$!
forward_signal() {
  trap - TERM INT
  kill -TERM "$helper_pid" 2>/dev/null || true
  wait "$helper_pid"
  child_status=$?
  exit "$child_status"
}
trap forward_signal TERM INT
wait "$helper_pid"
exit "$?"
'''
        process = subprocess.Popen(
            ["bash", "-c", wrapper, "_", str(HELPER), *helper_args],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if events.exists() and '"method":"turn/started"' in events.read_text(encoding="utf-8"):
                break
            if process.poll() is not None:
                break
            time.sleep(0.02)
        self.assertIsNone(process.poll(), "detached shell exited before receiving SIGTERM")
        os.kill(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=14)
        self.assertEqual(process.returncode, 130, stderr or stdout)
        interrupt = next(m for m in self.traced_messages()
                         if m.get("method") == "turn/interrupt")
        self.assertEqual(interrupt["params"], {
            "threadId": "thread-fixture", "turnId": "turn-fixture",
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
PY
