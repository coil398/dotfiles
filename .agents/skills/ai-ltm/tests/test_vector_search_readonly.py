#!/usr/bin/env python3
"""Regression tests for the read-only search and explicit write paths."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "vector_search.py"


def _seed_database(db_path: Path, *, with_idf: bool = True) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE episodes (
          id INTEGER PRIMARY KEY,
          summary TEXT NOT NULL,
          context TEXT,
          tags TEXT,
          embedding TEXT,
          used_count INTEGER DEFAULT 0,
          last_used_at DATETIME,
          archived INTEGER DEFAULT 0,
          created_at DATETIME
        );
        CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT);
        CREATE VIRTUAL TABLE episodes_fts USING fts5(
          summary, context, tags, content='episodes', content_rowid='id'
        );
        """
    )
    episodes = [
        (
            1,
            "SQLite read only search",
            "The search path must not migrate or commit.",
            "sqlite readonly",
            json.dumps({"sqlite": 1.0, "read": 1.0, "only": 1.0}),
            3,
            "2026-08-30 00:00:00",
            0,
            "2026-08-01 00:00:00",
        ),
        (
            2,
            "Unrelated memory",
            "A different topic.",
            "other",
            json.dumps({"unrelated": 1.0}),
            0,
            None,
            0,
            "2026-08-02 00:00:00",
        ),
        (
            3,
            "Another unrelated memory",
            "A second different topic.",
            "other",
            json.dumps({"another": 1.0}),
            7,
            "2026-08-29 00:00:00",
            0,
            "2026-08-03 00:00:00",
        ),
    ]
    conn.executemany(
        """
        INSERT INTO episodes
          (id, summary, context, tags, embedding, used_count, last_used_at,
           archived, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        episodes,
    )
    conn.executemany(
        "INSERT INTO episodes_fts(rowid, summary, context, tags) VALUES (?, ?, ?, ?)",
        [(row[0], row[1], row[2], row[3]) for row in episodes],
    )
    conn.executemany(
        "INSERT INTO config(key, value) VALUES (?, ?)",
        [
            ("fts_weight", "0.5"),
            ("vector_weight", "0.5"),
            ("time_decay_days", "30"),
            ("usage_boost_weight", "0.3"),
            ("usage_recency_days", "30"),
            ("archive_after_days", "180"),
        ]
        + ([
            (
                "_idf",
                json.dumps(
                    {"sqlite": 1.0, "read": 1.0, "only": 1.0, "search": 1.0},
                    separators=(",", ":"),
                ),
            )
        ] if with_idf else []),
    )
    conn.commit()
    conn.close()


def _seed_incomplete_database(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE episodes (
          id INTEGER PRIMARY KEY,
          summary TEXT NOT NULL,
          context TEXT,
          tags TEXT,
          embedding TEXT,
          created_at DATETIME
        );
        CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT);
        INSERT INTO config(key, value) VALUES ('_idf', '{}');
        """
    )
    conn.commit()
    conn.close()


def _replace_config_table(db_path: Path, definition: str) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute("DROP TABLE config")
    conn.execute(f"CREATE TABLE config ({definition})")
    conn.commit()
    conn.close()


