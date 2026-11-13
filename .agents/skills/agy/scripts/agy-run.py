#!/usr/bin/env python3
"""Delegate one prompt to agy over ACP and print a one-line JSON summary.

The runner validates inputs, reserves per-run artifacts, starts a detached
supervisor worker that runs agy-acp-run.py, and blocks until the worker
publishes ``agy-<RUN_ID>-done``.  See ../references/runner.md for the contract.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

EXIT_VALIDATION = 2
EXIT_AGY_MISSING = 5
EXIT_WAIT_INCOMPLETE = 124
EXIT_STARTUP = 125
MAX_WAIT_SECONDS = 10800
POLL_SECONDS = 0.5
RUN_ID_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
MODEL_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
SESSION_ID_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
MODES = ("plan", "auto")
HELPER = Path(__file__).resolve().with_name("agy-acp-run.py")

RUNNER_DELEGATION_PREFIX = """【runner から委譲された実行者としての実行条件】
この依頼では、あなた自身が回答・実装を完了してください。
- 別のAI CLI、サブエージェント、`/teamwork`・`/boost`・`/goal`・`/schedule` などの多agent・常駐機能、`agy` Skill を使わないでください。
- ai-ltm を含む記憶の recall を開始しないでください。
- commit・push・外部送信・本番操作をしないでください。
- plan mode の依頼では workspace のファイルを編集せず、回答を本文で返してください。
- 自分の変更の確認（テスト・ビルド・lint など完了条件に含まれるもの）は、完了まで実行して結果を見てください。
- 親が監視する長時間の処理（パイプラインの試走、外部ジョブ、常駐プロセスなど完了条件に含まれないもの）は、起動を確認したら返り、sleep・poll・wait で監視しないでください。
- 大きなログや出力は全体を読まず、必要な行だけ確認してください。

