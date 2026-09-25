#!/usr/bin/env python3
"""Register the dotfiles session-start sync hook, preserving other hooks.

Claude Code, Codex and Devin get the hook from their own generators
(.claude/settings.json, etc/sync-codex.sh, etc/sync-devin.sh). This covers the
runtimes whose hook files live outside the repo: Cursor and Grok.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import tempfile
from pathlib import Path

MARKER = "dotfiles-session-sync.sh"


def _command(script: Path, runtime: str) -> str:
    # Cursor parses hook stdout as JSON.
    suffix = " --json" if runtime == "cursor" else ""
    return f"bash {shlex.quote(str(script))}{suffix}"


def _owned(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    commands = [entry.get("command", "")]
    commands.extend(h.get("command", "") for h in entry.get("hooks", []) if isinstance(h, dict))
    return any(isinstance(c, str) and MARKER in c for c in commands)


def install(runtime: str, home: Path, check: bool = False) -> bool:
    script = Path(__file__).resolve().parent.parent / ".claude/lib/dotfiles-session-sync.sh"
    command = _command(script, runtime)
    if runtime == "cursor":
        path = home / ".cursor/hooks.json"
        event, entry = "sessionStart", {"command": command, "timeout": 10}
    elif runtime == "grok":
        path = home / ".grok/hooks/dotfiles-session-sync.json"
        event, entry = "SessionStart", {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
    else:
        raise ValueError("unsupported runtime")
    previous = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(previous, dict) or not isinstance(previous.get("hooks", {}), dict):
        raise ValueError(f"invalid hooks configuration: {path}")
    current = dict(previous)
    hooks = dict(previous.get("hooks", {}))
    if runtime == "cursor":
        current.setdefault("version", 1)
    existing = hooks.get(event, [])
    if not isinstance(existing, list):
        raise ValueError("hook event must be a list")
    hooks[event] = [e for e in existing if not _owned(e)] + [entry]
    current["hooks"] = hooks
    if current == previous:
        return False
    if check:
        raise ValueError(f"hooks would change: {path}")
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
        parser.exit(1, f"session-sync hook install: {exc}\n")
    print(f"session-sync hook {args.runtime}: {'updated' if changed else 'unchanged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
