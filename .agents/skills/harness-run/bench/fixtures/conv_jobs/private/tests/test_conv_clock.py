import ast
from datetime import datetime, timedelta
from pathlib import Path

JOBS = Path(__file__).resolve().parent.parent / "jobs"
NOW = datetime(2030, 6, 1, 12, 0, 0)
FORBIDDEN = {("datetime", "now"), ("datetime", "utcnow"), ("datetime", "today"), ("time", "time")}


def _run(monkeypatch, records, ttl=30, now=NOW):
    from jobs import clock
    from jobs.runner import run
    from jobs.store import MemoryStore

    monkeypatch.setattr(clock, "_override", now)
    store = MemoryStore(records)
    result = run({"type": "purge_expired", "ttl_days": ttl}, store)
    return result, sorted(r["id"] for r in store.all())


def test_boundary_follows_clock(monkeypatch):
    from helpers import rec

    records = [rec(1, NOW - timedelta(days=30, seconds=1)), rec(2, NOW - timedelta(days=30)),
               rec(3, NOW - timedelta(days=7))]
    assert _run(monkeypatch, records) == ({"removed": 1}, [2, 3])


def test_far_past_clock_expires_nothing(monkeypatch):
    from helpers import rec

    now = datetime(2000, 1, 1)
    records = [rec(1, datetime(1999, 12, 31)), rec(2, datetime(1999, 12, 20))]
    assert _run(monkeypatch, records, now=now) == ({"removed": 0}, [1, 2])


def test_no_direct_time_calls_added():
    count = 0
    for path in JOBS.rglob("*.py"):
        if path.name == "clock.py":
            continue
        for n in ast.walk(ast.parse(path.read_text())):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                owner = n.func.value
                owner = getattr(owner, "id", getattr(owner, "attr", ""))
                if (owner, n.func.attr) in FORBIDDEN:
                    count += 1
    assert count <= 1  # legacy.py has one pre-existing utcnow call
