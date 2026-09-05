#!/usr/bin/env python3
"""Isolated regression tests for the ai-ltm session recall runner."""

from __future__ import annotations

import importlib.util
import base64
import hashlib
import json
from pathlib import Path
import os
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Optional
import unittest


PYTHON = "/usr/bin/python3"
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "session_recall.py"
MODULE_SPEC = importlib.util.spec_from_file_location("session_recall_under_test", SCRIPT)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
SESSION_RECALL = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = SESSION_RECALL
MODULE_SPEC.loader.exec_module(SESSION_RECALL)


FAKE_GIT = """#!/usr/bin/python3
import json
import os
import signal
import sys
import time

args = sys.argv[1:]
log_path = os.environ.get("FAKE_GIT_LOG")
record = {
    "args": args,
    "stdin_isatty": sys.stdin.isatty(),
    "env": {
        key: os.environ.get(key)
        for key in ("GIT_TERMINAL_PROMPT", "GIT_ASKPASS", "SSH_ASKPASS", "GIT_SSH_COMMAND")
    },
}
if log_path:
    with open(log_path, "a") as handle:
        handle.write(json.dumps(record) + "\\n")

mode = os.environ.get("FAKE_GIT_MODE", "clean")
if "status" in args:
    if mode == "dirty":
        print(" M tracked.txt")
        sys.exit(0)
    if mode == "status-fail":
        print("status failed", file=sys.stderr)
        sys.exit(6)
    if mode == "status-sleep":
        time.sleep(10)
    sys.exit(0)

if "pull" in args:
    if mode == "pull-auth-fail":
        print("fatal: Authentication failed", file=sys.stderr)
        sys.exit(9)
    if mode == "pull-transient":
        counter_path = os.environ["FAKE_GIT_COUNTER"]
        with open(counter_path) as handle:
            count = int(handle.read() or "0")
        with open(counter_path, "w") as handle:
            handle.write(str(count + 1))
        if count == 0:
            print("fatal: Could not resolve host", file=sys.stderr)
            sys.exit(128)
    if mode == "pull-sleep":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        time.sleep(10)
    sys.exit(0)

sys.exit(4)
"""

FAKE_VECTOR = """#!/usr/bin/python3
import json
import os
import signal
import sys
import time

log_path = os.environ.get("FAKE_VECTOR_LOG")
if log_path:
    with open(log_path, "a") as handle:
        handle.write(json.dumps(sys.argv[1:]) + "\\n")
if os.environ.get("FAKE_VECTOR_MODE") == "fail":
    print("search failed", file=sys.stderr)
    sys.exit(7)
if os.environ.get("FAKE_VECTOR_MODE") == "secret-fail":
    secret = "token-shaped-secret-7f3b2c9d"
    print(secret)
    print(secret, file=sys.stderr)
    sys.exit(23)
if os.environ.get("FAKE_VECTOR_MODE") == "sleep":
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(10)
print(json.dumps([{"id": 41}, {"id": 42}]))
"""

SLEEPER = """import signal
import time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
time.sleep(10)
"""


