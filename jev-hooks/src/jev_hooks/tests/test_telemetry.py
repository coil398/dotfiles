from __future__ import annotations

import os
import sqlite3
import stat
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from jev_hooks.telemetry import INPUT_RATE_ENV, database_path, normalize_cwd, record_event, summarize


class TelemetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / "private state"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _record(self, **kwargs) -> bool:
        defaults = {
            "policy_id": "policy-a",
            "runtime": "codex",
            "event": "stop",
            "model": "jev-1.13.0",
            "status": "ok",
            "reason": "evaluated",
            "api_attempted": True,
            "usage": {"input_tokens": 1_000_000, "output_tokens": 500},
            "elapsed_ms": 120,
        }
        defaults.update(kwargs)
        return record_event(self.state, **defaults)

    def test_known_price_override_and_unknown_cost_are_distinct(self) -> None:
        self.assertTrue(self._record(recorded_at="2026-09-20T12:00:00Z"))
        self.assertTrue(
            self._record(
                policy_id="policy-b", runtime="cursor", usage={"input_tokens": 10, "output_tokens": 2},
                environ={INPUT_RATE_ENV: "0.1"}, recorded_at="2026-09-21T12:00:00Z",
            )
        )
        self.assertTrue(self._record(model="unknown-model", recorded_at="2026-09-21T13:00:00Z"))
        self.assertTrue(self._record(usage=["malformed"], recorded_at="2026-09-21T14:00:00Z"))
        self.assertTrue(
            self._record(
                usage={"input_tokens": 0, "output_tokens": 0},
                recorded_at="2026-09-22T09:00:00Z",
            )
        )
        self.assertTrue(
            self._record(
                status="skipped", reason="local_gate", api_attempted=False, usage={"input_tokens": 900},
                recorded_at="2026-09-21T15:00:00Z",
            )
        )

        now = datetime(2026, 9, 22, tzinfo=timezone.utc)
        data = summarize(self.state, days=30, now=now)
        self.assertEqual(data["totals"]["calls"], 6)
        self.assertEqual(data["totals"]["api_attempted"], 5)
        self.assertEqual(data["totals"]["cost_unknown_calls"], 2)
        self.assertEqual(data["totals"]["cost_known_calls"], 4)
        self.assertAlmostEqual(data["totals"]["estimated_cost_usd"], 0.042001)
        self.assertEqual(data["monthly"][0]["period"], "2026-09")
        self.assertEqual([row["period"] for row in data["daily"]], ["2026-09-20", "2026-09-21", "2026-09-22"])
        self.assertEqual(data["by_policy"][0]["period"], "policy-a")
        self.assertEqual(data["by_runtime"][0]["period"], "codex")
        self.assertEqual(data["skip_reasons"], {"local_gate": 1})

        with closing(sqlite3.connect(database_path(self.state))) as conn:
            rates = conn.execute("SELECT input_usd_per_million, output_usd_per_million, price_source, cost_usd FROM usage ORDER BY id").fetchall()
        self.assertEqual(rates[0], (0.042, 0.0, "default", 0.042))
        self.assertEqual(rates[1], (0.1, 0.0, "environment", 0.000001))
        self.assertEqual(rates[2][0:2], (None, None))
        self.assertIsNone(rates[2][3])
        self.assertEqual(rates[4][3], 0.0)
        self.assertEqual(rates[5][3], 0.0)

    def test_invalid_price_override_uses_known_default(self) -> None:
        for invalid in ("NaN", "inf", "-0.01", "not-a-price"):
            self.assertTrue(
                self._record(
                    usage={"input_tokens": 1_000_000, "output_tokens": 0},
                    environ={INPUT_RATE_ENV: invalid},
                )
            )
        with closing(sqlite3.connect(database_path(self.state))) as conn:
            rates = conn.execute("SELECT input_usd_per_million, price_source, cost_usd FROM usage").fetchall()
        self.assertEqual(rates, [(0.042, "default_invalid_override", 0.042)] * 4)

    def test_concurrent_appends_keep_one_row_per_call(self) -> None:
        count = 40
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(
                pool.map(
                    lambda index: self._record(
                        policy_id=f"policy-{index % 3}",
                        usage={"input_tokens": index + 1, "output_tokens": index % 2},
                    ),
                    range(count),
                )
            )
        self.assertTrue(all(results))
        self.assertEqual(summarize(self.state)["totals"]["calls"], count)

    def test_cwd_filter_separates_success_and_failure_rows(self) -> None:
        first = self.root / "projects" / "one"
        second = self.root / "projects" / "two"
        self.assertTrue(self._record(cwd=first))
        self.assertTrue(self._record(cwd=second, status="error", reason="API_TIMEOUT"))

        first_report = summarize(self.state, cwd=first)
        second_report = summarize(self.state, cwd=second)
        self.assertEqual(first_report["cwd"], str(first.resolve()))
        self.assertEqual(first_report["totals"]["calls"], 1)
        self.assertEqual(first_report["totals"]["error_count"], 0)
        self.assertEqual(second_report["totals"]["calls"], 1)
        self.assertEqual(second_report["totals"]["error_count"], 1)
        self.assertEqual(second_report["failure_reasons"], {"API_TIMEOUT": 1})
        self.assertEqual(summarize(self.state)["totals"]["calls"], 2)

    def test_relative_cwd_filter_resolves_from_the_process_directory(self) -> None:
        self.assertEqual(normalize_cwd("."), str(Path.cwd().resolve()))

    def test_legacy_rows_stay_unattributed_after_schema_migration(self) -> None:
        self.state.mkdir(parents=True)
        path = database_path(self.state)
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        with closing(sqlite3.connect(path)) as conn:
            conn.execute(
                """CREATE TABLE usage (
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
                    price_source TEXT NOT NULL
                )"""
            )
            conn.execute(
                """INSERT INTO usage (
                    recorded_at, policy_id, runtime, event, model, status, reason,
                    api_attempted, input_tokens, output_tokens, elapsed_ms, cost_usd,
                    input_usd_per_million, output_usd_per_million, price_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (timestamp, "legacy", "codex", "stop", "unknown", "error", "API_TIMEOUT", 1, None, None, None, None, None, None, "unknown_model"),
            )
            conn.commit()

        project = self.root / "project"
        self.assertEqual(summarize(self.state, cwd=project)["totals"]["calls"], 0)
        with closing(sqlite3.connect(path)) as conn:
            columns_before_write = {row[1] for row in conn.execute("PRAGMA table_info(usage)")}
        self.assertNotIn("cwd", columns_before_write)

        self.assertTrue(self._record(cwd=project))
        scoped = summarize(self.state, cwd=project)
        self.assertEqual(scoped["totals"]["calls"], 1)
        self.assertEqual(summarize(self.state)["totals"]["calls"], 2)
        with closing(sqlite3.connect(path)) as conn:
            rows = conn.execute("SELECT policy_id, cwd FROM usage ORDER BY id").fetchall()
        self.assertEqual(rows, [("legacy", None), ("policy-a", str(project.resolve()))])

    def test_cwd_read_does_not_turn_broken_database_into_empty_data(self) -> None:
        self.state.mkdir(parents=True)
        path = database_path(self.state)
        with closing(sqlite3.connect(path)) as conn:
            conn.execute("CREATE TABLE unrelated (value TEXT)")
            conn.commit()

        report = summarize(self.state, cwd=self.root / "project")
        self.assertTrue(report["has_database"])
        self.assertFalse(report["available"])
        with closing(sqlite3.connect(path)) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables, {"unrelated"})

    def test_new_database_is_private_and_missing_database_is_empty(self) -> None:
        empty = summarize(self.state, cwd=self.root / "project")
        self.assertFalse(empty["has_database"])
        self.assertEqual(empty["totals"]["calls"], 0)
        self.assertEqual(empty["daily"], [])
        self.assertEqual(empty["cwd"], str((self.root / "project").resolve()))
        self.assertFalse(self.state.exists())
        self.state.mkdir(mode=0o755)
        os.chmod(self.state, 0o755)
        self.assertTrue(self._record())
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(database_path(self.state).stat().st_mode), 0o600)

    def test_metrics_input_type_errors_do_not_raise(self) -> None:
        for usage in (
            None,
            "not-a-mapping",
            {"input_tokens": True, "output_tokens": -1},
            {"input_tokens": 10**100, "output_tokens": 0},
        ):
            self.assertTrue(self._record(usage=usage))
        data = summarize(self.state)
        self.assertEqual(data["totals"]["calls"], 4)
        self.assertEqual(data["totals"]["cost_unknown_calls"], 4)
        self.assertEqual(data["totals"]["known_token_calls"], 1)


if __name__ == "__main__":
    unittest.main()
