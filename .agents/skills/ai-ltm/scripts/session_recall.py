#!/usr/bin/env python3
"""Run the deterministic, non-blocking session-start ai-ltm recall flow.

The script writes JSON Lines to stdout.  Every object except the final one is
a progress event; the final object has ``type=terminal`` and contains exactly
one value from :data:`TERMINAL_STATUSES`.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from dataclasses import dataclass
import errno
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

try:
    import fcntl
except ImportError:  # pragma: no cover - the supported runtime is POSIX.
    fcntl = None  # type: ignore


TERMINAL_STATUSES = (
    "completed",
    "dirty",
    "setup-needed",
    "pull-failed",
    "search-failed",
    "timed-out",
    "failed",
)
DEFAULT_COMMAND_TIMEOUT = 15.0
DEFAULT_LOCK_TIMEOUT = 0.25
DEFAULT_LOCK_DIRECTORY_PREFIX = "ai-ltm-recall-"
DEFAULT_LOCK_FILENAME_PREFIX = "repo-"
TERM_GRACE_SECONDS = 0.25
KILL_GRACE_SECONDS = 0.25

_TRANSIENT_PULL_MARKERS = (
    "could not resolve host",
    "temporary failure in name resolution",
    "connection timed out",
    "connection reset",
    "connection refused",
    "failed to connect",
    "could not connect",
    "couldn't connect",
    "network is unreachable",
    "temporary failure",
    "remote end hung up",
    "early eof",
    "service unavailable",
    "502 bad gateway",
    "503 service unavailable",
    "504 gateway timeout",
)
_NON_TRANSIENT_PULL_MARKERS = (
    "authentication failed",
    "could not read username",
    "terminal prompts disabled",
    "permission denied",
    "repository not found",
    "could not read from remote repository",
    "access denied",
)


@dataclass
class CommandResult:
    """Captured result of a bounded child process."""

    returncode: Optional[int]
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    termination: Optional[str] = None


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _kill_process_group(process: subprocess.Popen, sig: signal.Signals) -> None:
    """Signal the child process group, falling back to the child itself."""
    if os.name == "posix":
        try:
            os.killpg(process.pid, sig)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    try:
        process.send_signal(sig)
    except (OSError, ProcessLookupError):
        pass


def _update_partial(
    stdout: str, stderr: str, exc: subprocess.TimeoutExpired
) -> Tuple[str, str]:
    """Keep output captured by communicate while a process is being killed."""
    if exc.output is not None:
        stdout = _as_text(exc.output)
    if exc.stderr is not None:
        stderr = _as_text(exc.stderr)
    return stdout, stderr


def run_bounded(
    argv: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: float = DEFAULT_COMMAND_TIMEOUT,
) -> CommandResult:
    """Run argv with DEVNULL stdin and converge TERM -> KILL -> reap.

    ``start_new_session`` gives the child a process group on POSIX, so a
    timeout cannot leave a descendant running after the parent is reaped.
    Every wait after a timeout has its own small bound.
    """
    popen_kwargs: Dict[str, Any] = {
        "cwd": str(cwd) if cwd is not None else None,
        "env": env,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True

    try:
        process = subprocess.Popen(list(argv), **popen_kwargs)
    except OSError as exc:
        return CommandResult(127, stderr=str(exc))

    stdout = ""
    stderr = ""
    try:
        stdout, stderr = process.communicate(timeout=max(0.0, timeout))
        return CommandResult(process.returncode, _as_text(stdout), _as_text(stderr))
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = _update_partial(stdout, stderr, exc)

    _kill_process_group(process, signal.SIGTERM)
    try:
        stdout, stderr = process.communicate(timeout=TERM_GRACE_SECONDS)
        return CommandResult(
            process.returncode,
            _as_text(stdout),
            _as_text(stderr),
            timed_out=True,
            termination="term",
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = _update_partial(stdout, stderr, exc)

    _kill_process_group(process, signal.SIGKILL)
    try:
        stdout, stderr = process.communicate(timeout=KILL_GRACE_SECONDS)
        return CommandResult(
            process.returncode,
            _as_text(stdout),
            _as_text(stderr),
            timed_out=True,
            termination="kill",
        )
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = _update_partial(stdout, stderr, exc)

    # A process that still owns a pipe can make communicate wait forever.
    # Kill the parent once more, close the pipes, and use a bounded wait to
    # reap it.  The process-group KILL above handles normal POSIX descendants.
    _kill_process_group(process, signal.SIGKILL)
    try:
        process.kill()
    except (OSError, ProcessLookupError):
        pass
    try:
        process.wait(timeout=KILL_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        pass
    for stream in (process.stdout, process.stderr):
        if stream is not None:
            try:
                stream.close()
            except OSError:
                pass
    return CommandResult(
        process.returncode,
        stdout,
        stderr,
        timed_out=True,
        termination="kill",
    )


def build_git_env(base_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Return an environment that cannot request credentials interactively."""
    result = dict(os.environ if base_env is None else base_env)
    result.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "/usr/bin/false",
            "SSH_ASKPASS": "/usr/bin/false",
            "GIT_SSH_COMMAND": "ssh -o BatchMode=yes -o ConnectTimeout=10",
        }
    )
    return result


