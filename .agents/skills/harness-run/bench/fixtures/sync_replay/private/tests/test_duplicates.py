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


def test_id_shared_across_keys():
    count, sink = execute([ev("id", "a"), ev("id", "b", 99)])
    assert count == 1
    assert sink.snapshot() == {"a": 1}
    assert sink.revisions == {"a": 1}


def test_changed_payload_redelivery_across_pages():
    sink = MemorySink(); cp = MemoryCheckpoint()
    source = FakeSource([([ev("id", rev=1)], "c"),
                         ([ev("id", rev=8, value="different")], None)])
    assert SyncEngine(source, sink, cp).run() == 1
    assert sink.snapshot() == {"k": 1}
    assert sink.revisions == {"k": 1}


def test_stale_id_is_consumed_globally():
    count, sink = execute([ev("new", rev=10), ev("old", rev=2),
                           ev("old", "other", 20)])
    assert count == 1
    assert sink.applied_ids == {"new", "old"}
    assert sink.snapshot() == {"k": 1}


def test_duplicate_delete_cannot_delete_newer_recreation():
    count, sink = execute([ev("d", rev=1, op="delete"), ev("p", rev=3),
                           ev("d", rev=9, op="delete")])
    assert count == 2
    assert sink.snapshot() == {"k": 1}
    assert sink.revisions == {"k": 3}


def test_stale_id_survives_journal_reconstruction(tmp_path):
    path = tmp_path / "state.json"
    execute([ev("new", rev=5), ev("stale", rev=1)], JournalSink(path))
    sink = JournalSink(path)
    assert sink.apply(ev("stale", "other", 9)) is False
    assert sink.snapshot() == {"k": 1}
    assert sink.applied_ids == {"new", "stale"}
