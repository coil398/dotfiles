"""Compute Codex hook trust hashes the same way rust-v0.153.4+ does.

Codex hashes a normalized identity (event key + matcher + handler) via
``version_for_toml``: TOML-serializable fields only, then canonical JSON,
then SHA-256. See openai/codex ``codex-rs/hooks/src/engine/discovery.rs``
and ``codex-rs/config/src/fingerprint.rs``.

Writing that hash into ``[hooks.state.<key>]`` is what ``/hooks`` trust
does. This module only records the current hash for the jev-stop-guard
Stop command; it does not disable trust checks or use
``--dangerously-bypass-hook-trust``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

STOP_SCRIPT = "jev-stop-guard-codex-hook.py"
POST_SCRIPT = "sync-codex-hook.py"


def _canonical_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _canonical_json(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [_canonical_json(v) for v in value]
    return value


def version_for_json(value: Any) -> str:
    canonical = _canonical_json(value)
    serialized = json.dumps(canonical, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(serialized).hexdigest()


def command_identity(
    event_key: str,
    command: str,
    *,
    matcher: Optional[str] = None,
    timeout: Optional[int] = None,
    status_message: Optional[str] = None,
    async_flag: bool = False,
) -> Dict[str, Any]:
    handler: Dict[str, Any] = {"type": "command", "command": command, "async": async_flag}
    if timeout is not None:
        handler["timeout"] = timeout
    if status_message is not None:
        handler["statusMessage"] = status_message
    identity: Dict[str, Any] = {"event_name": event_key, "hooks": [handler]}
    if matcher is not None:
        identity["matcher"] = matcher
    return identity


def hook_hash(
    event_key: str,
    command: str,
    *,
    matcher: Optional[str] = None,
    timeout: Optional[int] = None,
    status_message: Optional[str] = None,
    async_flag: bool = False,
) -> str:
    return version_for_json(
        command_identity(
            event_key,
            command,
            matcher=matcher,
            timeout=timeout,
            status_message=status_message,
            async_flag=async_flag,
        )
    )


def _unquote_toml(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        return raw[1:-1]
    return raw


def parse_stop_command(text: str) -> Optional[Dict[str, Any]]:
    """Extract the jev-stop-guard Stop handler fields from generated TOML."""
    block = re.search(
        r"\[\[hooks\.Stop\.hooks\]\]\n(.*?)(?:\n\[|\Z)",
        text,
        re.S,
    )
    if not block:
        return None
    body = block.group(1)
    fields: Dict[str, Any] = {}
    cmd = re.search(r'^command\s*=\s*(.+)$', body, re.M)
    if not cmd or STOP_SCRIPT not in cmd.group(1):
        return None
    fields["command"] = _unquote_toml(cmd.group(1))
    timeout = re.search(r'^timeout\s*=\s*(\d+)\s*$', body, re.M)
    if timeout:
        fields["timeout"] = int(timeout.group(1))
    status = re.search(r'^statusMessage\s*=\s*(.+)$', body, re.M)
    if status:
        fields["status_message"] = _unquote_toml(status.group(1))
    return fields


def parse_post_command(text: str) -> Optional[Dict[str, Any]]:
    block = re.search(
        r"\[\[hooks\.PostToolUse\]\]\n(.*?)\[\[hooks\.PostToolUse\.hooks\]\]\n(.*?)(?:\n\[|\Z)",
        text,
        re.S,
    )
    if not block:
        return None
    group, handler = block.group(1), block.group(2)
    cmd = re.search(r'^command\s*=\s*(.+)$', handler, re.M)
    if not cmd or POST_SCRIPT not in cmd.group(1):
        return None
    matcher_m = re.search(r'^matcher\s*=\s*(.+)$', group, re.M)
    return {
        "command": _unquote_toml(cmd.group(1)),
        "matcher": _unquote_toml(matcher_m.group(1)) if matcher_m else None,
    }


def state_keys_for(config_path: Path) -> List[str]:
    # Use the path Codex was asked to write, not the resolved symlink target.
    # Resolving would add a new key when config.toml is a runtime symlink.
    keys = [f"{config_path}:stop:0:0"]
    home = Path(os.path.expanduser("~/.codex/config.toml"))
    home_key = f"{home}:stop:0:0"
    if home_key not in keys:
        keys.append(home_key)
    return keys


def _replace_or_append_state(text: str, key: str, digest: str) -> str:
    table = f'[hooks.state."{key}"]'
    block = f'{table}\ntrusted_hash = "{digest}"\n'
    pattern = re.compile(re.escape(table) + r"\n(?:[^\[]*\n)*")
    if pattern.search(text):
        return pattern.sub(block + "\n", text, count=1)
    if "[hooks.state]" not in text:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n[hooks.state]\n"
    return text.rstrip() + "\n\n" + block + "\n"


def apply_stop_trust(config_path: Path, key_source: Optional[Path] = None) -> Tuple[bool, str]:
    """Trust each managed inline Stop at its actual group/handler index."""
    import tomllib
    text = config_path.read_text(encoding="utf-8")
    data = tomllib.loads(text)
    updated = text
    digest = ""
    source = key_source or config_path
    for group_index, group in enumerate(data.get("hooks", {}).get("Stop", [])):
        for handler_index, handler in enumerate(group.get("hooks", [])):
            if STOP_SCRIPT not in handler.get("command", ""):
                continue
            digest = hook_hash("stop", handler["command"], matcher=group.get("matcher"),
                               timeout=handler.get("timeout"), status_message=handler.get("statusMessage"),
                               async_flag=handler.get("async", False))
            key = f"{source}:stop:{group_index}:{handler_index}"
            updated = _replace_or_append_state(updated, key, digest)
    if updated != text:
        config_path.write_text(updated, encoding="utf-8")
    return updated != text, digest


def install_codex_hook(home: Path, source_config: Path) -> bool:
    """Merge the managed Stop hook into CODEX_HOME, leaving other settings intact."""
    import shutil
    import time
    import tomllib
    import shlex
    target = home / "config.toml"
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    config = tomllib.loads(text)
    source = tomllib.loads(source_config.read_text(encoding="utf-8"))
    groups = [g for g in source.get("hooks", {}).get("Stop", []) if any(STOP_SCRIPT in h.get("command", "") for h in g.get("hooks", []))]
    if len(groups) != 1:
        raise ValueError("Expected exactly one generated Jev Stop definition")
    for handler in groups[0]["hooks"]:
        handler["command"] = "env CODEX_HOME=" + shlex.quote(str(home)) + " " + handler["command"]
    if any(STOP_SCRIPT in h.get("command", "") for g in config.get("hooks", {}).get("Stop", []) for h in g.get("hooks", [])):
        return apply_stop_trust(target)[0]
    path = home / "hooks.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"hooks": {}}
    stops = data.setdefault("hooks", {}).setdefault("Stop", [])
    matches = [i for i,g in enumerate(stops) if any(STOP_SCRIPT in h.get("command", "") for h in g.get("hooks", []))]
    if len(matches) > 1:
        raise ValueError("Duplicate Jev Stop registrations")
    index = matches[0] if matches else len(stops)
    if matches: stops[index] = groups[0]
    else: stops.append(groups[0])
    for j,h in enumerate(groups[0]["hooks"]):
        digest = hook_hash("stop",h["command"],matcher=groups[0].get("matcher"),timeout=h.get("timeout"),status_message=h.get("statusMessage"),async_flag=h.get("async",False))
        text = _replace_or_append_state(text,f"{path}:stop:{index}:{j}",digest)
    tomllib.loads(text)
    home.mkdir(parents=True,exist_ok=True)
    changed=False
    for file,value in [(path,json.dumps(data,ensure_ascii=False,indent=2)+"\n"),(target,text)]:
        if file.exists() and file.read_text(encoding="utf-8")==value: continue
        if file.exists(): shutil.copy2(file,file.with_name(file.name+f".backup-{time.time_ns()}"))
        temp=file.with_name(file.name+".jev-tmp")
        temp.write_text(value,encoding="utf-8")
        temp.replace(file)
        changed=True
    return changed
