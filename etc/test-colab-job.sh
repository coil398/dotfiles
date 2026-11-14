#!/usr/bin/env bash
# Contract test for .agents/skills/colab/scripts/colab-job.py using a fake `colab` CLI.
# Never invokes the real colab CLI or allocates a Colab VM.
set -euo pipefail

DOT_DIR="$(cd -P "$(dirname "$0")/.." && pwd)"
RUNNER="${DOT_DIR}/.agents/skills/colab/scripts/colab-job.py"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/colab-job-test.XXXXXX")"
trap 'rm -rf "$TEST_ROOT"' EXIT

timeout 300 python3 - "$RUNNER" "$TEST_ROOT" <<'PY'
import json
import os
import signal
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path

runner = Path(sys.argv[1])
root = Path(sys.argv[2])
bin_dir = root / "bin"
bin_dir.mkdir()
work_dir = root / "work"
content_root = root / "fake_content"
content_root.mkdir()
balance_file = root / "balance.txt"
balance_file.write_text("100.00\n", encoding="utf-8")
call_log = root / "fake_calls.jsonl"

fake_colab = bin_dir / "colab"
fake_colab.write_text(r'''#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

content_root = Path(os.environ["FAKE_COLAB_CONTENT"])
balance_file = Path(os.environ["FAKE_COLAB_BALANCE"])
call_log = Path(os.environ["FAKE_COLAB_CALLS"])
scenario = os.environ.get("FAKE_COLAB_SCENARIO", "ok")
exec_started_marker = os.environ.get("FAKE_COLAB_EXEC_MARKER")


def log_call(cmd, args, config):
    with call_log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"cmd": cmd, "args": args, "config": config}) + "\n")


def load_sessions(config_path):
    if not config_path:
        return {}
    p = Path(config_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_sessions(config_path, data):
    if not config_path:
        return
    p = Path(config_path)
    p.write_text(json.dumps(data), encoding="utf-8")


def session_dir(session_name):
    d = content_root / session_name
    d.mkdir(parents=True, exist_ok=True)
    return d


def map_remote(session_name, remote_path):
    rel = remote_path
    if rel.startswith("/content/"):
        rel = rel[len("/content/"):]
    elif rel == "/content":
        rel = ""
    return session_dir(session_name) / rel


args = sys.argv[1:]
config_path = None
if len(args) >= 2 and args[0] == "--config":
    config_path = args[1]
    args = args[2:]

if not args:
    sys.stderr.write("missing subcommand\n")
    sys.exit(2)

cmd = args[0]
rest = args[1:]
log_call(cmd, rest, config_path)

if cmd == "usage":
    bal = float(balance_file.read_text(encoding="utf-8").strip())
    sys.stdout.write(
        f"Current balance: {bal:.2f} compute units\n"
        "Usage rate: 1.15/hr\n"
        "Active assignments: 0\n"
    )
    sys.exit(0)

if cmd == "new":
    if scenario == "new_fail":
        sys.stderr.write("400 accelerator unavailable\n")
        sys.exit(1)
    sname = rest[rest.index("-s") + 1]
    sessions = load_sessions(config_path)
    sessions[sname] = {"active": True}
    save_sessions(config_path, sessions)
    bal = float(balance_file.read_text(encoding="utf-8").strip())
    balance_file.write_text(f"{bal - 0.50:.2f}\n", encoding="utf-8")
    sys.stdout.write("[colab] Session READY.\n")
    sys.exit(0)

if cmd == "upload":
    sname = rest[rest.index("-s") + 1]
    idx = rest.index("-s") + 2
    local_path = Path(rest[idx])
    remote_path = rest[idx + 1]
    dest = map_remote(sname, remote_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(local_path, dest)
    sys.exit(0)

if cmd == "exec":
    sname = rest[rest.index("-s") + 1]
    script_path = Path(rest[rest.index("-f") + 1])
    if exec_started_marker:
        Path(exec_started_marker).write_text("started\n", encoding="utf-8")
    if scenario == "exec_fail":
        sys.stderr.write("exec transport error\n")
        sys.exit(1)
    code = script_path.read_text(encoding="utf-8")
    sdir = session_dir(sname)
    code = code.replace("/content", str(sdir))
    if scenario == "remote_timeout":
        code = code.replace('\\"max_minutes\\": 1', '\\"max_minutes\\": 0.02')
    if scenario == "pip_fail":
        # Intercept pip module invocation via a fake pip package on PYTHONPATH
        fake_pkg = sdir / "_fake_pip"
        fake_pkg.mkdir(parents=True, exist_ok=True)
        (fake_pkg / "pip.py").write_text("import sys\nprint('pip failed intentionally')\nsys.exit(2)\n", encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(fake_pkg) + os.pathsep + env.get("PYTHONPATH", "")
    else:
        env = os.environ.copy()
    proc = subprocess.run([sys.executable, "-c", code], env=env)
    # Real colab exec returns 0 even if remote script fails.
    sys.exit(0)

if cmd == "download":
    sname = rest[rest.index("-s") + 1]
    idx = rest.index("-s") + 2
    remote_path = rest[idx]
    local_path = Path(rest[idx + 1])
    if scenario == "bad_out_tar" and remote_path.endswith("out.tgz"):
        with tarfile.open(local_path, "w:gz") as tar:
            data = b"pwn"
            info = tarfile.TarInfo("../escape.txt")
            info.size = len(data)
            import io
            tar.addfile(info, io.BytesIO(data))
        sys.exit(0)
    src = map_remote(sname, remote_path)
    if not src.exists():
        sys.stderr.write(f"missing remote file: {remote_path}\n")
        sys.exit(1)
    shutil.copy2(src, local_path)
    sys.exit(0)

if cmd == "stop":
    sname = rest[rest.index("-s") + 1]
    sessions = load_sessions(config_path)
    sessions.pop(sname, None)
    save_sessions(config_path, sessions)
    sys.stdout.write("[colab] Session terminated.\n")
    sys.exit(0)

if cmd == "sessions":
    sessions = load_sessions(config_path)
    if not sessions:
        sys.stdout.write("No active sessions found on server.\n")
    else:
        for name in sorted(sessions):
            sys.stdout.write(f"{name}\n")
    sys.exit(0)

sys.stderr.write(f"unknown command: {cmd}\n")
sys.exit(2)
''', encoding="utf-8")
fake_colab.chmod(0o700)


