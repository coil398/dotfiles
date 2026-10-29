#!/usr/bin/env python3
"""Summarize fork_turns values in Codex JSONL session records."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


CATEGORIES = ("none", "all", "numeric", "omitted", "other", "unparsed")
DATE_PATTERN = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)")


def path_is_since(path: Path, since: date) -> bool:
    candidates = []
    for match in DATE_PATTERN.findall(str(path)):
        try:
            candidates.append(date.fromisoformat(match))
        except ValueError:
            pass
    parts = path.parts
    for index in range(len(parts) - 2):
        if re.fullmatch(r"\d{4}", parts[index]) and all(
            re.fullmatch(r"\d{2}", part) for part in parts[index + 1 : index + 3]
        ):
            try:
                candidates.append(date(int(parts[index]), int(parts[index + 1]), int(parts[index + 2])))
            except ValueError:
                pass
    return any(candidate >= since for candidate in candidates)


def classify_arguments(raw: Any) -> tuple[str, Any]:
    if isinstance(raw, str):
        try:
            arguments = json.loads(raw)
        except json.JSONDecodeError:
            return "unparsed", None
    elif isinstance(raw, dict):
        arguments = raw
    else:
        return "unparsed", None

    if not isinstance(arguments, dict):
        return "unparsed", None
    if "fork_turns" not in arguments:
        return "omitted", arguments
    value = arguments["fork_turns"]
    if value == "none":
        return "none", arguments
    if value == "all":
        return "all", arguments
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "numeric", arguments
    if isinstance(value, str) and re.fullmatch(r"\d+(?:\.\d+)?", value):
        return "numeric", arguments
    return "other", arguments


def source_kind(source: Any) -> str:
    if isinstance(source, str):
        return "root"
    if isinstance(source, dict) and isinstance(source.get("subagent"), dict):
        if isinstance(source["subagent"].get("thread_spawn"), dict):
            return "subagent"
    return "unknown"


def call_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False)


def iter_session_files(directory: Path, since: date | None) -> list[Path]:
    files = sorted(path for path in directory.rglob("*.jsonl") if path.is_file())
    if since is None:
        return files
    return [path for path in files if path_is_since(path, since)]


def inspect_file(
    path: Path,
    by_origin: dict[str, Counter[str]],
    violations: list[tuple[Path, int, str, str]],
    code_mode: Counter[str],
) -> int:
    origin = "unknown"
    unreadable = 0
    try:
        handle = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return 1

    with handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                unreadable += 1
                continue
            if not isinstance(record, dict):
                unreadable += 1
                continue

            if origin == "unknown":
                payload = record.get("payload")
                if record.get("type") == "session_meta":
                    payload = record.get("payload")
                    payload = payload if isinstance(payload, dict) else {}
                    origin = source_kind(payload.get("source"))

            payload = record.get("payload")
            if not isinstance(payload, dict) or payload.get("type") != "function_call":
                continue
            name = payload.get("name")
            if name == "spawn_agent":
                category, arguments = classify_arguments(payload.get("arguments", payload.get("input")))
                by_origin[origin][category] += 1
                if category != "none":
                    violations.append((path, line_number, category, call_text(arguments)))
            elif name == "exec":
                code = call_text(payload.get("arguments", payload.get("input")))
                if "spawn_agent(" in code:
                    code_mode[origin] += 1
    return unreadable


def main() -> int:
    default_dir = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser() / "sessions"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_dir", nargs="?", type=Path, default=default_dir)
    parser.add_argument("--since", type=date.fromisoformat, metavar="YYYY-MM-DD")
    args = parser.parse_args()

    if not args.session_dir.is_dir():
        print(f"Session directory not found: {args.session_dir}", file=sys.stderr)
        return 2

    files = iter_session_files(args.session_dir, args.since)
    by_origin: dict[str, Counter[str]] = defaultdict(Counter)
    code_mode: Counter[str] = Counter()
    violations: list[tuple[Path, int, str, str]] = []
    unreadable = 0
    for path in files:
        unreadable += inspect_file(path, by_origin, violations, code_mode)

    print(f"Session files: {len(files)}")
    print("spawn_agent calls (none/all/numeric/omitted/other/unparsed):")
    for origin in ("root", "subagent", "unknown"):
        counts = by_origin[origin]
        summary = " ".join(f"{category}={counts[category]}" for category in CATEGORIES)
        print(f"  {origin}: {summary}")
    code_total = sum(code_mode.values())
    print(f"code-mode spawn_agent( occurrences: {code_total}")
    print(f"unreadable lines/files: {unreadable}")

    if violations:
        print("Calls requiring review:")
        for path, line_number, category, _arguments in violations:
            print(f"  {path}:{line_number} ({category})")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
