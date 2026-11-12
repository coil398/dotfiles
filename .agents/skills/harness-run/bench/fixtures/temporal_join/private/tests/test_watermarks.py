from tests_hidden.helper import *
import pytest


def test_one_sided_eviction_is_immediate():
    e = TemporalJoin(2,1)
    for t in (0,6,7,8): e.push(Event("left",str(t),t,t))
    assert e.push(Watermark("right",10)) == []
    assert (e.retained,e.key_count) == (2,2)
    assert e.stats["evicted"] == 2


def test_opposite_frontiers_are_independent():
    e = TemporalJoin(2)
    for s in ("left","right"):
        for t in (0,8,10): e.push(Event(s,t,t,None))
    e.push(Watermark("left",3))
    e.push(Watermark("right",12))
    assert (e.retained,e.key_count) == (3,3)
    assert e.stats["evicted"] == 3


def test_retention_boundary_can_still_match():
    e = TemporalJoin(3,2)
    a = Event("left","a",5,0)
    e.push(a)
    e.push(Watermark("right",10))
    assert e.retained == 1
    b = Event("right","a",8,0)
    assert e.push(b) == [Match(a,b,8)]
    e.push(Watermark("right",11))
    assert e.retained == 1


def test_decrease_is_atomic_but_equal_is_valid():
    e = TemporalJoin(1)
    e.push(Event("left","a",8,0))
    e.push(Watermark("right",9))
    before = (e.retained,e.key_count,dict(e.stats),dict(e.watermarks))
    with pytest.raises(ValueError): e.push(Watermark("right",8))
    assert (e.retained,e.key_count,dict(e.stats),dict(e.watermarks)) == before
    assert e.push(Watermark("right",9)) == []
    assert e.retained == 1


def test_immediate_discard_does_not_suppress_known_match():
    e = TemporalJoin(2)
    b = Event("right",1,0,0)
    e.push(b)
    e.push(Watermark("right",100))
    a = Event("left",1,1,0)
    assert e.push(a) == [Match(a,b,1)]
    assert e.retained == 1
    assert e.stats["evicted"] == 1