def check(name, cond, detail=""):
    if not cond:
        print(f"FAIL {name}: {detail}")
        sys.exit(1)
    print(f"PASS {name}")


def make_job_dir(name, entry_code, extra_files=None):
    jdir = root / f"job_{name}"
    jdir.mkdir(parents=True, exist_ok=True)
    (jdir / "run.py").write_text(entry_code, encoding="utf-8")
    for rel, content in (extra_files or {}).items():
        p = jdir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return jdir


def run_runner(args_list, *, scenario="ok", path=None, marker=None):
    env = os.environ.copy()
    env["FAKE_COLAB_CONTENT"] = str(content_root)
    env["FAKE_COLAB_BALANCE"] = str(balance_file)
    env["FAKE_COLAB_CALLS"] = str(call_log)
    env["FAKE_COLAB_SCENARIO"] = scenario
    if marker:
        env["FAKE_COLAB_EXEC_MARKER"] = str(marker)
    else:
        env.pop("FAKE_COLAB_EXEC_MARKER", None)
    env["PATH"] = path if path is not None else f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
    proc = subprocess.run(
        [sys.executable, str(runner), *args_list],
        env=env,
        text=True,
        capture_output=True,
        timeout=60,
    )
    lines = proc.stdout.strip().splitlines()
    assert len(lines) == 1, (proc.returncode, proc.stdout, proc.stderr)
    return proc.returncode, json.loads(lines[0]), proc.stderr


def last_calls_since(start_idx):
    lines = call_log.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[start_idx:]]


def call_count():
    if not call_log.exists():
        return 0
    return len(call_log.read_text(encoding="utf-8").splitlines())


