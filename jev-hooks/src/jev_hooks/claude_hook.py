"""Claude Code ``Stop`` hook adapter.

Claude Code uses the same ``{"decision":"block","reason":...}`` output as
Codex and reports ``stop_hook_active``. The turn is the documented
``prompt_id``; when absent, the latest real user prompt in the transcript
identifies it. A stop while ``background_tasks`` are in flight is a pause for
background work, so it is allowed without evaluation.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

from . import jev_client, logbook, policy
from .codex_hook import evaluate
from .config import Config, load_config
from .transcript import claude_prompt_id

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


def to_codex_payload(payload: Dict[str, Any], cfg: Config) -> Dict[str, Any]:
    session = payload.get("session_id")
    session = session if isinstance(session, str) else ""
    turn = payload.get("prompt_id")
    if not isinstance(turn, str) or not turn:
        turn = claude_prompt_id(payload.get("transcript_path"), cfg.max_transcript_bytes)
    mapped: Dict[str, Any] = {
        "session_id": session,
        "turn_id": turn,
        "transcript_path": payload.get("transcript_path"),
        "cwd": payload.get("cwd"),
        "hook_event_name": "Stop",
        "_runtime": "claude",
        "permission_mode": payload.get("permission_mode") or "default",
        "stop_hook_active": payload.get("stop_hook_active") is True,
        "last_assistant_message": payload.get("last_assistant_message"),
    }
    tasks = payload.get("background_tasks")
    if isinstance(tasks, list) and tasks:
        mapped["_skip"] = "BACKGROUND_TASKS_PENDING"
    return mapped


def run_hook(stdin: Any, stdout: Any, environ: Optional[Dict[str, str]] = None, ask_fn: AskFn = jev_client.ask) -> int:
    cfg = load_config(environ)
    payload = _read_payload(stdin)
    mapped = to_codex_payload(payload, cfg)
    if mapped.get("_skip"):
        if cfg.mode != "off":
            logbook.append(
                cfg.state_path(),
                {"verdict": policy.SKIPPED, "reason_code": mapped["_skip"], "action": "allow", "event": "Stop", "runtime": "claude"},
                cfg.log_max_bytes,
            )
        stdout.write("{}")
        stdout.flush()
        return 0
    outcome = evaluate(mapped, cfg, environ=environ, ask_fn=ask_fn)
    if cfg.mode != "off":
        logbook.append(cfg.state_path(), outcome.record, cfg.log_max_bytes)
    stdout.write(json.dumps(outcome.output, ensure_ascii=False))
    stdout.flush()
    return 0


def main() -> int:
    return run_hook(sys.stdin, sys.stdout)
