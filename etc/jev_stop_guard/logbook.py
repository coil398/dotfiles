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

LOG_NAME = "decisions.jsonl"


def log_path(state_dir: Path) -> Path:
    return state_dir / LOG_NAME


def append(state_dir: Path, record: Dict[str, Any], max_bytes: int) -> bool:
    path = log_path(state_dir)
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"), default=str) + "\n"
        try:
            if path.stat().st_size + len(line) > max_bytes:
                os.replace(path, path.with_suffix(".jsonl.1"))
        except FileNotFoundError:
            pass
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
        return True
    except OSError:
        return False


def tail(state_dir: Path, count: int) -> List[Dict[str, Any]]:
    path = log_path(state_dir)
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out: List[Dict[str, Any]] = []
    for line in lines[-count:]:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
