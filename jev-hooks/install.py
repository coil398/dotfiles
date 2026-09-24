#!/usr/bin/env python3
"""Install only Jev-owned hook entries, preserving other hooks and settings."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shlex
import tempfile


_OWNED_MARKERS = ("jev-hooks/hook.sh", "jev-stop-guard", "jev_stop_guard")


def owned(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    commands = [entry.get("command", "")]
    commands.extend(h.get("command", "") for h in entry.get("hooks", []) if isinstance(h, dict))
    return any(isinstance(c, str) and any(m in c for m in _OWNED_MARKERS) for c in commands)


def without_owned(entries: list) -> list:
    kept = []
    for entry in entries:
        if not owned(entry):
            kept.append(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("hooks"), list):
            handlers = [h for h in entry["hooks"] if not owned(h)]
            if handlers:
                kept.append(dict(entry, hooks=handlers))
    return kept


def install(runtime: str, home: Path, check: bool = False) -> bool:
    root = Path(__file__).resolve().parent
    command = f"sh {shlex.quote(str(root / 'hook.sh'))} {runtime}"
    if runtime == "cursor":
        path = home / ".cursor/hooks.json"
        additions = {"stop": [{"command": command, "timeout": 10, "loop_limit": 2}],
                     "postToolUse": [{"command": command, "timeout": 10}],
                     "postToolUseFailure": [{"command": command, "timeout": 10}]}
    elif runtime == "grok":
        path = home / ".grok/hooks/jev-hooks.json"
        additions = {event: [{"hooks": [{"type": "command", "command": command, "timeout": 10}]}]
                     for event in ("PreToolUse", "PostToolUse", "PostToolUseFailure")}
    else:
        raise ValueError("unsupported runtime")
    previous = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(previous, dict) or not isinstance(previous.get("hooks", {}), dict):
        raise ValueError("invalid hooks configuration")
    current = dict(previous)
    hooks = dict(previous.get("hooks", {}))
    if runtime == "cursor":
        current.setdefault("version", 1)
    for event, entries in additions.items():
        existing = hooks.get(event, [])
        if not isinstance(existing, list):
            raise ValueError("hook event must be a list")
        hooks[event] = without_owned(existing) + entries
    current["hooks"] = hooks
    if current == previous:
        return False
    if check:
        raise ValueError(f"hooks would change: {path}")
    # Preserve symlink ownership while publishing atomically to its real destination.
    target = path.resolve() if path.is_symlink() else path
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = target.stat().st_mode & 0o777 if target.exists() else 0o600
    fd, tmp = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(current, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.chmod(tmp, mode)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", choices=["cursor", "grok"])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args()
    try:
        changed = install(args.runtime, args.home, args.check)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"jev-hooks install: {exc}\n")
    print(f"jev-hooks {args.runtime}: {'updated' if changed else 'unchanged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
