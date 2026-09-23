#!/usr/bin/env python3
"""claude lifecycle adapter for optional Jev judgments."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from jev_hooks.cli import hook_main
if __name__ == "__main__":
    raise SystemExit(hook_main("claude"))