def _git_config_argv() -> List[str]:
    return [
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "rebase.autoStash=false",
        "-c",
        "protocol.ext.allow=never",
        "-c",
        "credential.interactive=false",
        "-c",
        "credential.helper=",
        "-c",
        "core.askPass=false",
    ]


def build_git_status_argv(git_executable: str = "git") -> List[str]:
    return [
        git_executable,
        *_git_config_argv(),
        "status",
        "--porcelain",
        "--untracked-files=all",
    ]


def build_git_pull_argv(git_executable: str = "git") -> List[str]:
    return [
        git_executable,
        *_git_config_argv(),
        "pull",
        "--rebase",
        "--quiet",
    ]


def is_transient_pull_failure(result: CommandResult) -> bool:
    """Classify only known network/service failures as retryable."""
    if result.timed_out or result.returncode not in (1, 128):
        return False
    text = (result.stdout + "\n" + result.stderr).lower()
    if any(marker in text for marker in _NON_TRANSIENT_PULL_MARKERS):
        return False
    return any(marker in text for marker in _TRANSIENT_PULL_MARKERS)


class AdvisoryFileLock:
    """Small bounded advisory lock for cooperating ai-ltm processes."""

    def __init__(
        self,
        path: Path,
        timeout: float = DEFAULT_LOCK_TIMEOUT,
        private_directory: Optional[Path] = None,
    ) -> None:
        self.path = path
        self.timeout = max(0.0, timeout)
        self.private_directory = private_directory
        self._handle: Optional[Any] = None
        self.acquired = False

    def _open_secure(self) -> bool:
        """Open an existing/new lock without following an unsafe final path."""
        try:
            existing = os.lstat(os.fspath(self.path))
        except FileNotFoundError:
            existing = None
        except OSError:
            return False
        if existing is not None and stat.S_ISLNK(existing.st_mode):
            return False

        flags = os.O_RDWR | os.O_CREAT
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        if nofollow:
            flags |= nofollow
        try:
            fd = os.open(os.fspath(self.path), flags, 0o600)
        except OSError:
            return False

        keep_fd = True
        try:
            metadata = os.fstat(fd)
            uid = _current_user_id()
            mode = stat.S_IMODE(metadata.st_mode)
            if (
                uid is None
                or metadata.st_uid != uid
                or not stat.S_ISREG(metadata.st_mode)
                or mode & ~0o600
            ):
                return False
            self._handle = os.fdopen(fd, "a+")
            keep_fd = False
            return True
        except (OSError, ValueError, AttributeError):
            return False
        finally:
            if keep_fd:
                try:
                    os.close(fd)
                except OSError:
                    pass

    def acquire(self) -> Tuple[bool, Optional[str]]:
        if fcntl is None:
            return False, "lock-unavailable"
        if self.private_directory is not None:
            try:
                _ensure_private_directory(self.private_directory)
            except OSError:
                return False, "lock-unavailable"
        if not self._open_secure():
            return False, "lock-unavailable"

        deadline = time.monotonic() + self.timeout
        while True:
            try:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.acquired = True
                return True, None
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    self.release()
                    return False, "lock-unavailable"
                if time.monotonic() >= deadline:
                    self.release()
                    return False, "busy"
                time.sleep(min(0.02, max(0.0, deadline - time.monotonic())))

    def release(self) -> None:
        if self._handle is None:
            return
        try:
            if self.acquired and fcntl is not None:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            self._handle.close()
        except OSError:
            pass
        self._handle = None
        self.acquired = False


