#!/usr/bin/env python3
"""Check that extracts.json quotes occur at their recorded source lines."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PureWindowsPath
from typing import Any


def normalize(value: str) -> str:
    """Collapse whitespace and remove Markdown list markers at line starts."""
    without_markers = re.sub(r"(?m)^\s*[-*]\s+", " ", value)
    return re.sub(r"\s+", " ", without_markers).strip()


def safe_source_path(sources_dir: Path, topic_dir: Path, name: str) -> Path | None:
    relative = Path(name)
    windows = PureWindowsPath(name)
    if (
        relative.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or ".." in relative.parts
        or ".." in windows.parts
    ):
        return None

    try:
        resolved_sources = sources_dir.resolve()
        resolved_topic = topic_dir.resolve()
        resolved_path = (sources_dir / relative).resolve()
    except (OSError, RuntimeError, ValueError):
        return None

    if (
        not resolved_sources.is_relative_to(resolved_topic)
        or not resolved_path.is_relative_to(resolved_sources)
        or not resolved_path.is_file()
    ):
        return None
    return resolved_path


def clean_label(value: Any) -> str:
    return " ".join(str(value).split()) or "<empty>"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic_dir", type=Path, help="directory containing extracts.json and sources/")
    args = parser.parse_args()

    topic_dir = args.topic_dir.expanduser()
    extracts_path = topic_dir / "extracts.json"
    try:
        data = json.loads(extracts_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(
            f"verify_quotes input_error path={extracts_path} reason={type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        print(
            f"verify_quotes input_error path={extracts_path} reason=expected_object_with_claims_array",
            file=sys.stderr,
        )
        return 2

    sources_dir = topic_dir / "sources"
    checked = ok_count = failed = 0
    print(
        f"verify_quotes start topic_dir={topic_dir} claims={len(data['claims'])}",
        file=sys.stderr,
    )

    def report_error(claim_no: int, heading: str, filename: str, line: Any, reason: str) -> None:
        nonlocal checked, failed
        checked += 1
        failed += 1
        print(
            f"claim={claim_no} heading={clean_label(heading)!r} "
            f"file={clean_label(filename)!r} line={line!r} reason={reason}",
            file=sys.stderr,
        )

    for claim_no, claim in enumerate(data["claims"], start=1):
        if not isinstance(claim, dict) or not isinstance(claim.get("claim"), str):
            report_error(claim_no, "<invalid claim>", "<unknown>", "<unknown>", "invalid_claim_shape")
            continue

        heading = claim["claim"]
        quotes = claim.get("quotes")
        if not isinstance(quotes, list):
            report_error(claim_no, heading, "<unknown>", "<unknown>", "quotes_must_be_array")
            continue

        for quote in quotes:
            filename = quote.get("file") if isinstance(quote, dict) else "<invalid quote>"
            line = quote.get("line") if isinstance(quote, dict) else "<unknown>"
            if not isinstance(quote, dict):
                report_error(claim_no, heading, str(filename), line, "quote_must_be_object")
                continue

            if not isinstance(filename, str) or not filename:
                report_error(claim_no, heading, str(filename), line, "file_must_be_nonempty_string")
                continue
            if isinstance(line, bool) or not isinstance(line, int) or line < 1:
                report_error(claim_no, heading, filename, line, "line_must_be_positive_integer")
                continue
            end = quote.get("end", line)
            if isinstance(end, bool) or not isinstance(end, int) or end < line:
                report_error(claim_no, heading, filename, line, "end_must_be_integer_at_or_after_line")
                continue
            text = quote.get("text")
            if not isinstance(text, str) or not text:
                report_error(claim_no, heading, filename, line, "text_must_be_nonempty_string")
                continue

            source_path = safe_source_path(sources_dir, topic_dir, filename)
            if source_path is None:
                report_error(claim_no, heading, filename, line, "unsafe_or_missing_source_file")
                continue
            try:
                source_text = source_path.read_text(encoding="utf-8")
                source_lines = source_text.split("\n")
                if source_text.endswith("\n"):
                    source_lines.pop()
            except (OSError, UnicodeError) as exc:
                report_error(claim_no, heading, filename, line, f"source_read_error:{type(exc).__name__}")
                continue
            if end > len(source_lines):
                report_error(claim_no, heading, filename, line, "line_range_out_of_bounds")
                continue

            excerpt = normalize(" ".join(source_lines[line - 1 : end]))
            if normalize(text) not in excerpt:
                report_error(claim_no, heading, filename, line, "quote_not_found_in_line_range")
                continue

            checked += 1
            ok_count += 1

    print(f"checked={checked} ok={ok_count} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
