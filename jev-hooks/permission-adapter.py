#!/usr/bin/env python3
"""Run the shared permission policy with a documented runtime response shape."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from jev_hooks.permission_hook import run_hook


RUNTIMES = {"claude", "codex", "cursor", "devin", "opencode", "antigravity", "grok"}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in RUNTIMES:
        sys.stderr.write("usage: permission-adapter.py " + "|".join(sorted(RUNTIMES)) + "\n")
        return 2
    return run_hook(sys.stdin, sys.stdout, runtime=sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())
