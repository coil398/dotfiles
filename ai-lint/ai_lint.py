#!/usr/bin/env python3
"""Advisory scanner for suspicious additions in AI-authored code."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import difflib
import json
import logging
import os
from pathlib import Path
import re
import sys
import time

logger = logging.getLogger("ai_lint")
ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = Path(__file__).with_name("rules.json")
EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".go", ".rs", ".rb", ".java", ".kt", ".swift", ".cs", ".sh", ".bash", ".zsh", ".toml", ".yaml", ".yml", ".json", ".sql"}
GENERATED_PARTS = {"generated", "node_modules", "vendor", "dist", "build"}


@dataclass(frozen=True)
class AddedLine:
    path: str
    number: int
    text: str


@dataclass(frozen=True)
class Hit:
    rule_id: str
    question: str
    path: str
    number: int
    text: str


def load_rules() -> list[dict]:
    data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    for rule in data:
        rule["compiled"] = [re.compile(pattern, re.IGNORECASE) for pattern in rule["patterns"]]
        rule["excluded"] = [re.compile(pattern, re.IGNORECASE) for pattern in rule.get("exclude_patterns", [])]
    return data


def _resolved_path(path: str, cwd: str | None = None) -> Path:
    candidate = Path(path.replace("\\", "/")).expanduser()
    if not candidate.is_absolute():
        candidate = Path(cwd or os.getcwd()) / candidate
    return candidate.resolve()


def _display_path(path: str, cwd: str | None = None) -> str:
    candidate = _resolved_path(path, cwd)
    base = Path(cwd or os.getcwd()).expanduser().resolve()
    try:
        return candidate.relative_to(base).as_posix()
    except ValueError:
        return str(candidate)


def path_skip_reason(path: str, cwd: str | None = None, root: Path = ROOT) -> str | None:
    candidate = Path(path.replace("\\", "/"))
    if not candidate.name or candidate.suffix.lower() not in EXTENSIONS:
        return "unsupported extension"
    try:
        resolved = _resolved_path(path, cwd)
        parts = resolved.parts
        lint_dir = (root / "ai-lint").resolve()
        try:
            resolved.relative_to(lint_dir)
            return "ai-lint source directory"
        except ValueError:
            pass
    except OSError:
        parts = candidate.parts
    if any(part in GENERATED_PARTS for part in parts):
        return "excluded directory"
    if any(part.startswith(".") and part not in {".claude", ".codex", ".cursor"} for part in parts[:-1]):
        return "excluded hidden directory"
    return None


def eligible_path(path: str, root: Path = ROOT) -> bool:
    return path_skip_reason(path, root=root) is None


def scan_lines(lines: list[AddedLine], rules: list[dict]) -> list[Hit]:
    hits = []
    for line in lines:
        if not eligible_path(line.path):
            continue
        for rule in rules:
            extensions = rule.get("extensions")
            if extensions and Path(line.path).suffix.lower() not in {ext.lower() for ext in extensions}:
                continue
            if any(pattern.search(line.text) for pattern in rule["compiled"]):
                if any(pattern.search(line.text) for pattern in rule["excluded"]):
                    continue
                hits.append(Hit(rule["id"], rule["question"], line.path, line.number, line.text.strip()))
    return hits


def _text_lines(text: str, path: str, start: int = 1) -> list[AddedLine]:
    return [AddedLine(path, start + index, line) for index, line in enumerate(text.splitlines())]


def _find_fragment_numbers(path: str, fragments: list[str], cwd: str | None = None) -> list[AddedLine]:
    try:
        content = _resolved_path(path, cwd).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        content = []
    result = []
    cursor = 0
    for fragment in fragments:
        fragment_lines = fragment.splitlines()
        if not fragment_lines:
            continue
        found = -1
        for index in range(cursor, max(cursor, len(content) - len(fragment_lines) + 1)):
            if content[index:index + len(fragment_lines)] == fragment_lines:
                found = index
                break
        if found < 0:
            result.extend(_text_lines(fragment, path))
        else:
            result.extend(_text_lines(fragment, path, found + 1))
            cursor = found + len(fragment_lines)
    return result


def parse_claude(event: dict) -> list[AddedLine]:
    tool = event.get("tool_name")
    data = event.get("tool_input") or {}
    source_path = str(data.get("file_path", ""))
    cwd = event.get("cwd")
    reason = path_skip_reason(source_path, cwd)
    if not source_path or tool not in {"Edit", "MultiEdit", "Write"}:
        return []
    if reason:
        logger.debug("input_skipped runtime=claude path=%s reason=%s", _display_path(source_path, cwd), reason)
        return []
    path = _display_path(source_path, cwd)
    response = event.get("tool_response") or {}
    patches = response.get("structuredPatch") if isinstance(response, dict) else None
    added = []
    if isinstance(patches, list):
        for patch in patches:
            if not isinstance(patch, dict):
                continue
            number = int(patch.get("newStart", 1))
            for line in patch.get("lines", []):
                if not isinstance(line, str):
                    continue
                if line.startswith("+") and not line.startswith("+++"):
                    added.append(AddedLine(path, number, line[1:]))
                    number += 1
                elif line.startswith(" "):
                    number += 1
        return added
    if tool == "Edit":
        fragments = [data.get("new_string", "")]
    elif tool == "MultiEdit":
        fragments = [edit.get("new_string", "") for edit in data.get("edits", []) if isinstance(edit, dict)]
    else:
        fragments = [data.get("content", "")]
    return _find_fragment_numbers(source_path, [fragment for fragment in fragments if isinstance(fragment, str)], cwd)


PATCH_FILE = re.compile(r"^\*\*\* (?:Update File|Add File): (.+)$")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_codex(event: dict) -> list[AddedLine]:
    if event.get("tool_name") != "apply_patch":
        return []
    tool_input = event.get("tool_input") or {}
    patch = tool_input.get("command") or tool_input.get("patch")
    cwd = event.get("cwd")
    if not isinstance(patch, str) or not isinstance(cwd, str):
        raise ValueError("apply_patch command and cwd must be strings")
    added, path, line_no = [], "", 1
    for line in patch.splitlines():
        match = PATCH_FILE.match(line)
        if match:
            raw_path = match.group(1)
            reason = path_skip_reason(raw_path, cwd)
            path = "" if reason else _display_path(raw_path, cwd)
            if reason:
                logger.debug("input_skipped runtime=codex path=%s reason=%s", _display_path(raw_path, cwd), reason)
            line_no = 1
            continue
        hunk = HUNK.match(line)
        if hunk:
            line_no = int(hunk.group(1))
            continue
        if line.startswith("*** "):
            path = ""
            continue
        if not path:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added.append(AddedLine(path, line_no, line[1:]))
            line_no += 1
        elif line.startswith(" "):
            line_no += 1
    return added


def parse_cursor(event: dict) -> list[AddedLine]:
    data = event.get("tool_input") or {}
    source_path = str(event.get("file_path") or data.get("file_path") or data.get("filePath") or data.get("path") or "")
    cwd = event.get("cwd") or os.getcwd()
    reason = path_skip_reason(source_path, cwd)
    if not source_path or reason:
        if source_path and reason:
            logger.debug("input_skipped runtime=cursor path=%s reason=%s", _display_path(source_path, cwd), reason)
        return []
    path = _display_path(source_path, cwd)
    edits = event.get("edits") or data.get("edits")
    added: list[AddedLine] = []
    if isinstance(edits, list):
        for edit in edits:
            if not isinstance(edit, dict):
                continue
            new_text = edit.get("new_string") or edit.get("newString")
            if not isinstance(new_text, str):
                continue
            old_text = edit.get("old_string") or edit.get("oldString")
            if isinstance(old_text, str):
                old_lines = old_text.splitlines()
                new_lines = new_text.splitlines()
                # Keep only inserted/replaced lines; common context in a replacement
                # is excluded using a line-level sequence diff.
                fragments = ["\n".join(new_lines[j1:j2]) for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False).get_opcodes() if tag in {"insert", "replace"}]
                added.extend(_find_fragment_numbers(source_path, fragments, cwd))
            else:
                added.extend(_text_lines(new_text, path))
        return added
    content = data.get("content")
    if isinstance(content, str):
        return _find_fragment_numbers(source_path, [content], cwd)
    new_text = data.get("new_string") or data.get("newString")
    if isinstance(new_text, str):
        old_text = data.get("old_string") or data.get("oldString")
        if isinstance(old_text, str):
            old_lines, new_lines = old_text.splitlines(), new_text.splitlines()
            fragments = ["\n".join(new_lines[j1:j2]) for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False).get_opcodes() if tag in {"insert", "replace"}]
            added.extend(_find_fragment_numbers(source_path, fragments, cwd))
            return added
        return _find_fragment_numbers(source_path, [new_text], cwd)
    return []


def parse_opencode(event: dict) -> list[AddedLine]:
    tool = event.get("tool_name") or event.get("tool")
    data = event.get("tool_input") or event.get("args") or {}
    cwd = event.get("cwd") or os.getcwd()
    if tool == "apply_patch":
        patch = data.get("patch") or data.get("patchText") or data.get("input")
        if not isinstance(patch, str):
            return []
        if patch.startswith("*** Begin Patch"):
            return parse_codex({"tool_name": "apply_patch", "cwd": cwd, "tool_input": {"patch": patch}})
        return parse_unified_diff(patch, cwd)
    path_value = data.get("filePath") or data.get("file_path") or data.get("path")
    if not isinstance(path_value, str) or not path_value or tool not in {"edit", "write"}:
        return []
    reason = path_skip_reason(path_value, cwd)
    if reason:
        logger.debug("input_skipped runtime=opencode path=%s reason=%s", _display_path(path_value, cwd), reason)
        return []
    if tool == "write":
        content = data.get("content")
        return _find_fragment_numbers(path_value, [content], cwd) if isinstance(content, str) else []
    old_text = data.get("oldString") or data.get("old_string")
    new_text = data.get("newString") or data.get("new_string")
    if not isinstance(new_text, str):
        return []
    if not isinstance(old_text, str):
        return _find_fragment_numbers(path_value, [new_text], cwd)
    old_lines, new_lines = old_text.splitlines(), new_text.splitlines()
    added = []
    fragments = ["\n".join(new_lines[j1:j2]) for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False).get_opcodes() if tag in {"insert", "replace"}]
    added.extend(_find_fragment_numbers(path_value, fragments, cwd))
    return added


def parse_devin(event: dict) -> list[AddedLine]:
    """Parse Devin CLI PostToolUse file operations using its native field names."""
    tool = event.get("tool_name")
    response = event.get("tool_response")
    if tool not in {"edit", "write", "apply_patch"} or (isinstance(response, dict) and response.get("success") is False):
        return []
    # Devin and OpenCode expose the same file-operation arguments for these tools.
    return parse_opencode({
        "tool": tool,
        "cwd": event.get("cwd") or os.getcwd(),
        "args": event.get("tool_input") or {},
    })


def parse_unified_diff(text: str, cwd: str | None = None) -> list[AddedLine]:
    path = ""
    number = 1
    added = []
    for line in text.splitlines():
        if line.startswith("+++ "):
            raw = line[4:].split("\t", 1)[0]
            path = "" if raw == "/dev/null" else _display_path(raw[2:] if raw.startswith("b/") else raw, cwd)
        else:
            hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if hunk:
                number = int(hunk.group(1))
            elif path and line.startswith("+") and not line.startswith("+++"):
                added.append(AddedLine(path, number, line[1:]))
                number += 1
            elif path and line.startswith(" "):
                number += 1
    return added


def render(hits: list[Hit]) -> str:
    if not hits:
        return ""
    counts = Counter(hit.rule_id for hit in hits)
    selected, shown = [], Counter()
    for hit in hits:
        if len(selected) >= 12:
            break
        if shown[hit.rule_id] >= 3:
            continue
        selected.append(hit)
        shown[hit.rule_id] += 1
    messages = ["AI Lint: 今回追加した次の箇所は本当に必要ですか。block ではありません。ユーザーの依頼・既存の規則から必要性を説明できなければ削除してください。"]
    for hit in selected:
        excerpt = hit.text[:120]
        messages.append(f"[{hit.rule_id}] {hit.path}:{hit.number} — {excerpt}\n{hit.question}")
    for rule_id, count in counts.items():
        hidden = count - shown[rule_id]
        if hidden > 0:
            messages.append(f"[{rule_id}] ほか {hidden} 件")
    return "\n".join(messages)


def state_file() -> Path:
    state_home = Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
    return state_home / "ai-lint" / "hits.jsonl"


def record_hits(hits: list[Hit], runtime: str, cwd: str) -> None:
    counts = Counter(hit.rule_id for hit in hits)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "runtime": runtime,
        "cwd": cwd,
        "files": sorted({hit.path for hit in hits}),
        "rules": dict(counts),
    }
    try:
        path = state_file()
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        os.chmod(path, 0o600)
    except OSError as exc:
        logger.warning("record_failed error=%s", type(exc).__name__)


def hook_main(runtime: str) -> int:
    started = time.perf_counter()
    try:
        event = json.load(sys.stdin)
        parsers = {"claude": parse_claude, "codex": parse_codex, "cursor": parse_cursor, "opencode": parse_opencode, "devin": parse_devin}
        lines = parsers[runtime](event)
        rules = load_rules()
        hits = scan_lines(lines, rules)
        logger.debug("input runtime=%s kind=%s target_lines=%d hits=%d elapsed_ms=%.1f", runtime, event.get("tool_name"), len(lines), len(hits), (time.perf_counter() - started) * 1000)
        if hits:
            record_hits(hits, runtime, str(event.get("cwd") or os.getcwd()))
            if runtime == "opencode":
                output = {"additional_context": render(hits)}
            else:
                output = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": render(hits)}}
            print(json.dumps(output, ensure_ascii=False))
    except Exception as exc:
        logger.error("analysis_failed runtime=%s error=%s", runtime, type(exc).__name__)
    return 0


def scan_command(paths: list[str]) -> int:
    rules = load_rules()
    lines = []
    scanned = 0
    skipped = 0
    for value in paths:
        if value == "-":
            diff_lines = parse_unified_diff(sys.stdin.read())
            diff_paths = sorted({line.path for line in diff_lines})
            lines.extend(line for line in diff_lines if path_skip_reason(line.path) is None)
            for path in diff_paths:
                reason = path_skip_reason(path)
                if reason:
                    skipped += 1
                    logger.warning("scan_skipped path=%s reason=%s", path, reason)
                else:
                    scanned += 1
            continue
        display = _display_path(value)
        reason = path_skip_reason(value)
        if reason:
            skipped += 1
            logger.warning("scan_skipped path=%s reason=%s", display, reason)
            continue
        path = _resolved_path(value)
        try:
            content = path.read_text(encoding="utf-8")
            scanned += 1
            lines.extend(_text_lines(content, display))
        except (OSError, UnicodeError) as exc:
            skipped += 1
            logger.warning("scan_skipped path=%s reason=unreadable error=%s", display, type(exc).__name__)
    hits = scan_lines(lines, rules)
    if hits:
        print(render(hits))
        print("\n".join(f"{key}: {value}" for key, value in sorted(Counter(hit.rule_id for hit in hits).items())))
    else:
        print(f"no hits ({scanned} files scanned, {skipped} skipped)")
    return 0


def stats_command(days: int) -> int:
    path = state_file()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rules, runtimes = Counter(), Counter()
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(raw)
                timestamp = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                if timestamp < since:
                    continue
                runtimes[item.get("runtime", "unknown")] += 1
                rules.update(item.get("rules", {}))
            except (ValueError, KeyError, TypeError):
                logger.warning("stats_invalid_record")
    except OSError as exc:
        logger.warning("stats_read_failed error=%s", type(exc).__name__)
    print("rules:")
    for key, value in sorted(rules.items()):
        print(f"  {key}: {value}")
    print("runtimes:")
    for key, value in sorted(runtimes.items()):
        print(f"  {key}: {value}")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.DEBUG if os.environ.get("AI_LINT_DEBUG") == "1" else logging.WARNING, format="%(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    parser.add_argument("--hook", choices=("claude", "codex", "cursor", "opencode", "devin"))
    sub.add_parser("diff")
    scan = sub.add_parser("scan")
    scan.add_argument("paths", nargs="+")
    stats = sub.add_parser("stats")
    stats.add_argument("--days", type=int, default=30)
    args = parser.parse_args(argv)
    try:
        if args.hook:
            return hook_main(args.hook)
        if args.command == "diff":
            return scan_command(["-"])
        if args.command == "scan":
            return scan_command(args.paths)
        return stats_command(max(0, args.days))
    except Exception as exc:
        logger.error("analysis_failed command=%s error=%s", args.command, type(exc).__name__)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
