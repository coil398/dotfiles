import pytest


def _store(n_old, n_new=1):
    from helpers import aged, rec
    from jobs import clock
    from jobs.store import MemoryStore

    now = clock.now()
    return MemoryStore([rec(i, aged(now, days=60)) for i in range(n_old)]
                       + [rec(100 + i, aged(now, days=1)) for i in range(n_new)])


def test_runs_and_items_counted():
    from jobs import metrics
    from jobs.runner import run

    run({"type": "purge_expired", "ttl_days": 30}, _store(2))
    assert metrics.get("jobs.purge_expired.runs") == 1
    assert metrics.get("jobs.purge_expired.items") == 2


def test_zero_items_still_counts_run():
    from jobs import metrics
    from jobs.runner import run

    run({"type": "purge_expired", "ttl_days": 30}, _store(0))
    assert metrics.get("jobs.purge_expired.runs") == 1
    assert metrics.get("jobs.purge_expired.items") == 0
    assert metrics.get("jobs.purge_expired.failures") == 0


def test_failure_counted_once():
    from jobs import metrics
    from jobs.runner import run

    with pytest.raises(Exception):
        run({"type": "purge_expired", "ttl_days": 0}, _store(1))
    assert metrics.get("jobs.purge_expired.runs") == 1
    assert metrics.get("jobs.purge_expired.failures") == 1