--- runner からの依頼 ---
"""


class RunnerError(Exception):
    def __init__(self, message, exit_code=EXIT_VALIDATION):
        super().__init__(message)
        self.exit_code = exit_code


def timestamp_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_exclusive(path: Path, content: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def append_text(path: Path, text: str) -> None:
    try:
        with path.open("a", encoding="utf-8") as stream:
            stream.write(text)
    except OSError:
        pass


def log_event(path: Path, run_id: str, name: str, **fields) -> None:
    parts = [timestamp_now(), f"run_id={run_id}", f"event={name}"]
    parts.extend(f"{key}={str(value).replace(' ', '_') or chr(34) * 2}" for key, value in fields.items())
    append_text(path, " ".join(parts) + "\n")


def artifact_paths(work_dir: Path, run_id: str) -> dict[str, Path]:
    prefix = f"agy-{run_id}-"
    return {
        "PROMPT_FILE": work_dir / f"{prefix}prompt.md",
        "FINAL_RESPONSE_FILE": work_dir / f"{prefix}last.md",
        "EVENTS_FILE": work_dir / f"{prefix}events.jsonl",
        "STDERR_FILE": work_dir / f"{prefix}err.txt",
        "RUN_LOG_FILE": work_dir / f"{prefix}run.log",
        "DONE_FILE": work_dir / f"{prefix}done",
        "HELPER_DONE_FILE": work_dir / f"{prefix}helper-done",
        "STATE_FILE": work_dir / f"{prefix}state.txt",
        "PID_FILE": work_dir / f"{prefix}pid",
    }


def check_regular_file(path: Path, label: str) -> None:
    info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RunnerError(f"{label} must be a regular non-symlink file: {path}")


def read_done(path: Path):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, UnicodeError):
        return None
    if len(lines) != 1 or not re.fullmatch(r"EXIT=[0-9]+", lines[0]):
        return None
    return int(lines[0][5:])


def read_state(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep:
                values[key] = value
    except (FileNotFoundError, UnicodeError):
        pass
    return values


def json_value(text, default):
    try:
        return json.loads(text) if text is not None else default
    except json.JSONDecodeError:
        return default


def resolve_agy() -> str:
    command = shutil.which("agy")
    if not command:
        raise RunnerError("agy CLI was not found on PATH", EXIT_AGY_MISSING)
    path = Path(command)
    if not path.is_absolute():
        raise RunnerError("resolved agy CLI path must be absolute", EXIT_AGY_MISSING)
    resolved = path.resolve()
    current = Path.cwd().resolve()
    if resolved == current or current in resolved.parents:
        raise RunnerError("resolved agy CLI path must not be inside the current working directory",
                          EXIT_AGY_MISSING)
    return str(resolved)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Delegate one prompt to agy over ACP.")
    prompt = parser.add_mutually_exclusive_group(required=True)
    prompt.add_argument("--prompt-file", type=Path)
    prompt.add_argument("--prompt")
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--session-file", type=Path)
    parser.add_argument("--_worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_agy-cmd", dest="agy_cmd", help=argparse.SUPPRESS)
    parser.add_argument("--_resume-session-id", dest="resume_session_id", help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def validate(args) -> tuple[str, str]:
    if not RUN_ID_RE.fullmatch(args.run_id):
        raise RunnerError("--run-id must match [A-Za-z0-9._-]+")
    if not MODEL_RE.fullmatch(args.model):
        raise RunnerError("--model must match [A-Za-z0-9._-]+")
    for label, path in (("--cwd", args.cwd), ("--work-dir", args.work_dir),
                        ("--session-file", args.session_file)):
        if path is not None and not path.is_absolute():
            raise RunnerError(f"{label} must be an absolute path")
    if not args.cwd.is_dir():
        raise RunnerError(f"--cwd is not an existing directory: {args.cwd}")
    if args.prompt_file is not None:
        if not args.prompt_file.is_absolute():
            raise RunnerError("--prompt-file must be an absolute path")
        prompt = args.prompt_file.read_text(encoding="utf-8")
    else:
        prompt = args.prompt
    if not prompt or not prompt.strip():
        raise RunnerError("prompt must not be empty")
    return str(args.cwd.resolve()), prompt


def session_info(session_file: Path | None, cwd: str, mode: str):
    """Return (resume_session_id, meta_path, is_new)."""
    if session_file is None:
        return None, None, False
    meta = session_file.with_name(session_file.name + ".meta")
    exists = [os.path.lexists(session_file), os.path.lexists(meta)]
    if not any(exists):
        return None, meta, True
    if not all(exists):
        raise RunnerError("SESSION_FILE and its .meta must both exist or both be absent")
    check_regular_file(session_file, "SESSION_FILE")
    check_regular_file(meta, "SESSION_META")
    lines = session_file.read_text(encoding="utf-8").splitlines()
    if len(lines) != 1 or not SESSION_ID_RE.fullmatch(lines[0]):
        raise RunnerError("SESSION_FILE must contain exactly one session id line")
    recorded = {}
    for line in meta.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep:
            recorded[key] = value
    if recorded.get("CWD") != cwd or recorded.get("MODE") != mode:
        raise RunnerError("SESSION_META CWD/MODE do not match this run: "
                          f"recorded CWD={recorded.get('CWD')} MODE={recorded.get('MODE')}")
    return lines[0], meta, False


def publish_session(session_file: Path, meta: Path, session_id: str, cwd: str, mode: str) -> None:
    """Publish the session id and metadata without replacing existing files."""
    temps = []
    linked = []
    try:
        for final, content in ((meta, f"CWD={cwd}\nMODE={mode}\n"), (session_file, f"{session_id}\n")):
            temp = final.with_name(f".{final.name}.{os.getpid()}.tmp")
            write_exclusive(temp, content)
            temps.append((temp, final))
        for temp, final in temps:
            os.link(temp, final)
            linked.append(final)
    except OSError:
        for final in linked:
            try:
                os.unlink(final)
            except OSError:
                pass
        raise
    finally:
        for temp, _ in temps:
            try:
                os.unlink(temp)
            except OSError:
                pass


def worker(args) -> int:
    """Detached supervisor: run the helper, then publish the DONE marker."""
    os.umask(0o077)
    work_dir = args.work_dir
    paths = artifact_paths(work_dir, args.run_id)
    cwd = str(args.cwd)
    exit_code = EXIT_STARTUP
    log_event(paths["RUN_LOG_FILE"], args.run_id, "worker_start", pid=os.getpid())
    try:
        command = [
            sys.executable, str(HELPER),
            "--agy-cmd", args.agy_cmd, "--cwd", cwd, "--model", args.model, "--mode", args.mode,
            "--prompt-file", str(paths["PROMPT_FILE"]), "--events", str(paths["EVENTS_FILE"]),
            "--final-response", str(paths["FINAL_RESPONSE_FILE"]),
            "--state", str(paths["STATE_FILE"]), "--run-log", str(paths["RUN_LOG_FILE"]),
            "--helper-done", str(paths["HELPER_DONE_FILE"]), "--run-id", args.run_id,
        ]
        if args.resume_session_id:
            command += ["--resume-session-id", args.resume_session_id]
        with paths["STDERR_FILE"].open("a", encoding="utf-8") as err:
            helper = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=err, stderr=err)
            try:
                write_exclusive(paths["PID_FILE"], f"{helper.pid}\n")
            except OSError as exc:
                err.write(f"agy worker: could not record helper PID: {exc}\n")
                err.flush()
                helper.terminate()
                helper.wait()
                raise
            exit_code = helper.wait()
        if exit_code < 0:
            exit_code = 128 - exit_code
        if args.session_file is not None and not args.resume_session_id:
            session_id = read_state(paths["STATE_FILE"]).get("SESSION_ID")
            if session_id and SESSION_ID_RE.fullmatch(session_id):
                meta = args.session_file.with_name(args.session_file.name + ".meta")
                try:
                    publish_session(args.session_file, meta, session_id, cwd, args.mode)
                except OSError as exc:
                    append_text(paths["STDERR_FILE"], f"agy worker: session save failed: {exc}\n")
                    if exit_code == 0:
                        exit_code = EXIT_STARTUP
    except OSError as exc:
        append_text(paths["STDERR_FILE"], f"agy worker: helper start failed: {exc}\n")
        exit_code = EXIT_STARTUP
    finally:
        log_event(paths["RUN_LOG_FILE"], args.run_id, "worker_end", exit=exit_code)
        write_exclusive(paths["DONE_FILE"], f"EXIT={exit_code}\n")
    return exit_code


def summary(args, paths, exit_code, wait_status, error=None, include_artifacts=True,
            started_at=None, elapsed=None):
    done_exit = read_done(paths["DONE_FILE"]) if paths and include_artifacts else None
    state = read_state(paths["STATE_FILE"]) if paths and include_artifacts else {}
    observed_model = state.get("OBSERVED_MODEL", "unavailable")
    observed_level = state.get("OBSERVED_THOUGHT_LEVEL", "unavailable")
    observed_mode = state.get("OBSERVED_MODE", "unavailable")
    if observed_model == "unavailable":
        model_match = "unavailable"
    elif args.model in (observed_model, f"{observed_model}-{observed_level}"):
        model_match = "match"
    else:
        model_match = "mismatch"
    mode_match = ("unavailable" if observed_mode == "unavailable"
                  else "match" if observed_mode == args.mode else "mismatch")
    permissions = json_value(state.get("PERMISSION_REJECTED"), [])
    final_body = None
    if paths and include_artifacts:
        try:
            final_body = paths["FINAL_RESPONSE_FILE"].read_text(encoding="utf-8")
        except (FileNotFoundError, UnicodeError):
            final_body = None
    warnings = []
    if permissions:
        warnings.append("permission_rejected")
    if wait_status == "completed" and not final_body:
        warnings.append("empty_final_response")
    if model_match == "mismatch":
        warnings.append("model_mismatch")
    if mode_match == "mismatch":
        warnings.append("mode_mismatch")
    result = {
        "EXIT": exit_code,
        "session_id": state.get("SESSION_ID"),
        "REQUESTED_MODEL": args.model,
        "REQUESTED_MODE": args.mode,
        "OBSERVED_MODEL": observed_model,
        "OBSERVED_THOUGHT_LEVEL": observed_level,
        "OBSERVED_MODE": observed_mode,
        "OBSERVED_SOURCE": "acp.session/update.config_option_update",
        "MODEL_MATCH_STATUS": model_match,
        "MODE_MATCH_STATUS": mode_match,
        "OBSERVED_CWD": str(args.cwd),
        "stop_reason": state.get("STOP_REASON"),
        "usage": json_value(state.get("USAGE"), None),
        "run": {
            "started_at": started_at,
            "ended_at": timestamp_now(),
            "elapsed_seconds": elapsed,
            "agent_version": state.get("AGENT_VERSION"),
            "tool_call_count": int(state.get("TOOL_CALL_COUNT", 0) or 0),
            "tool_call_failed_count": int(state.get("TOOL_CALL_FAILED_COUNT", 0) or 0),
            "permission_rejected_count": len(permissions),
            "permission_rejected": permissions,
            "unknown_requests": json_value(state.get("UNKNOWN_REQUESTS"), []),
            "agy_exit": state.get("AGY_EXIT"),
            "failure": state.get("FAILURE"),
        },
        "final_response": {
            "path": str(paths["FINAL_RESPONSE_FILE"]) if paths else None,
            "body": final_body,
        },
        "warnings": warnings,
        "wait_status": wait_status,
        "done": {
            "path": str(paths["DONE_FILE"]) if paths else None,
            "created": done_exit is not None,
            "exit": done_exit,
        },
        "log": {
            "path": str(paths["RUN_LOG_FILE"]) if paths else None,
            "available": state.get("RUN_LOG_AVAILABLE", "True") == "True" if include_artifacts else False,
        },
        "artifacts": {key: str(value) for key, value in paths.items()} if paths else {},
    }
    if args.session_file is not None:
        result["SESSION_FILE"] = str(args.session_file)
        result["SESSION_META"] = str(args.session_file.with_name(args.session_file.name + ".meta"))
    if error:
        result["error"] = error
    print(json.dumps(result, ensure_ascii=False))
    return exit_code


def main(argv=None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        code = int(exc.code or 0)
        if code != 0:
            print(json.dumps({
                "EXIT": code, "wait_status": "invocation_error",
                "error": "invalid command-line arguments",
                "done": {"path": None, "created": False, "exit": None},
            }, ensure_ascii=False))
        return code
    if args._worker:
        return worker(args)
    os.umask(0o077)
    started_at = timestamp_now()
    started = time.monotonic()
    paths = None
    try:
        cwd, prompt = validate(args)
        args.cwd = Path(cwd)
        args.work_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        args.work_dir = args.work_dir.resolve()
        if not args.work_dir.is_dir():
            raise RunnerError(f"--work-dir is not a directory: {args.work_dir}")
        paths = artifact_paths(args.work_dir, args.run_id)
        conflicts = [str(p) for p in paths.values() if os.path.lexists(p)]
        if conflicts:
            raise RunnerError("RUN_ID already has artifacts: " + ", ".join(conflicts))
        if args.session_file is not None:
            args.session_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            args.session_file = args.session_file.parent.resolve() / args.session_file.name
            meta = args.session_file.with_name(args.session_file.name + ".meta")
            if {args.session_file, meta} & set(paths.values()):
                raise RunnerError("SESSION_FILE paths collide with RUN_ID artifacts")
        resume_id, _meta, _is_new = session_info(args.session_file, cwd, args.mode)
        agy_cmd = resolve_agy()
        write_exclusive(paths["PROMPT_FILE"], RUNNER_DELEGATION_PREFIX + prompt)
        write_exclusive(paths["STDERR_FILE"], "")
        write_exclusive(paths["RUN_LOG_FILE"], "")
    except (OSError, UnicodeError, RunnerError) as exc:
        code = exc.exit_code if isinstance(exc, RunnerError) else EXIT_VALIDATION
        return summary(args, paths, code, "invocation_error", error=str(exc),
                       include_artifacts=False, started_at=started_at,
                       elapsed=round(time.monotonic() - started, 3))

    log_event(paths["RUN_LOG_FILE"], args.run_id, "runner_start", cwd=cwd, model=args.model,
              mode=args.mode, resume=bool(resume_id))
    worker_cmd = [
        sys.executable, str(Path(__file__).resolve()), "--_worker",
        "--prompt", "-", "--cwd", cwd, "--model", args.model, "--mode", args.mode,
        "--work-dir", str(args.work_dir), "--run-id", args.run_id, "--_agy-cmd", agy_cmd,
    ]
    if args.session_file is not None:
        worker_cmd += ["--session-file", str(args.session_file)]
    if resume_id:
        worker_cmd += ["--_resume-session-id", resume_id]
    try:
        with paths["STDERR_FILE"].open("a", encoding="utf-8") as err:
            supervisor = subprocess.Popen(worker_cmd, stdin=subprocess.DEVNULL,
                                          stdout=subprocess.DEVNULL, stderr=err,
                                          start_new_session=True)
    except OSError as exc:
        append_text(paths["STDERR_FILE"], f"agy runner: worker start failed: {exc}\n")
        return summary(args, paths, EXIT_STARTUP, "worker_start_failed", error=str(exc),
                       started_at=started_at, elapsed=round(time.monotonic() - started, 3))

    deadline = started + MAX_WAIT_SECONDS
    try:
        while True:
            done_exit = read_done(paths["DONE_FILE"])
            if done_exit is not None:
                wait_status, exit_code = "completed", done_exit
                break
            if supervisor.poll() is not None:
                done_exit = read_done(paths["DONE_FILE"])
                if done_exit is not None:
                    wait_status, exit_code = "completed", done_exit
                else:
                    wait_status, exit_code = "supervisor_exited_without_done", None
                break
            if time.monotonic() >= deadline:
                wait_status, exit_code = "timed_out", None
                break
            time.sleep(POLL_SECONDS)
    except OSError as exc:
        append_text(paths["STDERR_FILE"], f"agy runner: wait failed: {exc}\n")
        wait_status, exit_code = "wait_error", None
    log_event(paths["RUN_LOG_FILE"], args.run_id, "runner_end", wait_status=wait_status,
              exit=exit_code, elapsed_s=round(time.monotonic() - started, 3))
    summary(args, paths, exit_code, wait_status, started_at=started_at,
            elapsed=round(time.monotonic() - started, 3))
    if exit_code is not None:
        return exit_code
    return EXIT_WAIT_INCOMPLETE if wait_status == "timed_out" else EXIT_STARTUP


if __name__ == "__main__":
    sys.exit(main())
