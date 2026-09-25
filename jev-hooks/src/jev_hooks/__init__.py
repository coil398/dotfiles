"""jev-hooks: detect abandoned requested work at a coding agent's Stop event.

Runtime-neutral core (config, redaction, Jev client, policy, state, log) plus
the Codex adapter (``transcript`` reader and ``codex_hook`` entry).
"""

__all__ = ["VERSION"]

VERSION = "0.2.0"