# 1. Success path with args, excluded dirs, artifacts, stop verification, CU accounting.
job_ok = make_job_dir(
    "ok",
    """import os, pathlib, sys
print("hello from colab", sys.argv[1:])
out_dir = pathlib.Path(os.environ["COLAB_JOB_OUT"])
(out_dir / "result.txt").write_text(",".join(sys.argv[1:]), encoding="utf-8")
""",
    extra_files={
        ".git/config": "ignored",
        "__pycache__/mod.pyc": "ignored",
        ".venv/bin/python": "ignored",
        "node_modules/pkg/index.js": "ignored",
        "sub/data.txt": "payload",
    },
)
c0 = call_count()
rc, summary, stderr = run_runner([
    "--job-dir", str(job_ok),
    "--entry", "run.py",
    "--arg", "alpha",
    "--arg", "beta space",
    "--gpu", "T4",
    "--high-mem",
    "--max-minutes", "5",
    "--work-dir", str(work_dir),
    "--run-id", "ok.1",
])
calls = last_calls_since(c0)
check("ok exit and status", rc == 0 and summary["status"] == "completed" and summary["EXIT"] == 0, summary)
check("ok job_exit and phase", summary["job_exit"] == 0 and summary["phase"] == "run", summary)
check("ok accelerator", summary["accelerator"] == "gpu:T4+high-mem", summary)
check("ok session normalized", summary["session"] == "cj-ok-1", summary)
check("ok stop verified", summary["stop_ok"] is True and summary["stop_verified"] is True, summary)
check("ok cu used", summary["balance_before"] == 100.0 and summary["balance_after"] == 99.5 and summary["cu_used"] == 0.5, summary)
out_file = Path(summary["out_dir"]) / "result.txt"
check("ok output extracted", summary["out_files"] == 1 and out_file.read_text(encoding="utf-8") == "alpha,beta space", summary)
check("ok stop and sessions called", [c["cmd"] for c in calls[-3:]] == ["stop", "sessions", "usage"], calls)
with tarfile.open(summary["artifacts"]["job_tgz"], "r:gz") as tar:
    names = tar.getnames()
check(
    "excluded dirs omitted from job.tgz",
    all(not any(p in {".git", "__pycache__", ".venv", "node_modules"} for p in n.split("/")) for n in names)
    and "sub/data.txt" in names,
    names,
)
check(
    "artifact permissions 0600/0700",
    stat.S_IMODE(work_dir.stat().st_mode) == 0o700
    and stat.S_IMODE(Path(summary["artifacts"]["summary_json"]).stat().st_mode) == 0o600
    and stat.S_IMODE(Path(summary["artifacts"]["run_log"]).stat().st_mode) == 0o600,
    summary["artifacts"],
)
run_log_text = Path(summary["artifacts"]["run_log"]).read_text(encoding="utf-8")
check("run.log has colab_call events", "colab_call" in run_log_text and "elapsed_ms=" in run_log_text, run_log_text)
check("stdout.log has entry output", "hello from colab ['alpha', 'beta space']" in Path(summary["artifacts"]["stdout_log"]).read_text(encoding="utf-8"))

# 2. Entry exits with sys.exit(7) -> EXIT 3, job_exit 7
job_exit7 = make_job_dir("exit7", "import sys\nprint('bye')\nsys.exit(7)\n")
rc, summary, _ = run_runner([
    "--job-dir", str(job_exit7),
    "--entry", "run.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "exit7",
])
check("sys.exit(7) -> EXIT 3", rc == 3 and summary["status"] == "job_failed" and summary["job_exit"] == 7 and summary["stop_verified"] is True, summary)

# 3. Entry raises uncaught exception -> EXIT 3
job_exc = make_job_dir("exc", "raise RuntimeError('boom')\n")
rc, summary, _ = run_runner([
    "--job-dir", str(job_exc),
    "--entry", "run.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "exc1",
])
check("exception -> EXIT 3", rc == 3 and summary["status"] == "job_failed" and summary["job_exit"] == 1 and summary["stop_verified"] is True, summary)
check("exception traceback in stdout.log", "RuntimeError: boom" in Path(summary["artifacts"]["stdout_log"]).read_text(encoding="utf-8"))

# 4. Requirements install failure -> EXIT 3, phase=install
job_req = make_job_dir("req", "print('should not run')\n", extra_files={"requirements.txt": "nonexistent==0.0.0\n"})
rc, summary, _ = run_runner([
    "--job-dir", str(job_req),
    "--entry", "run.py",
    "--requirements", "requirements.txt",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "reqfail",
], scenario="pip_fail")
check("pip install fail -> EXIT 3 phase=install", rc == 3 and summary["status"] == "job_failed" and summary["phase"] == "install" and summary["stop_verified"] is True, summary)

# 5. Timeout (remote max-minutes exceeded via fake clock shortening) -> EXIT 124 and stopped
job_to = make_job_dir("timeout", "import time\ntime.sleep(30)\n")
rc, summary, _ = run_runner([
    "--job-dir", str(job_to),
    "--entry", "run.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "to1",
], scenario="remote_timeout")
check("timeout -> EXIT 124 and stopped", rc == 124 and summary["status"] == "timed_out" and summary["stop_ok"] is True and summary["stop_verified"] is True, summary)

# 6. Allocation failure (`new` fails) -> EXIT 125
rc, summary, _ = run_runner([
    "--job-dir", str(job_ok),
    "--entry", "run.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "newfail",
], scenario="new_fail")
check("new fail -> EXIT 125", rc == 125 and summary["status"] == "allocation_failed" and summary["EXIT"] == 125, summary)

