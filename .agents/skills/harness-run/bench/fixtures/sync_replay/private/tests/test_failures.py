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


def test_partial_write_then_resume():
    events = [ev(str(i), str(i)) for i in range(4)]
    pages = [(events, "done"), ([], None)]
    sink = MemorySink(); cp = MemoryCheckpoint()
    with pytest.raises(OSError):
        SyncEngine(FakeSource(pages), FailingSink(sink, 3), cp).run()
    assert cp.load() is None
    assert cp.history == []
    assert sink.snapshot() == {"0": 1, "1": 1}
    assert SyncEngine(FakeSource(pages), sink, cp).run() == 2
    assert sink.snapshot() == {str(i): 1 for i in range(4)}


def test_failure_on_duplicate_stops_before_ack():
    events = [ev("a"), ev("a"), ev("b", "b")]
    sink = MemorySink(); cp = MemoryCheckpoint(); failing = FailingSink(sink, 2)
    pages = [(events, "next"), ([], None)]
    with pytest.raises(OSError):
        SyncEngine(FakeSource(pages), failing, cp).run()
    assert cp.history == []
    assert failing.calls == 2
    assert SyncEngine(FakeSource(pages), failing, cp).run() == 1
    assert sink.snapshot() == {"k": 1, "b": 1}


def test_second_page_failure_keeps_previous_checkpoint():
    pages = [([ev("a")], "one"), ([ev("b", "b"), ev("c", "c")], "two"),
             ([ev("d", "d")], None)]
    sink = MemorySink(); cp = MemoryCheckpoint(); source = FakeSource(pages)
    with pytest.raises(OSError):
        SyncEngine(source, FailingSink(sink, 3), cp).run()
    assert cp.load() == "one"
    assert cp.history == ["one"]
    assert source.calls == [None, "one"]
    assert SyncEngine(FakeSource(pages), sink, cp).run() == 2
    assert len(sink.snapshot()) == 4


def test_invalid_event_after_valid_prefix_is_atomic():
    bad = ev("bad", rev=True)
    cp = MemoryCheckpoint(); sink = MemorySink()
    with pytest.raises(ValueError):
        SyncEngine(FakeSource([([ev("ok"), bad], "c"), ([], None)]),sink,cp).run()
    assert cp.history == []
    assert sink.applied_ids == {"ok"}
    assert sink.revisions == {"k": 1}


def test_journal_publish_failure_is_atomic(tmp_path, monkeypatch):
    import sync_replay.storage as storage
    sink = JournalSink(tmp_path / "state.json"); cp = MemoryCheckpoint()
    sink.apply(ev("seed", rev=0))
    old_bytes = sink.path.read_bytes()
    def fail(*args):
        raise OSError("replace failed")
    with monkeypatch.context() as patch:
        patch.setattr(storage.os, "replace", fail)
        with pytest.raises(OSError, match="replace failed"):
            SyncEngine(FakeSource([([ev("next", rev=2)], "c"), ([], None)]),sink,cp).run()
    assert cp.history == []
    assert sink.path.read_bytes() == old_bytes
    assert sink.applied_ids == {"seed"}
    assert sink.revisions == {"k": 0}
    assert JournalSink(sink.path).snapshot() == {"k": 1}
