from temporal_join import Event, Match, Watermark, Flush, TemporalJoin, join
import pytest


def test_basic_pair():
    a,b = Event("left","a",1,1), Event("right","a",2,2)
    assert list(join([a,b],3)) == [Match(a,b,2)]


def test_closed_boundary():
    assert len(list(join([Event("left",1,0,0),Event("right",1,2,0)],2))) == 1


def test_keys_and_same_side():
    assert list(join([Event("left",1,0,0),Event("left",1,0,1),Event("right",2,0,0)],1)) == []


def test_zero_window_duplicates():
    a,b = Event("left",0,0,0),Event("right",0,0,0)
    assert len(list(join([a,a,b],0))) == 2


def test_ordering():
    items = [Event("left",1,t,t) for t in (2,0,1)] + [Event("right",1,1,0)]
    assert [m.left.timestamp for m in join(items,3)] == [0,1,2]


def test_lateness_equality():
    items = [Event("left",1,9,0),Watermark("right",10),Event("right",1,9,0)]
    assert len(list(join(items,3,1))) == 1


def test_watermark_retention():
    e = TemporalJoin(2)
    e.push(Event("left",1,0,0));e.push(Watermark("right",3))
    assert e.retained == 0


def test_monotonic_watermark():
    e = TemporalJoin(1)
    e.push(Watermark("left",3))
    with pytest.raises(ValueError): e.push(Watermark("left",2))


def test_flush_and_closed():
    e = TemporalJoin(1)
    e.push(Event("left",1,0,0));e.push(Flush())
    assert e.closed and e.retained == 0
    with pytest.raises(RuntimeError): e.push(Flush())


def test_constructor_validation():
    with pytest.raises(ValueError): TemporalJoin(-1)
    with pytest.raises(TypeError): TemporalJoin(True)