def _current_user_id() -> Optional[int]:
    getuid = getattr(os, "getuid", None)
    if getuid is None:
        return None
    return int(getuid())


def _canonical_temp_base() -> Path:
    """Resolve the platform temp base before adding any lock-specific path."""
    return Path(tempfile.gettempdir()).expanduser().resolve()


def _default_lock_directory() -> Path:
    uid = _current_user_id()
    if uid is None:
        raise OSError(errno.ENOSYS, "current user id is unavailable")
    return _canonical_temp_base() / "{}{}".format(DEFAULT_LOCK_DIRECTORY_PREFIX, uid)


def _ensure_private_directory(path: Path) -> None:
    """Create or validate the current user's private lock directory."""
    uid = _current_user_id()
    if uid is None:
        raise OSError(errno.ENOSYS, "current user id is unavailable")
    try:
        metadata = os.lstat(os.fspath(path))
    except FileNotFoundError:
        try:
            os.mkdir(os.fspath(path), 0o700)
        except FileExistsError:
            pass
        metadata = os.lstat(os.fspath(path))

    mode = stat.S_IMODE(metadata.st_mode)
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != uid
        or mode != 0o700
    ):
        raise OSError(errno.EPERM, "unsafe private lock directory")


def _default_lock_path(repo: Path) -> Path:
    """Return a stable per-user temp lock path outside the repository."""
    canonical_repo = repo.expanduser().resolve()
    repo_hash = hashlib.sha256(os.fsencode(str(canonical_repo))).hexdigest()
    return _default_lock_directory() / "{}{}.lock".format(
        DEFAULT_LOCK_FILENAME_PREFIX, repo_hash
    )


def _error_detail(
    result: CommandResult,
    stage: str = "child",
    reason: str = "child-failed",
) -> Dict[str, Any]:
    """Return failure metadata without exposing child output.

    Child stdout and stderr are intentionally available only to internal
    classification/parsing code.  Emitted diagnostics are limited to fixed
    categories and bounded process metadata.
    """
    detail: Dict[str, Any] = {
        "stage": stage,
        "reason": reason,
        "exit": result.returncode,
    }
    if result.timed_out:
        detail["timeout"] = True
        detail["termination"] = (
            result.termination if result.termination in ("term", "kill") else "none"
        )
    return detail


def _decode_base64_utf8(value: str, option: str) -> str:
    """Decode one strict standard-base64 UTF-8 command-line value."""
    try:
        encoded = value.encode("ascii")
        decoded = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, ValueError, binascii.Error) as exc:
        raise ValueError("{} must be strict base64".format(option)) from exc
    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("{} must decode as UTF-8".format(option)) from exc


def _result_ids(stdout: str) -> List[int]:
    value = json.loads(stdout)
    if not isinstance(value, list):
        raise ValueError("combined search output must be a JSON list")
    ids: List[int] = []
    for item in value:
        if not isinstance(item, dict) or isinstance(item.get("id"), bool):
            raise ValueError("combined search result must contain numeric IDs")
        episode_id = item.get("id")
        if not isinstance(episode_id, int):
            raise ValueError("combined search result must contain numeric IDs")
        ids.append(episode_id)
    return ids


def emit_event(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), flush=True)


