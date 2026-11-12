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


def test_save_observes_fully_applied_page():
    sink = MemorySink()
    class Checkpoint(MemoryCheckpoint):
        def save(self, cursor):
            assert sink.snapshot() == {"a": 1, "b": 1}
            super().save(cursor)
    cp = Checkpoint()
    SyncEngine(FakeSource([([ev("a", "a"), ev("b", "b")], None)]),sink,cp).run()
    assert cp.history == [None]


def test_empty_pages_ack_exactly_once():
    cp = MemoryCheckpoint(); source = FakeSource([([], ""), ([], "x"), ([], None)])
    assert SyncEngine(source, MemorySink(), cp).run() == 0
    assert cp.history == ["", "x", None]
    assert source.calls == [None, "", "x"]


def test_save_failure_replays_without_rollback():
    class Checkpoint(MemoryCheckpoint):
        def save(self, cursor):
            raise OSError("checkpoint offline")
    sink = MemorySink(); cp = Checkpoint(); source = FakeSource([([ev("a")], None)])
    with pytest.raises(OSError, match="checkpoint offline"):
        SyncEngine(source,sink,cp).run()
    assert sink.snapshot() == {"k": 1}
    assert cp.load() is None
    assert execute([ev("a")], sink)[0] == 0


def test_mixed_page_ack_trace():
    cp = MemoryCheckpoint(); sink = MemorySink()
    pages = [([ev("a")], "a"), ([], "b"),
             ([ev("a"), ev("b", rev=0)], "c"), ([ev("c", "c")], None)]
    assert SyncEngine(FakeSource(pages),sink,cp,page_size=1).run() == 2
    assert cp.history == ["a", "b", "c", None]
    assert sink.snapshot() == {"k": 1, "c": 1}


def test_file_checkpoint_failed_replace_preserves_cursor(tmp_path, monkeypatch):
    import sync_replay.storage as storage
    path = tmp_path / "checkpoint.json"
    cp = FileCheckpoint(path); cp.save("start")
    source = FakeSource([([], "start"), ([ev("a")], None)])
    sink = MemorySink()
    def fail(*args):
        raise OSError("save failed")
    with monkeypatch.context() as patch:
        patch.setattr(storage.os, "replace", fail)
        with pytest.raises(OSError):
            SyncEngine(source,sink,cp).run()
    assert FileCheckpoint(path).load() == "start"
    assert sink.snapshot() == {"k": 1}
    assert source.calls == ["start"]
