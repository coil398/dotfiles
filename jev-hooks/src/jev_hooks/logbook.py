"""Append-only JSONL decision log with a size cap (one rotation generation).

Records contain verdicts, reason codes, probabilities, timings, counters and
usage. They never contain conversation text or secret values.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from .telemetry import normalize_cwd

LOG_NAME = "decisions.jsonl"


def log_path(state_dir: Path) -> Path:
    return state_dir / LOG_NAME


def append(
    state_dir: Path,
    record: Dict[str, Any],
    max_bytes: int,
    *,
    cwd: Path | str | None = None,
) -> bool:
    path = log_path(state_dir)
    try:
        state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(state_dir, 0o700)
        entry = dict(record)
        entry["cwd"] = normalize_cwd(cwd)
        line = json.dumps(entry, ensure_ascii=False, separators=(",", ":"), default=str) + "\n"
        try:
            if path.stat().st_size + len(line) > max_bytes:
                rotated = path.with_suffix(".jsonl.1")
                os.replace(path, rotated)
                os.chmod(rotated, 0o600)
        except FileNotFoundError:
            pass
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as fh:
                fd = -1
                fh.write(line)
        finally:
            if fd >= 0:
                os.close(fd)
        return True
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def tail(state_dir: Path, count: int, *, cwd: Path | str | None = None) -> List[Dict[str, Any]]:
    path = log_path(state_dir)
    try:
        cwd_value = normalize_cwd(cwd) if cwd is not None else None
    except (OSError, RuntimeError, TypeError, ValueError):
        return []
    out: List[Dict[str, Any]] = []
    for source in (path.with_suffix(".jsonl.1"), path):
        try:
            lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
        except (OSError, RuntimeError, TypeError, ValueError):
            continue
        for line in lines:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if isinstance(entry, dict) and (cwd_value is None or entry.get("cwd") == cwd_value):
                out.append(entry)
    return out[-max(0, count):] if count else []


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
