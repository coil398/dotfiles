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


def test_rerun_terminal_deduplicates():
    pages = [([ev("a")], "c"), ([ev("b", "b")], None)]
    sink = MemorySink(); cp = MemoryCheckpoint()
    assert SyncEngine(FakeSource(pages),sink,cp).run() == 2
    assert cp.load() is None
    source = FakeSource(pages)
    assert SyncEngine(source,sink,cp).run() == 0
    assert source.calls == [None, "c"]
    assert cp.history == ["c", None, "c", None]


def test_resume_empty_string_and_terminal_delete():
    pages = [([ev("skipped", "skip")], ""), ([], "later"),
             ([ev("d", rev=3, op="delete")], None)]
    sink = MemorySink(); cp = MemoryCheckpoint("")
    source = FakeSource(pages)
    assert SyncEngine(source,sink,cp).run() == 1
    assert source.calls == ["", "later"]
    assert cp.history == ["later", None]
    assert sink.snapshot() == {}
    assert sink.revisions == {"k": 3}


def test_durable_resume_after_partial_page(tmp_path):
    sp, cp_path = tmp_path / "data", tmp_path / "cursor"
    pages = [([ev("a", "a")], "a"),
             ([ev("b", "b"), ev("c", "c")], "b"), ([], None)]
    sink = JournalSink(sp); cp = FileCheckpoint(cp_path)
    with pytest.raises(OSError):
        SyncEngine(FakeSource(pages),FailingSink(sink,3),cp).run()
    assert FileCheckpoint(cp_path).load() == "a"
    source = FakeSource(pages); reopened = JournalSink(sp)
    assert SyncEngine(source,reopened,FileCheckpoint(cp_path)).run() == 1
    assert source.calls == ["a", "b"]
    assert FileCheckpoint(cp_path).load() is None
    assert reopened.snapshot() == {"a": 1, "b": 1, "c": 1}


def test_terminal_failure_replays_last_page():
    pages = [([ev("a", "a")], "x"),
             ([ev("b", "b"), ev("c", "c")], None)]
    sink = MemorySink(); cp = MemoryCheckpoint()
    with pytest.raises(OSError):
        SyncEngine(FakeSource(pages),FailingSink(sink,3),cp).run()
    assert cp.load() == "x"
    assert SyncEngine(FakeSource(pages),sink,cp).run() == 1
    assert cp.history == ["x", None]
    assert sink.snapshot() == {"a": 1, "b": 1, "c": 1}


def test_fetch_exception_does_not_reset_checkpoint():
    failure = RuntimeError("source unavailable")
    class Source:
        def fetch(self, cursor):
            if cursor == "saved":
                raise failure
            return [ev("a")], "saved"
    cp = MemoryCheckpoint(); sink = MemorySink()
    with pytest.raises(RuntimeError) as caught:
        SyncEngine(Source(),sink,cp).run()
    assert caught.value is failure
    assert cp.load() == "saved" and cp.history == ["saved"]
    source = FakeSource([([], "saved"), ([ev("a"), ev("b", "b")], None)])
    assert SyncEngine(source,sink,cp).run() == 1
    assert cp.load() is None
    assert sink.snapshot() == {"k": 1, "b": 1}
