#!/usr/bin/env python3
"""Run one local job directory on a Google Colab VM and collect outputs.

Creates per-run artifacts in WORK_DIR, packs JOB_DIR, allocates a Colab VM,
uploads the job tarball, runs a generated bootstrap script via ``colab exec``,
downloads status and outputs, always terminates the VM in a finally block,
and prints a single-line JSON summary to stdout.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time
from datetime import datetime
from pathlib import Path, PurePosixPath

EXIT_OK = 0
EXIT_VALIDATION = 2
EXIT_JOB_FAILED = 3
EXIT_RUNNER_FAILED = 4
EXIT_COLAB_MISSING = 5
EXIT_TIMEOUT = 124
EXIT_ALLOCATION_FAILED = 125
EXIT_INTERRUPTED = 130

GPU_TYPES = ("T4", "L4", "G4", "H100", "A100")
TPU_TYPES = ("v5e1", "v6e1")
EXCLUDE_DIRS = frozenset({".git", "__pycache__", ".venv", "node_modules"})
RUN_ID_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
BALANCE_RE = re.compile(r"Current\s+balance:\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)

REMOTE_RUNNER_DIR = "/content/_runner"
REMOTE_JOB_TGZ = "/content/_runner_job.tgz"
REMOTE_STATUS_JSON = "/content/_runner/status.json"
REMOTE_OUT_TGZ = "/content/_runner/out.tgz"
REMOTE_JOB_DIR = "/content/job"
REMOTE_OUT_DIR = "/content/out"

CONTROL_TIMEOUT_S = 120
USAGE_TIMEOUT_S = 60
LOCAL_EXEC_SLACK_S = 900

BOOTSTRAP_TEMPLATE = """import json
import os
import shutil
import signal
import subprocess
import sys
import tarfile
import threading
import time
import traceback
from pathlib import Path, PurePosixPath

CONFIG = json.loads({config_json_literal})
RUNNER_DIR = Path("/content/_runner")
JOB_TGZ = Path("/content/_runner_job.tgz")
STATUS_JSON = Path("/content/_runner/status.json")
OUT_TGZ = Path("/content/_runner/out.tgz")
JOB_DIR = Path("/content/job")
OUT_DIR = Path("/content/out")


def safe_extract(tgz_path: Path, dest_dir: Path) -> None:
    dest_resolved = dest_dir.resolve()
    with tarfile.open(tgz_path, "r:gz") as tar:
        members = tar.getmembers()
        for member in members:
            raw_name = member.name
            if not raw_name or raw_name.startswith("/") or raw_name.startswith("\\\\"):
                raise ValueError(f"unsafe tar member path: {{raw_name}}")
            if os.path.splitdrive(raw_name)[0]:
                raise ValueError(f"unsafe tar member drive: {{raw_name}}")
            parts = [p for p in raw_name.replace("\\\\", "/").split("/") if p]
            if ".." in parts:
                raise ValueError(f"tar member contains '..': {{raw_name}}")
            if (
                member.issym()
                or member.islnk()
                or member.isdev()
                or member.ischr()
                or member.isblk()
                or member.isfifo()
                or not (member.isdir() or member.isfile())
            ):
                raise ValueError(f"unsafe tar member type: {{raw_name}}")
            if parts and parts != ["."]:
                target = (dest_resolved / PurePosixPath(*parts)).resolve()
                if target != dest_resolved and dest_resolved not in target.parents:
                    raise ValueError(f"tar member escapes destination: {{raw_name}}")

        for member in members:
            parts = [p for p in member.name.replace("\\\\", "/").split("/") if p and p != "."]
            if not parts:
                continue
            target = dest_resolved.joinpath(*parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                src = tar.extractfile(member)
                if src is None:
                    raise ValueError(f"cannot read tar member: {{member.name}}")
                with src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)


def pack_outputs(out_dir: Path, out_tgz: Path) -> None:
    with tarfile.open(out_tgz, "w:gz") as tar:
        if not out_dir.is_dir():
            return
        for root, dirnames, filenames in os.walk(out_dir, followlinks=False):
            dirnames.sort()
            filenames.sort()
            root_path = Path(root)
            kept_dirs = []
            for dname in dirnames:
                dpath = root_path / dname
                if dpath.is_symlink():
                    continue
                kept_dirs.append(dname)
                rel = dpath.relative_to(out_dir).as_posix()
                tar.add(dpath, arcname=rel, recursive=False)
            dirnames[:] = kept_dirs
            for fname in filenames:
                fpath = root_path / fname
                if fpath.is_symlink() or not fpath.is_file():
                    continue
                rel = fpath.relative_to(out_dir).as_posix()
                tar.add(fpath, arcname=rel, recursive=False)


