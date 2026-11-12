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


def test_empty_chain_and_opaque_cursors():
    source = FakeSource([([], ""), ([], "日本/二"), ([ev("e")], None)])
    assert source.fetch(None) == ([], "")
    assert source.fetch("") == ([], "日本/二")
    assert source.fetch("日本/二") == ([ev("e")], None)
    assert source.calls == [None, "", "日本/二"]


def test_redelivery_is_nonconsuming():
    source = FakeSource([([ev("e")], "a"), ([ev("e"), ev("f")], None)])
    assert source.fetch("a") == source.fetch("a")
    assert source.fetch(None) == ([ev("e")], "a")
    assert source.calls == ["a", "a", None]


def test_payload_after_does_not_route():
    event = ev("a"); event["after"] = "wrong"
    source = FakeSource([([event], "x"), ([ev("b")], None)])
    assert source.fetch(None) == ([event], "x")
    assert source.fetch("x") == ([ev("b")], None)
    with pytest.raises(KeyError):
        source.fetch("wrong")
    assert source.calls[-1] == "wrong"


def test_source_snapshot_and_fetch_copy():
    event = ev("a", value={"items": [1]})
    pages = [([event], None)]
    source = FakeSource(pages)
    event["value"]["items"].append(2)
    first, cursor = source.fetch(None)
    first[0]["value"]["items"].append(3)
    assert source.fetch(None) == ([ev("a", value={"items": [1]})], None)
    assert cursor is None


def test_empty_and_invalid_chains():
    assert FakeSource([]).fetch(None) == ([], None)
    for pages in [[([], "x")], [([], None), ([], None)],
                  [([], "a"), ([], "a"), ([], None)]]:
        with pytest.raises(ValueError):
            FakeSource(pages)
    with pytest.raises(KeyError):
        FakeSource([]).fetch("missing")
