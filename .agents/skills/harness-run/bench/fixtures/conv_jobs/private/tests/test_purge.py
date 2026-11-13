import pytest


def test_removes_only_expired():
    from helpers import aged, rec
    from jobs import clock
    from jobs.runner import run
    from jobs.store import MemoryStore

    now = clock.now()
    store = MemoryStore([rec(1, aged(now, days=5)), rec(2, aged(now, days=29)),
                         rec(3, aged(now, days=31)), rec(4, aged(now, days=90))])
    assert run({"type": "purge_expired", "ttl_days": 30}, store) == {"removed": 2}
    assert sorted(r["id"] for r in store.all()) == [1, 2]


def test_nothing_expired_does_not_call_delete():
    from helpers import FlakyStore, aged, rec
    from jobs import clock
    from jobs.runner import run

    store = FlakyStore([rec(1, aged(clock.now(), days=2))], fail_times=0)
    assert run({"type": "purge_expired", "ttl_days": 30}, store) == {"removed": 0}
    assert store.delete_calls == []
    assert run({"type": "purge_expired", "ttl_days": 30}, FlakyStore([], 0)) == {"removed": 0}


def test_invalid_ttl_fails():
    from helpers import rec
    from jobs import clock
    from jobs.runner import run
    from jobs.store import MemoryStore

    store = MemoryStore([rec(1, clock.now())])
    for bad in (0, -5, "30", 1.5, True, None):
        with pytest.raises(Exception):
            run({"type": "purge_expired", "ttl_days": bad}, store)
    with pytest.raises(Exception):
        run({"type": "purge_expired"}, store)
    assert len(store.all()) == 1
