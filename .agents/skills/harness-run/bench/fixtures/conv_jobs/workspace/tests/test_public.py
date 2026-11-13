from datetime import datetime, timedelta

import pytest

from jobs import clock, metrics, retry
from jobs.errors import StoreUnavailable
from jobs.runner import run
from jobs.store import MemoryStore


def test_report():
    store = MemoryStore([{"id": 1, "kind": "a", "created_at": datetime(2024, 1, 1)}])
    assert run({"type": "report"}, store) == {"records": 1}


def test_unknown_type():
    with pytest.raises(ValueError):
        run({"type": "nope"}, MemoryStore())


def test_clock_returns_datetime():
    assert isinstance(clock.now(), datetime)


def test_metrics():
    metrics.reset()
    metrics.incr("x.y", 2)
    assert metrics.get("x.y") == 2


def test_retry_gives_up(monkeypatch):
    monkeypatch.setattr(retry, "_sleep", lambda s: None)
    calls = []

    @retry.retry(attempts=2)
    def f():
        calls.append(1)
        raise StoreUnavailable()

    with pytest.raises(StoreUnavailable):
        f()
    assert len(calls) == 2


def test_purge_expired_example():
    old = clock.now() - timedelta(days=90)
    store = MemoryStore([{"id": 1, "kind": "a", "created_at": old}])
    assert run({"type": "purge_expired", "ttl_days": 30}, store) == {"removed": 1}
