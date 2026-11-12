from tests_hidden.helper import *
import pytest


def test_constructor_types_and_distances():
    for field in (0,1):
        for value, error in ((True,TypeError),(1.0,TypeError),("1",TypeError),(None,TypeError),(-1,ValueError)):
            args = [1,0]; args[field] = value
            with pytest.raises(error): TemporalJoin(*args)
    assert TemporalJoin(0,0).retained == 0


def test_timestamp_types_rejected_atomically():
    e = TemporalJoin(2)
    e.push(Event("left",1,1,0))
    for cls in (Event,Watermark):
        for t in (False,1.5,None,"3"):
            item = cls("right",1,t,0) if cls is Event else cls("right",t)
            before = (e.retained,dict(e.stats),dict(e.watermarks))
            with pytest.raises(TypeError): e.push(item)
            assert (e.retained,dict(e.stats),dict(e.watermarks)) == before


def test_bad_sides_and_unsupported_items():
    e = TemporalJoin(1)
    for s in ("LEFT",None,[],1):
        with pytest.raises(ValueError): e.push(Event(s,1,0,0))
        with pytest.raises(ValueError): e.push(Watermark(s,0))
    for item in (None,{},(),0):
        with pytest.raises(TypeError): e.push(item)
    assert e.retained == 0 and e.key_count == 0
    assert dict(e.stats) == dict(range_probes=0,candidate_visits=0,evicted=0)


def test_key_validation_precedes_late_filter():
    e = TemporalJoin(1)
    e.push(Watermark("left",10))
    for key in ([],{},set()):
        with pytest.raises(TypeError): e.push(Event("left",key,0,0))
    assert e.retained == 0


def test_payload_identity_and_readonly_observability():
    value = {"a": []}
    a,b = Event("left",None,0,value),Event("right",None,0,[])
    e = TemporalJoin(0)
    e.push(a); out = e.push(b)
    assert out[0].left is a and out[0].right is b
    assert value == {"a": []}
    with pytest.raises((AttributeError,TypeError)): e.stats["evicted"] = 10
    with pytest.raises(AttributeError): e.retained = 99
    with pytest.raises(AttributeError): a.timestamp = 7