def _write_executable(path: Path, contents: str) -> None:
    path.write_text(contents)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _read_json_lines(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


class SessionRecallTests(unittest.TestCase):
    def _fixture(self):
        temporary_directory = tempfile.TemporaryDirectory()
        root = Path(temporary_directory.name)
        repo = root / "ltm"
        repo.mkdir()
        (repo / ".git").mkdir()
        db = root / "memory.db"
        db.write_bytes(b"isolated test database")
        fake_git = root / "fake-git.py"
        fake_vector = root / "fake-vector.py"
        _write_executable(fake_git, FAKE_GIT)
        _write_executable(fake_vector, FAKE_VECTOR)
        git_log = root / "git.jsonl"
        vector_log = root / "vector.jsonl"
        lock_path = root / "recall.lock"
        env = os.environ.copy()
        env.update(
            {
                "FAKE_GIT_LOG": str(git_log),
                "FAKE_VECTOR_LOG": str(vector_log),
                "FAKE_GIT_MODE": "clean",
                "FAKE_VECTOR_MODE": "ok",
            }
        )
        return temporary_directory, root, repo, db, fake_git, fake_vector, git_log, vector_log, lock_path, env

    def _run(
        self,
        repo: Path,
        db: Path,
        fake_git: Path,
        fake_vector: Path,
        lock_path: Path,
        env,
        *extra: str,
        query: Optional[str] = "archive dry-run reviewer fix",
        summary: Optional[str] = "fix read-only recall",
        query_b64: Optional[str] = None,
        summary_b64: Optional[str] = None,
    ):
        arguments = [
            PYTHON,
            str(SCRIPT),
            "--repo",
            str(repo),
            "--db",
            str(db),
            "--limit",
            "2",
            "--git",
            str(fake_git),
            "--vector-search",
            str(fake_vector),
        ]
        if lock_path is not None:
            arguments.extend(["--lock-path", str(lock_path)])
        if query_b64 is not None:
            arguments.extend(["--query-b64", query_b64])
        else:
            arguments.extend(["--query", query or ""])
        if summary_b64 is not None:
            arguments.extend(["--summary-b64", summary_b64])
        elif summary is not None:
            arguments.extend(["--summary", summary])
        arguments.extend(extra)
        return subprocess.run(
            arguments,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    @staticmethod
    def _events(result: subprocess.CompletedProcess):
        if result.stdout:
            return [json.loads(line) for line in result.stdout.splitlines()]
        return []

    @staticmethod
    def _terminal(events):
        terminals = [event for event in events if event.get("type") == "terminal"]
        if len(terminals) != 1:
            raise AssertionError("expected exactly one terminal record: {}".format(events))
        return terminals[0]

    def test_query_forwarding_and_hardened_git_invocation(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, _, repo, db, fake_git, fake_vector, git_log, vector_log, lock_path, env = fixture
            result = self._run(repo, db, fake_git, fake_vector, lock_path, env)
            events = self._events(result)
            terminal = self._terminal(events)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(terminal["terminal_status"], "completed")
            self.assertEqual(terminal["query"], "archive dry-run reviewer fix")
            self.assertEqual(terminal["summary"], "fix read-only recall")
            self.assertEqual(terminal["result_ids"], [41, 42])
            vector_args = _read_json_lines(vector_log)
            self.assertEqual(len(vector_args), 1)
            self.assertIn("combined", vector_args[0])
            self.assertEqual(vector_args[0][vector_args[0].index("--query") + 1], "archive dry-run reviewer fix")
            self.assertEqual(vector_args[0][vector_args[0].index("--limit") + 1], "2")

            git_records = _read_json_lines(git_log)
            self.assertEqual(len(git_records), 2)
            pull = next(record for record in git_records if "pull" in record["args"])
            self.assertFalse(pull["stdin_isatty"])
            self.assertEqual(pull["env"]["GIT_TERMINAL_PROMPT"], "0")
            self.assertEqual(pull["env"]["GIT_ASKPASS"], "/usr/bin/false")
            self.assertEqual(pull["env"]["SSH_ASKPASS"], "/usr/bin/false")
            self.assertIn("BatchMode=yes", pull["env"]["GIT_SSH_COMMAND"])
            self.assertIn("ConnectTimeout=10", pull["env"]["GIT_SSH_COMMAND"])
            args = pull["args"]
            for config in (
                "core.hooksPath=/dev/null",
                "rebase.autoStash=false",
                "protocol.ext.allow=never",
                "credential.interactive=false",
                "credential.helper=",
                "core.askPass=false",
            ):
                self.assertIn(config, args)
            self.assertIn("--rebase", args)
            self.assertIn("--quiet", args)

    def test_dirty_skips_pull_but_still_searches(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, _, repo, db, fake_git, fake_vector, git_log, vector_log, lock_path, env = fixture
            env["FAKE_GIT_MODE"] = "dirty"
            result = self._run(repo, db, fake_git, fake_vector, lock_path, env)
            events = self._events(result)
            terminal = self._terminal(events)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(terminal["terminal_status"], "dirty")
            self.assertEqual(terminal["pull_status"], "skipped")
            self.assertEqual(terminal["search_status"], "completed")
            self.assertEqual(len(_read_json_lines(vector_log)), 1)
            self.assertEqual(len(_read_json_lines(git_log)), 1)
            self.assertNotIn("pull", _read_json_lines(git_log)[0]["args"])

    def test_setup_needed_and_missing_database_are_explicit(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, repo, db, fake_git, fake_vector, _, vector_log, lock_path, env = fixture
            missing_repo = root / "missing-repo"
            result = self._run(missing_repo, db, fake_git, fake_vector, lock_path, env)
            terminal = self._terminal(self._events(result))
            self.assertEqual(terminal["terminal_status"], "setup-needed")
            self.assertEqual(terminal["pull_status"], "skipped")
            self.assertEqual(terminal["search_status"], "completed")
            self.assertEqual(len(_read_json_lines(vector_log)), 1)

            missing_db = root / "missing.db"
            result = self._run(repo, missing_db, fake_git, fake_vector, lock_path, env)
            terminal = self._terminal(self._events(result))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(terminal["terminal_status"], "search-failed")
            self.assertEqual(terminal["search_status"], "missing-database")

    def test_base64_hostile_values_are_forwarded_without_shell_side_effects(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, repo, db, fake_git, fake_vector, _, vector_log, lock_path, env = fixture
            side_effect = root / "unexpected-side-effect"
            query = (
                f'$(touch {side_effect}) `touch {side_effect}` "quoted" \'single\';'
                f" ;\nnext-query"
            )
            summary = (
                f"summary $(touch {side_effect}) `touch {side_effect}` \"quoted\";"
                f"\nnext-summary"
            )
            result = self._run(
                repo,
                db,
                fake_git,
                fake_vector,
                lock_path,
                env,
                query=None,
                summary=None,
                query_b64=base64.b64encode(query.encode("utf-8")).decode("ascii"),
                summary_b64=base64.b64encode(summary.encode("utf-8")).decode("ascii"),
            )
            events = self._events(result)
            terminal = self._terminal(events)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(terminal["query"], query)
            self.assertEqual(terminal["summary"], summary)
            vector_args = _read_json_lines(vector_log)
            self.assertEqual(len(vector_args), 1)
            self.assertEqual(
                vector_args[0][vector_args[0].index("--query") + 1], query
            )
            self.assertFalse(side_effect.exists())

    def test_base64_decode_is_strict(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, _, repo, db, fake_git, fake_vector, _, _, lock_path, env = fixture
            result = self._run(
                repo,
                db,
                fake_git,
                fake_vector,
                lock_path,
                env,
                query=None,
                query_b64="not-valid-base64!",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("--query-b64 must be strict base64", result.stderr)

            result = self._run(
                repo,
                db,
                fake_git,
                fake_vector,
                lock_path,
                env,
                query=None,
                query_b64="/w==",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("--query-b64 must decode as UTF-8", result.stderr)

            result = self._run(
                repo,
                db,
                fake_git,
                fake_vector,
                lock_path,
                env,
                query=None,
                summary=None,
                query_b64=base64.b64encode(b"valid query").decode("ascii"),
                summary_b64="not-valid-base64!",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("--summary-b64 must be strict base64", result.stderr)

    def test_child_secret_output_is_not_emitted_in_jsonl(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, _, repo, db, fake_git, fake_vector, _, _, lock_path, env = fixture
            env["FAKE_VECTOR_MODE"] = "secret-fail"
            secret = "token-shaped-secret-7f3b2c9d"
            result = self._run(repo, db, fake_git, fake_vector, lock_path, env)
            events = self._events(result)
            terminal = self._terminal(events)

            self.assertEqual(result.returncode, 23)
            self.assertEqual(terminal["terminal_status"], "search-failed")
            self.assertNotIn(secret, result.stdout)
            self.assertNotIn(secret, result.stderr)
            for event in events:
                self.assertNotIn(secret, json.dumps(event, ensure_ascii=False))

    def test_pull_failure_is_not_masked_and_transient_retry_is_bounded(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, repo, db, fake_git, fake_vector, git_log, _, lock_path, env = fixture
            env["FAKE_GIT_MODE"] = "pull-auth-fail"
            result = self._run(repo, db, fake_git, fake_vector, lock_path, env)
            terminal = self._terminal(self._events(result))
            self.assertEqual(result.returncode, 9)
            self.assertEqual(terminal["terminal_status"], "pull-failed")
            self.assertEqual(terminal["pull_exit"], 9)
            self.assertEqual(terminal["retry_count"], 0)
            self.assertEqual(len([record for record in _read_json_lines(git_log) if "pull" in record["args"]]), 1)

            counter = root / "counter"
            counter.write_text("0")
            env["FAKE_GIT_MODE"] = "pull-transient"
            env["FAKE_GIT_COUNTER"] = str(counter)
            git_log.write_text("")
            result = self._run(repo, db, fake_git, fake_vector, lock_path, env)
            terminal = self._terminal(self._events(result))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(terminal["terminal_status"], "completed")
            self.assertEqual(terminal["retry_count"], 1)
            self.assertEqual(len([record for record in _read_json_lines(git_log) if "pull" in record["args"]]), 2)

    def test_failure_terminal_statuses_are_normalized(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, _, repo, db, fake_git, fake_vector, _, _, lock_path, env = fixture
            env["FAKE_GIT_MODE"] = "status-fail"
            result = self._run(repo, db, fake_git, fake_vector, lock_path, env)
            terminal = self._terminal(self._events(result))
            self.assertEqual(terminal["terminal_status"], "failed")
            self.assertNotEqual(result.returncode, 0)

            env["FAKE_GIT_MODE"] = "clean"
            env["FAKE_VECTOR_MODE"] = "fail"
            result = self._run(repo, db, fake_git, fake_vector, lock_path, env)
            terminal = self._terminal(self._events(result))
            self.assertEqual(terminal["terminal_status"], "search-failed")
            self.assertNotEqual(result.returncode, 0)

    def test_timeout_kills_process_group_and_converges(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, repo, db, fake_git, fake_vector, _, _, lock_path, env = fixture
            sleeper = root / "sleeper.py"
            sleeper.write_text(SLEEPER)
            started = time.monotonic()
            command = SESSION_RECALL.run_bounded([PYTHON, str(sleeper)], timeout=0.05)
            elapsed = time.monotonic() - started
            self.assertTrue(command.timed_out)
            self.assertEqual(command.termination, "kill")
            self.assertLess(elapsed, 2.0)
            self.assertIsNotNone(command.returncode)

            env["FAKE_GIT_MODE"] = "pull-sleep"
            started = time.monotonic()
            result = self._run(
                repo,
                db,
                fake_git,
                fake_vector,
                lock_path,
                env,
                "--timeout",
                "0.5",
                "--pull-timeout",
                "0.05",
            )
            elapsed = time.monotonic() - started
            terminal = self._terminal(self._events(result))
            self.assertEqual(terminal["terminal_status"], "timed-out")
            self.assertNotEqual(result.returncode, 0)
            self.assertLess(elapsed, 2.0)

    def test_busy_lock_returns_timed_out_without_waiting_indefinitely(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, _, repo, db, fake_git, fake_vector, _, _, lock_path, env = fixture
            holder = SESSION_RECALL.AdvisoryFileLock(lock_path, timeout=1.0)
            acquired, error = holder.acquire()
            self.assertTrue(acquired, error)
            try:
                started = time.monotonic()
                result = self._run(
                    repo,
                    db,
                    fake_git,
                    fake_vector,
                    lock_path,
                    env,
                    "--lock-timeout",
                    "0.03",
                )
                elapsed = time.monotonic() - started
            finally:
                holder.release()
            terminal = self._terminal(self._events(result))
            self.assertEqual(terminal["terminal_status"], "timed-out")
            self.assertEqual(terminal["detail"]["reason"], "busy")
            self.assertLess(elapsed, 1.0)

    @staticmethod
    def _default_path_with_temp_base(repo: Path, temp_base: Path) -> Path:
        previous_tempdir = tempfile.tempdir
        tempfile.tempdir = str(temp_base)
        try:
            return SESSION_RECALL._default_lock_path(repo)
        finally:
            tempfile.tempdir = previous_tempdir

    def test_default_lock_is_private_temp_path_and_does_not_dirty_repo(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, repo, db, fake_git, fake_vector, git_log, vector_log, _, env = fixture
            temp_base = root / "sandbox-temp"
            temp_base.mkdir()
            expected_lock = self._default_path_with_temp_base(repo, temp_base)
            before_repo = sorted(str(path.relative_to(repo)) for path in repo.rglob("*"))
            env["TMPDIR"] = str(temp_base)

            result = self._run(
                repo,
                db,
                fake_git,
                fake_vector,
                None,
                env,
            )

            terminal = self._terminal(self._events(result))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(terminal["terminal_status"], "completed")
            self.assertTrue(expected_lock.is_file())
            self.assertEqual(stat.S_IMODE(expected_lock.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(expected_lock.parent.stat().st_mode), 0o700)
            self.assertNotIn(repo, expected_lock.parents)
            self.assertEqual(
                before_repo,
                sorted(str(path.relative_to(repo)) for path in repo.rglob("*")),
            )
            self.assertEqual(len(_read_json_lines(git_log)), 2)
            self.assertEqual(len(_read_json_lines(vector_log)), 1)

    def test_default_lock_paths_hash_canonical_repo_and_canonical_temp_base(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, repo, _, _, _, _, _, _, _ = fixture
            real_temp_base = root / "real-temp"
            real_temp_base.mkdir()
            temp_alias = root / "temp-alias"
            temp_alias.symlink_to(real_temp_base, target_is_directory=True)
            other_repo = root / "other-repo"
            repo_alias = root / "repo-alias"
            repo_alias.symlink_to(repo, target_is_directory=True)

            first = self._default_path_with_temp_base(repo, temp_alias)
            second = self._default_path_with_temp_base(repo_alias, temp_alias)
            other = self._default_path_with_temp_base(other_repo, temp_alias)
            repo_hash = hashlib.sha256(os.fsencode(str(repo.resolve()))).hexdigest()

            self.assertEqual(first, second)
            self.assertNotEqual(first, other)
            self.assertEqual(first.parent, real_temp_base.resolve() / (
                SESSION_RECALL.DEFAULT_LOCK_DIRECTORY_PREFIX + str(os.getuid())
            ))
            self.assertIn(repo_hash, first.name)

    def test_default_private_directory_rejects_unsafe_existing_mode(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, repo, db, fake_git, fake_vector, git_log, vector_log, _, env = fixture
            temp_base = root / "unsafe-temp"
            temp_base.mkdir()
            expected_lock = self._default_path_with_temp_base(repo, temp_base)
            expected_lock.parent.mkdir()
            expected_lock.parent.chmod(0o755)
            env["TMPDIR"] = str(temp_base)

            result = self._run(repo, db, fake_git, fake_vector, None, env)

            terminal = self._terminal(self._events(result))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(terminal["terminal_status"], "timed-out")
            self.assertEqual(terminal["detail"]["reason"], "lock-unavailable")
            self.assertFalse(expected_lock.exists())
            self.assertEqual(_read_json_lines(git_log), [])
            self.assertEqual(_read_json_lines(vector_log), [])

    def test_default_private_directory_rejects_symlink_and_non_directory(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, _, _, _, _, _, _, _, _ = fixture
            symlink_target = root / "directory-target"
            symlink_target.mkdir()
            symlink_path = root / "directory-symlink"
            symlink_path.symlink_to(symlink_target, target_is_directory=True)
            non_directory = root / "not-a-directory"
            non_directory.write_text("keep this data")

            with self.assertRaises(OSError):
                SESSION_RECALL._ensure_private_directory(symlink_path)
            with self.assertRaises(OSError):
                SESSION_RECALL._ensure_private_directory(non_directory)
            self.assertTrue(symlink_path.is_symlink())
            self.assertTrue(symlink_target.is_dir())
            self.assertEqual(non_directory.read_text(), "keep this data")

    def test_symlink_lock_is_rejected_without_touching_target(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, repo, db, fake_git, fake_vector, git_log, vector_log, _, env = fixture
            target = root / "lock-target"
            target.write_bytes(b"target data")
            target.chmod(0o600)
            lock_path = root / "symlink.lock"
            lock_path.symlink_to(target)
            before = (target.read_bytes(), target.stat().st_mtime_ns, stat.S_IMODE(target.stat().st_mode))

            result = self._run(repo, db, fake_git, fake_vector, lock_path, env)

            terminal = self._terminal(self._events(result))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(terminal["terminal_status"], "timed-out")
            self.assertEqual(terminal["detail"]["reason"], "lock-unavailable")
            self.assertEqual(
                before,
                (target.read_bytes(), target.stat().st_mtime_ns, stat.S_IMODE(target.stat().st_mode)),
            )
            self.assertTrue(lock_path.is_symlink())
            self.assertEqual(_read_json_lines(git_log), [])
            self.assertEqual(_read_json_lines(vector_log), [])

    def test_unsafe_lock_mode_is_rejected_without_repairing_file(self) -> None:
        fixture = self._fixture()
        with fixture[0]:
            _, root, repo, db, fake_git, fake_vector, git_log, vector_log, _, env = fixture
            lock_path = root / "unsafe.lock"
            lock_path.write_bytes(b"keep this data")
            lock_path.chmod(0o640)
            before = (lock_path.read_bytes(), lock_path.stat().st_mtime_ns, stat.S_IMODE(lock_path.stat().st_mode))

            result = self._run(repo, db, fake_git, fake_vector, lock_path, env)

            terminal = self._terminal(self._events(result))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(terminal["terminal_status"], "timed-out")
            self.assertEqual(terminal["detail"]["reason"], "lock-unavailable")
            self.assertEqual(
                before,
                (lock_path.read_bytes(), lock_path.stat().st_mtime_ns, stat.S_IMODE(lock_path.stat().st_mode)),
            )
            self.assertEqual(_read_json_lines(git_log), [])
            self.assertEqual(_read_json_lines(vector_log), [])


if __name__ == "__main__":
    unittest.main()
