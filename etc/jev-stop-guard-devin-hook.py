#!/usr/bin/env python3
"""Route cached Devin Stop registrations to the current Jev hook."""

import os
from pathlib import Path


if __name__ == "__main__":
    launcher = Path(__file__).resolve().parent.parent / "jev-hooks" / "hook.sh"
    os.execvp("sh", ["sh", str(launcher), "devin"])
