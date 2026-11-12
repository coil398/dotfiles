import pytest
from sync_replay import (SyncEngine, FakeSource, MemorySink, MemoryCheckpoint,
                         FailingSink, JournalSink, FileCheckpoint)


def ev(i, key="k", rev=1, value=1, op="put"):
    event = dict(id=i, key=key, revision=rev, op=op)
    if op == "put":
        event["value"] = value
    return event


def execute(events, sink=None):
    sink = MemorySink() if sink is None else sink
    count = SyncEngine(FakeSource([(events, None)]), sink, MemoryCheckpoint()).run()
    return count, sink


def test_delete_absent_then_stale_put():
    count, sink = execute([ev("d", rev=5, op="delete"), ev("p", rev=4)])
    assert count == 1
    assert sink.snapshot() == {}
    assert sink.revisions == {"k": 5}


def test_update_delete_recreate_and_delayed_stale():
    count, sink = execute([ev("a", rev=1), ev("d", rev=3, op="delete"),
        ev("old", rev=2), ev("new", rev=4, value=None), ev("late", rev=3)])
    assert count == 3
    assert sink.snapshot() == {"k": None}
    assert sink.revisions == {"k": 4}


def test_delete_then_equal_put():
    count, sink = execute([ev("d", rev=0, op="delete"), ev("p", rev=0)])
    assert count == 1
    assert sink.snapshot() == {}
    assert sink.applied_ids == {"d", "p"}


def test_tombstone_is_per_key_across_pages():
    sink = MemorySink()
    execute([ev("d", "a", 8, op="delete"), ev("p", "b", 0)], sink)
    count, _ = execute([ev("s", "a", 7), ev("q", "b", 1, False)], sink)
    assert count == 1
    assert sink.snapshot() == {"b": False}
    assert sink.revisions == {"a": 8, "b": 1}


def test_durable_tombstone_survives_reopen(tmp_path):
    path = tmp_path / "sub" / "sink.json"
    execute([ev("p"), ev("d", rev=9, op="delete")], JournalSink(path))
    sink = JournalSink(path)
    assert sink.apply(ev("late", rev=8)) is False
    assert sink.snapshot() == {}
    assert sink.revisions == {"k": 9}
    assert sink.apply(ev("recreate", rev=10, value=[])) is True
    assert sink.snapshot() == {"k": []}
