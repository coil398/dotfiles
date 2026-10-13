#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONDONTWRITEBYTECODE=1 python3 - "${SCRIPT_DIR}/../.agents/skills/codex/scripts/codex-app-run.py" <<'PY'
import errno
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


HELPER = Path(sys.argv[1]).resolve()
RUNNER = HELPER.with_name("codex-run.py")
sys.argv = [sys.argv[0]]
if not HELPER.is_file() or not RUNNER.is_file():
    print(f"BLOCKED: app-server helper or runner is unavailable: {HELPER}", file=sys.stderr)
    raise SystemExit(2)

FAKE_SERVER = r'''#!/usr/bin/env python3
import json
import os
import select
import sys
import time

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
        if mode in ("interrupt", "hold"):
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
        if mode == "hold":
            interrupted = False
            while not os.path.exists(os.environ["APP_FAKE_RELEASE"]):
                readable, _, _ = select.select([sys.stdin], [], [], 0.01)
                if not readable:
                    continue
                incoming = receive()
                if incoming is None:
                    break
                if incoming.get("method") == "turn/interrupt":
                    respond(incoming, {})
                    completed("interrupted")
                    interrupted = True
                    break
            if interrupted:
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
        session_conflict = os.environ.get("APP_FAKE_CREATE_SESSION")
        if session_conflict:
            with open(session_conflict, "w", encoding="utf-8") as stream:
                stream.write("contender\n")
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
        self.runner_temp = tempfile.TemporaryDirectory(
            prefix="codex-runner-private-", dir=str(Path.home()))
        self.addCleanup(self.runner_temp.cleanup)
        self.runner_base = Path(self.runner_temp.name)
        self.prompt = self.base / "prompt.md"
        self.prompt.write_text("fixture prompt\n", encoding="utf-8")
        self.prompt.chmod(0o600)
        self.fake = self.base / "fake-codex"
        self.fake.write_text(FAKE_SERVER, encoding="utf-8")
        self.fake.chmod(0o755)
        self.state = self.base / "state.txt"
        self.done = self.base / "done"
        self.child_pid = self.base / "child-pid"
        self.cwd = self.base / "workspace"
        self.cwd.mkdir()
        self.trace = self.base / "fake-server-trace.jsonl"
        self.state_home = self.base / "xdg-state"
        self.holds = self.state_home / "dotfiles-autosync" / "holds"
        self.release = self.base / "release"

    def invoke(self, mode, thread_id=None, wait=True, sandbox="read-only",
               signal_timing=None, signum=signal.SIGTERM, detached=False):
        last = self.base / "last.md"
        events = self.base / "events.jsonl"
        env = dict(os.environ, APP_FAKE_MODE=mode, APP_FAKE_TRACE=str(self.trace),
                   APP_FAKE_CWD=str(self.cwd.resolve()), XDG_STATE_HOME=str(self.state_home),
                   APP_FAKE_RELEASE=str(self.release))
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

    def invoke_runner(self, run_id="runner-fixture", model="fixture-model", prompt=None,
                      prompt_file=None, work_dir=None, session_file=None, mode="normal",
                      max_wait_seconds=None, supervisor_exits=False,
                      supervisor_writes_done=False, done_read_fails=False,
                      session_save_conflict=False, wait=True, runner_cwd=None):
        bin_dir = self.base / "bin"
        bin_dir.mkdir(exist_ok=True)
        codex = bin_dir / "codex"
        codex.write_text(FAKE_SERVER, encoding="utf-8")
        codex.chmod(0o755)
        work_dir = work_dir or self.runner_base / "runner-work"
        command = [
            sys.executable, str(RUNNER),
            "--cwd", str(self.cwd.resolve()),
            "--model", model,
            "--effort", "medium",
            "--sandbox", "read-only",
            "--work-dir", str(work_dir),
            "--run-id", run_id,
        ]
        if prompt_file is not None:
            command.extend(["--prompt-file", str(prompt_file)])
        else:
            command.extend(["--prompt", prompt if prompt is not None else "fixture prompt"])
        if session_file is not None:
            command.extend(["--session-file", str(session_file)])
        if (max_wait_seconds is not None or supervisor_exits or supervisor_writes_done
                or done_read_fails):
            harness = self.base / "runner-harness.py"
            harness_lines = [
                "import importlib.util", "import sys", "",
                "runner_path = sys.argv[1]", "runner_args = sys.argv[2:]",
                "spec = importlib.util.spec_from_file_location('codex_runner', runner_path)",
                "module = importlib.util.module_from_spec(spec)", "spec.loader.exec_module(module)", "",
            ]
            if max_wait_seconds is not None:
                harness_lines.append(f"module.MAX_WAIT_SECONDS = {max_wait_seconds!r}")
            if supervisor_exits:
                harness_lines.extend([
                    "original_popen = module.subprocess.Popen",
                    "def popen(command, *args, **kwargs):",
                    "    if isinstance(command, list) and '--_worker' in command:",
                    "        command = [sys.executable, '-c', 'pass']",
                    "    return original_popen(command, *args, **kwargs)",
                    "module.subprocess.Popen = popen",
                ])
            if supervisor_writes_done:
                harness_lines.extend([
                    "from pathlib import Path",
                    "class ExitingWorker:",
                    "    def __init__(self, done_path):",
                    "        self.done_path = done_path",
                    "    def poll(self):",
                    "        self.done_path.write_text('EXIT=0\\n', encoding='utf-8')",
                    "        return 0",
                    "original_popen = module.subprocess.Popen",
                    "def popen(command, *args, **kwargs):",
                    "    if isinstance(command, list) and '--_worker' in command:",
                    "        done_path = Path(command[command.index('--_done') + 1])",
                    "        return ExitingWorker(done_path)",
                    "    return original_popen(command, *args, **kwargs)",
                    "module.subprocess.Popen = popen",
                ])
            if done_read_fails:
                harness_lines.extend([
                    "class RunningWorker:",
                    "    def poll(self):",
                    "        return None",
                    "original_popen = module.subprocess.Popen",
                    "def popen(command, *args, **kwargs):",
                    "    if isinstance(command, list) and '--_worker' in command:",
                    "        return RunningWorker()",
                    "    return original_popen(command, *args, **kwargs)",
                    "module.subprocess.Popen = popen",
                    "def fail_read_done(path):",
                    "    raise PermissionError('fixture marker read failure')",
                    "module._read_done = fail_read_done",
                ])
            harness_lines.extend(["", "raise SystemExit(module.main(runner_args))", ""])
            harness.write_text("\n".join(harness_lines), encoding="utf-8")
            command = [sys.executable, str(harness), str(RUNNER), *command[2:]]
        env = dict(os.environ, APP_FAKE_MODE=mode, APP_FAKE_TRACE=str(self.trace),
                   APP_FAKE_CWD=str(self.cwd.resolve()), XDG_STATE_HOME=str(self.state_home),
                   APP_FAKE_RELEASE=str(self.release))
        if session_save_conflict and session_file is not None:
            env["APP_FAKE_CREATE_SESSION"] = str(session_file)
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        process = subprocess.Popen(command, env=env, cwd=runner_cwd,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if not wait:
            self.addCleanup(self.reap_process, process)
            return process
        stdout, stderr = process.communicate(timeout=12)
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)

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

    def test_autosync_hold_exists_during_job_and_is_removed_on_success(self):
        process, _last, events = self.invoke("hold", wait=False)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if events.exists() and '"method":"turn/started"' in events.read_text(encoding="utf-8"):
                break
            if process.poll() is not None:
                break
            time.sleep(0.02)
        self.assertTrue(events.exists() and '"method":"turn/started"' in
                        events.read_text(encoding="utf-8"), "turn did not start")
        hold_files = list(self.holds.glob("*.hold"))
        self.assertEqual(len(hold_files), 1)
        self.assertEqual(hold_files[0].read_text(encoding="utf-8"), f"{process.pid}\n")
        self.release.write_text("continue\n", encoding="utf-8")
        stdout, stderr = process.communicate(timeout=15)
        self.assertEqual(process.returncode, 0, stderr or stdout)
        self.assert_completion(0)
        self.assertEqual(list(self.holds.glob("*.hold")), [])

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
        hold_files = list(self.holds.glob("*.hold"))
        self.assertEqual(len(hold_files), 1)
        self.assertEqual(hold_files[0].read_text(encoding="utf-8"), f"{process.pid}\n")
        os.kill(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=14)
        self.assertEqual(process.returncode, 130, stderr or stdout)
        self.assert_completion(130)
        self.assertEqual(list(self.holds.glob("*.hold")), [])
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

    def test_runner_rejects_invalid_model_with_machine_summary(self):
        result = self.invoke_runner(model="invalid model")
        self.assertEqual(result.returncode, 2, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["EXIT"], 2)
        self.assertIn("MODEL", summary["error"])
        self.assertFalse(self.trace.exists(), "Codex started after input validation failed")

    def test_runner_rejects_prompt_file_without_private_mode(self):
        if os.name == "nt":
            self.skipTest("Windows prompt privacy is enforced by ACLs")
        prompt_file = self.base / "public-prompt.md"
        prompt_file.write_text("fixture prompt\n", encoding="utf-8")
        prompt_file.chmod(0o644)
        result = self.invoke_runner(run_id="public-prompt", prompt_file=prompt_file)
        self.assertEqual(result.returncode, 2, result.stderr)
        summary = json.loads(result.stdout)
        self.assertIn("PROMPT_FILE must have mode 0600", summary["error"])
        self.assertFalse(self.trace.exists(), "Codex started with a public prompt file")

    def test_runner_argparse_error_uses_machine_summary_schema(self):
        valid = self.invoke_runner(run_id="schema-valid")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        valid_summary = json.loads(valid.stdout)
        invalid = subprocess.run([sys.executable, str(RUNNER)], capture_output=True,
                                 text=True, timeout=5)
        self.assertEqual(invalid.returncode, 2)
        invalid_summary = json.loads(invalid.stdout)

        def schema(value):
            if isinstance(value, dict):
                return {key: schema(child) for key, child in value.items()}
            if isinstance(value, list):
                return [schema(value[0])] if value else []
            return None

        self.assertEqual(schema(invalid_summary), schema(valid_summary))
        self.assertEqual(invalid_summary["wait_status"], "invocation_error")
        self.assertFalse(invalid_summary["done"]["created"])

    def test_usage_uses_latest_thread_total_not_last_or_subagent(self):
        spec = importlib.util.spec_from_file_location("codex_runner_usage_fixture", RUNNER)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        events = [
            {"type": "thread.started", "thread_id": "target-thread"},
            {"method": "thread/tokenUsage/updated", "params": {
                "threadId": "subagent-thread",
                "tokenUsage": {
                    "total": {"totalTokens": 700, "inputTokens": 500,
                              "cachedInputTokens": 400, "outputTokens": 200},
                    "last": {"totalTokens": 70, "inputTokens": 50,
                             "cachedInputTokens": 40, "outputTokens": 20},
                },
            }},
            {"method": "thread/tokenUsage/updated", "params": {
                "threadId": "target-thread",
                "tokenUsage": {
                    "total": {"totalTokens": 12, "inputTokens": 8,
                              "cachedInputTokens": 3, "outputTokens": 4},
                    "last": {"totalTokens": 5, "inputTokens": 3,
                             "cachedInputTokens": 1, "outputTokens": 2},
                },
            }},
            {"method": "thread/tokenUsage/updated", "params": {
                "threadId": "target-thread",
                "tokenUsage": {
                    "total": {"totalTokens": 24, "inputTokens": 15,
                              "cachedInputTokens": 5, "outputTokens": 9},
                    "last": {"totalTokens": 4, "inputTokens": 2,
                             "cachedInputTokens": 1, "outputTokens": 2},
                },
            }},
            {"method": "thread/tokenUsage/updated", "params": {
                "threadId": "subagent-thread",
                "tokenUsage": {
                    "total": {"totalTokens": 900, "inputTokens": 600,
                              "cachedInputTokens": 450, "outputTokens": 300},
                    "last": {"totalTokens": 90, "inputTokens": 60,
                             "cachedInputTokens": 45, "outputTokens": 30},
                },
            }},
        ]
        thread_id = runner._thread_id(events)
        self.assertEqual(runner._usage_from_events(events, thread_id), {
            "total_tokens": 24,
            "input_tokens": 15,
            "cached_input_tokens": 5,
            "output_tokens": 9,
        })
        self.assertEqual(runner._sandbox_value({"type": "readOnly"}), "read-only")
        self.assertEqual(runner._sandbox_value({"type": "workspaceWrite"}), "workspace-write")
        self.assertEqual(runner._sandbox_value({"type": "dangerFullAccess"}), "danger-full-access")

    def test_runner_rejects_relative_codex_resolution(self):
        spec = importlib.util.spec_from_file_location("codex_runner_relative_path", RUNNER)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with mock.patch.object(runner.Path, "home", return_value=self.base):
            with mock.patch.object(runner.shutil, "which", return_value="codex"):
                with self.assertRaisesRegex(runner.RunnerError, "must be absolute"):
                    runner._resolve_codex_cmd()

    def test_runner_rejects_codex_resolution_inside_current_directory(self):
        spec = importlib.util.spec_from_file_location("codex_runner_local_path", RUNNER)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        fake_codex = self.cwd / "codex"
        fake_codex.write_text("fixture", encoding="utf-8")
        original_cwd = Path.cwd()
        try:
            os.chdir(self.cwd)
            with mock.patch.object(runner.Path, "home", return_value=self.base):
                with mock.patch.object(runner.shutil, "which", return_value=str(fake_codex)):
                    with self.assertRaisesRegex(runner.RunnerError, "inside the current working directory"):
                        runner._resolve_codex_cmd()
        finally:
            os.chdir(original_cwd)

    def test_runner_rejects_existing_run_id_without_overwriting_artifact(self):
        work_dir = self.runner_base / "runner-work"
        work_dir.mkdir()
        existing_done = work_dir / "codex-collision-done"
        existing_done.write_text("EXIT=0\n", encoding="utf-8")
        result = self.invoke_runner(run_id="collision", work_dir=work_dir)
        self.assertEqual(result.returncode, 2, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["EXIT"], 2)
        self.assertIn("already has artifacts", summary["error"])
        self.assertEqual(existing_done.read_text(encoding="utf-8"), "EXIT=0\n")
        self.assertFalse(self.trace.exists(), "Codex started after RUN_ID collision")
        self.assertEqual(summary["wait_status"], "invocation_error")
        self.assertFalse(summary["done"]["created"])

    def test_runner_rejects_session_path_colliding_with_done_artifact(self):
        work_dir = self.runner_base / "runner-work"
        work_dir.mkdir()
        done_file = work_dir / "codex-session-collision-done"
        result = self.invoke_runner(run_id="session-collision", work_dir=work_dir,
                                    session_file=done_file)
        self.assertEqual(result.returncode, 2, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["wait_status"], "invocation_error")
        self.assertFalse(summary["done"]["created"])
        self.assertIn("SESSION_FILE paths collide", summary["error"])
        self.assertFalse(done_file.exists())
        self.assertFalse(self.trace.exists(), "Codex started after SESSION_FILE collision")

    def test_runner_rejects_meta_symlink_resolving_to_done_artifact(self):
        work_dir = self.runner_base / "runner-work"
        work_dir.mkdir()
        done_file = work_dir / "codex-meta-collision-done"
        session_file = self.runner_base / "meta-session"
        Path(f"{session_file}.meta").symlink_to(done_file)
        result = self.invoke_runner(run_id="meta-collision", work_dir=work_dir,
                                    session_file=session_file)
        self.assertEqual(result.returncode, 2, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["wait_status"], "invocation_error")
        self.assertFalse(summary["done"]["created"])
        self.assertIn("SESSION_META", summary["error"])
        self.assertFalse(done_file.exists())
        self.assertFalse(self.trace.exists(), "Codex started after SESSION_META collision")

    def test_runner_propagates_failed_turn_exit_to_summary_and_done_marker(self):
        result = self.invoke_runner(run_id="failed-turn", mode="failure")
        self.assertEqual(result.returncode, 1, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["EXIT"], 1)
        self.assertEqual(summary["wait_status"], "completed")
        self.assertTrue(summary["done"]["created"])
        done_file = Path(summary["done"]["path"])
        self.assertEqual(done_file.read_text(encoding="utf-8"), "EXIT=1\n")

    def test_runner_saves_new_session_after_failed_turn(self):
        session_file = self.runner_base / "failed-session" / "thread.txt"
        result = self.invoke_runner(run_id="failed-session", session_file=session_file,
                                    mode="failure")
        self.assertEqual(result.returncode, 1, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["thread_id"], "thread-fixture")
        self.assertEqual(session_file.read_text(encoding="utf-8"), "thread-fixture\n")
        self.assertTrue(Path(f"{session_file}.meta").is_file())

    def test_runner_preserves_failed_turn_exit_when_session_save_fails(self):
        session_file = self.runner_base / "failed-save-session" / "thread.txt"
        result = self.invoke_runner(run_id="failed-save", session_file=session_file,
                                    mode="failure", session_save_conflict=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["EXIT"], 1)
        self.assertEqual(session_file.read_text(encoding="utf-8"), "contender\n")
        self.assertFalse(Path(f"{session_file}.meta").exists())
        self.assertTrue(any("refusing to overwrite" in line
                            for line in summary["stderr"]["tail"]))

    def test_runner_marks_successful_turn_as_startup_error_when_session_save_fails(self):
        session_file = self.runner_base / "successful-save-session" / "thread.txt"
        result = self.invoke_runner(run_id="successful-save", session_file=session_file,
                                    session_save_conflict=True)
        self.assertEqual(result.returncode, 125, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["EXIT"], 125)
        self.assertEqual(Path(summary["done"]["path"]).read_text(encoding="utf-8"), "EXIT=125\n")
        self.assertEqual(session_file.read_text(encoding="utf-8"), "contender\n")

    def test_runner_timeout_returns_incomplete_summary_and_leaves_job_running(self):
        result = self.invoke_runner(run_id="runner-timeout", mode="hold",
                                    max_wait_seconds=0.8)
        self.assertEqual(result.returncode, 124, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["wait_status"], "timed_out")
        self.assertIsNone(summary["EXIT"])
        self.assertFalse(summary["done"]["created"])
        self.assertIsNone(summary["done"]["exit"])
        self.assertTrue(any(message.get("method") == "turn/start"
                            for message in self.traced_messages()))
        done_file = Path(summary["done"]["path"])
        try:
            self.assertFalse(done_file.exists())
            self.release.touch()
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline and not done_file.exists():
                time.sleep(0.02)
            self.assertEqual(done_file.read_text(encoding="utf-8"), "EXIT=0\n")
        finally:
            if not self.release.exists():
                self.release.touch()

    def test_runner_detects_supervisor_exit_without_done_marker(self):
        result = self.invoke_runner(run_id="supervisor-exit", supervisor_exits=True)
        self.assertEqual(result.returncode, 125, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["wait_status"], "supervisor_exited_without_done")
        self.assertIsNone(summary["EXIT"])
        self.assertFalse(summary["done"]["created"])
        self.assertFalse(Path(summary["done"]["path"]).exists())

    def test_runner_rechecks_done_after_supervisor_exit(self):
        result = self.invoke_runner(run_id="supervisor-writes-done",
                                    supervisor_writes_done=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["wait_status"], "completed")
        self.assertEqual(summary["EXIT"], 0)
        self.assertTrue(summary["done"]["created"])
        self.assertEqual(summary["done"]["exit"], 0)
        self.assertEqual(Path(summary["done"]["path"]).read_text(encoding="utf-8"), "EXIT=0\n")

    def test_runner_reports_done_marker_read_io_error(self):
        result = self.invoke_runner(run_id="done-read-error", done_read_fails=True)
        self.assertEqual(result.returncode, 125, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["wait_status"], "wait_error")
        self.assertIsNone(summary["EXIT"])
        self.assertFalse(summary["done"]["created"])
        self.assertIsNone(summary["done"]["exit"])
        self.assertIn("fixture marker read failure", summary["error"])
        self.assertFalse(Path(summary["done"]["path"]).exists())
        self.assertFalse(self.trace.exists(), "Codex started after marker read failed")

    def test_runner_blocks_until_done_and_returns_machine_summary(self):
        bin_dir = self.base / "bin"
        bin_dir.mkdir()
        codex = bin_dir / "codex"
        codex.write_text(FAKE_SERVER, encoding="utf-8")
        codex.chmod(0o755)
        work_dir = self.runner_base / "runner-work"
        command = [
            sys.executable, str(RUNNER),
            "--prompt-file", str(self.prompt),
            "--cwd", str(self.cwd.resolve()),
            "--model", "fixture-model",
            "--effort", "medium",
            "--sandbox", "read-only",
            "--work-dir", str(work_dir),
            "--run-id", "blocking-fixture",
        ]
        env = dict(os.environ, APP_FAKE_MODE="hold", APP_FAKE_TRACE=str(self.trace),
                   APP_FAKE_CWD=str(self.cwd.resolve()), XDG_STATE_HOME=str(self.state_home),
                   APP_FAKE_RELEASE=str(self.release))
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        done = work_dir / "codex-blocking-fixture-done"
        events = work_dir / "codex-blocking-fixture-events.jsonl"
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if self.trace.exists() and any(
                    message.get("method") == "turn/start" for message in self.traced_messages()
                ):
                    break
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    self.fail(f"runner exited before the held turn was released: {stdout} {stderr}")
                time.sleep(0.02)
            self.assertTrue(self.trace.exists() and any(
                message.get("method") == "turn/start" for message in self.traced_messages()
            ), "fake app-server did not reach the held turn")
            self.assertIsNone(process.poll(), "runner returned before DONE_FILE appeared")
            self.assertFalse(done.exists(), "DONE_FILE appeared before helper completion")
            self.release.touch()
            stdout, stderr = process.communicate(timeout=12)
            self.assertEqual(process.returncode, 0, stderr)
            summary = json.loads(stdout)
            self.assertEqual(summary["EXIT"], 0)
            self.assertEqual(summary["thread_id"], "thread-fixture")
            self.assertEqual(summary["REQUESTED_MODEL"], "fixture-model")
            self.assertEqual(summary["REQUESTED_EFFORT"], "medium")
            self.assertEqual(summary["REQUESTED_SANDBOX"], "read-only")
            self.assertEqual(summary["OBSERVED_MODEL"], "fixture-model")
            self.assertEqual(summary["OBSERVED_EFFORT"], "unavailable")
            self.assertEqual(summary["OBSERVED_SANDBOX"], "read-only")
            self.assertEqual(summary["final_response"]["body"], "fixture final answer")
            self.assertEqual(summary["final_response"]["path"], str((work_dir / "codex-blocking-fixture-last.md").resolve()))
            self.assertEqual(summary["events"]["path"], str(events.resolve()))
            self.assertGreater(summary["events"]["lines"], 0)
            self.assertEqual(summary["usage"]["total_tokens"], "unavailable")
            self.assertEqual(done.read_text(encoding="utf-8"), "EXIT=0\n")
        finally:
            if not self.release.exists():
                self.release.touch()
            if process.poll() is None:
                process.communicate(timeout=12)

    def test_runner_helper_sigterm_interrupts_held_turn_and_writes_done(self):
        work_dir = self.runner_base / "runner-interrupt"
        process = self.invoke_runner(run_id="runner-interrupt", work_dir=work_dir,
                                     mode="hold", wait=False)
        done = work_dir / "codex-runner-interrupt-done"
        pid_file = work_dir / "codex-runner-interrupt-pid"
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if pid_file.is_file() and any(
                    message.get("method") == "turn/start" for message in self.traced_messages()
                ):
                    break
                if process.poll() is not None:
                    stdout, stderr = process.communicate()
                    self.fail(f"runner exited before the fake turn was held: {stdout} {stderr}")
                time.sleep(0.02)
            self.assertTrue(pid_file.is_file(), "runner did not publish PID_FILE")
            self.assertTrue(any(message.get("method") == "turn/start"
                                for message in self.traced_messages()),
                            "fake Codex did not start the turn")
            helper_pid = int(pid_file.read_text(encoding="utf-8").strip())
            os.kill(helper_pid, signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=12)
            self.assertEqual(process.returncode, 130, stderr)
            summary = json.loads(stdout)
            self.assertEqual(summary["EXIT"], 130)
            self.assertEqual(done.read_text(encoding="utf-8"), "EXIT=130\n")
            self.assertTrue(any(message.get("method") == "turn/interrupt"
                                for message in self.traced_messages()))
        finally:
            if not self.release.exists():
                self.release.touch()
            if process.poll() is None:
                process.communicate(timeout=12)

    def test_runner_canonicalizes_work_dir_and_session_parent(self):
        work_target = self.runner_base / "real-work-parent"
        work_target.mkdir()
        work_alias = self.runner_base / "linked-work-parent"
        work_alias.symlink_to(work_target, target_is_directory=True)
        work_dir = work_alias / "runner-work"

        session_target = self.runner_base / "real-session-parent"
        session_target.mkdir()
        session_alias = self.runner_base / "linked-session-parent"
        session_alias.symlink_to(session_target, target_is_directory=True)
        session_file = session_alias / "thread.txt"

        result = self.invoke_runner(run_id="canonical-parents", work_dir=work_dir,
                                    session_file=session_file)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        canonical_work = work_target / "runner-work"
        canonical_session = session_target / "thread.txt"
        self.assertEqual(summary["EXIT"], 0)
        self.assertEqual(summary["final_response"]["path"],
                         str((canonical_work / "codex-canonical-parents-last.md").resolve()))
        self.assertEqual(summary["SESSION_FILE"], str(canonical_session))
        self.assertEqual(summary["SESSION_META"], str(Path(f"{canonical_session}.meta")))
        self.assertEqual(canonical_session.read_text(encoding="utf-8"), "thread-fixture\n")
        self.assertTrue(Path(f"{canonical_session}.meta").is_file())
        self.assertEqual(Path(f"{work_alias}/runner-work").resolve(), canonical_work.resolve())

    def test_runner_rejects_group_writable_work_dir(self):
        work_dir = self.runner_base / "group-writable"
        work_dir.mkdir(mode=0o700)
        work_dir.chmod(0o770)
        result = self.invoke_runner(run_id="group-writable", work_dir=work_dir)
        self.assertEqual(result.returncode, 2, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["EXIT"], 2)
        self.assertIn("group/world writable", summary["error"])
        self.assertFalse(self.trace.exists())

    def test_runner_rejects_group_writable_work_dir_ancestor(self):
        unsafe_parent = self.runner_base / "group-writable-parent"
        unsafe_parent.mkdir(mode=0o700)
        unsafe_parent.chmod(0o770)
        work_dir = unsafe_parent / "runner-work"
        result = self.invoke_runner(run_id="group-writable-ancestor", work_dir=work_dir)
        self.assertEqual(result.returncode, 2, result.stderr)
        summary = json.loads(result.stdout)
        self.assertIn("ancestor is group/world writable", summary["error"])
        self.assertFalse(work_dir.exists())
        self.assertFalse(self.trace.exists())

    def test_runner_rejects_unsafe_resume_files(self):
        session_dir = self.runner_base / "resume-session"
        session_dir.mkdir(mode=0o700)
        session_file = session_dir / "thread.txt"
        session_meta = Path(f"{session_file}.meta")
        session_file.write_text("thread-fixture\n", encoding="utf-8")
        session_meta.write_text(
            f"CWD={self.cwd.resolve()}\nSANDBOX=read-only\n", encoding="utf-8")
        session_file.chmod(0o622)
        result = self.invoke_runner(run_id="unsafe-session", session_file=session_file)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("group/world writable", json.loads(result.stdout)["error"])
        self.assertFalse(self.trace.exists())

if __name__ == "__main__":
    unittest.main(verbosity=2)
PY
