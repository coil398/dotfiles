from tests_hidden.helper import *
import pytest


def test_flush_clears_and_closes_with_error_precedence():
    e = TemporalJoin(1)
    e.push(Event("left",1,0,0))
    before = dict(e.stats)
    assert e.push(Flush()) == []
    assert e.closed and e.retained == 0 and e.key_count == 0
    assert dict(e.stats) == before
    for item in (Flush(),None,Event("bad",[],True,0),Watermark("left",0)):
        with pytest.raises(RuntimeError): e.push(item)


def test_iterator_stops_at_flush_without_reading_tail():
    def source():
        yield Event("left",0,0,0)
        yield Event("right",0,0,0)
        yield Flush()
        raise AssertionError("read beyond Flush")
    assert len(list(join(source(),0))) == 1


def test_iterator_no_read_ahead_within_batch():
    trace = []
    def source():
        for item in [Event("left",1,0,0),Event("left",1,0,1),Event("right",1,0,2)]:
            trace.append(item)
            yield item
        raise LookupError("source failure")
    stream = join(source(),0)
    assert trace == []
    assert next(stream).left.value == 0
    assert len(trace) == 3
    assert next(stream).left.value == 1
    assert len(trace) == 3
    with pytest.raises(LookupError, match="source failure"): next(stream)


def test_input_iterated_once_and_empty_exhaustion():
    class Once:
        calls = 0
        def __iter__(self):
            self.calls += 1
            assert self.calls == 1
            yield Event("right",0,2,0)
            yield Event("left",0,2,0)
    source = Once()
    assert len(list(join(source,0))) == 1
    assert source.calls == 1
    assert list(join(iter(()),0)) == []
    assert list(join([Event("left",0,0,0)],1)) == []


def test_independent_engines_and_empty_flush():
    a,b = TemporalJoin(0),TemporalJoin(0)
    a.push(Event("left",1,0,0))
    assert b.push(Event("right",1,0,0)) == []
    assert b.push(Flush()) == []
    assert b.closed and not a.closed
    assert len(a.push(Event("right",1,0,0))) == 1
    assert a.retained == 2
