#!/usr/bin/env python3
"""Jev hooks diagnostics, usage dashboard and explicit decision commands."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from jev_hooks.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
