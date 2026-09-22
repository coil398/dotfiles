"""``--doctor``: show effective configuration, key presence, state and Codex registration."""

from __future__ import annotations

import os
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any, List

from . import VERSION, logbook
from .config import API_KEY_ENV, load_config, resolve_api_key
from .telemetry import normalize_cwd, summarize

_HOOK_SCRIPT = "hook.sh"


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
    hooks_path = codex_home / "hooks.json"
    if hooks_path.is_file():
        try:
            groups=json.loads(hooks_path.read_text(encoding="utf-8")).get("hooks",{}).get("Stop",[])
            registered=registered or any(_HOOK_SCRIPT in h.get("command","") for g in groups for h in g.get("hooks",[]))
        except (OSError,ValueError,AttributeError): lines.append("codex hooks.json  : unreadable")
    lines.append(f"codex Stop hook   : {'registered' if registered else 'NOT registered (run: bash etc/sync-codex.sh)'}")
    hooks_enabled = re.search(r"^\s*hooks\s*=\s*false", text, re.M) is None
    lines.append(f"codex features.hooks: {'enabled' if hooks_enabled else 'DISABLED'}")
    trust_keys = re.findall(r'^\[hooks\.state\."([^"]+:stop:\d+:\d+)"\]', text, re.M)
    if registered:
        user_trust = [k for k in trust_keys if k.startswith(str(config)+":stop:") or k.startswith(str(hooks_path)+":stop:")]
        if user_trust:
            lines.append("codex hook trust  : user Stop recorded (" + str(len(user_trust)) + " state keys)")
        else:
            lines.append("codex hook trust  : user Stop hash not recorded (run bash etc/sync-codex.sh)")
        other = [k for k in trust_keys if k not in user_trust]
        if other:
            lines.append("                    (other Stop trusts: " + str(len(other)) + " project entries)")


def _path_registration(lines: List[str], label: str, path: Path, needle: str) -> None:
    if path.is_file() and needle in path.read_text(encoding="utf-8", errors="replace"):
        lines.append(f"{label}: registered ({path})")
    else:
        lines.append(f"{label}: NOT registered ({path})")


def doctor(out: Any) -> int:
    cfg = load_config()
    key, source = resolve_api_key()
    lines: List[str] = []
    lines.append(f"jev-hooks {VERSION}")
    lines.append(f"python            : {platform.python_version()} ({sys.executable})")
    lines.append(f"config file       : {cfg.source_file or '(none; defaults)'}")
    lines.append(f"mode              : {cfg.mode}")
    lines.append(f"model             : {cfg.model}")
    lines.append(f"api_url           : {cfg.api_url}")
    lines.append(f"confidence_threshold: {cfg.confidence_threshold}")
    lines.append(f"timeouts          : api {cfg.api_timeout_s}s / total {cfg.total_timeout_s}s")
    lines.append(f"max_continuations : {cfg.max_continuations}")
    lines.append(f"api key           : {'present' if key else 'MISSING'} (source: {source}; env {API_KEY_ENV} only)")
    state_dir = cfg.state_path()
    writable = os.access(state_dir, os.W_OK) if state_dir.exists() else os.access(state_dir.parent, os.W_OK) if state_dir.parent.exists() else False
    lines.append(f"state dir         : {state_dir} ({'writable' if writable else 'NOT writable / missing parent'})")
    lines.append(f"log               : {logbook.log_path(state_dir)}")
    for w in cfg.warnings:
        lines.append(f"config warning    : {w}")
    _codex_registration(lines)
    _path_registration(lines, "cursor stop hook ", Path.home() / ".cursor/hooks.json", "hook.sh")
    _path_registration(lines, "devin Stop hook  ", Path.home() / ".config/devin/config.json", "hook.sh")
    lines.append(f"usage database    : {state_dir / 'usage.sqlite3'}")
    _path_registration(lines, "grok tool hooks  ", Path.home() / ".grok/hooks/jev-hooks.json", "hook.sh")
    cwd = normalize_cwd()
    lines.append(f"current cwd       : {cwd}")
    cwd_usage = summarize(state_dir, days=30, cwd=cwd)
    if cwd_usage["available"]:
        totals = cwd_usage["totals"]
        lines.append(
            "cwd usage (30d)   : {calls} calls / API {api_attempted} / skip {skip_count} / error {error_count}".format(**totals)
        )
    else:
        lines.append("cwd usage (30d)   : records unreadable")
    recall = Path(__file__).resolve().parents[3] / ".agents/skills/ai-ltm/scripts/session_recall.py"
    bridge = recall.with_name("jev_bridge.py")
    lines.append("ai-ltm recall     : " + (
        "candidate delivery + optional Jev annotations (key/mode required)"
        if recall.is_file() and bridge.is_file() else "not installed; skipped"
    ))
    recent = logbook.tail(state_dir, 5, cwd=cwd)
    if recent:
        lines.append("recent policy decisions (current cwd):")
        for rec in recent:
            if rec.get("policy_id"):
                choices = ", ".join(f"{name}={answer.get('choice')}" for name, answer in rec.get("answers", {}).items())
                lines.append(
                    f"  {rec.get('ts')} policy={rec['policy_id']} mode_at_record={rec.get('mode', '(unknown)')}: {choices}"
                )
                continue
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
        lines.append("recent policy decisions (current cwd): (none logged yet)")
    out.write("\n".join(lines) + "\n")
    return 0
