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


def test_equal_put_is_first_writer():
    count, sink = execute([ev("a", rev=0, value="first"),
                           ev("b", rev=0, value="second")])
    assert count == 1
    assert sink.get("k") == "first"
    assert sink.applied_ids == {"a", "b"}


def test_equal_delete_cannot_override_put():
    count, sink = execute([ev("p", rev=7), ev("d", rev=7, op="delete")])
    assert count == 1
    assert sink.snapshot() == {"k": 1}
    assert sink.revisions == {"k": 7}


def test_interleaved_keys_and_nonmonotonic_order():
    events = [ev("a", "", 10, "first"), ev("b", "x", 0, None),
              ev("c", "", 10, "tie"), ev("d", "x", 0, False),
              ev("e", "", 2, "stale")]
    count, sink = execute(events)
    assert count == 2
    assert sink.snapshot() == {"": "first", "x": None}
    assert sink.revisions == {"": 10, "x": 0}


def test_same_visible_value_new_revision_counts():
    count, sink = execute([ev("a", rev=1), ev("b", rev=2), ev("c", rev=2)])
    assert count == 2
    assert sink.revisions == {"k": 2}


def test_equal_revision_across_engine_instances():
    sink = MemorySink()
    assert execute([ev("a", rev=6, value=[1])], sink)[0] == 1
    assert execute([ev("b", rev=6, value=[2]), ev("c", rev=4)], sink)[0] == 0
    assert sink.snapshot() == {"k": [1]}
