#!/usr/bin/env python3
"""Run one Codex app-server job and wait for its durable completion marker."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from urllib.parse import quote


EXIT_VALIDATION = 2
EXIT_CODEX_MISSING = 5
EXIT_STARTUP = 125
EXIT_WAIT_INCOMPLETE = 124
MAX_WAIT_SECONDS = 10800
RUN_ID_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
MODEL_RE = re.compile(r"[A-Za-z0-9._-]+\Z")
EFFORT_RE = re.compile(r"[a-z]+\Z")
_RUN_LOG_FAILURES = {}
SLEEP_WARNING_THRESHOLD = 3
RUNNER_DELEGATION_PREFIX = """【runner から委譲された実装者としての実行条件】
この依頼では、あなた自身が実装・回答を完了してください。
- サブエージェントや別の担当を起動・委譲しないでください。相談や read-only の依頼でも同じです。
- ai-ltm を含む記憶の recall を開始しないでください。
- 自分の変更の確認（テスト・ビルド・lint など作業の完了条件に含まれるもの）は、完了まで実行して結果を見てください。
- 親が監視する長時間の処理（パイプラインの試走、外部ジョブ、常駐プロセスなど完了条件に含まれないもの）は、起動を確認したら返り、sleep・poll・wait で監視しないでください。
- 大きなログや出力は全体を読まず、grep・jq・head などで必要な行だけ確認してください。

