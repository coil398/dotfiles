#!/usr/bin/env python3
"""Behavioral tests for the runtime-neutral check-updates scripts."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SKILL_DIR.parents[2]
RUNTIME_SCRIPTS = (
    PROJECT_ROOT / ".agents/skills/check-updates/scripts/check-updates.sh",
    PROJECT_ROOT / ".codex/skills/check-updates/scripts/check-updates.sh",
    PROJECT_ROOT / ".cursor/skills/check-updates/scripts/check-updates.sh",
)


def run_git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed ({result.returncode}): "
            f"{result.stdout}\n{result.stderr}"
        )
    return result


def configure_identity(repo: Path) -> None:
    run_git("config", "user.name", "check-updates-test", cwd=repo)
    run_git("config", "user.email", "check-updates-test@example.invalid", cwd=repo)


def make_fixture(base: Path, clone_relative: Path = Path("marketplace/plugin/version 1")) -> dict[str, Path]:
    remote = base / "remote.git"
    seed = base / "seed"
    root = base / "cache root with spaces"
    clone = root / clone_relative
    root.mkdir(parents=True)

    run_git("init", "--bare", str(remote), cwd=base)
    run_git("init", "-b", "main", str(seed), cwd=base)
    configure_identity(seed)
    (seed / "state.txt").write_text("initial\n", encoding="utf-8")
    run_git("add", "state.txt", cwd=seed)
    run_git("commit", "-m", "initial", cwd=seed)
    run_git("remote", "add", "origin", str(remote), cwd=seed)
    run_git("push", "-u", "origin", "main", cwd=seed)

    clone.parent.mkdir(parents=True)
    run_git("clone", "-b", "main", str(remote), str(clone), cwd=base)
    configure_identity(clone)
    return {"remote": remote, "seed": seed, "root": root, "clone": clone}


def advance_remote(fixture: dict[str, Path], content: str = "remote update\n") -> None:
    seed = fixture["seed"]
    (seed / "state.txt").write_text(content, encoding="utf-8")
    run_git("add", "state.txt", cwd=seed)
    run_git("commit", "-m", "remote update", cwd=seed)
    run_git("push", cwd=seed)


def run_check(script: Path, *roots: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        ["bash", str(script), *(str(root) for root in roots)],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


class CheckUpdatesScriptsTest(unittest.TestCase):
    def for_each_runtime(self):
        for script in RUNTIME_SCRIPTS:
            self.subTest(runtime=script.parents[3].name)
            yield script

    def test_scripts_have_same_runtime_neutral_source(self) -> None:
        sources = [script.read_bytes() for script in RUNTIME_SCRIPTS]
        self.assertTrue(all(source == sources[0] for source in sources[1:]))

    def test_clean_clone_is_fast_forwarded_at_current_cache_depth(self) -> None:
        for script in self.for_each_runtime():
            with tempfile.TemporaryDirectory(prefix="check-updates-ff-") as temp:
                fixture = make_fixture(Path(temp))
                before = run_git("rev-parse", "HEAD", cwd=fixture["clone"]).stdout.strip()
                advance_remote(fixture)

                result = run_check(script, fixture["root"])

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("UPDATED:", result.stdout)
                self.assertIn("CHECKED: 1", result.stdout)
                self.assertIn("UPDATED_COUNT: 1", result.stdout)
                self.assertIn("remote update", (fixture["clone"] / "state.txt").read_text())
                after = run_git("rev-parse", "HEAD", cwd=fixture["clone"]).stdout.strip()
                remote_head = run_git(
                    "rev-parse", "refs/remotes/origin/main", cwd=fixture["clone"]
                ).stdout.strip()
                self.assertNotEqual(before, after)
                self.assertEqual(after, remote_head)
                parents = run_git("show", "-s", "--format=%P", "HEAD", cwd=fixture["clone"]).stdout.split()
                self.assertEqual(len(parents), 1)

    def test_only_explicit_roots_are_scanned(self) -> None:
        for script in self.for_each_runtime():
            with tempfile.TemporaryDirectory(prefix="check-updates-explicit-roots-") as temp:
                base = Path(temp)
                codex_fixture_base = base / "Codex fixture"
                cursor_fixture_base = base / "Cursor fixture"
                codex_fixture_base.mkdir()
                cursor_fixture_base.mkdir()
                codex_fixture = make_fixture(codex_fixture_base)
                cursor_fixture = make_fixture(cursor_fixture_base)
                advance_remote(codex_fixture, "codex update\n")
                advance_remote(cursor_fixture, "cursor update\n")
                cursor_before = run_git("rev-parse", "HEAD", cwd=cursor_fixture["clone"]).stdout.strip()

                result = run_check(script, codex_fixture["root"])

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("CHECKED: 1", result.stdout)
                self.assertIn("UPDATED_COUNT: 1", result.stdout)
                self.assertIn("codex update", (codex_fixture["clone"] / "state.txt").read_text())
                self.assertEqual(
                    cursor_before,
                    run_git("rev-parse", "HEAD", cwd=cursor_fixture["clone"]).stdout.strip(),
                )
                self.assertEqual("initial\n", (cursor_fixture["clone"] / "state.txt").read_text())

    def test_dirty_clone_is_preserved_without_fetch(self) -> None:
        for script in self.for_each_runtime():
            with tempfile.TemporaryDirectory(prefix="check-updates-dirty-") as temp:
                fixture = make_fixture(Path(temp))
                clone = fixture["clone"]
                before_head = run_git("rev-parse", "HEAD", cwd=clone).stdout.strip()
                before_remote = run_git(
                    "rev-parse", "refs/remotes/origin/main", cwd=clone
                ).stdout.strip()
                (clone / "state.txt").write_text("local dirty\n", encoding="utf-8")
                advance_remote(fixture)

                result = run_check(script, fixture["root"])

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("DIRTY:", result.stdout)
                self.assertIn("preserved", result.stdout)
                self.assertEqual(before_head, run_git("rev-parse", "HEAD", cwd=clone).stdout.strip())
                self.assertEqual(
                    before_remote,
                    run_git("rev-parse", "refs/remotes/origin/main", cwd=clone).stdout.strip(),
                )
                self.assertEqual("local dirty\n", (clone / "state.txt").read_text())

    def test_diverged_clone_is_preserved_without_merge(self) -> None:
        for script in self.for_each_runtime():
            with tempfile.TemporaryDirectory(prefix="check-updates-diverged-") as temp:
                fixture = make_fixture(Path(temp))
                clone = fixture["clone"]
                (clone / "state.txt").write_text("local commit\n", encoding="utf-8")
                run_git("add", "state.txt", cwd=clone)
                run_git("commit", "-m", "local commit", cwd=clone)
                before_head = run_git("rev-parse", "HEAD", cwd=clone).stdout.strip()
                advance_remote(fixture)

                result = run_check(script, fixture["root"])

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("DIVERGED:", result.stdout)
                self.assertEqual(before_head, run_git("rev-parse", "HEAD", cwd=clone).stdout.strip())
                self.assertEqual("local commit\n", (clone / "state.txt").read_text())
                self.assertEqual("", run_git("status", "--porcelain", cwd=clone).stdout)

    def test_ahead_clone_is_preserved_without_push(self) -> None:
        for script in self.for_each_runtime():
            with tempfile.TemporaryDirectory(prefix="check-updates-ahead-") as temp:
                fixture = make_fixture(Path(temp))
                clone = fixture["clone"]
                (clone / "state.txt").write_text("local only\n", encoding="utf-8")
                run_git("add", "state.txt", cwd=clone)
                run_git("commit", "-m", "local only", cwd=clone)
                before_head = run_git("rev-parse", "HEAD", cwd=clone).stdout.strip()
                remote_head = run_git("rev-parse", "main", cwd=fixture["seed"]).stdout.strip()

                result = run_check(script, fixture["root"])

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("AHEAD:", result.stdout)
                self.assertEqual(before_head, run_git("rev-parse", "HEAD", cwd=clone).stdout.strip())
                self.assertEqual(remote_head, run_git("rev-parse", "refs/remotes/origin/main", cwd=clone).stdout.strip())

    def test_no_upstream_is_reported_and_preserved(self) -> None:
        for script in self.for_each_runtime():
            with tempfile.TemporaryDirectory(prefix="check-updates-no-upstream-") as temp:
                base = Path(temp)
                root = base / "skills root"
                repo = root / "user" / "local skill"
                repo.mkdir(parents=True)
                run_git("init", "-b", "main", str(repo), cwd=base)
                configure_identity(repo)
                (repo / "SKILL.md").write_text("local\n", encoding="utf-8")
                run_git("add", "SKILL.md", cwd=repo)
                run_git("commit", "-m", "local skill", cwd=repo)
                before_head = run_git("rev-parse", "HEAD", cwd=repo).stdout.strip()

                result = run_check(script, root)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("NO_UPSTREAM:", result.stdout)
                self.assertEqual(before_head, run_git("rev-parse", "HEAD", cwd=repo).stdout.strip())

    def test_fetch_failure_is_nonzero_and_preserves_head(self) -> None:
        for script in self.for_each_runtime():
            with tempfile.TemporaryDirectory(prefix="check-updates-fetch-failure-") as temp:
                base = Path(temp)
                fixture = make_fixture(base)
                clone = fixture["clone"]
                before_head = run_git("rev-parse", "HEAD", cwd=clone).stdout.strip()
                missing_remote = base / "missing remote.git"
                run_git("remote", "set-url", "origin", str(missing_remote), cwd=clone)

                result = run_check(script, fixture["root"])

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("FETCH_FAILED:", result.stdout)
                self.assertEqual(before_head, run_git("rev-parse", "HEAD", cwd=clone).stdout.strip())

    def test_non_repo_and_managed_roots_are_not_checked(self) -> None:
        for script in self.for_each_runtime():
            with tempfile.TemporaryDirectory(prefix="check-updates-scope-") as temp:
                base = Path(temp)
                root = base / "managed root with spaces"
                root.mkdir()
                (root / "plain directory").mkdir()
                (root / "plain directory" / "README").write_text("managed\n", encoding="utf-8")
                fake_managed = root / "managed repository"
                fake_managed.mkdir()
                (fake_managed / ".git").write_text("managed by parent\n", encoding="utf-8")
                too_deep = make_fixture(base, Path("a/b/c/d/too-deep"))

                result = run_check(script, root)
                deep_result = run_check(script, too_deep["root"])

                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("CHECKED: 0", result.stdout)
                self.assertIn("ERRORS: 0", result.stdout)
                self.assertEqual(deep_result.returncode, 0, deep_result.stdout + deep_result.stderr)
                self.assertIn("CHECKED: 0", deep_result.stdout)
                self.assertNotIn("NO_UPSTREAM:", deep_result.stdout)

    def test_missing_root_and_empty_arguments_fail(self) -> None:
        for script in self.for_each_runtime():
            with tempfile.TemporaryDirectory(prefix="check-updates-missing-") as temp:
                missing = Path(temp) / "root-does-not-exist"
                result = run_check(script, missing)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("INVALID_ROOT:", result.stdout)

            empty = subprocess.run(
                ["bash", str(script)],
                cwd=PROJECT_ROOT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(empty.returncode, 2)
            self.assertIn("Usage:", empty.stderr)


if __name__ == "__main__":
    unittest.main()
