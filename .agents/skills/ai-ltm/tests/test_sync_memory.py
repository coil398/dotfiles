import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = SKILL_DIR / "scripts" / "sync_memory.py"
REPO_ROOT = SKILL_DIR.parents[2]
RUNTIME_SYNC_SCRIPTS = (
    SYNC_SCRIPT,
    REPO_ROOT / ".codex/skills/ai-ltm/scripts/sync_memory.py",
    REPO_ROOT / ".cursor/skills/ai-ltm/scripts/sync_memory.py",
)
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import sync_memory


SCHEMA = """
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
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE VIRTUAL TABLE episodes_fts USING fts5(
  summary, context, tags, content='episodes', content_rowid='id'
);
CREATE TRIGGER episodes_ai AFTER INSERT ON episodes BEGIN
  INSERT INTO episodes_fts(rowid, summary, context, tags)
  VALUES (new.id, new.summary, new.context, new.tags);
END;
CREATE TRIGGER episodes_ad AFTER DELETE ON episodes BEGIN
  INSERT INTO episodes_fts(episodes_fts, rowid, summary, context, tags)
  VALUES ('delete', old.id, old.summary, old.context, old.tags);
END;
CREATE TRIGGER episodes_au AFTER UPDATE ON episodes BEGIN
  INSERT INTO episodes_fts(episodes_fts, rowid, summary, context, tags)
  VALUES ('delete', old.id, old.summary, old.context, old.tags);
  INSERT INTO episodes_fts(rowid, summary, context, tags)
  VALUES (new.id, new.summary, new.context, new.tags);
END;
"""


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "LTM Test",
        "GIT_AUTHOR_EMAIL": "ltm@example.invalid",
        "GIT_COMMITTER_NAME": "LTM Test",
        "GIT_COMMITTER_EMAIL": "ltm@example.invalid",
    })
    return subprocess.run(
        ["git", *args], cwd=repo, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check,
    )


def execute(db: Path, sql: str, parameters: tuple = ()) -> None:
    with sqlite3.connect(db) as conn:
        conn.execute(sql, parameters)


def rows(db: Path, sql: str) -> list[tuple]:
    with sqlite3.connect(db) as conn:
        return conn.execute(sql).fetchall()


class SyncMemoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ltm-sync-test-")
        self.root = Path(self.temporary.name)
        self.remote = self.root / "remote.git"
        self.local = self.root / "local"
        self.other = self.root / "other"
        git(self.root, "init", "--bare", str(self.remote))
        git(self.root, "init", "-b", "main", str(self.local))
        git(self.local, "remote", "add", "origin", str(self.remote))
        self.db = self.local / "memory.db"
        with sqlite3.connect(self.db) as conn:
            conn.executescript(SCHEMA)
            conn.execute(
                "INSERT INTO episodes VALUES (1, 'base', 'base context', 'base', NULL, 0, NULL, 0, '2026-01-01')"
            )
            conn.execute("INSERT INTO config VALUES ('fts_weight', '0.5')")
            conn.execute("INSERT INTO config VALUES ('vector_weight', '0.5')")
            conn.execute("INSERT INTO config VALUES ('_idf', '{\"base\":1.0}')")
            conn.execute("INSERT INTO meta VALUES ('schema_version', '1')")
            conn.execute("UPDATE episodes SET embedding = '{\"base\":1.0}'")
        git(self.local, "add", "memory.db")
        git(self.local, "commit", "-m", "initial")
        git(self.local, "push", "-u", "origin", "main")
        git(self.root, "clone", "-b", "main", str(self.remote), str(self.other))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_sync(
        self, command: str = "pull", *, script: Path = SYNC_SCRIPT
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), command, "--repo", str(self.local),
             "--db", str(self.db), "--message", "test sync"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    def commit_other(self, message: str = "remote update") -> None:
        git(self.other, "add", "memory.db")
        git(self.other, "commit", "-m", message)
        git(self.other, "push", "origin", "main")

    def test_pull_merges_remote_and_dirty_rows_id_collision_usage_meta_and_config(self) -> None:
        other_db = self.other / "memory.db"
        execute(other_db, "UPDATE episodes SET used_count = 3, last_used_at = '2026-03-01' WHERE id = 1")
        execute(other_db, "INSERT INTO episodes VALUES (2, 'remote two', NULL, 'remote', NULL, 0, NULL, 0, '2026-02-01')")
        execute(other_db, "INSERT INTO episodes VALUES (3, 'remote three', NULL, 'remote', NULL, 0, NULL, 0, '2026-02-02')")
        execute(other_db, "UPDATE config SET value = '0.7' WHERE key = 'fts_weight'")
        execute(other_db, "INSERT INTO meta VALUES ('remote_revision', '2')")
        self.commit_other()

        execute(self.db, "UPDATE episodes SET used_count = 2, last_used_at = '2026-02-15' WHERE id = 1")
        for episode_id in (2, 4, 5, 6, 7):
            execute(
                self.db,
                "INSERT INTO episodes VALUES (?, ?, NULL, 'local', NULL, 0, NULL, 0, '2026-02-10')",
                (episode_id, f"local {episode_id}"),
            )
        execute(self.db, "UPDATE config SET value = '0.8' WHERE key = 'vector_weight'")
        execute(self.db, "INSERT INTO meta VALUES ('local_revision', '3')")

        result = self.run_sync()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ltm-sync: pull ok", result.stdout)
        summaries = {row[0] for row in rows(self.db, "SELECT summary FROM episodes")}
        self.assertEqual(
            summaries,
            {"base", "remote two", "remote three", "local 2", "local 4", "local 5", "local 6", "local 7"},
        )
        self.assertEqual(rows(self.db, "SELECT used_count, last_used_at FROM episodes WHERE id = 1"), [(5, "2026-03-01")])
        self.assertEqual(dict(rows(self.db, "SELECT key, value FROM meta")), {
            "schema_version": "1", "remote_revision": "2", "local_revision": "3",
        })
        self.assertEqual(dict(rows(self.db, "SELECT key, value FROM config")), {
            "fts_weight": "0.7", "vector_weight": "0.8",
        })
        self.assertEqual(rows(self.db, "SELECT DISTINCT embedding FROM episodes"), [(None,)])
        self.assertEqual(
            rows(self.db, "SELECT summary FROM episodes_fts WHERE episodes_fts MATCH 'local' ORDER BY summary"),
            [("local 2",), ("local 4",), ("local 5",), ("local 6",), ("local 7",)],
        )
        self.assertEqual(git(self.local, "status", "--short").stdout.strip(), "M memory.db")

    def test_conflicting_config_change_fails_without_changing_local_data(self) -> None:
        execute(self.other / "memory.db", "UPDATE config SET value = '0.7' WHERE key = 'fts_weight'")
        self.commit_other()
        execute(self.db, "UPDATE config SET value = '0.2' WHERE key = 'fts_weight'")
        before = rows(self.db, "SELECT * FROM config ORDER BY key")
        head_before = git(self.local, "rev-parse", "HEAD").stdout

        result = self.run_sync()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("simultaneous conflicting changes", result.stderr)
        self.assertEqual(rows(self.db, "SELECT * FROM config ORDER BY key"), before)
        self.assertEqual(git(self.local, "rev-parse", "HEAD").stdout, head_before)

    def test_unrelated_dirty_file_stops_before_fetch_or_database_change(self) -> None:
        execute(self.db, "INSERT INTO episodes (summary, created_at) VALUES ('dirty', '2026-04-01')")
        unrelated = self.local / "notes.txt"
        unrelated.write_text("keep me", encoding="utf-8")
        before = rows(self.db, "SELECT id, summary FROM episodes ORDER BY id")

        result = self.run_sync()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("memory.db以外の変更", result.stderr)
        self.assertEqual(rows(self.db, "SELECT id, summary FROM episodes ORDER BY id"), before)
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep me")

    def test_existing_rebase_marker_stops_safely(self) -> None:
        marker = Path(git(self.local, "rev-parse", "--git-path", "rebase-merge").stdout.strip())
        if not marker.is_absolute():
            marker = self.local / marker
        marker.mkdir(parents=True)
        before = rows(self.db, "SELECT id, summary FROM episodes")

        result = self.run_sync()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("既存のGit操作", result.stderr)
        self.assertEqual(rows(self.db, "SELECT id, summary FROM episodes"), before)

    def test_push_commits_only_database_and_updates_remote(self) -> None:
        execute(self.db, "INSERT INTO episodes (summary, created_at) VALUES ('pushed', '2026-05-01')")

        result = self.run_sync("push")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ltm-sync: push ok", result.stdout)
        git(self.other, "pull", "--ff-only")
        self.assertEqual(rows(self.other / "memory.db", "SELECT summary FROM episodes WHERE summary = 'pushed'"), [("pushed",)])
        changed = git(self.local, "show", "--pretty=format:", "--name-only", "HEAD").stdout.split()
        self.assertEqual(changed, ["memory.db"])

    def test_push_failure_keeps_local_database_commit_for_retry(self) -> None:
        execute(self.db, "INSERT INTO episodes (summary, created_at) VALUES ('push retained', '2026-05-03')")
        head_before = git(self.local, "rev-parse", "HEAD").stdout.strip()
        real_git = sync_memory._git

        def fail_push(
            repo: Path, *args: str, check: bool = True
        ) -> subprocess.CompletedProcess[str]:
            if args[:3] == ("push", "origin", "HEAD"):
                return subprocess.CompletedProcess(["git", *args], 1, "", "network unavailable")
            return real_git(repo, *args, check=check)

        with mock.patch.object(sync_memory, "_git", side_effect=fail_push):
            with self.assertRaisesRegex(sync_memory.SyncError, "git push origin HEAD failed"):
                sync_memory.synchronize("push", self.local, self.db, "retained push")

        head_after = git(self.local, "rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(head_after, head_before)
        self.assertEqual(
            git(self.local, "show", "--pretty=format:", "--name-only", "HEAD").stdout.split(),
            ["memory.db"],
        )
        self.assertEqual(
            rows(self.db, "SELECT summary FROM episodes WHERE summary = 'push retained'"),
            [("push retained",)],
        )
        self.assertEqual(git(self.local, "status", "--short").stdout.strip(), "")

    def test_push_rejects_unpushed_non_database_history_even_when_net_diff_is_empty(self) -> None:
        transient = self.local / "transient.txt"
        transient.write_text("temporary", encoding="utf-8")
        git(self.local, "add", "transient.txt")
        git(self.local, "commit", "-m", "add transient path")
        git(self.local, "rm", "-q", "transient.txt")
        git(self.local, "commit", "-m", "remove transient path")

        # A final-tree diff misses this add-then-delete history; a push would
        # still publish both commits unless each commit's changed paths is read.
        self.assertEqual(
            git(self.local, "diff", "--name-only", "origin/main", "HEAD").stdout.strip(),
            "",
        )
        execute(self.db, "INSERT INTO episodes (summary, created_at) VALUES ('must stay local', '2026-08-03')")
        head_before = git(self.local, "rev-parse", "HEAD").stdout.strip()
        remote_head_before = git(self.other, "rev-parse", "HEAD").stdout.strip()
        rows_before = rows(self.db, "SELECT id, summary FROM episodes ORDER BY id")

        for script in RUNTIME_SYNC_SCRIPTS:
            with self.subTest(script=script):
                result = self.run_sync("push", script=script)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("未pushコミットにmemory.db以外の変更", result.stderr)
                self.assertEqual(git(self.local, "rev-parse", "HEAD").stdout.strip(), head_before)
                self.assertEqual(rows(self.db, "SELECT id, summary FROM episodes ORDER BY id"), rows_before)
                self.assertEqual(git(self.local, "status", "--short").stdout.rstrip(), " M memory.db")
        self.assertEqual(git(self.other, "rev-parse", "HEAD").stdout.strip(), remote_head_before)

    def test_remote_only_episode_change_invalidates_cached_vectors(self) -> None:
        execute(
            self.other / "memory.db",
            "INSERT INTO episodes VALUES (2, 'remote cache change', NULL, 'remote', '{\"stale\":1}', 0, NULL, 0, '2026-05-02')",
        )
        self.commit_other()

        result = self.run_sync()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(rows(self.db, "SELECT value FROM config WHERE key = '_idf'"), [])
        self.assertEqual(rows(self.db, "SELECT DISTINCT embedding FROM episodes"), [(None,)])
        self.assertEqual(
            rows(self.db, "SELECT summary FROM episodes_fts WHERE episodes_fts MATCH 'cache'"),
            [("remote cache change",)],
        )

    def test_diverged_binary_history_is_logically_merged(self) -> None:
        execute(
            self.db,
            "INSERT INTO episodes (summary, created_at) VALUES ('local committed', '2026-06-01')",
        )
        git(self.local, "add", "memory.db")
        git(self.local, "commit", "-m", "local commit")
        execute(
            self.other / "memory.db",
            "INSERT INTO episodes (summary, created_at) VALUES ('remote committed', '2026-06-02')",
        )
        self.commit_other("remote divergent commit")
        execute(
            self.db,
            "INSERT INTO episodes (summary, created_at) VALUES ('local dirty', '2026-06-03')",
        )

        result = self.run_sync()

        self.assertEqual(result.returncode, 0, result.stderr)
        summaries = {row[0] for row in rows(self.db, "SELECT summary FROM episodes")}
        self.assertEqual(summaries, {"base", "local committed", "remote committed", "local dirty"})
        parents = git(self.local, "show", "-s", "--format=%P", "HEAD").stdout.split()
        self.assertEqual(len(parents), 2)
        self.assertEqual(git(self.local, "status", "--short").stdout.strip(), "M memory.db")

    def test_failure_after_fast_forward_restores_database_head_and_branch(self) -> None:
        execute(
            self.other / "memory.db",
            "INSERT INTO episodes (summary, created_at) VALUES ('remote', '2026-07-01')",
        )
        self.commit_other()
        execute(
            self.db,
            "INSERT INTO episodes (summary, created_at) VALUES ('dirty', '2026-07-02')",
        )
        head_before = git(self.local, "rev-parse", "HEAD").stdout.strip()
        branch_before = git(self.local, "branch", "--show-current").stdout.strip()
        rows_before = rows(self.db, "SELECT id, summary FROM episodes ORDER BY id")
        real_atomic_copy = sync_memory._atomic_copy

        def fail_final_replace(source: Path, destination: Path) -> None:
            if source.name == "working-merged.db":
                raise OSError("injected final replace failure")
            real_atomic_copy(source, destination)

        with mock.patch.object(sync_memory, "_atomic_copy", side_effect=fail_final_replace):
            with self.assertRaisesRegex(OSError, "injected final replace failure"):
                sync_memory.synchronize("pull", self.local, self.db)

        self.assertEqual(git(self.local, "rev-parse", "HEAD").stdout.strip(), head_before)
        self.assertEqual(git(self.local, "branch", "--show-current").stdout.strip(), branch_before)
        self.assertEqual(rows(self.db, "SELECT id, summary FROM episodes ORDER BY id"), rows_before)
        self.assertEqual(git(self.local, "status", "--short").stdout.strip(), "M memory.db")

    def test_push_non_fast_forward_resynchronizes_once(self) -> None:
        execute(
            self.db,
            "INSERT INTO episodes (summary, created_at) VALUES ('local push', '2026-08-01')",
        )
        real_git = sync_memory._git
        raced = False

        def race_before_first_push(
            repo: Path, *args: str, check: bool = True
        ) -> subprocess.CompletedProcess[str]:
            nonlocal raced
            if args[:3] == ("push", "origin", "HEAD") and not raced:
                raced = True
                execute(
                    self.other / "memory.db",
                    "INSERT INTO episodes (summary, created_at) VALUES ('remote race', '2026-08-02')",
                )
                self.commit_other("remote push race")
            return real_git(repo, *args, check=check)

        with mock.patch.object(sync_memory, "_git", side_effect=race_before_first_push):
            sync_memory.synchronize("push", self.local, self.db, "local race push")

        git(self.other, "pull", "--ff-only")
        remote_summaries = {
            row[0] for row in rows(self.other / "memory.db", "SELECT summary FROM episodes")
        }
        self.assertIn("local push", remote_summaries)
        self.assertIn("remote race", remote_summaries)
        self.assertTrue(raced)


if __name__ == "__main__":
    unittest.main()