def _replace_fts_with_plain_table(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute("DROP TABLE episodes_fts")
    conn.execute(
        "CREATE TABLE episodes_fts (rowid INTEGER, summary TEXT, context TEXT, tags TEXT)"
    )
    conn.commit()
    conn.close()


def _run(db_path: Path, command: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), command, "--db", str(db_path), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def _snapshot(db_path: Path) -> tuple[str, int]:
    snapshot = {}
    for sidecar in (
        db_path,
        Path(str(db_path) + "-wal"),
        Path(str(db_path) + "-shm"),
        Path(str(db_path) + "-journal"),
    ):
        if sidecar.exists():
            snapshot[str(sidecar)] = (
                hashlib.sha256(sidecar.read_bytes()).hexdigest(),
                sidecar.stat().st_mtime_ns,
            )
    return snapshot


def _add_old_episode(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT INTO episodes
          (id, summary, context, tags, embedding, used_count, last_used_at,
           archived, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            4,
            "Old archive candidate",
            "This episode is old and unused.",
            "archive candidate",
            json.dumps({"archive": 1.0}),
            0,
            None,
            0,
            "2020-01-01 00:00:00",
        ),
    )
    conn.execute(
        "INSERT INTO episodes_fts(rowid, summary, context, tags) VALUES (?, ?, ?, ?)",
        (4, "Old archive candidate", "This episode is old and unused.", "archive candidate"),
    )
    conn.commit()
    conn.close()


class ReadOnlySearchTests(unittest.TestCase):
    def test_search_and_combined_leave_database_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            db_path = Path(temporary_directory) / "memory.db"
            _seed_database(db_path)
            before = _snapshot(db_path)

            for command in ("search", "combined"):
                result = _run(db_path, command, "--query", "sqlite read only", "--limit", "2")
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertIsInstance(payload, list)
                self.assertLessEqual(len(payload), 2)
                self.assertTrue(payload)
                self.assertTrue(
                    all(isinstance(item, dict) and isinstance(item.get("id"), int) for item in payload)
                )
                self.assertTrue({item["id"] for item in payload}.issubset({1, 2, 3}))
                self.assertIn(1, {item["id"] for item in payload})

            self.assertEqual(_snapshot(db_path), before)

    def test_read_only_permissions_allow_both_search_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            db_path = Path(temporary_directory) / "memory.db"
            _seed_database(db_path)
            os.chmod(db_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            try:
                for command in ("search", "combined"):
                    result = _run(db_path, command, "--query", "sqlite", "--limit", "5")
                    self.assertEqual(result.returncode, 0, result.stderr)
            finally:
                os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)

    def test_missing_idf_fails_without_mutating_database(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            db_path = Path(temporary_directory) / "memory.db"
            _seed_database(db_path, with_idf=False)
            before = _snapshot(db_path)

            for command in ("search", "combined"):
                result = _run(db_path, command, "--query", "sqlite")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("cached IDF", result.stderr)
                self.assertEqual(_snapshot(db_path), before)

    def test_invalid_config_fails_clearly(self) -> None:
        for key, value in (
            ("time_decay_days", "0"),
            ("time_decay_days", "nan"),
            ("usage_recency_days", "-1"),
            ("usage_recency_days", "inf"),
            ("fts_weight", "-0.1"),
            ("usage_boost_weight", "nan"),
        ):
            with self.subTest(key=key, value=value), tempfile.TemporaryDirectory() as temporary_directory:
                db_path = Path(temporary_directory) / "memory.db"
                _seed_database(db_path)
                with sqlite3.connect(str(db_path)) as conn:
                    conn.execute("UPDATE config SET value = ? WHERE key = ?", (value, key))
                before = _snapshot(db_path)

                result = _run(db_path, "combined", "--query", "sqlite")

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"invalid config value for {key}", result.stderr)
                self.assertEqual(_snapshot(db_path), before)

    def test_negative_limit_is_rejected_for_both_search_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            db_path = Path(temporary_directory) / "memory.db"
            _seed_database(db_path)

            for command in ("search", "combined"):
                with self.subTest(command=command):
                    result = _run(db_path, command, "--query", "sqlite", "--limit", "-1")
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("--limit must be a non-negative integer", result.stderr)

    def test_missing_schema_fails_without_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            db_path = Path(temporary_directory) / "memory.db"
            _seed_incomplete_database(db_path)
            before = _snapshot(db_path)

            for command in ("search", "combined"):
                result = _run(db_path, command, "--query", "sqlite")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("requires existing schema", result.stderr)
                self.assertEqual(_snapshot(db_path), before)

    def test_missing_config_columns_fail_without_traceback_or_mutation(self) -> None:
        for definition, missing in (
            ("key TEXT PRIMARY KEY", "value"),
            ("value TEXT", "key"),
        ):
            with self.subTest(definition=definition), tempfile.TemporaryDirectory() as temporary_directory:
                db_path = Path(temporary_directory) / "memory.db"
                _seed_database(db_path)
                _replace_config_table(db_path, definition)
                before = _snapshot(db_path)

                for command in ("search", "combined"):
                    with self.subTest(command=command):
                        result = _run(db_path, command, "--query", "sqlite")
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("missing config column(s): " + missing, result.stderr)
                        self.assertNotIn("Traceback", result.stderr)
                        self.assertEqual(_snapshot(db_path), before)

    def test_broken_fts_fails_instead_of_succeeding_vector_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            db_path = Path(temporary_directory) / "memory.db"
            _seed_database(db_path)
            _replace_fts_with_plain_table(db_path)
            before = _snapshot(db_path)

            result = _run(db_path, "combined", "--query", "sqlite")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("usable episodes_fts index", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(_snapshot(db_path), before)

    def test_mark_used_updates_only_requested_episode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            db_path = Path(temporary_directory) / "memory.db"
            _seed_database(db_path)
            conn = sqlite3.connect(str(db_path))
            before = conn.execute(
                "SELECT id, used_count, last_used_at FROM episodes ORDER BY id"
            ).fetchall()
            conn.close()

            result = _run(db_path, "mark-used", "--ids", "2")
            self.assertEqual(result.returncode, 0, result.stderr)

            conn = sqlite3.connect(str(db_path))
            after = conn.execute(
                "SELECT id, used_count, last_used_at FROM episodes ORDER BY id"
            ).fetchall()
            conn.close()
            self.assertEqual(after[0], before[0])
            self.assertEqual(after[2], before[2])
            self.assertEqual(after[1][0], 2)
            self.assertEqual(after[1][1], before[1][1] + 1)
            self.assertIsNotNone(after[1][2])

    def test_archive_dry_run_is_read_only_including_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            db_path = Path(temporary_directory) / "memory.db"
            _seed_database(db_path)
            _add_old_episode(db_path)
            before = _snapshot(db_path)

            result = _run(db_path, "archive", "--dry-run")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Would archive 1 episodes", result.stdout)
            self.assertEqual(_snapshot(db_path), before)
            conn = sqlite3.connect(str(db_path))
            self.assertEqual(conn.execute("SELECT archived FROM episodes WHERE id = 4").fetchone()[0], 0)
            conn.close()

    def test_archive_dry_run_missing_schema_fails_without_migration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            db_path = Path(temporary_directory) / "memory.db"
            _seed_incomplete_database(db_path)
            before = _snapshot(db_path)

            result = _run(db_path, "archive", "--dry-run")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("archive --dry-run requires existing schema/config", result.stderr)
            self.assertEqual(_snapshot(db_path), before)


if __name__ == "__main__":
    unittest.main()
