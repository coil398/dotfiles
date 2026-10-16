#!/usr/bin/env python3
"""Run one Codex app-server turn over JSON-RPC stdio."""

import argparse
from datetime import datetime
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
from urllib.parse import quote


HANDSHAKE_TIMEOUT_SECONDS = 120
INTERRUPT_GRACE_SECONDS = 10
INTERRUPT_RESPONSE_CODE = -32800
HEARTBEAT_INTERVAL_SECONDS = 30
ROLLOUT_OBSERVATION_INITIAL_INTERVAL_SECONDS = 0.5
ROLLOUT_OBSERVATION_MAX_INTERVAL_SECONDS = 10.0
AGENT_MESSAGE_SUMMARY_LIMIT = 120


def _timestamp_now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _safe_log_value(value):
    rendered = str(value)
    try:
        parsed = datetime.fromisoformat(rendered.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            return rendered
    except ValueError:
        pass
    return quote(rendered, safe="._:/-")


def _agent_message_summary(text):
    normalized = re.sub(r"[\x00-\x1f\x7f-\x9f]+", " ", text)
    normalized = " ".join(normalized.split())
    normalized = re.sub(
        r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]+", r"\1 [REDACTED]", normalized
    )
    normalized = re.sub(
        r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password|authorization)"
        r"\s*[:=]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        normalized,
    )
    normalized = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "[REDACTED]", normalized)
    normalized = re.sub(r"\bgh[pousr]_[A-Za-z0-9_]{12,}\b", "[REDACTED]", normalized)
    normalized = re.sub(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "[REDACTED]", normalized)
    normalized = re.sub(r"\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
                        "[REDACTED]", normalized)
    if len(normalized) > AGENT_MESSAGE_SUMMARY_LIMIT:
        normalized = normalized[:AGENT_MESSAGE_SUMMARY_LIMIT - 3].rstrip() + "..."
    return normalized


class RunLog:
    """Write private, INFO-level, fixed-event key=value lines for one run."""

    def __init__(self, path, run_id, reserved=False, state_path=None):
        self.path = Path(path)
        self.run_id = run_id
        self.state_path = Path(state_path) if state_path is not None else None
        self.stream = None
        self.failure_reason = None
        try:
            if reserved:
                info = self.path.lstat()
                if not self.path.is_file() or self.path.is_symlink():
                    raise AppServerFailure(
                        "reserved run log must be a regular non-symlink file"
                    )
                if info.st_mode & 0o077:
                    raise AppServerFailure("reserved run log must be private")
                self.stream = self.path.open("a", encoding="utf-8")
            else:
                self.stream = self.path.open("x", encoding="utf-8")
        except (OSError, AppServerFailure) as exc:
            self._mark_unavailable(exc)
            return
        self._record_status(True, "available")

    @staticmethod
    def _reason(exc):
        detail = getattr(exc, "strerror", None) or str(exc) or type(exc).__name__
        detail = re.sub(r"[\x00-\x1f\x7f-\x9f]+", " ", detail).strip()
        return f"{type(exc).__name__}:{_safe_log_value(detail)}"

    def _record_status(self, available, reason):
        if self.state_path is None:
            return
        try:
            _append_state(self.state_path, {
                "RUN_LOG_AVAILABLE": str(available).lower(),
                "RUN_LOG_REASON": reason,
            })
        except OSError as exc:
            print(
                f"app-server helper could not update run-log status: {type(exc).__name__}",
                file=sys.stderr, flush=True,
            )

    def _mark_unavailable(self, exc):
        if self.failure_reason is not None:
            return
        self.failure_reason = self._reason(exc)
        stream, self.stream = self.stream, None
        if stream is not None:
            try:
                stream.close()
            except OSError:
                pass
        self._record_status(False, self.failure_reason)
        print(
            f"RUN_LOG_UNAVAILABLE path={_safe_log_value(self.path)} "
            f"reason={self.failure_reason}",
            file=sys.stderr, flush=True,
        )

    def info(self, event, **fields):
        parts = [f"event={event}", f"run_id={_safe_log_value(self.run_id)}",
                 f"at={_timestamp_now()}"]
        for key, value in fields.items():
            rendered = (json.dumps(str(value), ensure_ascii=False)
                        if key == "summary" else _safe_log_value(value))
            parts.append(f"{key}={rendered}")
        if self.stream is None:
            return
        try:
            self.stream.write("INFO " + " ".join(parts) + "\n")
            self.stream.flush()
        except OSError as exc:
            self._mark_unavailable(exc)

    def close(self):
        if self.stream is None:
            return
        try:
            self.stream.flush()
            self.stream.close()
        except OSError as exc:
            self._mark_unavailable(exc)