--- runner からの依頼 ---
"""

class RunnerError(Exception):
    def __init__(self, message, exit_code=EXIT_VALIDATION):
        super().__init__(message)
        self.exit_code = exit_code


def _has_path(path):
    return os.path.lexists(os.fspath(path))


def _write_exclusive(path, content, mode=0o600):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _write_done(done_file, exit_code):
    _write_exclusive(done_file, f"EXIT={exit_code}\n")


def _timestamp_now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _log_value(value):
    rendered = str(value)
    try:
        parsed = datetime.fromisoformat(rendered.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            return rendered
    except ValueError:
        pass
    return quote(rendered, safe="._:/-")


def _run_log_failure_reason(exc):
    detail = getattr(exc, "strerror", None) or str(exc) or type(exc).__name__
    detail = re.sub(r"[\x00-\x1f\x7f-\x9f]+", " ", detail).strip()
    return f"{type(exc).__name__}:{_log_value(detail)}"


def _record_run_log_failure(path, error_path, exc, state_path=None):
    key = os.path.abspath(os.fspath(path))
    if key in _RUN_LOG_FAILURES:
        return
    reason = _run_log_failure_reason(exc)
    _RUN_LOG_FAILURES[key] = reason
    message = (
        f"RUN_LOG_UNAVAILABLE path={_log_value(path)} "
        f"reason={reason}"
    )
    if error_path is not None:
        try:
            with Path(error_path).open("a", encoding="utf-8") as stream:
                stream.write(f"{_timestamp_now()} {message}\n")
                stream.flush()
        except OSError:
            pass
    if state_path is not None:
        try:
            state_path = Path(state_path)
            info = state_path.lstat()
            if stat.S_ISREG(info.st_mode) and not state_path.is_symlink():
                with state_path.open("a", encoding="utf-8") as stream:
                    stream.write(f"RUN_LOG_AVAILABLE=false\nRUN_LOG_REASON={reason}\n")
                    stream.flush()
        except OSError:
            pass
    print(message, file=sys.stderr, flush=True)


def _log_event(path, run_id, event, *, error_path=None, state_path=None, **fields):
    parts = [f"event={event}", f"run_id={quote(str(run_id), safe='._:/-')}",
             f"at={_timestamp_now()}"]
    parts.extend(f"{key}={_log_value(value)}" for key, value in fields.items())
    try:
        fd = os.open(path, os.O_WRONLY | os.O_APPEND)
        with os.fdopen(fd, "a", encoding="utf-8") as stream:
            stream.write("INFO " + " ".join(parts) + "\n")
            stream.flush()
    except OSError as exc:
        _record_run_log_failure(path, error_path, exc, state_path)


def _check_directory_chain(path, label):
    current = Path(path.anchor)
    components = (None, *path.parts[1:])
    for component in components:
        if component is not None:
            current = current / component
        if not _has_path(current):
            continue
        try:
            info = current.stat()
        except OSError as exc:
            raise RunnerError(f"could not inspect {label} path component {current}: {exc}")
        if not stat.S_ISDIR(info.st_mode):
            raise RunnerError(f"{label} path component must be a directory: {current}")


def _ensure_private_directory(path, label):
    if path.name in ("", ".", ".."):
        raise RunnerError(f"{label} must name a directory")
    canonical_parent = path.parent.resolve(strict=False)
    path = (canonical_parent / path.name).resolve(strict=False)
    _check_directory_chain(path, label)
    try:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
    except OSError as exc:
        raise RunnerError(f"could not create {label} directory {path}: {exc}")
    _check_directory_chain(path, label)
    return path


def _check_regular_file(path, label):
    try:
        info = path.lstat()
    except OSError as exc:
        raise RunnerError(f"could not inspect {label} file {path}: {exc}")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise RunnerError(f"{label} must be a regular non-symlink file: {path}")


def _windows_detached_flags():
    return subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS


def _detached_options():
    if os.name == "nt":
        return {"creationflags": _windows_detached_flags()}
    return {"start_new_session": True}


def _resolve_codex_cmd():
    if os.name == "nt":
        npm_codex = Path.home() / "AppData" / "Roaming" / "npm" / "codex.cmd"
        if npm_codex.is_file():
            return str(npm_codex.resolve())
    command = shutil.which("codex")
    if command:
        command_path = Path(command)
        if not command_path.is_absolute():
            raise RunnerError("resolved Codex CLI path must be absolute", EXIT_CODEX_MISSING)
        resolved = command_path.resolve()
        current_directory = Path.cwd().resolve()
        if resolved == current_directory or current_directory in resolved.parents:
            raise RunnerError("resolved Codex CLI path must not be inside the current working directory",
                              EXIT_CODEX_MISSING)
        return str(resolved)
    raise RunnerError("Codex CLI was not found in the supported locations", EXIT_CODEX_MISSING)


def _paths(work_dir, run_id):
    prefix = f"codex-{run_id}-"
    return {
        "PROMPT_FILE": work_dir / f"{prefix}prompt.md",
        "FINAL_RESPONSE_FILE": work_dir / f"{prefix}last.md",
        "EVENTS_FILE": work_dir / f"{prefix}events.jsonl",
        "STDERR_FILE": work_dir / f"{prefix}err.txt",
        "DONE_FILE": work_dir / f"{prefix}done",
        "HELPER_DONE_FILE": work_dir / f"{prefix}helper-done",
        "STATE_FILE": work_dir / f"{prefix}state.txt",
        "PID_FILE": work_dir / f"{prefix}pid",
        "RUN_LOG_FILE": work_dir / f"{prefix}run.log",
    }


def _read_events(path):
    events = []
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                except (json.JSONDecodeError, UnicodeError):
                    continue
                if isinstance(event, dict):
                    events.append(event)
    except OSError:
        pass
    return events


def _thread_id(events):
    for event in events:
        if event.get("type") == "thread.started":
            value = event.get("thread_id")
            if isinstance(value, str) and value:
                return value
    return None


def _thread_properties(events):
    sandbox = "unavailable"
    for event in events:
        result = event.get("result")
        if not isinstance(result, dict):
            result = {}
        thread = result.get("thread")
        if isinstance(thread, dict):
            candidate = thread.get("sandbox")
            if candidate is not None:
                sandbox = _sandbox_value(candidate)
        candidate = result.get("sandbox")
        if candidate is not None:
            sandbox = _sandbox_value(candidate)
    return sandbox


def _sandbox_value(value):
    if isinstance(value, dict):
        kind = value.get("type")
    else:
        kind = value
    if not isinstance(kind, str) or not kind:
        return "unavailable"
    return {
        "readOnly": "read-only",
        "workspaceWrite": "workspace-write",
        "dangerFullAccess": "danger-full-access",
        "read-only": "read-only",
        "workspace-write": "workspace-write",
        "danger-full-access": "danger-full-access",
    }.get(kind, kind)


def _run_log_failure_from_tail(stderr_tail, run_log_path=None):
    if run_log_path is not None:
        known = _RUN_LOG_FAILURES.get(os.path.abspath(os.fspath(run_log_path)))
        if known is not None:
            return known
    for line in stderr_tail:
        if "RUN_LOG_UNAVAILABLE" not in line:
            continue
        match = re.search(r"\breason=([^\s]+)", line)
        return match.group(1) if match else "run_log_write_failed"
    return None


def _run_log_available(run_log_path, state, stderr_tail):
    if _run_log_failure_from_tail(stderr_tail, run_log_path) is not None:
        return False
    if state.get("RUN_LOG_AVAILABLE") == "false":
        return False
    if run_log_path is None:
        return False
    try:
        return run_log_path.is_file() and not run_log_path.is_symlink()
    except OSError:
        return False


def _run_log_reason(run_log_path, state, stderr_tail):
    failure = _run_log_failure_from_tail(stderr_tail, run_log_path)
    if failure is not None:
        return failure
    state_reason = state.get("RUN_LOG_REASON")
    if state.get("RUN_LOG_AVAILABLE") == "false" and state_reason:
        return state_reason
    if _run_log_available(run_log_path, state, stderr_tail):
        return "available"
    if state_reason not in (None, "unavailable", "not_initialized"):
        return state_reason
    return "not_created"


USAGE_ALIASES = {
    "total_tokens": ("total_tokens", "totalTokens"),
    "input_tokens": ("input_tokens", "inputTokens"),
    "cached_input_tokens": ("cached_input_tokens", "cachedInputTokens"),
    "output_tokens": ("output_tokens", "outputTokens"),
}


def _usage_from_events(events, target_thread_id):
    values = {name: "unavailable" for name in USAGE_ALIASES}
    if not target_thread_id:
        return values
    total_usage = None
    for event in events:
        if event.get("method") != "thread/tokenUsage/updated":
            continue
        params = event.get("params")
        if not isinstance(params, dict) or params.get("threadId") != target_thread_id:
            continue
        token_usage = params.get("tokenUsage")
        if isinstance(token_usage, dict) and isinstance(token_usage.get("total"), dict):
            total_usage = token_usage["total"]
    if total_usage is None:
        return values
    for output_name, aliases in USAGE_ALIASES.items():
        for alias in aliases:
            value = total_usage.get(alias)
            if isinstance(value, int) and not isinstance(value, bool):
                values[output_name] = value
                break
    return values


def _activity_counts(events, target_thread_id):
    child_calls = set()
    sleep_calls = set()
    for index, event in enumerate(events):
        if event.get("method") not in ("item/started", "item/completed"):
            continue
        params = event.get("params")
        if not isinstance(params, dict) or params.get("threadId") != target_thread_id:
            continue
        item = params.get("item")
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        event_key = str(item_id) if isinstance(item_id, str) and item_id else f"event-{index}"
        item_type = re.sub(r"[^a-z]", "", str(item.get("type", "")).lower())
        tool = re.sub(r"[^a-z]", "", str(item.get("tool", "")).lower())
        if item_type in ("collabagenttoolcall", "collabtoolcall") and tool == "spawnagent":
            child_calls.add(event_key)
        elif item_type == "mcptoolcall":
            server = re.sub(r"[^a-z]", "", str(item.get("server", "")).lower())
            if tool in ("sleep", "clocksleep") or ("clock" in server and tool.endswith("sleep")):
                sleep_calls.add(event_key)
        elif item_type == "commandexecution":
            command = item.get("command")
            if isinstance(command, list):
                command = " ".join(str(part) for part in command)
            if isinstance(command, str) and re.search(
                r"(?:^|[\s;&|()])(?:[^\s;&|()]*/)?sleep(?=\s|$)", command
            ):
                sleep_calls.add(event_key)
    return {
        "child_launch_count": len(child_calls),
        "sleep_count": len(sleep_calls),
    }


def _read_key_value(path):
    values = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator:
                values[key] = value
    except OSError:
        pass
    return values


def _state_number(state, key, kind=int):
    raw = state.get(key)
    if raw is None or raw == "unavailable":
        return "unavailable"
    try:
        return kind(raw)
    except (TypeError, ValueError, OverflowError):
        return "unavailable"


def _tail(path, limit=5):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return lines[-limit:]


def _summary(paths=None, requested=None, exit_code=None, error=None, session_file=None,
             wait_status="completed", done_created=True, include_artifacts=True):
    paths = paths or {}
    requested = requested or {}

    def path_value(name):
        path = paths.get(name)
        return str(path) if path is not None else None

    events_path = paths.get("EVENTS_FILE")
    state_path = paths.get("STATE_FILE")
    final_response_path = paths.get("FINAL_RESPONSE_FILE")
    stderr_path = paths.get("STDERR_FILE")
    run_log_path = paths.get("RUN_LOG_FILE")
    events = _read_events(events_path) if include_artifacts and events_path is not None else []
    state = _read_key_value(state_path) if include_artifacts and state_path is not None else {}
    observed_sandbox = _thread_properties(events)
    observed_model = state.get("OBSERVED_MODEL", "unavailable")
    observed_effort = state.get("OBSERVED_EFFORT", "unavailable")
    thread_id = _thread_id(events)

    def match_status(field, observed):
        status = state.get(field)
        if status in ("match", "mismatch", "unavailable") and not (
            status == "unavailable" and observed != "unavailable"
        ):
            return status
        requested_value = requested.get(
            "model" if field == "MODEL_MATCH_STATUS" else "effort"
        )
        if observed == "unavailable" or requested_value is None:
            return "unavailable"
        return "match" if observed == requested_value else "mismatch"

    model_match_status = match_status("MODEL_MATCH_STATUS", observed_model)
    effort_match_status = match_status("EFFORT_MATCH_STATUS", observed_effort)
    requested_model_source = state.get(
        "REQUESTED_MODEL_SOURCE",
        "runner.cli.--model" if requested.get("model") is not None else "unavailable",
    )
    requested_effort_source = state.get(
        "REQUESTED_EFFORT_SOURCE",
        "runner.cli.--effort" if requested.get("effort") is not None else "unavailable",
    )
    requested_sandbox_source = state.get("REQUESTED_SANDBOX_SOURCE")
    if requested_sandbox_source is None:
        sandbox_value = requested.get("sandbox")
        if sandbox_value is None:
            requested_sandbox_source = "unavailable"
        elif sandbox_value == "user-config":
            requested_sandbox_source = "codex.user_config"
        else:
            requested_sandbox_source = "runner.cli.--sandbox"
    body = None
    if include_artifacts and final_response_path is not None:
        try:
            body = final_response_path.read_text(encoding="utf-8")
        except OSError:
            pass
    try:
        event_lines = sum(1 for _ in events_path.open("r", encoding="utf-8")) if include_artifacts and events_path is not None else 0
    except OSError:
        event_lines = 0
    stderr_tail = _tail(stderr_path) if include_artifacts and stderr_path is not None else []
    done_path = path_value("DONE_FILE")
    warnings = []
    if model_match_status == "mismatch":
        warnings.append({
            "field": "model", "requested": requested.get("model"),
            "observed": observed_model,
            "source": state.get("OBSERVED_MODEL_SOURCE", "unavailable"),
        })
    if effort_match_status == "mismatch":
        warnings.append({
            "field": "effort", "requested": requested.get("effort"),
            "observed": observed_effort,
            "source": state.get("OBSERVED_EFFORT_SOURCE", "unavailable"),
        })
    current_tokens = {
        "total_tokens": _state_number(state, "CURRENT_TOTAL_TOKENS"),
        "input_tokens": _state_number(state, "CURRENT_INPUT_TOKENS"),
        "cached_input_tokens": _state_number(state, "CURRENT_CACHED_INPUT_TOKENS"),
        "output_tokens": _state_number(state, "CURRENT_OUTPUT_TOKENS"),
    }
    activity = _activity_counts(events, thread_id)
    if activity["child_launch_count"] >= 1:
        warnings.append({
            "field": "child_launch", "count": activity["child_launch_count"],
            "message": "runner 経由の Codex が子を起動しました。委譲された実装者は自分で作業する規則です",
        })
    if activity["sleep_count"] >= SLEEP_WARNING_THRESHOLD:
        warnings.append({
            "field": "sleep", "count": activity["sleep_count"],
            "message": "sleep による待機が多い実行です。起動後に返る規則です",
        })
    activity.update({
        "model_call_count": _state_number(state, "OBSERVATION_MODEL_CALL_COUNT"),
        "average_context_length_tokens": _state_number(
            state, "OBSERVATION_AVERAGE_CONTEXT_LENGTH_TOKENS", float
        ),
        "average_context_sample_count": _state_number(
            state, "OBSERVATION_CONTEXT_SAMPLE_COUNT"
        ),
        "context_token_sum": _state_number(state, "OBSERVATION_CONTEXT_TOKEN_SUM"),
        "model_call_count_source": "codex_rollout.token_usage_record",
        "activity_event_scope": "runner_thread",
    })
    run_details = {
        "started_at": state.get("STARTED_AT", "unavailable"),
        "ended_at": state.get("ENDED_AT", "unavailable"),
        "elapsed_seconds": _state_number(state, "ELAPSED_SECONDS", float),
        "turn_status": state.get("TURN_STATUS", "unavailable"),
        "last_agent_message_summary": state.get("LAST_AGENT_MESSAGE_SUMMARY", "unavailable"),
        "command_execution_count": _state_number(state, "COMMAND_EXECUTION_COUNT"),
        "command_execution_failure_count": _state_number(
            state, "COMMAND_EXECUTION_FAILURE_COUNT"
        ),
        "heartbeat_count": _state_number(state, "HEARTBEAT_COUNT"),
        "current_tokens": current_tokens,
        "signal": {
            "name": state.get("SIGNAL_NAME", "none"),
            "at": state.get("SIGNAL_AT", "unavailable"),
            "sender_pid": state.get("SIGNAL_SENDER_PID", "unavailable"),
            "sender_pid_reason": state.get("SIGNAL_SENDER_PID_REASON", "unavailable"),
        },
        "rollout_observation": {
            "root": state.get("OBSERVATION_ROLLOUT_ROOT", "unavailable"),
            "root_source": state.get("OBSERVATION_ROLLOUT_ROOT_SOURCE", "unavailable"),
            "thread_id": state.get("OBSERVATION_ROLLOUT_THREAD_ID", "unavailable"),
            "turn_id": state.get("OBSERVATION_ROLLOUT_TURN_ID", "unavailable"),
            "run_started_at": state.get("OBSERVATION_ROLLOUT_STARTED_AT", "unavailable"),
            "candidate_files": _state_number(
                state, "OBSERVATION_ROLLOUT_CANDIDATE_FILES"
            ),
            "readable_files": _state_number(
                state, "OBSERVATION_ROLLOUT_READABLE_FILES"
            ),
            "read_failures": _state_number(
                state, "OBSERVATION_ROLLOUT_READ_FAILURES"
            ),
            "contexts": _state_number(state, "OBSERVATION_ROLLOUT_CONTEXTS"),
            "search_path": state.get(
                "OBSERVATION_ROLLOUT_SEARCH_PATH", "unavailable"
            ),
            "search_pattern": state.get(
                "OBSERVATION_ROLLOUT_SEARCH_PATTERN", "unavailable"
            ),
            "selected_at": state.get("OBSERVATION_ROLLOUT_SELECTED_AT", "unavailable"),
            "selected_path": state.get("OBSERVATION_ROLLOUT_SELECTED_PATH", "unavailable"),
            "reason": state.get("OBSERVATION_ROLLOUT_REASON", "unavailable"),
        },
    }
    return {
        "EXIT": exit_code,
        "thread_id": thread_id,
        "REQUESTED_MODEL": requested.get("model"),
        "REQUESTED_MODEL_SOURCE": requested_model_source,
        "REQUESTED_EFFORT": requested.get("effort"),
        "REQUESTED_EFFORT_SOURCE": requested_effort_source,
        "REQUESTED_SANDBOX": requested.get("sandbox", "user-config"),
        "REQUESTED_SANDBOX_SOURCE": requested_sandbox_source,
        "OBSERVED_MODEL": observed_model,
        "OBSERVED_MODEL_SOURCE": state.get("OBSERVED_MODEL_SOURCE", "unavailable"),
        "OBSERVED_MODEL_REASON": state.get("OBSERVED_MODEL_REASON", "state_not_available"),
        "OBSERVED_EFFORT": observed_effort,
        "OBSERVED_EFFORT_SOURCE": state.get("OBSERVED_EFFORT_SOURCE", "unavailable"),
        "OBSERVED_EFFORT_REASON": state.get("OBSERVED_EFFORT_REASON", "state_not_available"),
        "MODEL_MATCH_STATUS": model_match_status,
        "EFFORT_MATCH_STATUS": effort_match_status,
        "THREAD_DEFAULT_MODEL": state.get("THREAD_DEFAULT_MODEL", "unavailable"),
        "THREAD_DEFAULT_MODEL_SOURCE": state.get("THREAD_DEFAULT_MODEL_SOURCE", "unavailable"),
        "THREAD_DEFAULT_MODEL_REASON": state.get(
            "THREAD_DEFAULT_MODEL_REASON", "thread_default_not_available"
        ),
        "THREAD_DEFAULT_EFFORT": state.get("THREAD_DEFAULT_EFFORT", "unavailable"),
        "THREAD_DEFAULT_EFFORT_SOURCE": state.get("THREAD_DEFAULT_EFFORT_SOURCE", "unavailable"),
        "THREAD_DEFAULT_EFFORT_REASON": state.get(
            "THREAD_DEFAULT_EFFORT_REASON", "thread_default_not_available"
        ),
        "OBSERVED_SANDBOX": observed_sandbox,
        "OBSERVED_CWD": state.get("OBSERVED_CWD", "unavailable"),
        "warnings": warnings,
        "run": run_details,
        "activity": activity,
        "usage": _usage_from_events(events, thread_id),
        "final_response": {"path": path_value("FINAL_RESPONSE_FILE"), "body": body},
        "events": {"path": path_value("EVENTS_FILE"), "lines": event_lines},
        "stderr": {"path": path_value("STDERR_FILE"), "tail": stderr_tail},
        "state": {"path": path_value("STATE_FILE")},
        "log": {
            "path": path_value("RUN_LOG_FILE"),
            "available": _run_log_available(run_log_path, state, stderr_tail),
            "reason": _run_log_reason(run_log_path, state, stderr_tail),
        },
        "done": {
            "path": done_path,
            "created": done_created,
            "exit": exit_code if done_created else None,
        },
        "wait_status": wait_status,
        "helper_done": {"path": path_value("HELPER_DONE_FILE")},
        "pid": {"path": path_value("PID_FILE")},
        "prompt": {"path": path_value("PROMPT_FILE")},
        "SESSION_FILE": str(session_file) if session_file else None,
        "SESSION_META": f"{session_file}.meta" if session_file else None,
        "error": error,
    }


def _emit_summary(summary):
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")), flush=True)


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    prompts = parser.add_mutually_exclusive_group(required=True)
    prompts.add_argument("--prompt-file", type=Path)
    prompts.add_argument("--prompt")
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--sandbox", choices=("read-only",))
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--session-file", type=Path)
    parser.add_argument("--_worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_codex-cmd", help=argparse.SUPPRESS)
    parser.add_argument("--_prompt-output", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_cwd-canonical", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_resume-thread-id", help=argparse.SUPPRESS)
    parser.add_argument("--_session-new", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_session-meta", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_final-response", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_events", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_stderr", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_done", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_helper-done", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_state", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_pid", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--_run-log", type=Path, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def _validate_inputs(args):
    if not MODEL_RE.fullmatch(args.model):
        raise RunnerError("MODEL must match [A-Za-z0-9._-]+")
    if not EFFORT_RE.fullmatch(args.effort):
        raise RunnerError("EFFORT must match [a-z]+")
    if not RUN_ID_RE.fullmatch(args.run_id):
        raise RunnerError("RUN_ID must match [A-Za-z0-9._-]+")
    if not args.cwd.is_absolute():
        raise RunnerError("CWD must be an absolute path")
    if not args.work_dir.is_absolute():
        raise RunnerError("WORK_DIR must be an absolute path")
    if args.work_dir.name in ("", ".", ".."):
        raise RunnerError("WORK_DIR must name a directory")
    cwd = args.cwd.resolve(strict=True)
    if not cwd.is_dir():
        raise RunnerError("CWD must be an existing directory")
    if args.session_file is not None and not args.session_file.is_absolute():
        raise RunnerError("SESSION_FILE must be an absolute path")
    if args.session_file is not None and args.session_file.name in ("", ".", ".."):
        raise RunnerError("SESSION_FILE must name a file")
    if args.prompt_file is not None:
        if not args.prompt_file.is_file():
            raise RunnerError("PROMPT_FILE must be an existing regular file")
        prompt = args.prompt_file.read_text(encoding="utf-8")
    else:
        prompt = args.prompt
    if prompt is None or not prompt.strip():
        raise RunnerError("PROMPT must be non-empty")
    return cwd, f"{RUNNER_DELEGATION_PREFIX}\n{prompt}"


def _session_info(session_file, cwd, sandbox):
    if session_file is None:
        return None, None, False
    parent = _ensure_private_directory(session_file.parent, "SESSION_FILE parent")
    session_file = parent / session_file.name
    meta = Path(f"{session_file}.meta")
    session_present = _has_path(session_file)
    meta_present = _has_path(meta)
    if session_present != meta_present:
        raise RunnerError("SESSION_FILE and SESSION_FILE.meta must both exist or both be absent")
    if not session_present:
        return None, meta, True
    for path in (session_file, meta):
        _check_regular_file(path, "continued session")
    content = session_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    if len(lines) != 1 or not lines[0]:
        raise RunnerError("SESSION_FILE must contain exactly one non-empty thread id line")
    metadata_lines = meta.read_text(encoding="utf-8").splitlines()
    expected = [f"CWD={cwd}", f"SANDBOX={sandbox or ''}"]
    if metadata_lines != expected:
        raise RunnerError("session metadata CWD or SANDBOX does not match this run")
    return lines[0], meta, False


def _artifact_conflicts(paths):
    return [str(path) for path in paths.values() if _has_path(path)]


def _session_artifact_conflicts(session_file, paths):
    if session_file is None:
        return []
    try:
        artifacts = {path.resolve(strict=False) for path in paths.values()}
        candidates = (
            ("SESSION_FILE", session_file),
            ("SESSION_META", Path(f"{session_file}.meta")),
        )
        conflicts = []
        for label, candidate in candidates:
            canonical = candidate.resolve(strict=False)
            if canonical in artifacts:
                conflicts.append(f"{label}={canonical}")
        return conflicts
    except (OSError, RuntimeError) as exc:
        raise RunnerError(f"could not canonicalize SESSION_FILE paths: {exc}")


def _save_session(session_file, meta_file, thread_id, cwd, sandbox, run_id):
    if not thread_id:
        raise OSError("app-server did not return a thread id for the new session")
    session_file.parent.mkdir(parents=True, exist_ok=True)
    if _has_path(session_file) or _has_path(meta_file):
        raise FileExistsError("refusing to overwrite an existing session file or metadata")
    suffix = f".tmp.{run_id}.{os.getpid()}"
    session_temp = Path(f"{session_file}{suffix}")
    meta_temp = Path(f"{meta_file}{suffix}")
    created_targets = []
    created_temps = []
    try:
        _write_exclusive(session_temp, f"{thread_id}\n")
        created_temps.append((session_temp, session_temp.lstat().st_ino))
        _write_exclusive(meta_temp, f"CWD={cwd}\nSANDBOX={sandbox or ''}\n")
        created_temps.append((meta_temp, meta_temp.lstat().st_ino))
        os.link(meta_temp, meta_file)
        created_targets.append((meta_file, meta_temp.lstat().st_ino))
        os.link(session_temp, session_file)
        created_targets.append((session_file, session_temp.lstat().st_ino))
    except Exception:
        for target, inode in reversed(created_targets):
            try:
                if target.lstat().st_ino == inode:
                    target.unlink()
            except OSError:
                pass
        raise
    finally:
        for temp, inode in created_temps:
            try:
                if temp.lstat().st_ino == inode:
                    temp.unlink()
            except FileNotFoundError:
                pass


def _helper_command(codex_cmd, prompt_file, args, paths):
    helper = Path(__file__).resolve().with_name("codex-app-run.py")
    if not helper.is_file():
        raise RunnerError(f"Codex app-server helper is missing: {helper}", EXIT_STARTUP)
    command = [
        sys.executable, str(helper),
        "--codex-cmd", codex_cmd,
        "--prompt-file", str(prompt_file),
        "--model", args.model,
        "--effort", args.effort,
        "--cwd", str(args._cwd_canonical),
        "--out-last", str(paths["FINAL_RESPONSE_FILE"]),
        "--out-events", str(paths["EVENTS_FILE"]),
        "--state-file", str(paths["STATE_FILE"]),
        "--done-file", str(paths["HELPER_DONE_FILE"]),
        "--run-log", str(paths["RUN_LOG_FILE"]),
        "--run-log-reserved",
        "--run-id", args.run_id,
    ]
    if args.sandbox:
        command.extend(["--sandbox", args.sandbox])
    if args._resume_thread_id:
        command.extend(["--thread-id", args._resume_thread_id])
    return command


def _worker(args):
    paths = {
        "PROMPT_FILE": args._prompt_output,
        "FINAL_RESPONSE_FILE": args._final_response,
        "EVENTS_FILE": args._events,
        "STDERR_FILE": args._stderr,
        "DONE_FILE": args._done,
        "HELPER_DONE_FILE": args._helper_done,
        "STATE_FILE": args._state,
        "PID_FILE": args._pid,
        "RUN_LOG_FILE": args._run_log,
    }
    exit_code = EXIT_STARTUP
    done_failed = False
    child = None
    received_signal = None
    received_signal_info = None
    signal_logged = False
    old_handlers = {}
    worker_started_at = _timestamp_now()
    worker_started_monotonic = time.monotonic()

    def note_signal(number, _frame):
        nonlocal received_signal, received_signal_info
        if received_signal is None:
            received_signal = number
            try:
                name = signal.Signals(number).name
            except ValueError:
                name = f"SIG{number}"
            received_signal_info = {"name": name, "at": _timestamp_now()}

    for signum in (signal.SIGINT, signal.SIGTERM):
        old_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, note_signal)
    try:
        os.umask(0o077)
        _log_event(paths["RUN_LOG_FILE"], args.run_id, "worker_start",
                   error_path=paths["STDERR_FILE"],
                   state_path=paths["STATE_FILE"],
                   started_at=worker_started_at, worker_pid=os.getpid())
        if received_signal is not None:
            exit_code = 130
            return exit_code
        helper_command = _helper_command(args._codex_cmd, args._prompt_output, args, paths)
        with args._stderr.open("a", encoding="utf-8") as error_stream:
            child = subprocess.Popen(
                helper_command,
                cwd=str(args._cwd_canonical),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=error_stream,
                **_detached_options(),
            )
            _log_event(paths["RUN_LOG_FILE"], args.run_id, "helper_start",
                       error_path=paths["STDERR_FILE"],
                       state_path=paths["STATE_FILE"],
                       helper_pid=child.pid)
            try:
                _write_exclusive(args._pid, f"{child.pid}\n")
            except OSError as exc:
                error_stream.write(f"runner could not record helper PID: {exc}\n")
                error_stream.flush()
                received_signal = signal.SIGTERM

            while child.poll() is None:
                if received_signal is not None:
                    if received_signal_info is not None:
                        _log_event(
                            paths["RUN_LOG_FILE"], args.run_id, "signal_received",
                            error_path=paths["STDERR_FILE"],
                            state_path=paths["STATE_FILE"],
                            signal_name=received_signal_info["name"],
                            signal_at=received_signal_info["at"],
                            sender_pid="unavailable",
                            sender_pid_reason="python_signal_handler_does_not_expose_sender_pid",
                        )
                        signal_logged = True
                    try:
                        child.send_signal(received_signal)
                    except OSError:
                        pass
                    received_signal = None
                try:
                    child.wait(timeout=0.25)
                except subprocess.TimeoutExpired:
                    continue
            child.wait()
            _log_event(
                paths["RUN_LOG_FILE"], args.run_id, "helper_end",
                error_path=paths["STDERR_FILE"],
                state_path=paths["STATE_FILE"],
                helper_pid=child.pid, exit_code=child.returncode,
                elapsed_s=f"{time.monotonic() - worker_started_monotonic:.3f}",
            )

            helper_exit = None
            try:
                marker = args._helper_done.read_text(encoding="utf-8").splitlines()
                if len(marker) == 1 and re.fullmatch(r"EXIT=[0-9]+", marker[0]):
                    helper_exit = int(marker[0][5:])
            except OSError:
                pass
            if helper_exit is None:
                if child.returncode is not None and child.returncode < 0:
                    helper_exit = 128 - child.returncode
                elif child.returncode is not None:
                    helper_exit = child.returncode
                else:
                    helper_exit = EXIT_STARTUP
                error_stream.write("runner did not find a valid helper EXIT marker\n")
                error_stream.flush()
            exit_code = helper_exit

            if args._session_new:
                events = _read_events(args._events)
                thread_id = _thread_id(events)
                if thread_id:
                    try:
                        _save_session(args.session_file, args._session_meta, thread_id,
                                      args._cwd_canonical, args.sandbox, args.run_id)
                    except OSError as exc:
                        error_stream.write(f"runner could not save the new session: {exc}\n")
                        error_stream.flush()
                        if exit_code == 0:
                            exit_code = EXIT_STARTUP
                elif exit_code == 0:
                    error_stream.write("runner could not save the new session: app-server did not return a thread id\n")
                    error_stream.flush()
                    exit_code = EXIT_STARTUP
    except Exception as exc:
        try:
            with args._stderr.open("a", encoding="utf-8") as error_stream:
                error_stream.write(f"runner failed before helper completion: {type(exc).__name__}: {exc}\n")
        except OSError:
            pass
        if received_signal is not None:
            exit_code = 130
        elif child is not None:
            if child.poll() is None:
                try:
                    child.send_signal(signal.SIGTERM)
                    child.wait()
                except OSError:
                    pass
            exit_code = child.returncode if child.returncode is not None else EXIT_STARTUP
            if exit_code < 0:
                exit_code = 128 - exit_code
    finally:
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
        try:
            if received_signal_info is not None and not signal_logged:
                _log_event(
                    paths["RUN_LOG_FILE"], args.run_id, "signal_received",
                    error_path=paths["STDERR_FILE"],
                    state_path=paths["STATE_FILE"],
                    signal_name=received_signal_info["name"],
                    signal_at=received_signal_info["at"],
                    sender_pid="unavailable",
                    sender_pid_reason="python_signal_handler_does_not_expose_sender_pid",
                )
            _log_event(
                paths["RUN_LOG_FILE"], args.run_id, "worker_end",
                error_path=paths["STDERR_FILE"],
                state_path=paths["STATE_FILE"],
                ended_at=_timestamp_now(), exit_code=exit_code,
                elapsed_s=f"{time.monotonic() - worker_started_monotonic:.3f}",
                signal_name=(received_signal_info or {}).get("name", "none"),
            )
            _write_done(args._done, exit_code)
        except OSError as exc:
            done_failed = True
            try:
                with args._stderr.open("a", encoding="utf-8") as error_stream:
                    error_stream.write(f"runner could not write DONE_FILE: {exc}\n")
            except OSError:
                pass
    return EXIT_STARTUP if done_failed else exit_code


def _worker_args(args, paths, codex_cmd, cwd, resume_thread_id, session_meta, session_new):
    command = [
        sys.executable, str(Path(__file__).resolve()), "--_worker",
        "--prompt", "worker-placeholder",
        "--cwd", str(cwd), "--model", args.model, "--effort", args.effort,
        "--work-dir", str(paths["DONE_FILE"].parent), "--run-id", args.run_id,
        "--_codex-cmd", codex_cmd,
        "--_prompt-output", str(paths["PROMPT_FILE"]),
        "--_cwd-canonical", str(cwd),
        "--_final-response", str(paths["FINAL_RESPONSE_FILE"]),
        "--_events", str(paths["EVENTS_FILE"]),
        "--_stderr", str(paths["STDERR_FILE"]),
        "--_done", str(paths["DONE_FILE"]),
        "--_helper-done", str(paths["HELPER_DONE_FILE"]),
        "--_state", str(paths["STATE_FILE"]),
        "--_pid", str(paths["PID_FILE"]),
        "--_run-log", str(paths["RUN_LOG_FILE"]),
    ]
    if args.sandbox:
        command.extend(["--sandbox", args.sandbox])
    if resume_thread_id:
        command.extend(["--_resume-thread-id", resume_thread_id])
    if session_meta is not None:
        command.extend(["--session-file", str(args.session_file), "--_session-meta", str(session_meta)])
    if session_new:
        command.append("--_session-new")
    return command


def _read_done(done_file):
    try:
        lines = done_file.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None
    except UnicodeError:
        return None
    if len(lines) != 1 or not re.fullmatch(r"EXIT=[0-9]+", lines[0]):
        return None
    return int(lines[0][5:])


def _main(args):
    os.umask(0o077)
    runner_started_at = _timestamp_now()
    runner_started_monotonic = time.monotonic()
    requested = {
        "model": args.model,
        "effort": args.effort,
        "sandbox": args.sandbox or "user-config",
    }
    session_file = args.session_file
    try:
        cwd, prompt = _validate_inputs(args)
    except (OSError, UnicodeError, RuntimeError, RunnerError) as exc:
        code = exc.exit_code if isinstance(exc, RunnerError) else EXIT_VALIDATION
        _emit_summary(_summary(requested=requested, exit_code=code, error=str(exc),
                               session_file=session_file, wait_status="invocation_error",
                               done_created=False, include_artifacts=False))
        return code

    paths = None
    try:
        canonical_work_dir = (args.work_dir.parent.resolve(strict=False) / args.work_dir.name).resolve(strict=False)
        paths = _paths(canonical_work_dir, args.run_id)
        work_dir = _ensure_private_directory(args.work_dir, "WORK_DIR")
        paths = _paths(work_dir, args.run_id)
    except (OSError, RuntimeError, RunnerError) as exc:
        code = exc.exit_code if isinstance(exc, RunnerError) else EXIT_VALIDATION
        _emit_summary(_summary(paths, requested, code, str(exc), session_file,
                               wait_status="invocation_error", done_created=False,
                               include_artifacts=False))
        return code

    conflicts = _artifact_conflicts(paths)
    if conflicts:
        message = "RUN_ID already has artifacts: " + ", ".join(conflicts)
        _emit_summary(_summary(paths, requested, EXIT_VALIDATION, message, session_file,
                               wait_status="invocation_error", done_created=False,
                               include_artifacts=False))
        return EXIT_VALIDATION

    try:
        if session_file is not None:
            session_parent = session_file.parent.resolve(strict=False)
            session_file = session_parent / session_file.name
            args.session_file = session_file
        session_conflicts = _session_artifact_conflicts(session_file, paths)
        if session_conflicts:
            message = "SESSION_FILE paths collide with RUN_ID artifacts: " + ", ".join(session_conflicts)
            _emit_summary(_summary(paths, requested, EXIT_VALIDATION, message, session_file,
                                   wait_status="invocation_error", done_created=False,
                                   include_artifacts=False))
            return EXIT_VALIDATION
        resume_thread_id, session_meta, session_new = _session_info(
            session_file, cwd, args.sandbox)
        if session_file is not None:
            session_file = session_file.parent / session_file.name
            args.session_file = session_file
    except (OSError, UnicodeError, RuntimeError, RunnerError) as exc:
        code = exc.exit_code if isinstance(exc, RunnerError) else EXIT_VALIDATION
        _emit_summary(_summary(paths, requested, code, str(exc), session_file,
                               wait_status="invocation_error", done_created=False,
                               include_artifacts=False))
        return code

    try:
        _write_exclusive(paths["PROMPT_FILE"], prompt)
        _write_exclusive(paths["STDERR_FILE"], "")
    except OSError as exc:
        _emit_summary(_summary(paths, requested, EXIT_VALIDATION,
                               f"could not reserve RUN_ID artifacts: {exc}", session_file,
                               wait_status="invocation_error", done_created=False,
                               include_artifacts=False))
        return EXIT_VALIDATION

    try:
        _write_exclusive(paths["RUN_LOG_FILE"], "")
    except OSError as exc:
        _record_run_log_failure(
            paths["RUN_LOG_FILE"], paths["STDERR_FILE"], exc,
            paths["STATE_FILE"],
        )

    _log_event(paths["RUN_LOG_FILE"], args.run_id, "runner_start",
               error_path=paths["STDERR_FILE"],
               state_path=paths["STATE_FILE"],
               started_at=runner_started_at, requested_model=args.model,
               requested_effort=args.effort, requested_sandbox=requested["sandbox"],
               cwd=cwd)

    try:
        codex_cmd = _resolve_codex_cmd()
    except RunnerError as exc:
        try:
            with paths["STDERR_FILE"].open("a", encoding="utf-8") as error_stream:
                error_stream.write(f"{exc}\n")
        except OSError:
            pass
        _log_event(paths["RUN_LOG_FILE"], args.run_id, "runner_end",
                   error_path=paths["STDERR_FILE"],
                   state_path=paths["STATE_FILE"],
                   ended_at=_timestamp_now(), wait_status="invocation_error",
                   exit_code=exc.exit_code,
                   elapsed_s=f"{time.monotonic() - runner_started_monotonic:.3f}")
        _emit_summary(_summary(paths, requested, exc.exit_code, str(exc), session_file,
                               wait_status="invocation_error", done_created=False,
                               include_artifacts=False))
        return exc.exit_code

    worker_args = _worker_args(args, paths, codex_cmd, cwd,
                               resume_thread_id, session_meta, session_new)
    worker = None
    worker_err = None
    wait_status = "invocation_error"
    result = None
    deadline = time.monotonic() + MAX_WAIT_SECONDS
    try:
        with paths["STDERR_FILE"].open("a", encoding="utf-8") as error_stream:
            try:
                worker = subprocess.Popen(
                    worker_args,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=error_stream,
                    **_detached_options(),
                )
            except OSError as exc:
                worker_err = f"could not start detached runner worker: {exc}"
                error_stream.write(worker_err + "\n")
                error_stream.flush()
                wait_status = "worker_start_failed"
                result = EXIT_STARTUP
        if worker is not None:
            _log_event(paths["RUN_LOG_FILE"], args.run_id, "worker_start",
                       error_path=paths["STDERR_FILE"],
                       state_path=paths["STATE_FILE"],
                       worker_pid=getattr(worker, "pid", "unavailable"))
            while True:
                result = _read_done(paths["DONE_FILE"])
                if result is not None:
                    wait_status = "completed"
                    break
                worker_status = worker.poll()
                if worker_status is not None:
                    result = _read_done(paths["DONE_FILE"])
                    if result is not None:
                        wait_status = "completed"
                        break
                    worker_err = (
                        "detached runner supervisor exited with status "
                        f"{worker_status} without a valid DONE_FILE"
                    )
                    wait_status = "supervisor_exited_without_done"
                    result = None
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    worker_err = (
                        f"runner wait timed out after {MAX_WAIT_SECONDS} seconds; "
                        "the detached supervisor and helper were left running"
                    )
                    wait_status = "timed_out"
                    result = None
                    break
                time.sleep(min(0.1, remaining))
    except OSError as exc:
        worker_err = f"runner could not wait for completion marker: {exc}"
        wait_status = "wait_error"
        result = None
        try:
            with paths["STDERR_FILE"].open("a", encoding="utf-8") as error_stream:
                error_stream.write(worker_err + "\n")
        except OSError:
            pass
    done_created = wait_status == "completed"
    _log_event(paths["RUN_LOG_FILE"], args.run_id, "runner_end",
               error_path=paths["STDERR_FILE"],
               state_path=paths["STATE_FILE"],
               ended_at=_timestamp_now(), wait_status=wait_status,
               exit_code=result if result is not None else "unavailable",
               elapsed_s=f"{time.monotonic() - runner_started_monotonic:.3f}")
    _emit_summary(_summary(paths, requested, result, worker_err, session_file,
                           wait_status=wait_status, done_created=done_created))
    if wait_status == "timed_out":
        return EXIT_WAIT_INCOMPLETE
    if wait_status == "supervisor_exited_without_done" or wait_status == "wait_error":
        return EXIT_STARTUP
    return result if result is not None else EXIT_STARTUP


def main(argv=None):
    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        code = int(exc.code or 0)
        if code != 0:
            _emit_summary(_summary(
                requested={"model": None, "effort": None, "sandbox": None},
                exit_code=code,
                error="invalid command-line arguments",
                wait_status="invocation_error",
                done_created=False,
                include_artifacts=False,
            ))
        return code
    if args._worker:
        required = (args._codex_cmd, args._prompt_output, args._cwd_canonical,
                    args._final_response, args._events, args._stderr, args._done,
                    args._helper_done, args._state, args._pid, args._run_log)
        if any(value is None for value in required):
            return EXIT_VALIDATION
        if args._session_new and (args.session_file is None or args._session_meta is None):
            return EXIT_VALIDATION
        return _worker(args)
    return _main(args)


if __name__ == "__main__":
    raise SystemExit(main())
