"""``--doctor``: show effective configuration, key presence, state and Codex registration."""

from __future__ import annotations

import os
import platform
import re
import sys
from pathlib import Path
from typing import Any, List

from . import VERSION, logbook
from .config import API_KEY_ENV, load_config, resolve_api_key, secret_file_path

_HOOK_SCRIPT = "jev-stop-guard-codex-hook.py"


def _codex_registration(lines: List[str]) -> None:
    codex_home = Path(os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex"))
    config = codex_home / "config.toml"
    lines.append(f"codex config      : {config}" + (" (symlink -> %s)" % os.readlink(config) if config.is_symlink() else ""))
    if not config.is_file():
        lines.append("codex hook        : config.toml not found")
        return
    try:
        text = config.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        lines.append(f"codex hook        : config unreadable ({exc.__class__.__name__})")
        return
    registered = _HOOK_SCRIPT in text and "[[hooks.Stop]]" in text
    lines.append(f"codex Stop hook   : {'registered' if registered else 'NOT registered (run: bash etc/sync-codex.sh)'}")
    hooks_enabled = re.search(r"^\s*hooks\s*=\s*false", text, re.M) is None
    lines.append(f"codex features.hooks: {'enabled' if hooks_enabled else 'DISABLED'}")
    trust_keys = re.findall(r'^\[hooks\.state\."([^"]+:stop:\d+:\d+)"\]', text, re.M)
    if registered:
        user_trust = [k for k in trust_keys if "jev-stop-guard" in k or k.endswith("config.toml:stop:0:0") or "/.codex/config.toml:stop:" in k]
        if user_trust:
            lines.append("codex hook trust  : user Stop " + ", ".join(user_trust))
        else:
            lines.append("codex hook trust  : user Stop not trusted yet -> Codex CLI で /hooks を開き jev-stop-guard を trust")
        other = [k for k in trust_keys if k not in user_trust]
        if other:
            lines.append("                    (other Stop trusts: " + str(len(other)) + " project entries)")


def doctor(out: Any) -> int:
    cfg = load_config()
    key, source = resolve_api_key()
    lines: List[str] = []
    lines.append(f"jev-stop-guard {VERSION}")
    lines.append(f"python            : {platform.python_version()} ({sys.executable})")
    lines.append(f"config file       : {cfg.source_file or '(none; defaults)'}")
    lines.append(f"mode              : {cfg.mode}")
    lines.append(f"model             : {cfg.model}")
    lines.append(f"api_url           : {cfg.api_url}")
    lines.append(f"confidence_threshold: {cfg.confidence_threshold}")
    lines.append(f"timeouts          : api {cfg.api_timeout_s}s / total {cfg.total_timeout_s}s")
    lines.append(f"max_continuations : {cfg.max_continuations}")
    lines.append(f"api key           : {'present' if key else 'MISSING'} (source: {source}; env {API_KEY_ENV} or {secret_file_path()})")
    state_dir = cfg.state_path()
    writable = os.access(state_dir, os.W_OK) if state_dir.exists() else os.access(state_dir.parent, os.W_OK) if state_dir.parent.exists() else False
    lines.append(f"state dir         : {state_dir} ({'writable' if writable else 'NOT writable / missing parent'})")
    lines.append(f"log               : {logbook.log_path(state_dir)}")
    for w in cfg.warnings:
        lines.append(f"config warning    : {w}")
    _codex_registration(lines)
    recent = logbook.tail(state_dir, 5)
    if recent:
        lines.append("recent decisions  :")
        for rec in recent:
            lines.append(
                "  {ts} verdict={verdict} reason={reason} action={action} cont={cont} {ms}ms".format(
                    ts=rec.get("ts"),
                    verdict=rec.get("verdict"),
                    reason=rec.get("reason_code"),
                    action=rec.get("action"),
                    cont=rec.get("continuations", "-"),
                    ms=rec.get("elapsed_ms", "-"),
                )
            )
    else:
        lines.append("recent decisions  : (none logged yet)")
    out.write("\n".join(lines) + "\n")
    return 0