def _append_state(path, values):
    with Path(path).open("a", encoding="utf-8") as stream:
        for key, value in values.items():
            safe_value = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(value))
            stream.write(f"{key}={safe_value}\n")
        stream.flush()


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
    parser.add_argument("--run-log", required=True)
    parser.add_argument("--run-log-reserved", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--run-id", default="standalone")
    parser.add_argument("--thread-id")
    args = parser.parse_args()
    if not args.codex_cmd.strip():
        parser.error("--codex-cmd must not be empty")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.model):
        parser.error("--model must match [A-Za-z0-9._-]+")
    if not re.fullmatch(r"[a-z]+", args.effort):
        parser.error("--effort must match [a-z]+")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.run_id):
        parser.error("--run-id must match [A-Za-z0-9._-]+")
    if args.thread_id is not None and not args.thread_id:
        parser.error("--thread-id must not be empty")
    return args


def create_autosync_hold():
    state_home = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local/state")
    holds_dir = Path(state_home) / "dotfiles-autosync" / "holds"
    holds_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    hold_path = holds_dir / f"codex-app-run-{os.getpid()}-{time.time_ns()}.hold"
    pending_path = holds_dir / f".{hold_path.name}.pending"
    try:
        with pending_path.open("x", encoding="utf-8") as stream:
            stream.write(f"{os.getpid()}\n")
        os.replace(pending_path, hold_path)
    except Exception:
        try:
            os.unlink(pending_path)
        except OSError:
            pass
        raise
    return hold_path


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
    run_log_path = Path(args.run_log)
    for output in (out_last, out_events):
        if not output.parent.is_dir():
            raise AppServerFailure("output parent directory must already exist")
        if output.exists() or output.is_symlink():
            raise AppServerFailure(f"refusing to overwrite an existing output: {output}")
    if not run_log_path.parent.is_dir():
        raise AppServerFailure("run log parent directory must already exist")
    if not args.run_log_reserved and (run_log_path.exists() or run_log_path.is_symlink()):
        raise AppServerFailure("refusing to overwrite an existing run log")

    last_stream = out_last.open("x", encoding="utf-8")
    try:
        events_stream = out_events.open("x", encoding="utf-8")
    except Exception:
        last_stream.close()
        raise
    try:
        run_log = RunLog(
            run_log_path, args.run_id or "standalone", args.run_log_reserved,
            state_path=args.state_file,
        )
    except Exception:
        last_stream.close()
        events_stream.close()
        raise
    return cwd, prompt, out_last, last_stream, events_stream, run_log


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
        self.name = None
        self.timestamp = None
        self.logged = False
        self.saved_handlers = {}

    def record(self, received_signal, _frame):
        if self.number is None:
            self.number = received_signal
            self.time = time.monotonic()
            try:
                self.name = signal.Signals(received_signal).name
            except ValueError:
                self.name = f"SIG{received_signal}"
            self.timestamp = _timestamp_now()

    def install(self):
        for signum in (signal.SIGTERM, signal.SIGINT):
            self.saved_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, self.record)

    def restore(self):
        for signum, handler in self.saved_handlers.items():
            signal.signal(signum, handler)


