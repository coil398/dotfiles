"""Cursor ``stop`` hook adapter.

Official input includes common fields plus ``status`` and ``loop_count``.
Continuation is ``{"followup_message": "..."}``. Aborted/error stops are
allowed. ``loop_count`` is the runtime's own auto-follow-up counter.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

from . import jev_client, logbook, policy
from .codex_hook import Outcome, evaluate
from .config import load_config

AskFn = Any


def _read_payload(stream: Any) -> Dict[str, Any]:
    try:
        raw = stream.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        data = json.loads(raw) if raw.strip() else {}
    except (ValueError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def to_codex_payload(payload: Dict[str, Any], max_continuations: int) -> Optional[Dict[str, Any]]:
    status = payload.get("status")
    if status in ("aborted", "error"):
        return None
    if payload.get("composer_mode") == "ask":
        return None
    conversation = payload.get("conversation_id") or payload.get("session_id")
    if not isinstance(conversation, str) or not conversation:
        return None
    loop_count = payload.get("loop_count")
    try:
        loops = int(loop_count) if loop_count is not None else 0
    except (TypeError, ValueError):
        loops = 0
    if loops >= max_continuations:
        return {
            "_skip": "LIMIT_REACHED",
            "session_id": conversation,
            "turn_id": conversation,
        }
    return {
        "session_id": conversation,
        "turn_id": conversation,
        "transcript_path": payload.get("transcript_path"),
        "cwd": (payload.get("workspace_roots") or [None])[0],
        "hook_event_name": "Stop",
        "model": payload.get("model") or payload.get("model_id"),
        "permission_mode": "plan" if payload.get("composer_mode") == "ask" else "default",
        "stop_hook_active": loops > 0,
        "last_assistant_message": payload.get("last_assistant_message") or payload.get("agent_message"),
    }


def run_hook(stdin: Any, stdout: Any, environ: Optional[Dict[str, str]] = None, ask_fn: AskFn = jev_client.ask) -> int:
    cfg = load_config(environ)
    payload = _read_payload(stdin)
    mapped = to_codex_payload(payload, cfg.max_continuations)
    if mapped is None:
        stdout.write("{}")
        stdout.flush()
        return 0
    if mapped.get("_skip"):
        if cfg.mode != "off":
            logbook.append(
                cfg.state_path(),
                {"verdict": policy.SKIPPED, "reason_code": mapped["_skip"], "action": "allow", "event": "stop"},
                cfg.log_max_bytes,
            )
        stdout.write("{}")
        stdout.flush()
        return 0
    outcome: Outcome = evaluate(mapped, cfg, environ=environ, ask_fn=ask_fn)
    if cfg.mode != "off":
        logbook.append(cfg.state_path(), outcome.record, cfg.log_max_bytes)
    if outcome.blocks:
        stdout.write(json.dumps({"followup_message": outcome.output.get("reason", "")}, ensure_ascii=False))
    else:
        stdout.write("{}")
    stdout.flush()
    return 0


def main() -> int:
    return run_hook(sys.stdin, sys.stdout)
