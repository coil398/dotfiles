#!/usr/bin/env python3
"""Safely synchronize a Git-tracked SQLite memory database."""

import argparse
import contextlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from merge_conflict import merge_databases, validate_database


class SyncError(RuntimeError):
    pass


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SyncError(f"git {' '.join(args)} failed: {detail}")
    return result


def _git_bytes(repo: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise SyncError(
            f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout


def _atomic_copy(source: Path, destination: Path) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as output, source.open("rb") as input_file:
            shutil.copyfileobj(input_file, output)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _sqlite_snapshot(source: Path, destination: Path) -> None:
    validate_database(source)
    with sqlite3.connect(source) as source_conn, sqlite3.connect(destination) as target_conn:
        source_conn.backup(target_conn)
    validate_database(destination)


def _write_revision_db(repo: Path, revision: str, db_relative: str, destination: Path) -> None:
    destination.write_bytes(_git_bytes(repo, "show", f"{revision}:{db_relative}"))
    validate_database(destination)


def _status_entries(repo: Path) -> list[tuple[str, str]]:
    output = _git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout
    entries = []
    for line in output.splitlines():
        if len(line) < 4:
            continue
        entries.append((line[:2], line[3:].strip('"')))
    return entries


def _assert_safe_state(repo: Path, db_relative: str) -> None:
    for operation in ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD"):
        marker = Path(_git(repo, "rev-parse", "--git-path", operation).stdout.strip())
        if not marker.is_absolute():
            marker = repo / marker
        if marker.exists():
            raise SyncError(f"既存のGit操作を検出したため停止しました: {operation}")

    for status, path in _status_entries(repo):
        if path != db_relative:
            raise SyncError(f"memory.db以外の変更があるため停止しました: {status} {path}")
        if status[0] != " " or status[1] not in (" ", "M"):
            raise SyncError(f"memory.dbの未ステージ変更以外は同期できません: {status} {path}")


@contextlib.contextmanager
def _repo_lock(repo: Path):
    git_dir = Path(_git(repo, "rev-parse", "--absolute-git-dir").stdout.strip())
    lock_path = git_dir / "ai-ltm-sync.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise SyncError(f"別のLTM同期処理が実行中です: {lock_path}") from exc
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as lock_file:
            lock_file.write(f"{os.getpid()}\n")
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def _upstream(repo: Path) -> str:
    result = _git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False)
    if result.returncode:
        branch = _git(repo, "branch", "--show-current").stdout.strip()
        if not branch:
            raise SyncError("detached HEADでは同期できません")
        candidate = f"origin/{branch}"
        if _git(repo, "rev-parse", "--verify", candidate, check=False).returncode:
            raise SyncError("upstream branchが設定されていません")
        return candidate
    return result.stdout.strip()


def _is_ancestor(repo: Path, older: str, newer: str) -> bool:
    result = _git(repo, "merge-base", "--is-ancestor", older, newer, check=False)
    if result.returncode not in (0, 1):
        raise SyncError(result.stderr.strip() or "git merge-base failed")
    return result.returncode == 0


def _integrate_remote(
    repo: Path,
    db: Path,
    db_relative: str,
    upstream: str,
    head: str,
    committed_merged: Path,
) -> None:
    if _is_ancestor(repo, upstream, head):
        return

    head_copy = committed_merged.parent / "head-for-checkout.db"
    _write_revision_db(repo, head, db_relative, head_copy)
    _atomic_copy(head_copy, db)

    if _is_ancestor(repo, head, upstream):
        _git(repo, "merge", "--ff-only", upstream)
        return

    merge = _git(repo, "merge", "--no-edit", "--no-commit", upstream, check=False)
    if merge.returncode:
        unmerged = set(filter(None, _git(repo, "diff", "--name-only", "--diff-filter=U").stdout.splitlines()))
        if unmerged != {db_relative}:
            _git(repo, "merge", "--abort", check=False)
            raise SyncError(f"memory.db以外のマージ競合があるため停止しました: {sorted(unmerged)}")
    _atomic_copy(committed_merged, db)
    _git(repo, "add", "--", db_relative)
    remaining = _git(repo, "diff", "--name-only", "--diff-filter=U").stdout.strip()
    if remaining:
        _git(repo, "merge", "--abort", check=False)
        raise SyncError(f"未解消の競合があるため停止しました: {remaining}")
    _git(repo, "commit", "--no-edit")


def _pull_locked(repo: Path, db: Path, db_relative: str) -> None:
    _assert_safe_state(repo, db_relative)
    original_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    original_branch = _git(repo, "branch", "--show-current").stdout.strip()
    if not original_branch:
        raise SyncError("detached HEADでは同期できません")
    with tempfile.TemporaryDirectory(prefix="ai-ltm-sync-") as temporary_dir:
        temporary = Path(temporary_dir)
        original = temporary / "original.db"
        _sqlite_snapshot(db, original)
        try:
            _git(repo, "fetch", "--prune", "origin")
            upstream = _upstream(repo)
            head = original_head
            merge_base = _git(repo, "merge-base", head, upstream).stdout.strip()
            remote_paths = set(
                filter(
                    None,
                    _git(repo, "diff", "--name-only", merge_base, upstream).stdout.splitlines(),
                )
            )
            if not remote_paths.issubset({db_relative}):
                raise SyncError(
                    f"remoteにmemory.db以外の変更があるため停止しました: {sorted(remote_paths)}"
                )

            base = temporary / "base.db"
            head_db = temporary / "head.db"
            remote = temporary / "remote.db"
            committed_merged = temporary / "committed-merged.db"
            working_merged = temporary / "working-merged.db"
            _write_revision_db(repo, merge_base, db_relative, base)
            _write_revision_db(repo, head, db_relative, head_db)
            _write_revision_db(repo, upstream, db_relative, remote)

            merge_databases(base, head_db, remote, committed_merged)
            merge_databases(head_db, original, committed_merged, working_merged)
            _integrate_remote(repo, db, db_relative, upstream, head, committed_merged)
            validate_database(working_merged)
            _atomic_copy(working_merged, db)
            validate_database(db)
        except Exception as exc:
            merge_head = Path(
                _git(repo, "rev-parse", "--git-path", "MERGE_HEAD").stdout.strip()
            )
            if not merge_head.is_absolute():
                merge_head = repo / merge_head
            if merge_head.exists():
                _git(repo, "merge", "--abort", check=False)
            current_head = _git(repo, "rev-parse", "HEAD", check=False).stdout.strip()
            if current_head and current_head != original_head:
                _git(
                    repo,
                    "update-ref",
                    f"refs/heads/{original_branch}",
                    original_head,
                    current_head,
                )
                _git(repo, "read-tree", original_head)
            _atomic_copy(original, db)
            restored_head = _git(repo, "rev-parse", "HEAD", check=False).stdout.strip()
            restored_branch = _git(repo, "branch", "--show-current", check=False).stdout.strip()
            if restored_head != original_head or restored_branch != original_branch:
                raise SyncError("同期失敗後に開始時のGit HEAD/branchを復元できませんでした") from exc
            raise


def _non_fast_forward(result: subprocess.CompletedProcess[str]) -> bool:
    output = f"{result.stdout}\n{result.stderr}".lower()
    return "non-fast-forward" in output or "fetch first" in output or "[rejected]" in output


def _push_with_one_resync(repo: Path, db: Path, db_relative: str) -> None:
    first = _git(repo, "push", "origin", "HEAD", check=False)
    if first.returncode == 0:
        return
    if not _non_fast_forward(first):
        detail = first.stderr.strip() or first.stdout.strip()
        raise SyncError(f"git push origin HEAD failed: {detail}")

    _pull_locked(repo, db, db_relative)
    second = _git(repo, "push", "origin", "HEAD", check=False)
    if second.returncode:
        detail = second.stderr.strip() or second.stdout.strip()
        raise SyncError(f"再同期後のgit pushに失敗しました: {detail}")


def synchronize(command: str, repo: Path, db: Path, message: str | None = None) -> None:
    repo = repo.expanduser().resolve()
    db = db.expanduser().resolve()
    if not (repo / ".git").exists():
        raise SyncError(f"Git repositoryではありません: {repo}")
    if not db.is_file():
        raise SyncError(f"databaseがありません: {db}")
    try:
        db_relative = db.relative_to(repo).as_posix()
    except ValueError as exc:
        raise SyncError("--dbは--repo配下である必要があります") from exc
    _git(repo, "ls-files", "--error-unmatch", "--", db_relative)

    with _repo_lock(repo):
        _pull_locked(repo, db, db_relative)
        if command == "pull":
            return

        _git(repo, "add", "--", db_relative)
        if _git(repo, "diff", "--cached", "--quiet", "--", db_relative, check=False).returncode:
            _git(repo, "commit", "-m", message or "sync: update long-term memory", "--", db_relative)
        _push_with_one_resync(repo, db, db_relative)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("pull", "push"))
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--message")
    args = parser.parse_args()
    try:
        synchronize(args.command, args.repo, args.db, args.message)
    except (SyncError, ValueError, sqlite3.Error, OSError) as exc:
        print(f"ltm-sync: error: {exc}", file=sys.stderr)
        return 1
    print(f"ltm-sync: {args.command} ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
