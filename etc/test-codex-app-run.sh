#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONDONTWRITEBYTECODE=1 python3 - "${SCRIPT_DIR}/../.agents/skills/codex/scripts/codex-app-run.py" <<'PY'
import errno
import json
import os
from pathlib import Path
import signal
import shlex
import stat
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

trace({"type": "argv", "argv": sys.argv[1:],
       "DOTFILES_AUTOSYNC_SKIP": os.environ.get("DOTFILES_AUTOSYNC_SKIP")})

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
    phase = "commentary" if mode == "partial_failure" else "final_answer"
    message_text = "fixture partial answer" if mode == "partial_failure" else "fixture final answer"
    send({"jsonrpc": "2.0", "method": "item/completed", "params": {
        "threadId": thread_id,
        "turnId": turn_id,
        "completedAtMs": 1,
        "item": {"id": "message-fixture", "type": "agentMessage",
                 "phase": phase, "text": message_text}
    }})
    send({"jsonrpc": "2.0", "method": "turn/completed", "params": {
        "threadId": thread_id,
        "turn": {"id": turn_id, "status": status, "items": [
            {"id": "message-fixture", "type": "agentMessage",
             "phase": phase, "text": message_text}
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
        status = "failed" if mode in ("failure", "partial_failure") else "completed"
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
        self.started_epoch = int(time.time())
        self.temp = tempfile.TemporaryDirectory(prefix="codex-app-run-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.prompt = self.base / "prompt.md"
        self.prompt.write_text("fixture prompt\n", encoding="utf-8")
        self.fake = self.base / "fake-codex"
        self.fake.write_text(FAKE_SERVER, encoding="utf-8")
        self.fake.chmod(0o755)
        self.state = self.base / "state.txt"
        self.done = self.base / "done"
        self.child_pid = self.base / "child-pid"
        self.cwd = self.base / "workspace"
        self.cwd.mkdir()
        self.trace = self.base / "fake-server-trace.jsonl"

    def invoke(self, mode, thread_id=None, wait=True, sandbox="read-only",
               signal_timing=None, signum=signal.SIGTERM, detached=False):
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
            "--cwd", str(self.cwd),
            "--out-last", str(last),
            "--out-events", str(events),
            "--state-file", str(self.state),
            "--done-file", str(self.done),
        ]
        if sandbox is not None:
            command.extend(["--sandbox", sandbox])
        if thread_id:
            command.extend(["--thread-id", thread_id])
        if signal_timing:
            harness = self.base / "signal-harness.py"
            harness.write_text('''import importlib.util
import os
from pathlib import Path
import signal
import sys

helper, timing, signum, child_pid = sys.argv[1:5]
sys.argv = [helper, *sys.argv[5:]]
spec = importlib.util.spec_from_file_location("codex_app_run", helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if timing == "before_launch":
    original = module.parse_args
    def parse_args():
        args = original()
        os.kill(os.getpid(), int(signum))
        return args
    module.parse_args = parse_args
elif timing == "before_pid":
    original = module.subprocess.Popen
    def popen(*args, **kwargs):
        process = original(*args, **kwargs)
        Path(child_pid).write_text(str(process.pid), encoding="utf-8")
        os.kill(os.getpid(), int(signum))
        return process
    module.subprocess.Popen = popen

raise SystemExit(module.main())
''', encoding="utf-8")
            command = [sys.executable, str(harness), str(HELPER), signal_timing,
                       str(signum), str(self.child_pid), *command[2:]]
        if detached:
            command.insert(0, "nohup")
        process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True,
                                   start_new_session=detached)
        self.addCleanup(self.reap_process, process)
        if wait:
            timeout = 5 if signal_timing == "before_launch" else 14 if signal_timing else 15
            stdout, stderr = process.communicate(timeout=timeout)
            self.assert_completion(process.returncode)
            return process.returncode, stdout, stderr, last, events
        return process, last, events

    def reap_process(self, process):
        if process.poll() is None:
            process.terminate()
            try:
                process.communicate(timeout=14)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=2)

    def assert_completion(self, code):
        self.assertEqual(self.done.read_text(encoding="utf-8"), f"EXIT={code}\n")
        self.assertEqual(stat.S_IMODE(self.done.stat().st_mode), 0o600)

    def assert_state(self, sandbox="read-only"):
        state = self.state.read_text(encoding="utf-8").splitlines()
        self.assertRegex(state[0], r"^START_EPOCH=[0-9]+$")
        start = int(state[0].split("=", 1)[1])
        self.assertLessEqual(start, time.time())
        self.assertGreaterEqual(start, self.started_epoch)
        self.assertEqual(state[1:], [
            f"OBSERVED_CWD={self.cwd.resolve()}", "REQUESTED_MODEL=fixture-model",
            "REQUESTED_EFFORT=medium", f"REQUESTED_SANDBOX={sandbox}",
        ])
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o600)

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
        startup = next(m for m in sent if m.get("type") == "argv")
        self.assertEqual(startup["argv"], ["app-server"])
        self.assertEqual(startup["DOTFILES_AUTOSYNC_SKIP"], "1")
        turn_start = next(m for m in sent if m.get("method") == "turn/start")
        self.assertEqual(turn_start["params"]["input"], [{"type": "text", "text": "fixture prompt\n"}])
        self.assertEqual(turn_start["params"]["effort"], "medium")
        lines = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
        self.assertIn({"type": "thread.started", "thread_id": "thread-fixture"}, lines)
        self.assertTrue(any(m.get("method") == "turn/completed" for m in lines))
        self.assert_state()

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

    def test_unset_sandbox_uses_user_configuration_without_agents_override(self):
        agents = self.cwd / ".agents"
        agents.mkdir()
        code, _stdout, stderr, _last, _events = self.invoke(
            "normal", sandbox=None)
        self.assertEqual(code, 0, stderr)
        argv = next(m["argv"] for m in self.traced_messages() if m.get("type") == "argv")
        self.assertEqual(argv, ["app-server"])
        thread_start = next(m for m in self.traced_messages()
                            if m.get("method") == "thread/start")
        self.assertEqual(thread_start["params"], {
            "cwd": str(self.cwd.resolve()), "model": "fixture-model",
            "approvalPolicy": "never",
        })
        self.assert_state("user-config")

    def test_resume_omits_unspecified_sandbox(self):
        code, _stdout, stderr, _last, _events = self.invoke(
            "normal", thread_id="thread-existing", sandbox=None)
        self.assertEqual(code, 0, stderr)
        resume = next(m for m in self.traced_messages()
                      if m.get("method") == "thread/resume")
        self.assertEqual(resume["params"], {
            "threadId": "thread-existing", "cwd": str(self.cwd.resolve()),
            "model": "fixture-model", "approvalPolicy": "never",
        })

    def test_failed_turn_exits_nonzero(self):
        code, _stdout, stderr, last, _events = self.invoke("failure")
        self.assertNotEqual(code, 0)
        self.assertIn("failed", stderr)
        self.assertEqual(last.read_text(encoding="utf-8"), "fixture final answer")

    def test_partial_answer_is_not_written_after_failed_turn(self):
        code, _stdout, stderr, last, _events = self.invoke("partial_failure")
        self.assertNotEqual(code, 0)
        self.assertIn("failed", stderr)
        self.assertEqual(last.read_text(encoding="utf-8"), "")

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
        self.assert_completion(130)
        sent = self.traced_messages()
        interrupt = next(m for m in sent if m.get("method") == "turn/interrupt")
        self.assertEqual(interrupt["params"], {
            "threadId": "thread-fixture", "turnId": "turn-fixture",
        })

    def check_detached_interrupt(self, signum):
        process, _last, events = self.invoke("interrupt", wait=False, detached=True)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if events.exists() and '"method":"turn/started"' in events.read_text(encoding="utf-8"):
                break
            if process.poll() is not None:
                break
            time.sleep(0.02)
        self.assertTrue(events.exists() and '"method":"turn/started"' in
                        events.read_text(encoding="utf-8"), "turn did not start")
        self.assertIsNone(process.poll(), "detached helper exited before receiving signal")
        self.assertFalse(self.done.exists(), "completion was published while turn was running")
        self.assert_state()
        os.kill(process.pid, signum)
        stdout, stderr = process.communicate(timeout=14)
        self.assertEqual(process.returncode, 130, stderr or stdout)
        self.assert_completion(130)
        interrupt = next(m for m in self.traced_messages()
                         if m.get("method") == "turn/interrupt")
        self.assertEqual(interrupt["params"], {
            "threadId": "thread-fixture", "turnId": "turn-fixture",
        })

    def test_detached_helper_handles_sigterm(self):
        self.check_detached_interrupt(signal.SIGTERM)

    def test_detached_helper_handles_sigint(self):
        self.check_detached_interrupt(signal.SIGINT)

    def check_interrupt_before_pid_assignment(self, signum):
        code, _stdout, stderr, _last, _events = self.invoke(
            "interrupt", signal_timing="before_pid", signum=signum, detached=True)
        self.assertEqual(code, 130, stderr)
        self.assert_state()
        pid = int(self.child_pid.read_text(encoding="utf-8"))
        with self.assertRaises(ProcessLookupError) as raised:
            os.kill(pid, 0)
        self.assertEqual(raised.exception.errno, errno.ESRCH)
        self.assertFalse(any(m.get("method") == "initialize" for m in self.traced_messages()))

    def test_helper_reaps_child_after_sigterm_before_pid_assignment(self):
        self.check_interrupt_before_pid_assignment(signal.SIGTERM)

    def test_helper_reaps_child_after_sigint_before_pid_assignment(self):
        self.check_interrupt_before_pid_assignment(signal.SIGINT)

    def check_pending_interrupt(self, signum):
        code, _stdout, stderr, _last, _events = self.invoke(
            "normal", signal_timing="before_launch", signum=signum, detached=True)
        self.assertEqual(code, 130, stderr)
        self.assert_state()
        self.assertFalse(self.trace.exists(), "app-server launched after a signal was already pending")

    def test_helper_does_not_launch_app_server_after_pending_sigterm(self):
        self.check_pending_interrupt(signal.SIGTERM)

    def test_helper_does_not_launch_app_server_after_pending_sigint(self):
        self.check_pending_interrupt(signal.SIGINT)

    def test_empty_prompt_records_startup_failure(self):
        self.prompt.write_text("", encoding="utf-8")
        code, _stdout, stderr, _last, _events = self.invoke("normal")
        self.assertEqual(code, 2, stderr)
        self.assert_state()
        self.assertFalse(self.trace.exists())

    def test_missing_cwd_records_exit_125(self):
        self.cwd.rmdir()
        code, _stdout, stderr, _last, _events = self.invoke("normal")
        self.assertEqual(code, 125, stderr)
        self.assertFalse(self.trace.exists())

    def test_existing_state_is_preserved_and_records_exit_125(self):
        self.state.write_text("existing state\n", encoding="utf-8")
        code, _stdout, stderr, _last, _events = self.invoke("normal")
        self.assertEqual(code, 125, stderr)
        self.assertEqual(self.state.read_text(encoding="utf-8"), "existing state\n")
        self.assertFalse(self.trace.exists())

    def test_missing_codex_command_records_failure(self):
        self.fake.unlink()
        code, _stdout, stderr, _last, _events = self.invoke("normal")
        self.assertEqual(code, 1, stderr)
        self.assert_state()
        self.assertIn("could not start", stderr)
        self.assertFalse(self.trace.exists())

    def test_documented_launch_runs_on_system_bash_with_helper_pid(self):
        runner = HELPER.parent.parent / "references" / "runner.md"
        launch = runner.read_text(encoding="utf-8").split("helper_args=(", 1)[1]
        launch = "helper_args=(" + launch.split("```", 1)[0]
        pid_file = self.base / "pid"
        err_file = self.base / "err.txt"
        last = self.base / "last.md"
        events = self.base / "events.jsonl"
        variables = {
            "CODEX_APP_RUN": str(HELPER), "CODEX_CMD": str(self.fake),
            "PROMPT_FILE": str(self.prompt), "MODEL": "fixture-model", "EFFORT": "medium",
            "CWD": str(self.cwd), "SANDBOX": "read-only", "SESSION_ID": "",
            "OUT_LAST": str(last), "OUT_EVENTS": str(events), "OUT_ERR": str(err_file),
            "STATE_FILE": str(self.state), "DONE_FILE": str(self.done), "PID_FILE": str(pid_file),
        }
        launcher = self.base / "launch.sh"
        launcher.write_text("umask 077\n" + "\n".join(
            f"{name}={shlex.quote(value)}" for name, value in variables.items()) + "\n" + launch)
        env = dict(os.environ, APP_FAKE_MODE="interrupt", APP_FAKE_TRACE=str(self.trace),
                   APP_FAKE_CWD=str(self.cwd.resolve()))
        result = subprocess.run(["/bin/bash", str(launcher)], env=env,
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        pid = int(pid_file.read_text(encoding="utf-8"))
        self.addCleanup(self.stop_detached_helper, pid)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if events.exists() and '"method":"turn/started"' in events.read_text(encoding="utf-8"):
                break
            time.sleep(0.02)
        self.assertTrue(events.exists() and '"method":"turn/started"' in events.read_text(encoding="utf-8"))
        self.assert_state()
        self.assertFalse(self.done.exists())
        observed = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                                  capture_output=True, text=True, timeout=5)
        self.assertEqual(observed.returncode, 0, observed.stderr)
        self.assertIn(str(HELPER), observed.stdout)
        os.kill(pid, signal.SIGINT)
        deadline = time.monotonic() + 14
        while not self.done.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assert_completion(130)
        self.assertEqual(last.read_text(encoding="utf-8"), "fixture final answer")
        self.assertTrue(any(m.get("method") == "turn/interrupt" for m in self.traced_messages()))

    def stop_detached_helper(self, pid):
        if not self.done.exists():
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                return
            deadline = time.monotonic() + 14
            while not self.done.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            if not self.done.exists():
                os.kill(pid, signal.SIGKILL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
PY
