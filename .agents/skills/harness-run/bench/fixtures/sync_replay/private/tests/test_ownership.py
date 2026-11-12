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


def test_nested_put_and_observers_detached():
    sink = MemorySink(); event = ev("a", value={"x": [1]})
    assert sink.apply(event) is True
    event["value"]["x"].append(2)
    for view in [sink.get("k"), sink.snapshot()["k"], sink.values["k"]]:
        view["x"].append(3)
    assert sink.snapshot() == {"k": {"x": [1]}}


def test_metadata_observers_detached():
    sink = MemorySink(); sink.apply(ev("a"))
    sink.applied_ids.clear(); sink.revisions.clear(); sink.values.clear()
    assert sink.applied_ids == {"a"}
    assert sink.revisions == {"k": 1}
    assert sink.snapshot() == {"k": 1}


def test_instances_are_independent(tmp_path):
    a, b = MemorySink(), MemorySink()
    a.apply(ev("a")); assert b.snapshot() == {}
    x, y = MemoryCheckpoint(), MemoryCheckpoint()
    x.save("x"); assert y.load() is None and y.history == []
    ja, jb = JournalSink(tmp_path / "a"), JournalSink(tmp_path / "b")
    ja.apply(ev("a")); assert jb.snapshot() == {}


def test_validation_is_before_id_shortcut():
    from sync_replay import validate_event
    sink = MemorySink(); event = ev("a", value=[{"x": 1}])
    sink.apply(event)
    copied = validate_event(event); copied["value"][0]["x"] = 2
    assert event["value"] == [{"x": 1}]
    for bad in [dict(event, revision=True), dict(event, op="unknown"),
                {"id": "a", "key": "k", "revision": 1, "op": "put"}]:
        with pytest.raises(ValueError):
            sink.apply(bad)
    assert sink.snapshot() == {"k": [{"x": 1}]}


def test_journal_serialization_error_keeps_state(tmp_path):
    sink = JournalSink(tmp_path / "sink.json"); sink.apply(ev("seed"))
    before = sink.path.read_bytes()
    with pytest.raises(TypeError):
        sink.apply(ev("bad", "other", value=object()))
    assert sink.path.read_bytes() == before
    assert sink.snapshot() == {"k": 1}
    assert sink.applied_ids == {"seed"}
