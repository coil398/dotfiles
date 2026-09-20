#!/usr/bin/env python3
"""Codex Stop hook entry: ask Jev whether requested work was abandoned.

Registered by etc/sync-codex.sh as ``[[hooks.Stop]]`` in the generated
``.codex/config.toml``. See etc/jev_stop_guard/README.md.
"""

from __future__ import annotations

import os
import sys

# Resolve the physical location so a symlinked entry still finds the package.
_HERE = os.path.dirname(os.path.realpath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from jev_stop_guard.codex_hook import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
