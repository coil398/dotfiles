"""Codex ``Stop`` hook: decide whether requested work was abandoned.

Input (stdin): Codex ``stop.command.input`` JSON. Output (stdout): ``{}`` to
allow the stop, or ``{"decision": "block", "reason": ...}`` to continue the
turn. Any failure is fail-open (``{}``) and exits 0.

Flow: cheap gates (mode, event, plan mode, duplicate, limit) -> bounded
transcript read -> local gates (abort, steer, progress, context) -> one Jev
request -> combine -> persist state -> emit.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from . import VERSION, jev_client, logbook, policy
from .config import Config, load_config, resolve_api_key
from .state import LockBusy, SessionState, StateError, StateStore, event_fingerprint
from .transcript import TranscriptError, TurnContext, load_turn_context

BUDGET_MARGIN_S = 0.3
MIN_API_BUDGET_S = 0.5
LOCK_TIMEOUT_S = 0.5

AskFn = Callable[..., jev_client.JevResult]


@dataclass
class Outcome:
    output: Dict[str, Any]
    record: Dict[str, Any] = field(default_factory=dict)

    @property
    def blocks(self) -> bool:
        return self.output.get("decision") == "block"


def _base_record(payload: Dict[str, Any], cfg: Config, started: float) -> Dict[str, Any]:
    return {
        "ts": logbook.now_iso(),
        "version": VERSION,
        "event": payload.get("hook_event_name"),
        "session_id": payload.get("session_id"),
        "turn_id": payload.get("turn_id"),
        "stop_hook_active": payload.get("stop_hook_active"),
        "mode": cfg.mode,
        "verdict": policy.SKIPPED,
        "reason_code": "",
        "action": "allow",
        "elapsed_ms": 0,
        "_started": started,
    }


def _finish(record: Dict[str, Any], output: Dict[str, Any]) -> Outcome:
    started = record.pop("_started", None)
    if started is not None:
        record["elapsed_ms"] = int((time.monotonic() - started) * 1000)
    return Outcome(output=output, record=record)


def _skip(record: Dict[str, Any], code: str, detail: str = "", verdict: str = policy.SKIPPED) -> Outcome:
    record["verdict"] = verdict
    record["reason_code"] = code
    if detail:
        record["detail"] = detail
    return _finish(record, {})


def _transcript_summary(ctx: TurnContext) -> Dict[str, Any]:
    return {
        "lines": ctx.total_lines,
        "window_truncated": ctx.window_truncated,
        "found_turn_start": ctx.found_turn_start,
        "user_messages": len(ctx.user_messages),
        "tool_records": len(ctx.tool_records),
        "tool_failed": ctx.failed_tool_records,
        "files_changed": len(ctx.files_changed),
        "hook_prompts_in_turn": ctx.hook_prompts_in_turn,
        "records_since_last_continuation": ctx.records_since_last_continuation,
        "compaction_seen": ctx.compaction_seen,
        "parse_errors": ctx.parse_errors,
    }


def evaluate(
    payload: Dict[str, Any],
    cfg: Config,
    *,
    environ: Optional[Dict[str, str]] = None,
    ask_fn: AskFn = jev_client.ask,
    dry_run: bool = False,
    store: Optional[StateStore] = None,
) -> Outcome:
    started = time.monotonic()
    record = _base_record(payload, cfg, started)

    if cfg.mode == "off":
        return _skip(record, "OFF")
    if payload.get("hook_event_name") != "Stop":
        return _skip(record, "NOT_STOP_EVENT")
    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")
    if not isinstance(session_id, str) or not session_id or not isinstance(turn_id, str) or not turn_id:
        return _skip(record, "MISSING_IDS")
    if payload.get("permission_mode") == "plan":
        return _skip(record, "PLAN_MODE", verdict=policy.ALLOW_STOP)

    stop_hook_active = payload.get("stop_hook_active") is True
    last_message = payload.get("last_assistant_message")
    if last_message is not None and not isinstance(last_message, str):
        last_message = None
    fingerprint = event_fingerprint(turn_id, last_message)

    store = store or StateStore(cfg.state_path())
    try:
        with store.locked(session_id, LOCK_TIMEOUT_S) as state:
            return _evaluate_locked(
                payload, cfg, record, state, store, fingerprint, stop_hook_active, last_message, environ, ask_fn, dry_run
            )
    except LockBusy:
        return _skip(record, "LOCK_BUSY")
    except StateError as exc:
        return _skip(record, "STATE_ERROR", str(exc))


def _evaluate_locked(
    payload: Dict[str, Any],
    cfg: Config,
    record: Dict[str, Any],
    state: SessionState,
    store: StateStore,
    fingerprint: str,
    stop_hook_active: bool,
    last_message: Optional[str],
    environ: Optional[Dict[str, str]],
    ask_fn: AskFn,
    dry_run: bool,
) -> Outcome:
    turn_id = payload["turn_id"]
    started = record["_started"]

    # Continuation accounting. A new turn_id means a real user turn started.
    # stop_hook_active=false means Codex has not continued this turn at all,
    # which is authoritative even if stale state says otherwise.
    if state.turn_id != turn_id:
        state.turn_id = turn_id
        state.continuations = 0
        state.last_fingerprint = ""
        state.last_verdict = ""
    elif not stop_hook_active and state.last_fingerprint != fingerprint:
        # Same turn id but Codex reports no continuation yet: trust Codex over
        # stale state. (An identical fingerprint is a duplicate, handled below.)
        state.continuations = 0
    if stop_hook_active and state.continuations == 0:
        # This turn was already continued, but not by a block we recorded
        # (another Stop hook, or lost state). Count it against the limit.
        state.continuations = 1
        record["prior_continuation_unknown"] = True
    record["continuations"] = state.continuations

    def persist(verdict: str) -> Optional[str]:
        state.last_fingerprint = fingerprint
        state.last_verdict = verdict
        if dry_run:
            return None
        try:
            store.save(state)
        except StateError as exc:
            return str(exc)
        return None

    if state.last_fingerprint == fingerprint:
        return _skip(record, "DUPLICATE_EVENT")
    if state.continuations >= cfg.max_continuations:
        persist(policy.SKIPPED)
        return _skip(record, "LIMIT_REACHED", f"{state.continuations}/{cfg.max_continuations}")

    try:
        ctx = load_turn_context(payload.get("transcript_path"), turn_id, cfg.max_transcript_bytes, policy.MAX_USER_MESSAGES)
    except TranscriptError as exc:
        persist(policy.SKIPPED)
        return _skip(record, "TRANSCRIPT_UNREADABLE", str(exc))
    record["transcript"] = _transcript_summary(ctx)

    if ctx.turn_aborted:
        persist(policy.ALLOW_STOP)
        return _skip(record, "TURN_ABORTED", verdict=policy.ALLOW_STOP)
    if ctx.user_message_after_last_assistant:
        persist(policy.ALLOW_STOP)
        return _skip(record, "USER_STEERED", verdict=policy.ALLOW_STOP)
    if not ctx.user_messages:
        persist(policy.SKIPPED)
        return _skip(record, "INSUFFICIENT_CONTEXT", "no user request found in transcript window")
    if stop_hook_active and ctx.hook_prompts_in_turn > 0 and ctx.records_since_last_continuation == 0:
        persist(policy.SKIPPED)
        return _skip(record, "NO_PROGRESS", "no execution records since last continuation")
    if not last_message and not ctx.last_assistant_text:
        persist(policy.SKIPPED)
        return _skip(record, "INSUFFICIENT_CONTEXT", "no assistant message")

    state_obj = policy.build_state(ctx, last_message, state.continuations)
    record["state_chars"] = len(json.dumps(state_obj, ensure_ascii=False))
    if dry_run:
        record["jev_state"] = state_obj

    api_key, key_source = resolve_api_key(environ)
    record["api_key_source"] = key_source
    if not api_key:
        persist(policy.SKIPPED)
        return _skip(record, "NO_API_KEY")

    remaining = cfg.total_timeout_s - (time.monotonic() - started) - BUDGET_MARGIN_S
    if remaining < MIN_API_BUDGET_S:
        persist(policy.SKIPPED)
        return _skip(record, "BUDGET_EXCEEDED", f"remaining={remaining:.2f}s")
    api_timeout = min(cfg.api_timeout_s, remaining)

    try:
        result = ask_fn(
            api_url=cfg.api_url,
            api_key=api_key,
            model=cfg.model,
            state=state_obj,
            questions=policy.QUESTIONS,
            timeout_s=api_timeout,
        )
    except jev_client.JevError as exc:
        persist(policy.SKIPPED)
        return _skip(record, exc.code, exc.detail)
    record["api_ms"] = result.elapsed_ms
    record["api_model"] = result.model
    record["usage"] = result.usage
    record["answers"] = {k: v.as_log() for k, v in result.answers.items()}
    record["threshold"] = cfg.confidence_threshold

    decision = policy.combine(result.answers, cfg.confidence_threshold)
    record["verdict"] = decision.verdict
    record["reason_code"] = decision.reason_code
    if decision.detail:
        record["detail"] = decision.detail

    if not decision.continues:
        persist(decision.verdict)
        return _finish(record, {})

    if cfg.mode == "observe":
        record["action"] = "observe"
        persist(decision.verdict)
        return _finish(record, {})

    state.continuations += 1
    record["continuations"] = state.continuations
    err = persist(decision.verdict)
    if err is not None:
        # Cannot guarantee the limit without persisted state: fail open.
        state.continuations -= 1
        record["continuations"] = state.continuations
        return _skip(record, "STATE_ERROR", err)
    record["action"] = "block"
    return _finish(record, {"decision": "block", "reason": policy.REASON_TEXT[decision.verdict]})


# ---- CLI ---------------------------------------------------------------


def _read_payload(stream: Any) -> Dict[str, Any]:
    try:
        raw = stream.read()
        data = json.loads(raw) if raw.strip() else {}
    except (ValueError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def run_hook(stdin: Any, stdout: Any, environ: Optional[Dict[str, str]] = None) -> int:
    cfg = load_config(environ)
    payload = _read_payload(stdin)
    try:
        outcome = evaluate(payload, cfg, environ=environ)
    except Exception as exc:  # noqa: BLE001 - fail open, never break the agent
        outcome = Outcome(
            output={},
            record={
                "ts": logbook.now_iso(),
                "version": VERSION,
                "event": payload.get("hook_event_name"),
                "session_id": payload.get("session_id"),
                "turn_id": payload.get("turn_id"),
                "mode": cfg.mode,
                "verdict": policy.SKIPPED,
                "reason_code": "INTERNAL_ERROR",
                "detail": exc.__class__.__name__,
                "action": "allow",
            },
        )
    if cfg.mode != "off":
        if cfg.warnings:
            outcome.record["config_warnings"] = list(cfg.warnings)
        logbook.append(cfg.state_path(), outcome.record, cfg.log_max_bytes)
    stdout.write(json.dumps(outcome.output, ensure_ascii=False))
    stdout.flush()
    return 0


def explain(stdin: Any, stdout: Any, environ: Optional[Dict[str, str]] = None) -> int:
    """Run the full pipeline in observe mode without persisting; print the record."""
    from dataclasses import replace

    cfg = replace(load_config(environ), mode="observe")
    payload = _read_payload(stdin)
    outcome = evaluate(payload, cfg, environ=environ, dry_run=True)
    stdout.write(json.dumps(outcome.record, ensure_ascii=False, indent=2, default=str) + "\n")
    return 0


def main(argv: Optional[list] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--doctor":
        from .doctor import doctor

        return doctor(sys.stdout)
    if args and args[0] == "--explain":
        return explain(sys.stdin, sys.stdout)
    if args and args[0] in ("-h", "--help"):
        sys.stdout.write(
            "usage: jev-stop-guard-codex-hook.py [--doctor | --explain]\n"
            "  (no args)  read Codex Stop payload on stdin, write hook output JSON\n"
            "  --doctor   print configuration / key / state / registration diagnostics\n"
            "  --explain  evaluate a Stop payload from stdin without side effects and print the record\n"
        )
        return 0
    return run_hook(sys.stdin, sys.stdout)