def stream_command(cmd, cwd: Path, env: dict, timeout_s: float | None = None):
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        start_new_session=True,
    )
    timed_out_event = threading.Event()
    timer = None
    if timeout_s is not None:
        def on_timeout() -> None:
            timed_out_event.set()
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    pass

        timer = threading.Timer(timeout_s, on_timeout)
        timer.daemon = True
        timer.start()

    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
        rc = proc.wait()
    finally:
        if timer is not None:
            timer.cancel()

    if rc < 0:
        rc = 128 + (-rc)
    return rc, timed_out_event.is_set()


def main() -> None:
    t0 = time.monotonic()
    phase = "extract"
    exit_code = 1
    timed_out = False
    try:
        RUNNER_DIR.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(JOB_DIR, ignore_errors=True)
        shutil.rmtree(OUT_DIR, ignore_errors=True)
        JOB_DIR.mkdir(parents=True, exist_ok=True)
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        safe_extract(JOB_TGZ, JOB_DIR)

        requirements = CONFIG.get("requirements")
        if requirements:
            phase = "install"
            req_path = JOB_DIR / requirements
            rc, _ = stream_command(
                [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
                cwd=JOB_DIR,
                env=os.environ.copy(),
            )
            if rc != 0:
                exit_code = rc
                return

        phase = "run"
        entry_path = JOB_DIR / CONFIG["entry"]
        env = os.environ.copy()
        env["COLAB_JOB_OUT"] = str(OUT_DIR)
        timeout_s = float(CONFIG["max_minutes"]) * 60.0
        rc, timed_out = stream_command(
            [sys.executable, str(entry_path), *CONFIG["args"]],
            cwd=JOB_DIR,
            env=env,
            timeout_s=timeout_s,
        )
        exit_code = 124 if (timed_out and rc == 0) else rc
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        elapsed_s = round(time.monotonic() - t0, 3)
        status_payload = {{
            "phase": phase,
            "exit": exit_code,
            "timed_out": timed_out,
            "elapsed_s": elapsed_s,
        }}
        STATUS_JSON.write_text(json.dumps(status_payload), encoding="utf-8")
        pack_outputs(OUT_DIR, OUT_TGZ)


main()
"""


class RunnerError(Exception):
    def __init__(self, message: str, exit_code: int = EXIT_VALIDATION, phase: str | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.phase = phase


class SignalInterrupt(BaseException):
    def __init__(self, signum: int):
        super().__init__(f"interrupted by signal {signum}")
        self.signum = signum


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise RunnerError(message, EXIT_VALIDATION, phase="validate")


class IsoFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        return datetime.fromtimestamp(record.created).astimezone().isoformat(timespec="seconds")


def setup_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(f"colab_job.{os.getpid()}.{id(log_path)}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    stream = os.fdopen(fd, "w", encoding="utf-8")
    handler = logging.StreamHandler(stream)
    handler.setFormatter(IsoFormatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


def close_logger(logger: logging.Logger | None) -> None:
    if logger is None:
        return
    for handler in list(logger.handlers):
        try:
            handler.flush()
            handler.close()
        except OSError:
            pass
        logger.removeHandler(handler)


def write_exclusive(path: Path, content: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def normalize_session_name(run_id: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9-]", "-", run_id)
    return f"cj-{normalized}"


def format_accelerator(gpu: str | None, tpu: str | None, high_mem: bool) -> str:
    if gpu:
        base = f"gpu:{gpu}"
    elif tpu:
        base = f"tpu:{tpu}"
    else:
        base = "cpu"
    return f"{base}+high-mem" if high_mem else base


def check_max_minutes(value: str) -> int:
    try:
        minutes = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer between 1 and 1440") from exc
    if not 1 <= minutes <= 1440:
        raise argparse.ArgumentTypeError("must be between 1 and 1440")
    return minutes


def build_parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(description="Execute a local job on Google Colab and collect outputs.")
    parser.add_argument("--job-dir", required=True, type=Path)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--arg", action="append", default=[])
    parser.add_argument("--requirements")
    accel = parser.add_mutually_exclusive_group()
    accel.add_argument("--gpu", choices=GPU_TYPES)
    accel.add_argument("--tpu", choices=TPU_TYPES)
    parser.add_argument("--high-mem", action="store_true")
    parser.add_argument("--max-minutes", required=True, type=check_max_minutes)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    return parser


def check_relative_job_file(job_dir: Path, job_resolved: Path, rel: str, label: str, must_be_py: bool = False) -> str:
    if not rel or "\\" in rel:
        raise RunnerError(f"{label} must be a relative POSIX path inside --job-dir: {rel!r}")
    rel_path = Path(rel)
    if rel_path.is_absolute():
        raise RunnerError(f"{label} must be relative to --job-dir: {rel}")
    parts = rel_path.parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise RunnerError(f"{label} must not contain '.' or '..' segments: {rel}")

    curr = job_dir
    for part in parts:
        curr = curr / part
        if not os.path.lexists(curr):
            raise RunnerError(f"{label} does not exist inside --job-dir: {rel}")
        if curr.is_symlink():
            raise RunnerError(f"{label} must not be or traverse a symlink: {curr}")

    info = os.lstat(curr)
    if not stat.S_ISREG(info.st_mode):
        raise RunnerError(f"{label} must be a regular file: {rel}")
    resolved = curr.resolve()
    if not resolved.is_relative_to(job_resolved):
        raise RunnerError(f"{label} resolves outside --job-dir: {rel}")
    if must_be_py and curr.suffix != ".py":
        raise RunnerError(f"{label} must be a .py file: {rel}")
    return PurePosixPath(*parts).as_posix()


def check_inputs(args: argparse.Namespace) -> dict[str, object]:
    if not RUN_ID_RE.fullmatch(args.run_id):
        raise RunnerError("--run-id must match [A-Za-z0-9._-]+")
    if not args.job_dir.is_absolute():
        raise RunnerError("--job-dir must be an absolute path")
    if not args.job_dir.is_dir():
        raise RunnerError(f"--job-dir is not an existing directory: {args.job_dir}")
    if not args.work_dir.is_absolute():
        raise RunnerError("--work-dir must be an absolute path")

    job_resolved = args.job_dir.resolve()
    entry_rel = check_relative_job_file(args.job_dir, job_resolved, args.entry, "--entry", must_be_py=True)
    req_rel = None
    if args.requirements is not None:
        req_rel = check_relative_job_file(args.job_dir, job_resolved, args.requirements, "--requirements")

    return {
        "job_dir": job_resolved,
        "entry": entry_rel,
        "requirements": req_rel,
    }


def resolve_colab() -> str:
    command = shutil.which("colab")
    if not command:
        raise RunnerError("colab CLI was not found on PATH", EXIT_COLAB_MISSING, phase="validate")
    return command


def artifact_paths(work_dir: Path, run_id: str) -> dict[str, Path]:
    prefix = f"colab-{run_id}-"
    return {
        "job_tgz": work_dir / f"{prefix}job.tgz",
        "sessions_json": work_dir / f"{prefix}sessions.json",
        "bootstrap_py": work_dir / f"{prefix}bootstrap.py",
        "stdout_log": work_dir / f"{prefix}stdout.log",
        "status_json": work_dir / f"{prefix}status.json",
        "out_tgz": work_dir / f"{prefix}out.tgz",
        "out_dir": work_dir / f"{prefix}out",
        "run_log": work_dir / f"{prefix}run.log",
        "summary_json": work_dir / f"{prefix}summary.json",
    }


def pack_job_dir(job_dir: Path, tgz_path: Path, logger: logging.Logger, run_id: str) -> tuple[int, int]:
    t0 = time.monotonic()
    file_count = 0
    fd = os.open(tgz_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as raw_fh:
        with tarfile.open(fileobj=raw_fh, mode="w:gz") as tar:
            for root, dirnames, filenames in os.walk(job_dir, followlinks=False):
                root_path = Path(root)
                kept_dirs = []
                for dname in sorted(dirnames):
                    if dname in EXCLUDE_DIRS:
                        continue
                    dpath = root_path / dname
                    if dpath.is_symlink():
                        logger.warning("skip_symlink run_id=%s path=%s", run_id, dpath.relative_to(job_dir).as_posix())
                        continue
                    kept_dirs.append(dname)
                    rel_dir = dpath.relative_to(job_dir).as_posix()
                    tar.add(dpath, arcname=rel_dir, recursive=False)
                dirnames[:] = kept_dirs

                for fname in sorted(filenames):
                    fpath = root_path / fname
                    if fpath.is_symlink():
                        logger.warning("skip_symlink run_id=%s path=%s", run_id, fpath.relative_to(job_dir).as_posix())
                        continue
                    if not fpath.is_file():
                        continue
                    rel_file = fpath.relative_to(job_dir).as_posix()
                    tar.add(fpath, arcname=rel_file, recursive=False)
                    file_count += 1
        raw_fh.flush()
        os.fsync(raw_fh.fileno())
    size_bytes = tgz_path.stat().st_size
    logger.info(
        "pack_job run_id=%s files=%d bytes=%d elapsed_ms=%.0f",
        run_id,
        file_count,
        size_bytes,
        (time.monotonic() - t0) * 1000,
    )
    return file_count, size_bytes


def run_colab(
    colab_cmd: str,
    sub_args: list[str],
    *,
    timeout_s: float,
    logger: logging.Logger,
    run_id: str,
    cmd_name: str,
    log_path: Path | None = None,
) -> tuple[int, str, bool]:
    t0 = time.monotonic()
    cmd = [colab_cmd, *sub_args]
    log_fh = None
    if log_path is not None:
        fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        log_fh = os.fdopen(fd, "w", encoding="utf-8", errors="replace")

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=log_fh if log_fh is not None else subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    timed_out = False
    output = ""
    try:
        if log_fh is not None:
            try:
                rc = proc.wait(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_proc(proc)
                rc = 124
        else:
            try:
                stdout_text, _ = proc.communicate(timeout=timeout_s)
                output = stdout_text or ""
                rc = proc.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_proc(proc)
                stdout_text, _ = proc.communicate()
                output = stdout_text or ""
                rc = 124
    except BaseException:
        terminate_proc(proc)
        if log_fh is None and proc.stdout is not None:
            proc.stdout.close()
        raise
    finally:
        if log_fh is not None:
            log_fh.flush()
            log_fh.close()

    elapsed_ms = (time.monotonic() - t0) * 1000
    logger.info(
        "colab_call run_id=%s cmd=%s rc=%d timed_out=%s elapsed_ms=%.0f",
        run_id,
        cmd_name,
        rc,
        timed_out,
        elapsed_ms,
    )
    return rc, output, timed_out


def terminate_proc(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    except OSError:
        pass


def fetch_balance(colab_cmd: str, logger: logging.Logger, run_id: str, when: str) -> float | None:
    try:
        rc, output, timed_out = run_colab(
            colab_cmd,
            ["usage"],
            timeout_s=USAGE_TIMEOUT_S,
            logger=logger,
            run_id=run_id,
            cmd_name="usage",
        )
    except OSError as exc:
        logger.warning("usage_failed run_id=%s when=%s reason=%s", run_id, when, type(exc).__name__)
        return None
    if timed_out or rc != 0:
        logger.warning("usage_nonzero run_id=%s when=%s rc=%d timed_out=%s", run_id, when, rc, timed_out)
        return None
    match = BALANCE_RE.search(output)
    if not match:
        logger.warning("usage_unparsed run_id=%s when=%s", run_id, when)
        return None
    balance = float(match.group(1))
    logger.info("usage_parsed run_id=%s when=%s balance=%.4f", run_id, when, balance)
    return balance


def read_status_json(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise RunnerError("downloaded status.json is missing or a symlink", EXIT_RUNNER_FAILED, phase="status")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RunnerError(f"invalid status.json: {exc}", EXIT_RUNNER_FAILED, phase="status") from exc
    if not isinstance(payload, dict):
        raise RunnerError("status.json must be a JSON object", EXIT_RUNNER_FAILED, phase="status")
    for field in ("phase", "exit", "timed_out"):
        if field not in payload:
            raise RunnerError(f"status.json missing field {field!r}", EXIT_RUNNER_FAILED, phase="status")
    if (
        not isinstance(payload["phase"], str)
        or isinstance(payload["exit"], bool)
        or not isinstance(payload["exit"], int)
        or not isinstance(payload["timed_out"], bool)
    ):
        raise RunnerError("status.json has invalid field types", EXIT_RUNNER_FAILED, phase="status")
    return payload


def extract_out_tgz(tgz_path: Path, out_dir: Path, logger: logging.Logger, run_id: str) -> int:
    t0 = time.monotonic()
    if not tgz_path.is_file() or tgz_path.is_symlink():
        raise RunnerError("downloaded out.tgz is missing or a symlink", EXIT_RUNNER_FAILED, phase="download")
    os.mkdir(out_dir, 0o700)
    out_resolved = out_dir.resolve()
    extracted_files = 0

    try:
        with tarfile.open(tgz_path, "r:gz") as tar:
            members = tar.getmembers()
            for member in members:
                raw_name = member.name
                if not raw_name or raw_name.startswith("/") or raw_name.startswith("\\"):
                    raise RunnerError(f"unsafe out.tgz member path: {raw_name}", EXIT_RUNNER_FAILED, phase="extract_out")
                if os.path.splitdrive(raw_name)[0]:
                    raise RunnerError(f"unsafe out.tgz member drive: {raw_name}", EXIT_RUNNER_FAILED, phase="extract_out")
                parts = [p for p in raw_name.replace("\\", "/").split("/") if p]
                if ".." in parts:
                    raise RunnerError(f"out.tgz member contains '..': {raw_name}", EXIT_RUNNER_FAILED, phase="extract_out")
                if (
                    member.issym()
                    or member.islnk()
                    or member.isdev()
                    or member.ischr()
                    or member.isblk()
                    or member.isfifo()
                    or not (member.isdir() or member.isfile())
                ):
                    raise RunnerError(f"unsafe out.tgz member type: {raw_name}", EXIT_RUNNER_FAILED, phase="extract_out")
                if parts and parts != ["."]:
                    target = (out_resolved / PurePosixPath(*parts)).resolve()
                    if target != out_resolved and out_resolved not in target.parents:
                        raise RunnerError(
                            f"out.tgz member escapes destination: {raw_name}",
                            EXIT_RUNNER_FAILED,
                            phase="extract_out",
                        )

            for member in members:
                parts = [p for p in member.name.replace("\\", "/").split("/") if p and p != "."]
                if not parts:
                    continue
                target = out_resolved.joinpath(*parts)
                if member.isdir():
                    target.mkdir(mode=0o700, parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    src = tar.extractfile(member)
                    if src is None:
                        raise RunnerError(
                            f"cannot extract out.tgz member: {member.name}",
                            EXIT_RUNNER_FAILED,
                            phase="extract_out",
                        )
                    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with src, os.fdopen(fd, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    extracted_files += 1
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise RunnerError(f"failed to extract out.tgz: {exc}", EXIT_RUNNER_FAILED, phase="extract_out") from exc

    logger.info(
        "extract_out run_id=%s out_files=%d elapsed_ms=%.0f",
        run_id,
        extracted_files,
        (time.monotonic() - t0) * 1000,
    )
    return extracted_files


def chmod_if_regular(path: Path) -> None:
    try:
        info = os.lstat(path)
        if stat.S_ISREG(info.st_mode):
            os.chmod(path, 0o600)
    except OSError:
        pass


def session_present_in_output(output: str, session_name: str) -> bool:
    if "No active sessions found" in output:
        return False
    pattern = re.compile(rf"(?<![A-Za-z0-9._-]){re.escape(session_name)}(?![A-Za-z0-9._-])")
    return bool(pattern.search(output))


def build_summary(
    *,
    run_id: str,
    status: str,
    exit_code: int,
    job_exit: int | None,
    phase: str | None,
    accelerator: str,
    session: str | None,
    elapsed_s: float,
    balance_before: float | None,
    balance_after: float | None,
    stop_ok: bool | None,
    stop_verified: bool | None,
    out_dir: str | None,
    out_files: int,
    artifacts: dict[str, str],
    error: str | None = None,
) -> dict[str, object]:
    cu_used = None
    if balance_before is not None and balance_after is not None:
        cu_used = round(balance_before - balance_after, 4)
    payload: dict[str, object] = {
        "run_id": run_id,
        "status": status,
        "EXIT": exit_code,
        "job_exit": job_exit,
        "phase": phase,
        "accelerator": accelerator,
        "session": session,
        "elapsed_s": elapsed_s,
        "balance_before": balance_before,
        "balance_after": balance_after,
        "cu_used": cu_used,
        "stop_ok": stop_ok,
        "stop_verified": stop_verified,
        "out_dir": out_dir,
        "out_files": out_files,
        "artifacts": artifacts,
    }
    if error:
        payload["error"] = error
    return payload


def emit_summary(payload: dict[str, object], summary_path: Path | None = None) -> None:
    line = json.dumps(payload, ensure_ascii=False)
    if summary_path is not None:
        write_exclusive(summary_path, line + "\n")
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def execute_remote_job(
    *,
    colab_cmd: str,
    args: argparse.Namespace,
    paths: dict[str, Path],
    session_name: str,
    logger: logging.Logger,
    mark_vm_started,
    set_phase,
) -> tuple[str, int, int | None, str, int, str | None, str | None]:
    new_args = ["--config", str(paths["sessions_json"]), "new", "-s", session_name]
    if args.gpu:
        new_args.extend(["--gpu", args.gpu])
    elif args.tpu:
        new_args.extend(["--tpu", args.tpu])
    if args.high_mem:
        new_args.append("--high-mem")

    set_phase("allocate")
    mark_vm_started()
    rc, new_out, timed_out = run_colab(
        colab_cmd,
        new_args,
        timeout_s=CONTROL_TIMEOUT_S,
        logger=logger,
        run_id=args.run_id,
        cmd_name="new",
    )
    chmod_if_regular(paths["sessions_json"])
    if timed_out or rc != 0:
        logger.error("allocation_failed run_id=%s rc=%d timed_out=%s", args.run_id, rc, timed_out)
        return (
            "allocation_failed",
            EXIT_ALLOCATION_FAILED,
            None,
            "allocate",
            0,
            None,
            f"colab new failed (rc={rc}, timed_out={timed_out}): {new_out.strip()[:300]}",
        )

    set_phase("upload")
    rc, up_out, timed_out = run_colab(
        colab_cmd,
        [
            "--config",
            str(paths["sessions_json"]),
            "upload",
            "-s",
            session_name,
            str(paths["job_tgz"]),
            REMOTE_JOB_TGZ,
        ],
        timeout_s=CONTROL_TIMEOUT_S,
        logger=logger,
        run_id=args.run_id,
        cmd_name="upload",
    )
    if timed_out or rc != 0:
        logger.error("upload_failed run_id=%s rc=%d timed_out=%s", args.run_id, rc, timed_out)
        return (
            "runner_failed",
            EXIT_RUNNER_FAILED,
            None,
            "upload",
            0,
            None,
            f"colab upload failed (rc={rc}, timed_out={timed_out}): {up_out.strip()[:300]}",
        )

    set_phase("exec")
    local_timeout = float(args.max_minutes * 60 + LOCAL_EXEC_SLACK_S)
    rc, _, timed_out = run_colab(
        colab_cmd,
        [
            "--config",
            str(paths["sessions_json"]),
            "exec",
            "-s",
            session_name,
            "-f",
            str(paths["bootstrap_py"]),
            "--timeout",
            "0",
        ],
        timeout_s=local_timeout,
        logger=logger,
        run_id=args.run_id,
        cmd_name="exec",
        log_path=paths["stdout_log"],
    )
    if timed_out:
        logger.error("exec_local_timeout run_id=%s timeout_s=%.0f", args.run_id, local_timeout)
        return "timed_out", EXIT_TIMEOUT, None, "exec", 0, None, f"local exec exceeded {local_timeout}s"
    if rc != 0:
        logger.error("exec_failed run_id=%s rc=%d", args.run_id, rc)
        return "runner_failed", EXIT_RUNNER_FAILED, None, "exec", 0, None, f"colab exec failed (rc={rc})"

    set_phase("download")
    st_rc, st_out, st_to = run_colab(
        colab_cmd,
        [
            "--config",
            str(paths["sessions_json"]),
            "download",
            "-s",
            session_name,
            REMOTE_STATUS_JSON,
            str(paths["status_json"]),
        ],
        timeout_s=CONTROL_TIMEOUT_S,
        logger=logger,
        run_id=args.run_id,
        cmd_name="download_status",
    )
    chmod_if_regular(paths["status_json"])
    if st_to or st_rc != 0:
        logger.error("download_status_failed run_id=%s rc=%d timed_out=%s", args.run_id, st_rc, st_to)
        return (
            "runner_failed",
            EXIT_RUNNER_FAILED,
            None,
            "download",
            0,
            None,
            f"colab download status.json failed (rc={st_rc}, timed_out={st_to}): {st_out.strip()[:300]}",
        )

    remote_status = read_status_json(paths["status_json"])
    phase = str(remote_status["phase"])
    job_exit = int(remote_status["exit"])
    remote_timed_out = bool(remote_status["timed_out"])

    out_rc, out_err, out_to = run_colab(
        colab_cmd,
        [
            "--config",
            str(paths["sessions_json"]),
            "download",
            "-s",
            session_name,
            REMOTE_OUT_TGZ,
            str(paths["out_tgz"]),
        ],
        timeout_s=CONTROL_TIMEOUT_S,
        logger=logger,
        run_id=args.run_id,
        cmd_name="download_out",
    )
    chmod_if_regular(paths["out_tgz"])
    if out_to or out_rc != 0:
        logger.error("download_out_failed run_id=%s rc=%d timed_out=%s", args.run_id, out_rc, out_to)
        return (
            "runner_failed",
            EXIT_RUNNER_FAILED,
            job_exit,
            phase,
            0,
            None,
            f"colab download out.tgz failed (rc={out_rc}, timed_out={out_to}): {out_err.strip()[:300]}",
        )

    out_files = extract_out_tgz(paths["out_tgz"], paths["out_dir"], logger, args.run_id)
    out_dir_str = str(paths["out_dir"])
    if remote_timed_out:
        return "timed_out", EXIT_TIMEOUT, job_exit, phase, out_files, out_dir_str, None
    if job_exit == 0:
        return "completed", EXIT_OK, job_exit, phase, out_files, out_dir_str, None
    return "job_failed", EXIT_JOB_FAILED, job_exit, phase, out_files, out_dir_str, None


def main(argv: list[str] | None = None) -> int:
    os.umask(0o077)
    started = time.monotonic()
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = int(exc.code or 0)
        return code
    except RunnerError as exc:
        payload = build_summary(
            run_id="",
            status="invocation_error",
            exit_code=exc.exit_code,
            job_exit=None,
            phase=exc.phase,
            accelerator="cpu",
            session=None,
            elapsed_s=round(time.monotonic() - started, 3),
            balance_before=None,
            balance_after=None,
            stop_ok=None,
            stop_verified=None,
            out_dir=None,
            out_files=0,
            artifacts={},
            error=str(exc),
        )
        emit_summary(payload)
        return exc.exit_code

    accelerator = format_accelerator(args.gpu, args.tpu, args.high_mem)
    session_name: str | None = None
    try:
        checked = check_inputs(args)
        args.work_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        work_dir = args.work_dir.resolve()
        if not work_dir.is_dir():
            raise RunnerError(f"--work-dir is not a directory: {work_dir}")
        paths = artifact_paths(work_dir, args.run_id)
        conflicts = [str(p) for p in paths.values() if os.path.lexists(p)]
        if conflicts:
            raise RunnerError("RUN_ID already has artifacts: " + ", ".join(conflicts))
        colab_cmd = resolve_colab()
    except (OSError, UnicodeError, RunnerError) as exc:
        code = exc.exit_code if isinstance(exc, RunnerError) else EXIT_VALIDATION
        payload = build_summary(
            run_id=args.run_id,
            status="invocation_error",
            exit_code=code,
            job_exit=None,
            phase="validate",
            accelerator=accelerator,
            session=None,
            elapsed_s=round(time.monotonic() - started, 3),
            balance_before=None,
            balance_after=None,
            stop_ok=None,
            stop_verified=None,
            out_dir=None,
            out_files=0,
            artifacts={},
            error=str(exc),
        )
        emit_summary(payload)
        return code

    session_name = normalize_session_name(args.run_id)
    artifacts_str = {k: str(v) for k, v in paths.items()}
    logger = setup_logger(paths["run_log"])

    in_cleanup = False
    previous_handlers: dict[int, object] = {}

    def handle_signal(signum: int, _frame: object) -> None:
        if in_cleanup:
            logger.warning("signal_during_cleanup run_id=%s signum=%d", args.run_id, signum)
            return
        raise SignalInterrupt(signum)

    for sig_name in ("SIGTERM", "SIGINT", "SIGHUP"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            previous_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, handle_signal)

    status = "runner_failed"
    exit_code = EXIT_RUNNER_FAILED
    job_exit: int | None = None
    phase: str | None = "prepare"
    error_msg: str | None = None
    balance_before: float | None = None
    balance_after: float | None = None
    stop_ok: bool | None = None
    stop_verified: bool | None = None
    out_files = 0
    out_dir_str: str | None = None
    vm_started = False

    try:
        logger.info(
            "start run_id=%s job_dir=%s entry=%s accelerator=%s max_minutes=%d session=%s has_requirements=%s arg_count=%d",
            args.run_id,
            checked["job_dir"],
            checked["entry"],
            accelerator,
            args.max_minutes,
            session_name,
            checked["requirements"] is not None,
            len(args.arg),
        )
        pack_job_dir(checked["job_dir"], paths["job_tgz"], logger, args.run_id)
        balance_before = fetch_balance(colab_cmd, logger, args.run_id, "before")

        bootstrap_config = {
            "entry": checked["entry"],
            "args": list(args.arg),
            "requirements": checked["requirements"],
            "max_minutes": args.max_minutes,
        }
        bootstrap_code = BOOTSTRAP_TEMPLATE.format(
            config_json_literal=json.dumps(json.dumps(bootstrap_config))
        )
        write_exclusive(paths["bootstrap_py"], bootstrap_code)

        def mark_vm_started() -> None:
            nonlocal vm_started
            vm_started = True

        def set_phase(value: str) -> None:
            nonlocal phase
            phase = value

        status, exit_code, job_exit, phase, out_files, out_dir_str, error_msg = execute_remote_job(
            colab_cmd=colab_cmd,
            args=args,
            paths=paths,
            session_name=session_name,
            logger=logger,
            mark_vm_started=mark_vm_started,
            set_phase=set_phase,
        )
    except SignalInterrupt as exc:
        logger.warning("signal_received run_id=%s signum=%d phase=%s", args.run_id, exc.signum, phase)
        status = "interrupted"
        exit_code = EXIT_INTERRUPTED
        error_msg = str(exc)
    except RunnerError as exc:
        logger.error("runner_error run_id=%s phase=%s msg=%s", args.run_id, exc.phase, exc)
        status = "runner_failed"
        exit_code = exc.exit_code
        if exc.phase:
            phase = exc.phase
        error_msg = str(exc)
    except (OSError, UnicodeError) as exc:
        logger.exception("io_error run_id=%s phase=%s", args.run_id, phase)
        status = "runner_failed"
        exit_code = EXIT_RUNNER_FAILED
        error_msg = str(exc)
    finally:
        in_cleanup = True
        if vm_started:
            try:
                stop_rc, _, stop_to = run_colab(
                    colab_cmd,
                    ["--config", str(paths["sessions_json"]), "stop", "-s", session_name],
                    timeout_s=CONTROL_TIMEOUT_S,
                    logger=logger,
                    run_id=args.run_id,
                    cmd_name="stop",
                )
                stop_ok = not stop_to and stop_rc == 0
            except OSError as exc:
                logger.warning("stop_failed run_id=%s reason=%s", args.run_id, type(exc).__name__)
                stop_ok = False

            try:
                sess_rc, sess_out, sess_to = run_colab(
                    colab_cmd,
                    ["--config", str(paths["sessions_json"]), "sessions"],
                    timeout_s=CONTROL_TIMEOUT_S,
                    logger=logger,
                    run_id=args.run_id,
                    cmd_name="sessions",
                )
                stop_verified = not sess_to and sess_rc == 0 and not session_present_in_output(sess_out, session_name)
            except OSError as exc:
                logger.warning("sessions_check_failed run_id=%s reason=%s", args.run_id, type(exc).__name__)
                stop_verified = False

            balance_after = fetch_balance(colab_cmd, logger, args.run_id, "after")

        for sig, prev in previous_handlers.items():
            signal.signal(sig, prev)

    elapsed_s = round(time.monotonic() - started, 3)
    payload = build_summary(
        run_id=args.run_id,
        status=status,
        exit_code=exit_code,
        job_exit=job_exit,
        phase=phase,
        accelerator=accelerator,
        session=session_name,
        elapsed_s=elapsed_s,
        balance_before=balance_before,
        balance_after=balance_after,
        stop_ok=stop_ok,
        stop_verified=stop_verified,
        out_dir=out_dir_str,
        out_files=out_files,
        artifacts=artifacts_str,
        error=error_msg,
    )
    logger.info(
        "done run_id=%s status=%s exit=%d job_exit=%s phase=%s stop_ok=%s stop_verified=%s cu_used=%s elapsed_s=%.3f",
        args.run_id,
        status,
        exit_code,
        job_exit,
        phase,
        stop_ok,
        stop_verified,
        payload["cu_used"],
        elapsed_s,
    )
    close_logger(logger)
    emit_summary(payload, paths["summary_json"])
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
