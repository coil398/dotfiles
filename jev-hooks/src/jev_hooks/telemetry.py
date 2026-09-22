"""Private, best-effort SQLite usage and cost telemetry for Jev calls."""

from __future__ import annotations

import json
import math
import os
import sqlite3
import threading
from collections import defaultdict
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional
from urllib.parse import quote

from .redact import clip, redact

DB_NAME = "usage.sqlite3"
INPUT_RATE_ENV = "JEV_HOOKS_INPUT_USD_PER_MILLION"
KNOWN_INPUT_RATE = 0.042
KNOWN_MODELS = {"jev-1.13.0"}
BUSY_TIMEOUT_MS = 750
_SCHEMA_LOCK = threading.Lock()
_MAX_SQLITE_INTEGER = (1 << 63) - 1


def database_path(state_dir: Path | str) -> Path:
    return Path(state_dir) / DB_NAME


def normalize_cwd(cwd: Optional[Path | str] = None) -> str:
    """Return a canonical cwd label for local telemetry and logs."""
    path = Path.cwd() if cwd is None else Path(cwd).expanduser()
    return str(path.resolve())


def _safe_label(value: Any, limit: int = 160) -> str:
    if not isinstance(value, str):
        return ""
    safe = "".join(char if char.isprintable() else " " for char in redact(value))
    safe = " ".join(safe.split())
    return clip(safe, limit)


def _nonnegative_integer(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= _MAX_SQLITE_INTEGER else None
    if isinstance(value, float) and math.isfinite(value) and value.is_integer() and value >= 0:
        number = int(value)
        return number if number <= _MAX_SQLITE_INTEGER else None
    return None


def _usage_counts(usage: Any) -> tuple[Optional[int], Optional[int]]:
    if not isinstance(usage, Mapping):
        return None, None
    return (
        _nonnegative_integer(usage.get("input_tokens")),
        _nonnegative_integer(usage.get("output_tokens")),
    )


def _input_rate(model: str, environ: Optional[Mapping[str, Any]]) -> tuple[Optional[float], str]:
    if model not in KNOWN_MODELS:
        return None, "unknown_model"
    raw = (environ or {}).get(INPUT_RATE_ENV)
    if raw is None or raw == "":
        return KNOWN_INPUT_RATE, "default"
    try:
        rate = float(raw)
    except (TypeError, ValueError, OverflowError):
        return KNOWN_INPUT_RATE, "default_invalid_override"
    if not math.isfinite(rate) or rate < 0:
        return KNOWN_INPUT_RATE, "default_invalid_override"
    return rate, "environment"


def _connect(state_dir: Path) -> sqlite3.Connection:
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(state_dir, 0o700)
    path = database_path(state_dir)
    conn = sqlite3.connect(str(path), timeout=BUSY_TIMEOUT_MS / 1000, isolation_level=None)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.Error:
            # WAL is an optimization; the main database remains usable without it.
            pass
        with _SCHEMA_LOCK:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY,
                    recorded_at TEXT NOT NULL,
                    policy_id TEXT NOT NULL,
                    runtime TEXT NOT NULL,
                    event TEXT NOT NULL,
                    model TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    api_attempted INTEGER NOT NULL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    elapsed_ms INTEGER,
                    cost_usd REAL,
                    input_usd_per_million REAL,
                    output_usd_per_million REAL,
                    price_source TEXT NOT NULL,
                    cwd TEXT
                )"""
            )
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(usage)")}
            if "cwd" not in columns:
                # Existing rows remain NULL: their original working directory is unknown.
                try:
                    conn.execute("ALTER TABLE usage ADD COLUMN cwd TEXT")
                except sqlite3.OperationalError:
                    # Another process may have completed the same migration concurrently.
                    columns = {row["name"] for row in conn.execute("PRAGMA table_info(usage)")}
                    if "cwd" not in columns:
                        raise
            conn.execute("CREATE INDEX IF NOT EXISTS usage_recorded_at_idx ON usage(recorded_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS usage_policy_idx ON usage(policy_id)")
        try:
            os.chmod(path, 0o600)
            for sidecar in (Path(str(path) + "-wal"), Path(str(path) + "-shm")):
                if sidecar.exists():
                    os.chmod(sidecar, 0o600)
        except OSError:
            pass
        return conn
    except Exception:
        conn.close()
        raise


def record_event(
    state_dir: Path | str,
    *,
    policy_id: Any,
    runtime: Any,
    event: Any,
    model: Any,
    status: Any,
    reason: Any,
    api_attempted: Any,
    usage: Any = None,
    elapsed_ms: Any = None,
    environ: Optional[Mapping[str, Any]] = None,
    recorded_at: Optional[str] = None,
    cwd: Optional[Path | str] = None,
) -> bool:
    """Append one metadata-only row. Any storage or input error returns False."""
    try:
        model_name = _safe_label(model, 120)
        attempted = bool(api_attempted)
        cwd_value = normalize_cwd(cwd)
        input_tokens, output_tokens = _usage_counts(usage)
        elapsed = _nonnegative_integer(elapsed_ms)
        if attempted:
            input_rate, rate_source = _input_rate(model_name, environ)
            if input_rate is not None and input_tokens is not None and output_tokens is not None:
                output_rate = 0.0
                cost = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
            else:
                output_rate = 0.0 if input_rate is not None else None
                cost = None
                if rate_source == "default" and (input_tokens is None or output_tokens is None):
                    rate_source = "unknown_usage"
        else:
            # A local skip cannot incur an API charge, so known zero differs from unknown.
            input_rate = output_rate = None
            rate_source = "no_charge"
            cost = 0.0
            input_tokens = output_tokens = None

        timestamp = recorded_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        with closing(_connect(Path(state_dir))) as conn:
            conn.execute(
                """INSERT INTO usage (
                    recorded_at, policy_id, runtime, event, model, status, reason,
                    api_attempted, input_tokens, output_tokens, elapsed_ms, cost_usd,
                    input_usd_per_million, output_usd_per_million, price_source, cwd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    _safe_label(timestamp, 40),
                    _safe_label(policy_id),
                    _safe_label(runtime, 80),
                    _safe_label(event, 120),
                    model_name,
                    _safe_label(status, 24),
                    _safe_label(reason, 160),
                    1 if attempted else 0,
                    input_tokens,
                    output_tokens,
                    elapsed,
                    cost,
                    input_rate,
                    output_rate,
                    rate_source,
                    cwd_value,
                ),
            )
        return True
    except (OSError, RuntimeError, sqlite3.Error, TypeError, ValueError, OverflowError):
        return False


