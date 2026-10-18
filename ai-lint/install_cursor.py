#!/usr/bin/env python3
"""Register the AI Lint Cursor post-tool hook without replacing user hooks."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import tempfile


def install(home: Path, check: bool = False) -> bool:
    root = Path(__file__).resolve().parent.parent
    path = home / ".cursor" / "hooks.json"
    command = f"python3 {shlex.quote(str(root / 'ai-lint' / 'ai_lint.py'))} --hook cursor"
    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(previous, dict) or not isinstance(previous.get("hooks", {}), dict):
        raise ValueError("invalid hooks configuration")
    current = dict(previous)
    current.setdefault("version", 1)
    hooks = dict(previous.get("hooks", {}))
    existing = hooks.get("postToolUse", [])
    if not isinstance(existing, list):
        raise ValueError("postToolUse must be a list")
    kept = [entry for entry in existing if not (
        isinstance(entry, dict)
        and isinstance(entry.get("command"), str)
        and "ai_lint.py" in entry["command"]
        and "--hook cursor" in entry["command"]
    )]
    entry = {"command": command, "timeout": 10}
    jev_index = next((index for index, item in enumerate(kept) if isinstance(item, dict) and "jev-hooks/hook.sh" in str(item.get("command", ""))), len(kept))
    kept.insert(jev_index, entry)
    hooks["postToolUse"] = kept
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
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
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
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--home", type=Path, default=Path.home())
    args = parser.parse_args()
    try:
        changed = install(args.home, args.check)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"ai-lint Cursor install: {exc}\n")
    print(f"ai-lint Cursor: {'updated' if changed else 'unchanged'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
