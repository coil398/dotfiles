"""Per-session continuation state with an advisory lock and atomic updates.

Layout under ``state_dir``::

    sessions/<session>.json   {"session_id","turn_id","continuations",
                               "last_fingerprint","last_verdict","updated_at"}
    sessions/<session>.lock   flock target (held for the whole hook run so
                              duplicate/concurrent runs of the same event
                              serialize and see each other's fingerprint)

State is keyed by session; the turn id is stored so the continuation count
resets when a new user turn starts.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

_SAFE = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")
PRUNE_AFTER_S = 7 * 24 * 3600
PRUNE_MAX_ENTRIES = 500


class StateError(Exception):
    pass


class LockBusy(StateError):
    pass


@dataclass
class SessionState:
    session_id: str
    turn_id: str = ""
    continuations: int = 0
    last_fingerprint: str = ""
    last_verdict: str = ""
    updated_at: float = 0.0

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Any, session_id: str) -> "SessionState":
        if not isinstance(data, dict) or data.get("session_id") != session_id:
            return cls(session_id=session_id)
        st = cls(session_id=session_id)
        st.turn_id = str(data.get("turn_id") or "")
        try:
            st.continuations = max(0, int(data.get("continuations") or 0))
        except (TypeError, ValueError):
            st.continuations = 0
        st.last_fingerprint = str(data.get("last_fingerprint") or "")
        st.last_verdict = str(data.get("last_verdict") or "")
        try:
            st.updated_at = float(data.get("updated_at") or 0.0)
        except (TypeError, ValueError):
            st.updated_at = 0.0
        return st


def safe_name(session_id: str) -> str:
    if _SAFE.match(session_id):
        return session_id
    return "h" + hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:32]


def event_fingerprint(turn_id: str, last_assistant_message: Optional[str]) -> str:
    h = hashlib.sha256()
    h.update(turn_id.encode("utf-8"))
    h.update(b"\n")
    h.update((last_assistant_message or "").encode("utf-8"))
    return h.hexdigest()


class StateStore:
    def __init__(self, state_dir: Path) -> None:
        self.dir = state_dir
        self.sessions = state_dir / "sessions"

    def _paths(self, session_id: str) -> "tuple[Path, Path]":
        name = safe_name(session_id)
        return self.sessions / f"{name}.json", self.sessions / f"{name}.lock"

    @contextmanager
    def locked(self, session_id: str, timeout_s: float = 0.5) -> Iterator[SessionState]:
        try:
            self.sessions.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StateError(f"state dir unavailable: {exc.__class__.__name__}") from exc
        json_path, lock_path = self._paths(session_id)
        try:
            lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        except OSError as exc:
            raise StateError(f"lock open failed: {exc.__class__.__name__}") from exc
        deadline = time.monotonic() + timeout_s
        try:
            while True:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise LockBusy("session lock busy")
                    time.sleep(0.02)
            yield self._load(json_path, session_id)
        finally:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(lock_fd)

    def _load(self, json_path: Path, session_id: str) -> SessionState:
        try:
            raw = json_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return SessionState(session_id=session_id)
        except OSError as exc:
            raise StateError(f"state read failed: {exc.__class__.__name__}") from exc
        try:
            data = json.loads(raw)
        except ValueError:
            return SessionState(session_id=session_id)
        return SessionState.from_json(data, session_id)

    def save(self, state: SessionState) -> None:
        json_path, _ = self._paths(state.session_id)
        state.updated_at = time.time()
        tmp = json_path.with_name(json_path.name + f".tmp{os.getpid()}")
        try:
            tmp.write_text(json.dumps(state.to_json(), ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, json_path)
        except OSError as exc:
            try:
                tmp.unlink()
            except OSError:
                pass
            raise StateError(f"state write failed: {exc.__class__.__name__}") from exc

    def prune(self, now: Optional[float] = None) -> int:
        """Remove session files idle for more than a week. Best effort."""
        now = time.time() if now is None else now
        removed = 0
        try:
            entries = list(self.sessions.iterdir())
        except OSError:
            return 0
        if len(entries) > PRUNE_MAX_ENTRIES:
            entries = entries[:PRUNE_MAX_ENTRIES]
        for p in entries:
            try:
                if now - p.stat().st_mtime > PRUNE_AFTER_S:
                    p.unlink()
                    removed += 1
            except OSError:
                continue
        return removed
