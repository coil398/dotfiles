import pytest


def _old(n=2):
    from helpers import aged, rec
    from jobs import clock

    return [rec(i, aged(clock.now(), days=60)) for i in range(1, n + 1)]


def test_recovers_after_transient_failures():
    from helpers import FlakyStore
    from jobs.runner import run

    store = FlakyStore(_old(), fail_times=2)
    assert run({"type": "purge_expired", "ttl_days": 30}, store) == {"removed": 2}
    assert len(store.delete_calls) == 3 and store.all() == []


def test_gives_up_after_three_attempts():
    from helpers import FlakyStore
    from jobs.errors import StoreUnavailable
    from jobs.runner import run

    store = FlakyStore(_old(), fail_times=10)
    with pytest.raises(StoreUnavailable):
        run({"type": "purge_expired", "ttl_days": 30}, store)
    assert len(store.delete_calls) == 3


def test_retry_uses_same_ids():
    from helpers import FlakyStore
    from jobs.runner import run

    store = FlakyStore(_old(3), fail_times=1)
    run({"type": "purge_expired", "ttl_days": 30}, store)
    assert store.delete_calls[0] == store.delete_calls[1]
    assert sorted(store.delete_calls[0]) == [1, 2, 3]
