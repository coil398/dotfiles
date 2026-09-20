#!/usr/bin/env python3
"""Cursor stop hook entry. See etc/jev_stop_guard/README.md."""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.realpath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from jev_stop_guard.cursor_hook import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