# 7. Exec failure (runner side) -> EXIT 4 and stopped
rc, summary, _ = run_runner([
    "--job-dir", str(job_ok),
    "--entry", "run.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "execfail",
], scenario="exec_fail")
check("exec fail -> EXIT 4 and stopped", rc == 4 and summary["status"] == "runner_failed" and summary["stop_ok"] is True and summary["stop_verified"] is True, summary)

# 8. SIGTERM interruption -> EXIT 130 and stopped
marker = root / "exec_started"
job_sig = make_job_dir("sig", "import time\ntime.sleep(30)\n")
env = os.environ.copy()
env["FAKE_COLAB_CONTENT"] = str(content_root)
env["FAKE_COLAB_BALANCE"] = str(balance_file)
env["FAKE_COLAB_CALLS"] = str(call_log)
env["FAKE_COLAB_SCENARIO"] = "ok"
env["FAKE_COLAB_EXEC_MARKER"] = str(marker)
env["PATH"] = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
proc = subprocess.Popen(
    [
        sys.executable, str(runner),
        "--job-dir", str(job_sig),
        "--entry", "run.py",
        "--max-minutes", "1",
        "--work-dir", str(work_dir),
        "--run-id", "sigterm1",
    ],
    env=env,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
deadline = time.monotonic() + 15
while not marker.exists():
    if time.monotonic() > deadline:
        proc.kill()
        check("sigterm marker", False, "exec marker did not appear")
    time.sleep(0.05)
proc.send_signal(signal.SIGTERM)
out_text, err_text = proc.communicate(timeout=30)
sig_summary = json.loads(out_text.strip())
check("SIGTERM -> EXIT 130 and stopped", proc.returncode == 130 and sig_summary["status"] == "interrupted" and sig_summary["stop_ok"] is True and sig_summary["stop_verified"] is True, (proc.returncode, sig_summary, err_text))

# 9. RUN_ID collision -> EXIT 2
rc, summary, _ = run_runner([
    "--job-dir", str(job_ok),
    "--entry", "run.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "ok.1",
])
check("run_id collision -> EXIT 2", rc == 2 and summary["status"] == "invocation_error" and summary["EXIT"] == 2, summary)

# 10. Missing colab binary -> EXIT 5
empty_bin = root / "empty_bin"
empty_bin.mkdir()
rc, summary, _ = run_runner([
    "--job-dir", str(job_ok),
    "--entry", "run.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "missingcolab",
], path=str(empty_bin))
check("missing colab -> EXIT 5", rc == 5 and summary["status"] == "invocation_error" and summary["EXIT"] == 5, summary)

# 11. Invalid arguments -> EXIT 2 and invocation_error JSON
rc, summary, _ = run_runner(["--unknown-flag"])
check("unknown flag -> invocation_error", rc == 2 and summary["status"] == "invocation_error", summary)

rc, summary, _ = run_runner([
    "--job-dir", str(job_ok),
    "--entry", "../outside.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "badentry1",
])
check("entry .. rejected -> EXIT 2", rc == 2 and summary["status"] == "invocation_error", summary)

sym_job = root / "job_sym"
sym_job.mkdir()
outside_py = root / "outside.py"
outside_py.write_text("print('outside')\n", encoding="utf-8")
(sym_job / "link.py").symlink_to(outside_py)
rc, summary, _ = run_runner([
    "--job-dir", str(sym_job),
    "--entry", "link.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "badsym1",
])
check("symlink entry rejected -> EXIT 2", rc == 2 and summary["status"] == "invocation_error", summary)

rc, summary, _ = run_runner([
    "--job-dir", str(job_ok),
    "--entry", "run.py",
    "--gpu", "T4",
    "--tpu", "v5e1",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "badaccel1",
])
check("mutually exclusive gpu/tpu -> EXIT 2", rc == 2 and summary["status"] == "invocation_error", summary)

# 12. out.tgz with '..' path traversal -> EXIT 4, rejected, stopped
rc, summary, _ = run_runner([
    "--job-dir", str(job_ok),
    "--entry", "run.py",
    "--max-minutes", "1",
    "--work-dir", str(work_dir),
    "--run-id", "badtar1",
], scenario="bad_out_tar")
check(
    "out.tgz '..' rejected -> EXIT 4 and stopped",
    rc == 4 and summary["status"] == "runner_failed" and summary["stop_ok"] is True and summary["stop_verified"] is True and not (work_dir / "escape.txt").exists(),
    summary,
)

print("ALL PASS")
PY