def _empty_bucket(label: str) -> Dict[str, Any]:
    return {
        "period": label,
        "calls": 0,
        "api_attempted": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "known_token_calls": 0,
        "estimated_cost_usd": 0.0,
        "cost_known_calls": 0,
        "cost_unknown_calls": 0,
        "latency_ms_total": 0,
        "latency_calls": 0,
        "skip_count": 0,
        "error_count": 0,
    }


def _add_row(bucket: Dict[str, Any], row: Mapping[str, Any]) -> None:
    bucket["calls"] += 1
    if row["api_attempted"]:
        bucket["api_attempted"] += 1
    if row["input_tokens"] is not None or row["output_tokens"] is not None:
        bucket["known_token_calls"] += 1
        bucket["input_tokens"] += row["input_tokens"] or 0
        bucket["output_tokens"] += row["output_tokens"] or 0
    if row["cost_usd"] is None:
        bucket["cost_unknown_calls"] += 1
    else:
        bucket["cost_known_calls"] += 1
        bucket["estimated_cost_usd"] += row["cost_usd"]
    if row["elapsed_ms"] is not None:
        bucket["latency_ms_total"] += row["elapsed_ms"]
        bucket["latency_calls"] += 1
    if row["status"] == "skipped":
        bucket["skip_count"] += 1
    elif row["status"] == "error":
        bucket["error_count"] += 1


def _finish_bucket(bucket: Dict[str, Any]) -> Dict[str, Any]:
    bucket["estimated_cost_usd"] = round(bucket["estimated_cost_usd"], 10)
    bucket["latency_ms_average"] = (
        round(bucket["latency_ms_total"] / bucket["latency_calls"], 1)
        if bucket["latency_calls"]
        else None
    )
    return bucket