class AppServerClient:
    def __init__(self, args, cwd, prompt, out_last, last_stream, events_stream,
                 state_path, run_log, signals, started_at, started_monotonic):
        self.args = args
        self.cwd = cwd
        self.prompt = prompt
        self.out_last = out_last
        self.last_stream = last_stream
        self.events_stream = events_stream
        self.state_path = Path(state_path)
        self.run_log = run_log
        self.started_at = started_at
        self.started_monotonic = started_monotonic
        self.process = None
        self.incoming = queue.Queue()
        self.responses = {}
        self.next_request_id = 1
        self.thread_id = None
        self.thread_id_confirmed = False
        self.thread_event_written = False
        self.turn_id = None
        self.turn_id_confirmed = False
        self.turn_started = False
        self.turn_status = None
        self.final_message = None
        self.last_agent_message = None
        self.last_agent_summary_logged = None
        self.command_items = {}
        self.thread_default_model = "unavailable"
        self.thread_default_model_source = "unavailable"
        self.thread_default_model_reason = "thread_start_response_model_missing"
        self.thread_default_effort = "unavailable"
        self.thread_default_effort_source = "unavailable"
        self.thread_default_effort_reason = "thread_start_response_reasoning_effort_missing"
        self.observed_model = "unavailable"
        self.observed_model_source = "unavailable"
        self.observed_model_reason = "same_thread_turn_context_and_turn_response_model_missing"
        self.observed_effort = "unavailable"
        self.observed_effort_source = "unavailable"
        self.observed_effort_reason = "same_thread_turn_context_and_turn_response_effort_missing"
        self.response_turn_model = None
        self.response_turn_effort = None
        self.codex_home = None
        self.rollout_root = "unavailable"
        self.rollout_root_source = "unavailable"
        self.rollout_search_path = "unavailable"
        self.rollout_search_pattern = "unavailable"
        self.rollout_reason = "not_checked"
        self.rollout_selected_at = "unavailable"
        self.rollout_selected_path = "unavailable"
        self.rollout_candidate_count = 0
        self.rollout_readable_file_count = 0
        self.rollout_read_failure_count = 0
        self.rollout_context_count = 0
        self.last_rollout_check = 0.0
        self.rollout_retry_interval = ROLLOUT_OBSERVATION_INITIAL_INTERVAL_SECONDS
        self.last_observation_state = None
        self.last_state_snapshot = None
        self.state_update_failure_reported = False
        self.latest_usage = {
            "total_tokens": "unavailable",
            "input_tokens": "unavailable",
            "cached_input_tokens": "unavailable",
            "output_tokens": "unavailable",
        }
        self.last_heartbeat = 0.0
        self.heartbeat_count = 0
        self.exit_code = None
        self.signals = signals
        self.interrupt_sent = False
        self.interrupt_response_id = None

    @staticmethod
    def _string_field(owner, key):
        if isinstance(owner, dict):
            value = owner.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    def capture_thread_defaults(self, result):
        thread = result.get("thread") or {}
        model = self._string_field(thread, "model") or self._string_field(result, "model")
        if model:
            self.thread_default_model = model
            self.thread_default_model_source = (
                "app_server.thread_start_response.thread.model"
                if self._string_field(thread, "model") else
                "app_server.thread_start_response.model"
            )
            self.thread_default_model_reason = "available"
        effort = (self._string_field(thread, "reasoningEffort")
                  or self._string_field(result, "reasoningEffort"))
        if effort:
            self.thread_default_effort = effort
            self.thread_default_effort_source = (
                "app_server.thread_start_response.thread.reasoningEffort"
                if self._string_field(thread, "reasoningEffort") else
                "app_server.thread_start_response.reasoningEffort"
            )
            self.thread_default_effort_reason = "available"

    def capture_turn_response(self, turn, source):
        model = self._string_field(turn, "model")
        effort = self._string_field(turn, "effort") or self._string_field(turn, "reasoningEffort")
        rank = {
            "app_server.turn_start_response.turn": 1,
            "app_server.turn_started_notification.turn": 2,
            "app_server.turn_completed_notification.turn": 3,
        }.get(source, 0)
        if model:
            if self.response_turn_model is None or rank >= self.response_turn_model[0]:
                self.response_turn_model = (rank, model, f"{source}.model")
                self.observed_model = model
                self.observed_model_source = f"{source}.model"
                self.observed_model_reason = "available"
        if effort:
            key = "effort" if self._string_field(turn, "effort") else "reasoningEffort"
            if self.response_turn_effort is None or rank >= self.response_turn_effort[0]:
                self.response_turn_effort = (rank, effort, f"{source}.{key}")
                self.observed_effort = effort
                self.observed_effort_source = f"{source}.{key}"
                self.observed_effort_reason = "available"

    def _set_turn_status(self, status, source):
        if not isinstance(status, str) or not status or status == self.turn_status:
            return
        previous = self.turn_status or "not_started"
        self.turn_status = status
        self.run_log.info("turn_status_transition", previous=previous,
                          current=status, source=source)

    def _usage_from_params(self, params):
        if not isinstance(params, dict) or params.get("threadId") != self.thread_id:
            return
        usage = params.get("tokenUsage")
        total = usage.get("total") if isinstance(usage, dict) else None
        if not isinstance(total, dict):
            return
        aliases = {
            "total_tokens": ("total_tokens", "totalTokens"),
            "input_tokens": ("input_tokens", "inputTokens"),
            "cached_input_tokens": ("cached_input_tokens", "cachedInputTokens"),
            "output_tokens": ("output_tokens", "outputTokens"),
        }
        for name, fields in aliases.items():
            for field in fields:
                value = total.get(field)
                if isinstance(value, int) and not isinstance(value, bool):
                    self.latest_usage[name] = value
                    break

    def _maybe_heartbeat(self, force=False):
        now = time.monotonic()
        if not force and now - self.last_heartbeat < HEARTBEAT_INTERVAL_SECONDS:
            return
        self.last_heartbeat = now
        self.heartbeat_count += 1
        usage_fields = {name: value for name, value in self.latest_usage.items()}
        self.run_log.info(
            "heartbeat", elapsed_s=f"{now - self.started_monotonic:.3f}",
            turn_status=self.turn_status or "not_started",
            **usage_fields,
        )

    def _rollout_context(self):
        self.rollout_candidate_count = 0
        self.rollout_readable_file_count = 0
        self.rollout_read_failure_count = 0
        self.rollout_context_count = 0
        self.rollout_selected_at = "unavailable"
        self.rollout_selected_path = "unavailable"
        thread_id = self.thread_id
        turn_id = self.turn_id
        env_home = os.environ.get("CODEX_HOME")
        if env_home:
            codex_home = Path(env_home).expanduser()
            self.rollout_root_source = "CODEX_HOME"
        elif self.codex_home:
            codex_home = Path(self.codex_home).expanduser()
            self.rollout_root_source = "app_server.initialize.codexHome"
        else:
            codex_home = Path.home() / ".codex"
            self.rollout_root_source = "default_codex_home"
        self.rollout_root = str(codex_home)
        sessions_dir = codex_home / "sessions"
        self.rollout_search_path = str(sessions_dir)
        if thread_id:
            self.rollout_search_pattern = (
                "rollout-*.jsonl; filename ends with "
                f"-{thread_id}.jsonl"
            )
        else:
            self.rollout_search_pattern = (
                "rollout-*.jsonl; filename ends with -<thread_id>.jsonl"
            )
        if not thread_id or not turn_id:
            return None, "thread_or_turn_id_unavailable"
        if not codex_home.is_dir():
            return None, "rollout_root_not_found"
        if not sessions_dir.is_dir():
            return None, "sessions_directory_not_found"
        suffix = f"-{thread_id}.jsonl"
        candidates = []
        try:
            for candidate in sessions_dir.rglob("rollout-*.jsonl"):
                if candidate.name.endswith(suffix) and candidate.is_file() and not candidate.is_symlink():
                    candidates.append(candidate)
        except OSError:
            return None, "rollout_search_failed"
        self.rollout_candidate_count = len(candidates)
        if not candidates:
            return None, "same_thread_rollout_not_found"
        try:
            parsed_start = datetime.fromisoformat(self.started_at)
            if parsed_start.tzinfo is None:
                return None, "run_start_timestamp_timezone_missing"
            run_started = parsed_start.timestamp()
        except (TypeError, ValueError):
            return None, "run_start_timestamp_invalid"
        contexts = []
        try:
            ordered_candidates = sorted(candidates, key=lambda item: item.stat().st_mtime_ns)
        except OSError:
            return None, "rollout_file_stat_failed"
        for candidate in ordered_candidates:
            try:
                with candidate.open("r", encoding="utf-8") as stream:
                    self.rollout_readable_file_count += 1
                    for line in stream:
                        try:
                            event = json.loads(line)
                        except (json.JSONDecodeError, UnicodeError):
                            continue
                        if not isinstance(event, dict) or event.get("type") != "turn_context":
                            continue
                        payload = event.get("payload")
                        if not isinstance(payload, dict):
                            continue
                        if payload.get("turn_id") == turn_id:
                            timestamp = event.get("timestamp")
                            try:
                                parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                                parsed_timestamp = (
                                    parsed.timestamp() if parsed.tzinfo is not None else None
                                )
                            except (AttributeError, TypeError, ValueError):
                                parsed_timestamp = None
                            contexts.append((payload, timestamp, parsed_timestamp, candidate))
            except OSError:
                self.rollout_read_failure_count += 1
        if not self.rollout_readable_file_count:
            return None, "rollout_files_read_failed"
        self.rollout_context_count = len(contexts)
        if not contexts:
            return None, "matching_turn_context_not_found"
        eligible = [item for item in contexts
                    if item[2] is not None and item[2] >= run_started]
        if not eligible:
            if any(item[2] is None for item in contexts):
                return None, "matching_turn_context_timestamp_missing_or_invalid"
            return None, "matching_turn_context_precedes_run_start"
        payload, timestamp, _epoch, candidate = max(eligible, key=lambda item: item[2])
        self.rollout_selected_at = timestamp
        self.rollout_selected_path = str(candidate)
        return payload, "available"

    def resolve_observations(self):
        self.last_rollout_check = time.monotonic()
        context, reason = self._rollout_context()
        self.rollout_reason = reason
        if context is not None:
            model = self._string_field(context, "model")
            effort = self._string_field(context, "effort")
            if model:
                self.observed_model = model
                self.observed_model_source = "codex_rollout.turn_context.payload.model"
                self.observed_model_reason = "available"
            else:
                if self.observed_model == "unavailable":
                    self.observed_model_reason = "turn_context_model_missing"
                else:
                    self.observed_model_reason = "turn_context_model_missing;turn_response_used"
            if effort:
                self.observed_effort = effort
                self.observed_effort_source = "codex_rollout.turn_context.payload.effort"
                self.observed_effort_reason = "available"
            else:
                if self.observed_effort == "unavailable":
                    self.observed_effort_reason = "turn_context_effort_missing"
                else:
                    self.observed_effort_reason = "turn_context_effort_missing;turn_response_used"
        else:
            if self.observed_model == "unavailable":
                self.observed_model_reason = f"{reason};turn_response_model_missing"
            if self.observed_effort == "unavailable":
                self.observed_effort_reason = f"{reason};turn_response_effort_missing"

        snapshot = self._observation_state_values()
        if snapshot != self.last_observation_state:
            self.last_observation_state = dict(snapshot)
            self.run_log.info(
                "rollout_observation", root=self.rollout_root,
                root_source=self.rollout_root_source,
                search_path=self.rollout_search_path,
                search_pattern=self.rollout_search_pattern,
                target_thread_id=self.thread_id or "unavailable",
                target_turn_id=self.turn_id or "unavailable",
                run_started_at=self.started_at,
                candidate_files=self.rollout_candidate_count,
                readable_files=self.rollout_readable_file_count,
                read_failures=self.rollout_read_failure_count,
                matching_turn_contexts=self.rollout_context_count,
                selected_timestamp=self.rollout_selected_at,
                reason=reason,
                selected_path=self.rollout_selected_path,
            )
            self.run_log.info(
                "configuration_observation",
                requested_model=self.args.model,
                requested_model_source="runner.cli.--model",
                requested_effort=self.args.effort,
                requested_effort_source="runner.cli.--effort",
                thread_default_model=self.thread_default_model,
                thread_default_model_source=self.thread_default_model_source,
                thread_default_model_reason=self.thread_default_model_reason,
                observed_model=self.observed_model,
                observed_model_source=self.observed_model_source,
                observed_model_reason=self.observed_model_reason,
                model_match_status=self._match_status(
                    self.args.model, self.observed_model
                ),
                thread_default_effort=self.thread_default_effort,
                thread_default_effort_source=self.thread_default_effort_source,
                thread_default_effort_reason=self.thread_default_effort_reason,
                observed_effort=self.observed_effort,
                observed_effort_source=self.observed_effort_source,
                observed_effort_reason=self.observed_effort_reason,
                effort_match_status=self._match_status(
                    self.args.effort, self.observed_effort
                ),
            )

        if snapshot != self.last_state_snapshot:
            values = dict(snapshot)
            values["ELAPSED_SECONDS"] = f"{time.monotonic() - self.started_monotonic:.3f}"
            try:
                _append_state(self.state_path, values)
                self.last_state_snapshot = dict(snapshot)
            except OSError as exc:
                if not self.state_update_failure_reported:
                    print(
                        "app-server helper could not update observation state: "
                        f"{type(exc).__name__}",
                        file=sys.stderr, flush=True,
                    )
                    self.state_update_failure_reported = True

        if reason == "available":
            self.rollout_retry_interval = ROLLOUT_OBSERVATION_INITIAL_INTERVAL_SECONDS
        else:
            self.rollout_retry_interval = min(
                ROLLOUT_OBSERVATION_MAX_INTERVAL_SECONDS,
                self.rollout_retry_interval * 2,
            )

    @staticmethod
    def _match_status(requested, observed):
        if observed == "unavailable":
            return "unavailable"
        return "match" if requested == observed else "mismatch"

    def _observation_state_values(self):
        return {
            "TURN_STATUS": self.turn_status or "not_started",
            "REQUESTED_MODEL_SOURCE": "runner.cli.--model",
            "REQUESTED_EFFORT_SOURCE": "runner.cli.--effort",
            "REQUESTED_SANDBOX_SOURCE": (
                "runner.cli.--sandbox" if self.args.sandbox is not None
                else "codex.user_config"
            ),
            "MODEL_MATCH_STATUS": self._match_status(
                self.args.model, self.observed_model
            ),
            "EFFORT_MATCH_STATUS": self._match_status(
                self.args.effort, self.observed_effort
            ),
            "OBSERVATION_ROLLOUT_ROOT": self.rollout_root,
            "OBSERVATION_ROLLOUT_ROOT_SOURCE": self.rollout_root_source,
            "OBSERVATION_ROLLOUT_SEARCH_PATH": self.rollout_search_path,
            "OBSERVATION_ROLLOUT_SEARCH_PATTERN": self.rollout_search_pattern,
            "OBSERVATION_ROLLOUT_THREAD_ID": self.thread_id or "unavailable",
            "OBSERVATION_ROLLOUT_TURN_ID": self.turn_id or "unavailable",
            "OBSERVATION_ROLLOUT_STARTED_AT": self.started_at,
            "OBSERVATION_ROLLOUT_CANDIDATE_FILES": self.rollout_candidate_count,
            "OBSERVATION_ROLLOUT_READABLE_FILES": self.rollout_readable_file_count,
            "OBSERVATION_ROLLOUT_READ_FAILURES": self.rollout_read_failure_count,
            "OBSERVATION_ROLLOUT_CONTEXTS": self.rollout_context_count,
            "OBSERVATION_ROLLOUT_SELECTED_AT": self.rollout_selected_at,
            "OBSERVATION_ROLLOUT_SELECTED_PATH": self.rollout_selected_path,
            "OBSERVATION_ROLLOUT_REASON": self.rollout_reason,
            "THREAD_DEFAULT_MODEL": self.thread_default_model,
            "THREAD_DEFAULT_MODEL_SOURCE": self.thread_default_model_source,
            "THREAD_DEFAULT_MODEL_REASON": self.thread_default_model_reason,
            "THREAD_DEFAULT_EFFORT": self.thread_default_effort,
            "THREAD_DEFAULT_EFFORT_SOURCE": self.thread_default_effort_source,
            "THREAD_DEFAULT_EFFORT_REASON": self.thread_default_effort_reason,
            "OBSERVED_MODEL": self.observed_model,
            "OBSERVED_MODEL_SOURCE": self.observed_model_source,
            "OBSERVED_MODEL_REASON": self.observed_model_reason,
            "OBSERVED_EFFORT": self.observed_effort,
            "OBSERVED_EFFORT_SOURCE": self.observed_effort_source,
            "OBSERVED_EFFORT_REASON": self.observed_effort_reason,
        }

    def _maybe_resolve_observations(self, force=False):
        if not self.thread_id or not self.turn_id:
            return
        if not force and self.rollout_reason == "available":
            return
        now = time.monotonic()
        if (not force and now - self.last_rollout_check
                < self.rollout_retry_interval):
            return
        self.resolve_observations()

    def _command_counts(self):
        return len(self.command_items), sum(1 for failed in self.command_items.values() if failed)

    def _state_observations(self, ended_at, elapsed):
        command_count, command_failures = self._command_counts()
        signal_name = self.signals.name or "none"
        signal_at = self.signals.timestamp or "unavailable"
        signal_sender_pid = "unavailable"
        signal_sender_reason = (
            "python_signal_handler_does_not_expose_sender_pid"
            if self.signals.number is not None else "no_signal_received"
        )
        return {
            "ENDED_AT": ended_at,
            "ELAPSED_SECONDS": f"{elapsed:.3f}",
            "LAST_AGENT_MESSAGE_SUMMARY": _agent_message_summary(self.last_agent_message or ""),
            "COMMAND_EXECUTION_COUNT": command_count,
            "COMMAND_EXECUTION_FAILURE_COUNT": command_failures,
            "HEARTBEAT_COUNT": self.heartbeat_count,
            "CURRENT_TOTAL_TOKENS": self.latest_usage["total_tokens"],
            "CURRENT_INPUT_TOKENS": self.latest_usage["input_tokens"],
            "CURRENT_CACHED_INPUT_TOKENS": self.latest_usage["cached_input_tokens"],
            "CURRENT_OUTPUT_TOKENS": self.latest_usage["output_tokens"],
            "SIGNAL_NAME": signal_name,
            "SIGNAL_AT": signal_at,
            "SIGNAL_SENDER_PID": signal_sender_pid,
            "SIGNAL_SENDER_PID_REASON": signal_sender_reason,
            **self._observation_state_values(),
        }

    def finish_observations(self):
        self.resolve_observations()
        ended_at = _timestamp_now()
        elapsed = time.monotonic() - self.started_monotonic
        command_count, command_failures = self._command_counts()
        if self.signals.number is not None:
            self.run_log.info(
                "signal_received", signal_name=self.signals.name,
                signal_at=self.signals.timestamp, sender_pid="unavailable",
                sender_pid_reason="python_signal_handler_does_not_expose_sender_pid",
            )
            self.signals.logged = True
        self.run_log.info("command_execution_summary", count=command_count,
                          failed_count=command_failures)
        if (self.observed_model != "unavailable"
                and self.observed_model != self.args.model):
            self.run_log.info(
                "configuration_warning", field="model", requested=self.args.model,
                observed=self.observed_model, source=self.observed_model_source,
                match_status=self._match_status(self.args.model, self.observed_model),
            )
        if (self.observed_effort != "unavailable"
                and self.observed_effort != self.args.effort):
            self.run_log.info(
                "configuration_warning", field="effort", requested=self.args.effort,
                observed=self.observed_effort, source=self.observed_effort_source,
                match_status=self._match_status(self.args.effort, self.observed_effort),
            )
        self.run_log.info(
            "run_end", ended_at=ended_at, elapsed_s=f"{elapsed:.3f}",
            exit_code=self.exit_code if self.exit_code is not None else "unavailable",
            turn_status=self.turn_status or "not_started",
        )
        try:
            _append_state(self.state_path, self._state_observations(ended_at, elapsed))
        except OSError as exc:
            print(f"app-server helper could not update state: {type(exc).__name__}",
                  file=sys.stderr, flush=True)

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
            self._maybe_heartbeat()
            self._maybe_resolve_observations()
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
        self._maybe_heartbeat()
        self._maybe_resolve_observations()
        self.check_interrupt()

    def handle_server_method(self, message):
        method = message.get("method")
        params = message.get("params") or {}
        if method == "thread/tokenUsage/updated":
            self._usage_from_params(params)
            self._maybe_heartbeat(force=True)
            return
        if "id" in message:
            self.refuse_server_request(message, method)
            return
        if method == "thread/started":
            thread = params.get("thread") or {}
            thread_id = thread.get("id")
            if not self.thread_id_confirmed and not self.thread_id:
                if isinstance(thread_id, str) and thread_id:
                    self.thread_id = thread_id
        elif method == "turn/started":
            thread_id = params.get("threadId")
            if not self.thread_id_confirmed or thread_id != self.thread_id:
                return
            turn = params.get("turn") or {}
            self.set_turn_id(turn.get("id"))
            self._set_turn_status(turn.get("status"), "turn/started")
            self.capture_turn_response(
                turn, "app_server.turn_started_notification.turn"
            )
            self._maybe_resolve_observations(force=True)
        elif method == "item/started":
            thread_id = params.get("threadId")
            if not self.thread_id_confirmed or thread_id != self.thread_id:
                return
            item = params.get("item") or {}
            if isinstance(item, dict) and item.get("type") == "commandExecution":
                self.capture_command_execution(item)
                command_count, command_failures = self._command_counts()
                self.run_log.info("command_execution_progress", phase="started",
                                  count=command_count, failed_count=command_failures)
        elif method == "item/completed":
            thread_id = params.get("threadId")
            if not self.thread_id_confirmed or thread_id != self.thread_id:
                return
            item = params.get("item") or {}
            self.capture_agent_message(item)
            if isinstance(item, dict) and item.get("type") == "commandExecution":
                command_count, command_failures = self._command_counts()
                self.run_log.info("command_execution_progress", phase="completed",
                                  count=command_count, failed_count=command_failures)
        elif method == "turn/completed":
            thread_id = params.get("threadId")
            if not self.thread_id_confirmed or thread_id != self.thread_id:
                return
            turn = params.get("turn") or {}
            turn_id = turn.get("id")
            if self.turn_id_confirmed and turn_id != self.turn_id:
                return
            self.set_turn_id(turn_id)
            self.capture_turn_messages(turn.get("items") or [])
            self._set_turn_status(turn.get("status"), "turn/completed")
            self.capture_turn_response(
                turn, "app_server.turn_completed_notification.turn"
            )

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
        self.run_log.info("server_request_refused", method=method, reason=reason)
        print(f"app-server request refused: {method}: {reason}", file=sys.stderr, flush=True)
        self.send(response)

    def set_thread_id(self, thread_id):
        if isinstance(thread_id, str) and thread_id:
            self.thread_id = thread_id
            self.thread_id_confirmed = True
            if not self.thread_event_written:
                self.write_event({"type": "thread.started", "thread_id": thread_id})
                self.thread_event_written = True

    def set_turn_id(self, turn_id, confirmed=False):
        if isinstance(turn_id, str) and turn_id:
            self.turn_id = turn_id
            if confirmed:
                self.turn_id_confirmed = True
            self.check_interrupt()

    def capture_agent_message(self, item):
        if item.get("type") == "commandExecution":
            self.capture_command_execution(item)
            return
        if item.get("type") != "agentMessage" or not isinstance(item.get("text"), str):
            return
        text = item["text"]
        self.last_agent_message = text
        summary = _agent_message_summary(text)
        if summary and summary != self.last_agent_summary_logged:
            self.run_log.info("agent_message_summary", chars=len(text), summary=summary)
            self.last_agent_summary_logged = summary
        if item.get("phase") in (None, "final_answer"):
            self.final_message = text

    def capture_command_execution(self, item):
        if not isinstance(item, dict) or item.get("type") != "commandExecution":
            return
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            item_id = f"anonymous-{len(self.command_items)}"
        exit_code = item.get("exitCode")
        status = item.get("status")
        failed = (
            (isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code != 0)
            or status in ("failed", "error", "cancelled", "interrupted")
            or item.get("isError") is True
        )
        self.command_items[item_id] = self.command_items.get(item_id, False) or failed

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
            self.run_log.info("turn_request", requested_model=self.args.model,
                              requested_effort=self.args.effort,
                              requested_sandbox=self.args.sandbox or "user-config")
            self._maybe_heartbeat(force=True)
            self.start()
            if self.signals.number is not None:
                raise AppServerFailure("interrupted")
            initialize_result = self.request("initialize", {
                "clientInfo": {
                    "name": "codex-runner",
                    "title": "Codex runner",
                    "version": "1",
                }
            })
            candidate_home = initialize_result.get("codexHome")
            if isinstance(candidate_home, str) and candidate_home:
                self.codex_home = candidate_home
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
            self.capture_thread_defaults(thread_result)
            thread = thread_result.get("thread") or {}
            self.set_thread_id(thread.get("id") or self.args.thread_id)
            if not self.thread_id_confirmed:
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
            self.capture_turn_response(turn, "app_server.turn_start_response.turn")
            self._set_turn_status(turn.get("status"), "turn/start_response")
            self.set_turn_id(turn.get("id"), confirmed=True)
            if not self.turn_id and self.turn_status not in ("completed", "interrupted", "failed"):
                raise AppServerFailure("app-server did not return a turn id")
            if self.turn_id:
                self._maybe_resolve_observations(force=True)

            status = self.wait_for_turn()
            self.exit_code = status
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
                self.exit_code = 130
                return 130
            self.terminate_child()
            self.exit_code = 1
            return 1
        except Exception as exc:
            print(f"app-server helper failed: {type(exc).__name__}", file=sys.stderr, flush=True)
            self.terminate_child()
            self.exit_code = 130 if self.signals.number is not None else 1
            return self.exit_code
        finally:
            if self.signals.number is not None and self.process and self.process.poll() is None:
                self.terminate_child()
            else:
                self.close_child()
            try:
                self.finish_observations()
            except Exception as exc:
                print(f"app-server helper could not finish observations: {type(exc).__name__}",
                      file=sys.stderr, flush=True)


