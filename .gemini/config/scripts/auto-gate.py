#!/usr/bin/env python3
"""Fail-closed PreToolUse gate for the Antigravity runtime.

The hook protocol is documented by the installed Antigravity runtime.  This
script deliberately does not try to prove arbitrary shell text safe with a
regular expression: only a small, exact argv allowlist is automatic.  Every
other valid request asks for confirmation, and malformed or unknown input is
also an ask rather than an allow.
"""

from __future__ import annotations

import json
import shlex
import sys
from typing import Any


# These commands have no write or network operation and are matched as exact
# argv tuples after shell parsing.  Paths, options, pipes, redirections,
# substitutions, and command prefixes are intentionally not accepted.
SAFE_READ_COMMANDS: set[tuple[str, ...]] = {
    ("pwd",),
    ("ls",),
    ("ls", "-la"),
    ("ls", "-al"),
    ("git", "diff", "--check"),
    ("git", "rev-parse", "--show-toplevel"),
}

REASONS = {
    "malformed_input": "hook入力を解釈できないため承認確認が必要です。",
    "unknown_schema": "hook入力のschemaが未知のため承認確認が必要です。",
    "unverified_tool": "このツールの自動承認条件を定義していないため承認確認が必要です。",
    "malformed_run_command": "run_commandの引数が不正なため承認確認が必要です。",
    "unverified_command": "コマンドを読み取り専用と構造化判定できないため承認確認が必要です。",
}


def emit(decision: str, category: str) -> None:
    """Emit only the documented response fields and a fixed reason."""

    payload: dict[str, str] = {"decision": decision}
    if decision == "ask":
        payload["reason"] = REASONS[category]
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def ask(category: str) -> None:
    emit("ask", category)


def parsed_safe_command(command_line: str) -> bool:
    """Return true only for an exact, shell-free read-only argv tuple."""

    if not command_line or any(char in command_line for char in ("\x00", "\n", "\r")):
        return False
    try:
        argv = tuple(shlex.split(command_line, posix=True))
    except (ValueError, TypeError):
        return False
    return argv in SAFE_READ_COMMANDS


def main() -> None:
    try:
        raw_input = sys.stdin.buffer.read()
        data: Any = json.loads(raw_input.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        ask("malformed_input")
        return

    if not isinstance(data, dict):
        ask("malformed_input")
        return

    tool_call = data.get("toolCall")
    if not isinstance(tool_call, dict):
        ask("unknown_schema")
        return

    name = tool_call.get("name")
    args = tool_call.get("args")
    if not isinstance(name, str) or not name or not isinstance(args, dict):
        ask("unknown_schema")
        return

    if name != "run_command":
        ask("unverified_tool")
        return

    command_line = args.get("CommandLine")
    if not isinstance(command_line, str):
        ask("malformed_run_command")
        return

    if parsed_safe_command(command_line):
        emit("allow", "")
    else:
        ask("unverified_command")

if __name__ == "__main__":
    main()