class RecallRunner:
    """Execute one preflight/pull/search/report sequence."""

    def __init__(
        self,
        *,
        repo: Path,
        db: Path,
        query: str,
        summary: str = "",
        limit: int = 5,
        vector_search: Path,
        git_executable: str = "git",
        lock_path: Optional[Path] = None,
        timeout: float = DEFAULT_COMMAND_TIMEOUT,
        pull_timeout: Optional[float] = None,
        search_timeout: Optional[float] = None,
        lock_timeout: float = DEFAULT_LOCK_TIMEOUT,
        emit: Callable[[Dict[str, Any]], None] = emit_event,
    ) -> None:
        self.repo = repo
        self.db = db
        self.query = query
        self.summary = summary
        self.limit = limit
        self.vector_search = vector_search
        self.git_executable = git_executable
        self.lock_path = lock_path if lock_path is not None else _default_lock_path(repo)
        self.private_lock_directory = (
            None if lock_path is not None else self.lock_path.parent
        )
        self.timeout = timeout
        self.pull_timeout = pull_timeout if pull_timeout is not None else timeout
        self.search_timeout = search_timeout if search_timeout is not None else timeout
        self.lock_timeout = lock_timeout
        self.emit = emit
        self.state: Dict[str, Any] = {
            "query": query,
            "summary": summary,
            "repo": str(repo),
            "db": str(db),
            "preflight_status": "not-run",
            "pull_status": "not-run",
            "search_status": "not-run",
            "pull_exit": None,
            "search_exit": None,
            "retry_count": 0,
            "result_ids": [],
            "details": {},
        }

    def _progress(self, stage: str, event: str, **fields: Any) -> None:
        payload: Dict[str, Any] = {
            "type": "progress",
            "stage": stage,
            "event": event,
        }
        payload.update(fields)
        self.emit(payload)

    def _progress_detail(
        self, stage: str, event: str, detail: Dict[str, Any]
    ) -> None:
        fields = {key: value for key, value in detail.items() if key != "stage"}
        self._progress(stage, event, **fields)

    def _finish(self, status: str, detail: Optional[Dict[str, Any]] = None) -> int:
        if status not in TERMINAL_STATUSES:
            detail = {"stage": "runner", "reason": "invalid-status"}
            status = "failed"
        self._progress("report", "started")
        terminal: Dict[str, Any] = {
            "type": "terminal",
            "stage": "report",
            "event": "terminal",
            "terminal_status": status,
            "status": status,
            "preflight_status": self.state["preflight_status"],
            "pull_status": self.state["pull_status"],
            "search_status": self.state["search_status"],
            "pull_exit": self.state["pull_exit"],
            "search_exit": self.state["search_exit"],
            "retry_count": self.state["retry_count"],
            "result_ids": self.state["result_ids"],
            "query": self.query,
            "summary": self.summary,
        }
        if detail:
            terminal["detail"] = detail
        self.emit(terminal)
        if status == "timed-out":
            return 124
        if status == "pull-failed":
            exit_code = self.state["pull_exit"]
            return exit_code if isinstance(exit_code, int) and 1 <= exit_code <= 255 else 1
        if status == "search-failed":
            exit_code = self.state["search_exit"]
            return exit_code if isinstance(exit_code, int) and 1 <= exit_code <= 255 else 1
        if status == "setup-needed" and self.state["search_status"] != "completed":
            return 1
        if status == "failed":
            return 1
        return 0

    def _skip_remaining(self, reason: str) -> None:
        self._progress("pull", "skipped", reason=reason)
        self._progress("search", "skipped", reason=reason)

    def _preflight(self) -> str:
        if not self.repo.is_dir() or not (self.repo / ".git").exists():
            self.state["preflight_status"] = "setup-needed"
            self._progress(
                "preflight",
                "completed",
                status="setup-needed",
                reason="repository missing",
            )
            return "setup-needed"

        result = run_bounded(
            build_git_status_argv(self.git_executable),
            cwd=self.repo,
            env=build_git_env(),
            timeout=self.timeout,
        )
        if result.timed_out:
            self.state["preflight_status"] = "timed-out"
            detail = _error_detail(result, "preflight", "child-timeout")
            self.state["details"]["preflight"] = detail
            self._progress_detail("preflight", "interrupted", detail)
            return "timed-out"
        if result.returncode != 0:
            self.state["preflight_status"] = "failed"
            detail = _error_detail(result, "preflight")
            self.state["details"]["preflight"] = detail
            self._progress_detail("preflight", "failed", detail)
            return "failed"

        if result.stdout.strip():
            self.state["preflight_status"] = "dirty"
            self._progress("preflight", "completed", status="dirty")
            return "dirty"
        self.state["preflight_status"] = "clean"
        self._progress("preflight", "completed", status="clean")
        return "clean"

    def _pull(self, preflight_status: str) -> str:
        self._progress("pull", "started")
        if preflight_status == "setup-needed":
            self.state["pull_status"] = "skipped"
            self._progress("pull", "skipped", reason="repository missing")
            return "skipped"
        if preflight_status == "dirty":
            self.state["pull_status"] = "skipped"
            self._progress("pull", "skipped", reason="dirty repository")
            return "skipped"

        for attempt in range(2):
            result = run_bounded(
                build_git_pull_argv(self.git_executable),
                cwd=self.repo,
                env=build_git_env(),
                timeout=self.pull_timeout,
            )
            self.state["pull_exit"] = result.returncode
            if result.timed_out:
                self.state["pull_status"] = "timed-out"
                detail = _error_detail(result, "pull", "child-timeout")
                self.state["details"]["pull"] = detail
                self._progress_detail("pull", "interrupted", detail)
                return "timed-out"
            if result.returncode == 0:
                self.state["pull_status"] = "completed"
                self._progress(
                    "pull", "completed", exit=result.returncode, retry_count=attempt
                )
                return "completed"
            if attempt == 0 and is_transient_pull_failure(result):
                self.state["retry_count"] = 1
                self._progress(
                    "pull",
                    "retrying",
                    exit=result.returncode,
                    reason="classified transient failure",
                )
                continue
            self.state["pull_status"] = "failed"
            detail = _error_detail(result, "pull")
            self.state["details"]["pull"] = detail
            self._progress_detail("pull", "failed", detail)
            return "failed"
        return "failed"  # pragma: no cover - the loop always returns.

    def _search(self) -> str:
        self._progress("search", "started")
        if not self.db.is_file():
            self.state["search_status"] = "missing-database"
            self.state["search_exit"] = 1
            detail = {"stage": "search", "reason": "database-missing", "exit": 1}
            self.state["details"]["search"] = detail
            self._progress_detail("search", "failed", detail)
            return "failed"

        # Popen receives an argv list directly; the decoded query never becomes
        # shell command text.
        argv = [
            sys.executable,
            str(self.vector_search),
            "combined",
            "--db",
            str(self.db),
            "--query",
            self.query,
            "--limit",
            str(self.limit),
        ]
        result = run_bounded(
            argv,
            cwd=self.repo if self.repo.is_dir() else None,
            env=dict(os.environ),
            timeout=self.search_timeout,
        )
        self.state["search_exit"] = result.returncode
        if result.timed_out:
            self.state["search_status"] = "timed-out"
            detail = _error_detail(result, "search", "child-timeout")
            self.state["details"]["search"] = detail
            self._progress_detail("search", "interrupted", detail)
            return "timed-out"
        if result.returncode != 0:
            self.state["search_status"] = "failed"
            detail = _error_detail(result, "search")
            self.state["details"]["search"] = detail
            self._progress_detail("search", "failed", detail)
            return "failed"
        try:
            ids = _result_ids(result.stdout)
        except (TypeError, ValueError, json.JSONDecodeError):
            self.state["search_status"] = "failed"
            detail = {
                "stage": "search",
                "reason": "invalid-output",
                "exit": result.returncode,
            }
            self.state["details"]["search"] = detail
            self._progress_detail("search", "failed", detail)
            return "failed"
        self.state["result_ids"] = ids
        self.state["search_status"] = "completed"
        self._progress("search", "completed", exit=0, result_ids=ids)
        return "completed"

    def run(self) -> int:
        self._progress("preflight", "started")
        lock = AdvisoryFileLock(
            self.lock_path,
            self.lock_timeout,
            private_directory=self.private_lock_directory,
        )
        acquired, lock_error = lock.acquire()
        if not acquired:
            self.state["preflight_status"] = "failed"
            self.state["details"]["preflight"] = {
                "stage": "preflight",
                "reason": lock_error or "busy",
                "timeout": (lock_error or "busy") == "busy",
                "termination": "none",
            }
            self._progress_detail(
                "preflight", "failed", self.state["details"]["preflight"]
            )
            self._skip_remaining("advisory lock unavailable")
            return self._finish("timed-out", self.state["details"]["preflight"])

        try:
            preflight_status = self._preflight()
            if preflight_status in ("failed", "timed-out"):
                self._skip_remaining("preflight failed")
                return self._finish(
                    "timed-out" if preflight_status == "timed-out" else "failed",
                    self.state["details"].get("preflight"),
                )

            pull_status = self._pull(preflight_status)
            if pull_status == "timed-out":
                self._progress("search", "skipped", reason="pull timed out")
                return self._finish("timed-out", self.state["details"].get("pull"))

            search_status = self._search()
            if search_status == "timed-out":
                return self._finish("timed-out", self.state["details"].get("search"))
            if search_status != "completed":
                # A missing repository is still setup-needed, but the search
                # failure remains explicit in search_status/detail and the
                # process exits nonzero.
                if preflight_status != "setup-needed":
                    return self._finish(
                        "search-failed", self.state["details"].get("search")
                    )
                return self._finish("setup-needed", self.state["details"].get("search"))
            if pull_status == "failed":
                return self._finish("pull-failed", self.state["details"].get("pull"))
            if preflight_status == "setup-needed":
                return self._finish("setup-needed")
            if preflight_status == "dirty":
                return self._finish("dirty")
            return self._finish("completed")
        except Exception:  # Keep a deterministic terminal record.
            self.state["details"]["runner"] = {
                "stage": "runner",
                "reason": "internal-error",
            }
            return self._finish("failed", self.state["details"]["runner"])
        finally:
            lock.release()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="deterministic ai-ltm session recall")
    parser.add_argument("--repo", default="~/ai-ltm-data", help="ai-ltm git repository")
    parser.add_argument("--db", help="memory.db path (defaults to REPO/memory.db)")
    query_group = parser.add_mutually_exclusive_group(required=True)
    query_group.add_argument(
        "--query", help="explicit current-task search query for direct API/test use"
    )
    query_group.add_argument(
        "--query-b64", help="strict standard-base64 UTF-8 current-task search query"
    )
    summary_group = parser.add_mutually_exclusive_group()
    summary_group.add_argument(
        "--summary", help="explicit current-task summary for direct API/test use"
    )
    summary_group.add_argument(
        "--summary-b64", help="strict standard-base64 UTF-8 current-task summary"
    )
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--vector-search",
        help="vector_search.py path (defaults to this script's sibling)",
    )
    parser.add_argument("--git", dest="git_executable", default="git")
    parser.add_argument("--lock-path", help="advisory lock path")
    parser.add_argument("--timeout", type=float, default=DEFAULT_COMMAND_TIMEOUT)
    parser.add_argument("--pull-timeout", type=float)
    parser.add_argument("--search-timeout", type=float)
    parser.add_argument("--lock-timeout", type=float, default=DEFAULT_LOCK_TIMEOUT)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit must be positive")
    try:
        query = (
            args.query
            if args.query is not None
            else _decode_base64_utf8(args.query_b64, "--query-b64")
        )
        summary = (
            args.summary
            if args.summary is not None
            else (
                _decode_base64_utf8(args.summary_b64, "--summary-b64")
                if args.summary_b64 is not None
                else ""
            )
        )
    except ValueError as exc:
        parser.error(str(exc))
    repo = Path(args.repo).expanduser()
    db = Path(args.db).expanduser() if args.db else repo / "memory.db"
    vector_search = (
        Path(args.vector_search).expanduser()
        if args.vector_search
        else Path(__file__).resolve().with_name("vector_search.py")
    )
    lock_path = Path(args.lock_path).expanduser() if args.lock_path else None
    runner = RecallRunner(
        repo=repo,
        db=db,
        query=query,
        summary=summary,
        limit=args.limit,
        vector_search=vector_search,
        git_executable=args.git_executable,
        lock_path=lock_path,
        timeout=max(0.0, args.timeout),
        pull_timeout=(
            max(0.0, args.pull_timeout) if args.pull_timeout is not None else None
        ),
        search_timeout=(
            max(0.0, args.search_timeout) if args.search_timeout is not None else None
        ),
        lock_timeout=max(0.0, args.lock_timeout),
    )
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
