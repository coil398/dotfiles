"""Runtime entrypoints and manual commands; optional failures never block tools."""
from __future__ import annotations
import argparse
import io
import json
import sys
from typing import Any


def hook_main(runtime_name: str, argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and runtime_name == "codex":
        from .codex_hook import main as codex_main
        return codex_main(args)
    try:
        raw = sys.stdin.read(2_000_000)
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
        event = payload.get("hook_event_name") or payload.get("hookEventName") or payload.get("event")
        if runtime_name in {"claude", "codex", "cursor", "devin"} and event in {None, "Stop", "stop"}:
            if runtime_name == "codex":
                from .codex_hook import run_hook
            elif runtime_name == "claude":
                from .claude_hook import run_hook
            elif runtime_name == "cursor":
                from .cursor_hook import run_hook
            else:
                from .devin_hook import run_hook
            payload.setdefault("hook_event_name", "Stop")
            # Buffer the response: an adapter error must not leave half a JSON object.
            output = io.StringIO()
            rc = run_hook(io.StringIO(json.dumps(payload)), output)
        else:
            from .runtime import run_hook
            output = io.StringIO()
            rc = run_hook(runtime_name, io.StringIO(json.dumps(payload)), output)
        sys.stdout.write(output.getvalue())
        return rc
    except Exception as exc:
        # Runtime boundary: optional hook failure must not prevent the original action.
        sys.stderr.write("jev-hooks: adapter skipped (" + type(exc).__name__ + ")\n")
        sys.stdout.write("{}")
        return 0


def _input() -> dict[str, Any]:
    value = json.load(sys.stdin)
    if not isinstance(value, dict):
        raise ValueError("stdin must be a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "usage":
        from .report import main as report_main
        return report_main(args[1:])
    parser = argparse.ArgumentParser(description="Jev hooks: optional judgments and usage visibility")
    parser.add_argument("command", choices=["doctor", "skills", "memory-annotate", "memory-rerank", "memory-classify"])
    parsed = parser.parse_args(args)
    if parsed.command == "doctor":
        from .doctor import doctor
        return doctor(sys.stdout)
    try:
        data = _input()
        if parsed.command == "skills":
            from .skills import select_skills
            result = select_skills(data.get("query", ""), cwd=data.get("cwd"))
        elif parsed.command == "memory-annotate":
            from .memory import annotate
            result = annotate(data.get("query", ""), data.get("results", []))
        elif parsed.command == "memory-rerank":
            from .memory import rerank
            result = rerank(data.get("query", ""), data.get("results", []))
        else:
            from .memory import classify_record
            result = classify_record(data.get("summary", ""), data.get("context", ""), db_path=data.get("db_path"))
    except (ValueError, TypeError) as exc:
        sys.stderr.write("jev-hooks: invalid input (" + type(exc).__name__ + ")\n")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