def summarize(
    state_dir: Path | str,
    *,
    days: int = 30,
    now: Optional[datetime] = None,
    cwd: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """Return aggregates from the last ``days`` UTC days, without inventing calls."""
    cwd_value: Optional[str] = None
    try:
        span = int(days)
        if span < 1:
            raise ValueError("days must be positive")
        span = min(span, 3660)
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        cutoff = (current.astimezone(timezone.utc) - timedelta(days=span)).isoformat(timespec="seconds").replace("+00:00", "Z")
        cwd_value = normalize_cwd(cwd) if cwd is not None else None
        path = database_path(Path(state_dir))
        if not path.is_file():
            return _empty_summary(span, has_database=False, cwd=cwd_value)
        uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=BUSY_TIMEOUT_MS / 1000)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(usage)")}
            required = {
                "recorded_at", "policy_id", "runtime", "status", "reason", "api_attempted",
                "input_tokens", "output_tokens", "elapsed_ms", "cost_usd",
            }
            if not required.issubset(columns):
                raise sqlite3.OperationalError("usage schema is incomplete")
            if cwd_value is not None and "cwd" not in columns:
                rows = []
            else:
                query = (
                    "SELECT recorded_at, policy_id, runtime, status, reason, api_attempted, "
                    "input_tokens, output_tokens, elapsed_ms, cost_usd "
                    "FROM usage WHERE recorded_at >= ?"
                )
                params: tuple[Any, ...] = (cutoff,)
                if cwd_value is not None:
                    query += " AND cwd = ?"
                    params += (cwd_value,)
                rows = conn.execute(query + " ORDER BY recorded_at, id", params).fetchall()
        totals = _empty_bucket("all")
        daily: Dict[str, Dict[str, Any]] = {}
        monthly: Dict[str, Dict[str, Any]] = {}
        policies: Dict[str, Dict[str, Any]] = {}
        runtimes: Dict[str, Dict[str, Any]] = {}
        skips: Dict[str, int] = defaultdict(int)
        failures: Dict[str, int] = defaultdict(int)
        for row in rows:
            _add_row(totals, row)
            date = str(row["recorded_at"])[:10]
            month = date[:7]
            for mapping, label in ((daily, date), (monthly, month)):
                bucket = mapping.setdefault(label, _empty_bucket(label))
                _add_row(bucket, row)
            for mapping, name in ((policies, row["policy_id"] or "(未設定)"), (runtimes, row["runtime"] or "(未設定)")):
                bucket = mapping.setdefault(str(name), _empty_bucket(str(name)))
                _add_row(bucket, row)
            if row["status"] == "skipped":
                skips[str(row["reason"] or "unknown")] += 1
            elif row["status"] == "error":
                failures[str(row["reason"] or "unknown")] += 1

        return {
            "available": True,
            "has_database": True,
            "days": span,
            "cutoff_utc": cutoff,
            "cwd": cwd_value,
            "totals": _finish_bucket(totals),
            "daily": [_finish_bucket(daily[key]) for key in sorted(daily)],
            "monthly": [_finish_bucket(monthly[key]) for key in sorted(monthly)],
            "by_policy": [_finish_bucket(policies[key]) for key in sorted(policies)],
            "by_runtime": [_finish_bucket(runtimes[key]) for key in sorted(runtimes)],
            "skip_reasons": dict(sorted(skips.items())),
            "failure_reasons": dict(sorted(failures.items())),
        }
    except (OSError, RuntimeError, sqlite3.Error, TypeError, ValueError, OverflowError):
        return _empty_summary(
            max(1, min(3660, int(days) if str(days).isdigit() else 30)),
            has_database=True,
            available=False,
            cwd=cwd_value,
        )


def _empty_summary(
    days: int,
    *,
    has_database: bool,
    available: bool = True,
    cwd: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "available": available,
        "has_database": has_database,
        "days": days,
        "cutoff_utc": None,
        "cwd": cwd,
        "totals": _finish_bucket(_empty_bucket("all")),
        "daily": [],
        "monthly": [],
        "by_policy": [],
        "by_runtime": [],
        "skip_reasons": {},
        "failure_reasons": {},
    }
