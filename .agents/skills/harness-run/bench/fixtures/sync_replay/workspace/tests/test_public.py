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


def test_one_page():
    count, sink = execute([ev("a")])
    assert count == 1 and sink.get("k") == 1


def test_checkpoint_terminal():
    cp = MemoryCheckpoint()
    SyncEngine(FakeSource([([ev("a")], "x"), ([], None)]),MemorySink(),cp).run()
    assert cp.load() is None


def test_duplicate():
    assert execute([ev("a"), ev("a")])[0] == 1


def test_equal_revision():
    count, sink = execute([ev("a"), ev("b", value=2)])
    assert count == 1 and sink.get("k") == 1


def test_tombstone():
    count, sink = execute([ev("d", rev=4, op="delete"), ev("p", rev=2)])
    assert count == 1 and sink.snapshot() == {}


def test_partial_failure():
    cp = MemoryCheckpoint(); sink = MemorySink()
    with pytest.raises(OSError):
        SyncEngine(FakeSource([([ev("a"),ev("b", "b")], "x"),( [],None)]),
                   FailingSink(sink,2),cp).run()
    assert cp.load() is None and sink.snapshot() == {"k": 1}


def test_empty_page_continues():
    source = FakeSource([([], "x"), ([ev("a")], None)])
    assert SyncEngine(source,MemorySink(),MemoryCheckpoint()).run() == 1


def test_false_value_is_present():
    assert execute([ev("a", value=False)])[1].snapshot() == {"k": False}


def test_durable_reopen(tmp_path):
    path = tmp_path / "state.json"
    execute([ev("a")], JournalSink(path))
    assert JournalSink(path).snapshot() == {"k": 1}


def test_observation_copy():
    sink = MemorySink(); sink.apply(ev("a", value=[1]))
    sink.get("k").append(2)
    assert sink.snapshot() == {"k": [1]}
