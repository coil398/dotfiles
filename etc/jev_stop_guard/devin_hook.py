"""Devin CLI ``Stop`` hook adapter.

Devin uses the same ``{"decision":"block","reason":...}`` output as Codex.
Stdin documents ``session_id``, ``prompt_id``, ``stop_hook_active``. A
transcript path is used when present; otherwise the hook fails open.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

from . import jev_client, logbook
from .codex_hook import evaluate
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


def to_codex_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    session = payload.get("session_id") or ""
    prompt = payload.get("prompt_id") or session
    return {
        "session_id": session if isinstance(session, str) else "",
        "turn_id": prompt if isinstance(prompt, str) and prompt else session,
        "transcript_path": payload.get("transcript_path"),
        "cwd": payload.get("cwd") or payload.get("DEVIN_PROJECT_DIR"),
        "hook_event_name": "Stop",
        "model": payload.get("model"),
        "permission_mode": payload.get("permission_mode") or "default",
        "stop_hook_active": payload.get("stop_hook_active") is True,
        "last_assistant_message": payload.get("last_assistant_message"),
    }


def run_hook(stdin: Any, stdout: Any, environ: Optional[Dict[str, str]] = None, ask_fn: AskFn = jev_client.ask) -> int:
    cfg = load_config(environ)
    payload = _read_payload(stdin)
    outcome = evaluate(to_codex_payload(payload), cfg, environ=environ, ask_fn=ask_fn)
    if cfg.mode != "off":
        logbook.append(cfg.state_path(), outcome.record, cfg.log_max_bytes)
    stdout.write(json.dumps(outcome.output, ensure_ascii=False))
    stdout.flush()
    return 0


def main() -> int:
    return run_hook(sys.stdin, sys.stdout)
