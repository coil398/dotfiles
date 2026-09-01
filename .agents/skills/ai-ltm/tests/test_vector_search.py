import hashlib
import importlib.util
import json
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "vector_search.py"


def load_vector_search():
    spec = importlib.util.spec_from_file_location("vector_search", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def file_snapshot(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest, path.stat().st_mtime_ns


class VectorSearchCliTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "memory.db"

    def tearDown(self):
        if self.db_path.exists():
            self.db_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        self.temp_dir.cleanup()

    def create_current_database(self):
        conn = sqlite3.connect(self.db_path)
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
              created_at DATETIME DEFAULT (datetime('now'))
            );
            CREATE TABLE config (key TEXT PRIMARY KEY, value TEXT);
            INSERT INTO config VALUES ('fts_weight', '0.5');
            INSERT INTO config VALUES ('vector_weight', '0.5');
            INSERT INTO config VALUES ('time_decay_days', '30');
            INSERT INTO config VALUES ('usage_boost_weight', '0.3');
            INSERT INTO config VALUES ('usage_recency_days', '30');
            INSERT INTO config VALUES ('archive_after_days', '180');
            INSERT INTO episodes
              (summary, context, tags, embedding, used_count, created_at)
            VALUES
              ('Python SQLite readonly', 'query only database search', 'python sqlite', NULL, 0, datetime('now')),
              ('Unrelated memory', 'gardening notes', 'garden', NULL, 2, datetime('now')),
              ('Old unused memory', 'archive candidate', 'old', NULL, 0, '2020-01-01');
            """
        )
        conn.commit()
        conn.close()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args, "--db", str(self.db_path)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_read_only_commands_work_without_idf_and_do_not_change_database(self):
        self.create_current_database()
        self.db_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        original = file_snapshot(self.db_path)

        search = self.run_cli("search", "--query", "sqlite readonly")
        self.assertEqual(search.returncode, 0, search.stderr)
        self.assertEqual(json.loads(search.stdout)[0]["summary"], "Python SQLite readonly")
        self.assertEqual(file_snapshot(self.db_path), original)

        combined = self.run_cli("combined", "--query", "sqlite readonly")
        self.assertEqual(combined.returncode, 0, combined.stderr)
        self.assertEqual(json.loads(combined.stdout)[0]["summary"], "Python SQLite readonly")
        self.assertEqual(file_snapshot(self.db_path), original)

        archive = self.run_cli("archive", "--dry-run")
        self.assertEqual(archive.returncode, 0, archive.stderr)
        self.assertIn("Would archive 1 episodes", archive.stdout)
        self.assertEqual(file_snapshot(self.db_path), original)

        conn = sqlite3.connect(f"{self.db_path.resolve().as_uri()}?mode=ro", uri=True)
        self.assertIsNone(
            conn.execute("SELECT value FROM config WHERE key = '_idf'").fetchone()
        )
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM episodes WHERE embedding IS NOT NULL").fetchone()[0],
            0,
        )
        conn.close()

    def test_read_only_connection_enables_query_only(self):
        self.create_current_database()
        module = load_vector_search()
        conn = module.open_database(self.db_path, read_only=True)
        self.assertEqual(conn.execute("PRAGMA query_only").fetchone()[0], 1)
        with self.assertRaises(sqlite3.OperationalError):
            conn.execute("UPDATE episodes SET summary = 'changed' WHERE id = 1")
        conn.close()

    def test_read_only_search_computes_missing_embeddings_with_cached_idf(self):
        self.create_current_database()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO config (key, value) VALUES ('_idf', ?)",
            (json.dumps({"sqlite": 1.0, "readonly": 1.0}),),
        )
        conn.execute("UPDATE episodes SET embedding = '' WHERE id = 1")
        conn.commit()
        conn.close()
        self.db_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        original = file_snapshot(self.db_path)

        for command in ("search", "combined"):
            with self.subTest(command=command):
                result = self.run_cli(command, "--query", "sqlite readonly")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    json.loads(result.stdout)[0]["summary"],
                    "Python SQLite readonly",
                )
                self.assertEqual(file_snapshot(self.db_path), original)

    def test_old_schema_reports_migration_required_without_changes(self):
        conn = sqlite3.connect(self.db_path)
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
            """
        )
        conn.commit()
        conn.close()
        self.db_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        original = file_snapshot(self.db_path)

        result = self.run_cli("search", "--query", "anything")

        self.assertEqual(result.returncode, 1)
        self.assertIn("migration required", result.stderr.lower())
        self.assertIn("archived", result.stderr)
        self.assertIn("used_count", result.stderr)
        self.assertEqual(file_snapshot(self.db_path), original)

    def test_writable_rebuild_still_migrates_and_updates_database(self):
        conn = sqlite3.connect(self.db_path)
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
            INSERT INTO episodes (summary, context, tags, created_at)
            VALUES ('Writable rebuild', 'migration', 'sqlite', datetime('now'));
            """
        )
        conn.commit()
        conn.close()

        result = self.run_cli("rebuild")

        self.assertEqual(result.returncode, 0, result.stderr)
        conn = sqlite3.connect(self.db_path)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(episodes)")}
        self.assertTrue({"used_count", "last_used_at", "archived"} <= columns)
        self.assertIsNotNone(
            conn.execute("SELECT value FROM config WHERE key = '_idf'").fetchone()
        )
        self.assertIsNotNone(conn.execute("SELECT embedding FROM episodes").fetchone()[0])
        conn.close()


if __name__ == "__main__":
    unittest.main()