def main():
    signals = RunSignals()
    signals.install()
    args = None
    last_stream = events_stream = None
    run_log = None
    client = None
    hold_path = None
    status = 125
    try:
        args = parse_args()
        os.umask(0o077)
        started_epoch = int(time.time())
        started_at = _timestamp_now()
        started_monotonic = time.monotonic()
        done_file = Path(args.done_file)
        if done_file.exists() or done_file.is_symlink():
            raise AppServerFailure(f"refusing to overwrite an existing output: {done_file}")
        cwd = Path(args.cwd).resolve(strict=True)
        if not cwd.is_dir():
            raise AppServerFailure("--cwd must be a directory")
        with Path(args.state_file).open("x", encoding="utf-8") as state_stream:
            state_stream.write(
                f"START_EPOCH={started_epoch}\n"
                f"STARTED_AT={started_at}\n"
                f"OBSERVED_CWD={cwd}\n"
                f"REQUESTED_MODEL={args.model}\n"
                "REQUESTED_MODEL_SOURCE=runner.cli.--model\n"
                f"REQUESTED_EFFORT={args.effort}\n"
                "REQUESTED_EFFORT_SOURCE=runner.cli.--effort\n"
                f"REQUESTED_SANDBOX={args.sandbox or 'user-config'}\n"
                f"REQUESTED_SANDBOX_SOURCE={'runner.cli.--sandbox' if args.sandbox is not None else 'codex.user_config'}\n"
                "MODEL_MATCH_STATUS=unavailable\n"
                "EFFORT_MATCH_STATUS=unavailable\n"
                "RUN_LOG_AVAILABLE=unavailable\n"
                "RUN_LOG_REASON=not_initialized\n"
                "OBSERVATION_ROLLOUT_SEARCH_PATH=unavailable\n"
                "OBSERVATION_ROLLOUT_SEARCH_PATTERN=unavailable\n"
                "THREAD_DEFAULT_MODEL=unavailable\n"
                "THREAD_DEFAULT_MODEL_SOURCE=unavailable\n"
                "THREAD_DEFAULT_MODEL_REASON=thread_start_response_not_received\n"
                "THREAD_DEFAULT_EFFORT=unavailable\n"
                "THREAD_DEFAULT_EFFORT_SOURCE=unavailable\n"
                "THREAD_DEFAULT_EFFORT_REASON=thread_start_response_not_received\n"
                "OBSERVED_MODEL=unavailable\n"
                "OBSERVED_MODEL_SOURCE=unavailable\n"
                "OBSERVED_MODEL_REASON=same_thread_turn_context_and_turn_response_model_missing\n"
                "OBSERVED_EFFORT=unavailable\n"
                "OBSERVED_EFFORT_SOURCE=unavailable\n"
                "OBSERVED_EFFORT_REASON=same_thread_turn_context_and_turn_response_effort_missing\n"
            )
        status = 2
        cwd, prompt, out_last, last_stream, events_stream, run_log = create_private_outputs(args)
        run_log.info("run_start", started_at=started_at,
                     requested_model=args.model, requested_effort=args.effort,
                     requested_model_source="runner.cli.--model",
                     requested_effort_source="runner.cli.--effort",
                     requested_sandbox=args.sandbox or "user-config", cwd=cwd)
        client = AppServerClient(
            args, cwd, prompt, out_last, last_stream, events_stream,
            args.state_file, run_log, signals, started_at, started_monotonic,
        )
        hold_path = create_autosync_hold()
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
                if run_log is not None and not signals.logged:
                    run_log.info(
                        "signal_received", signal_name=signals.name,
                        signal_at=signals.timestamp, sender_pid="unavailable",
                        sender_pid_reason="python_signal_handler_does_not_expose_sender_pid",
                    )
                    signals.logged = True
                    try:
                        _append_state(args.state_file, {
                            "SIGNAL_NAME": signals.name,
                            "SIGNAL_AT": signals.timestamp,
                            "SIGNAL_SENDER_PID": "unavailable",
                            "SIGNAL_SENDER_PID_REASON":
                                "python_signal_handler_does_not_expose_sender_pid",
                        })
                    except OSError:
                        pass
            if hold_path is not None:
                try:
                    os.unlink(hold_path)
                except FileNotFoundError:
                    pass
                except OSError as exc:
                    print(f"app-server helper could not remove autosync hold: {exc}", file=sys.stderr)
                    status = 125
            if signals.number is not None:
                status = 130
            if run_log is not None:
                if client is None:
                    run_log.info("run_end", ended_at=_timestamp_now(), exit_code=status,
                                 turn_status="not_started")
                try:
                    run_log.close()
                except OSError as exc:
                    print(f"app-server helper could not close run log: {type(exc).__name__}",
                          file=sys.stderr, flush=True)
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
