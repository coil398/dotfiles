from tests_hidden.helper import *


def test_long_sparse_single_key_comparison_budget():
    e = TemporalJoin(1)
    outputs = 0
    for i in range(8192):
        for s in ("left","right"):
            outputs += len(e.push(Event(s,0,i*10,i)))
            assert e.stats["candidate_visits"] <= 2*(i+1)
    assert outputs == 8192
    assert e.stats["range_probes"] <= 600000
    assert e.stats["candidate_visits"] <= 16384
    assert e.retained == 16384


def test_out_of_order_narrow_ranges_skip_history():
    e = TemporalJoin(1)
    for i in range(2048): e.push(Event("left",0,i*10,i))
    before = dict(e.stats)
    for i in reversed(range(2048)):
        assert len(e.push(Event("right",0,i*10,i))) == 1
    assert e.stats["candidate_visits"] - before["candidate_visits"] == 2048
    assert e.stats["range_probes"] - before["range_probes"] <= 2048*52


def test_many_keys_single_watermark_bounded_retention():
    e = TemporalJoin(1)
    for i in range(4096):
        e.push(Event("left",i,i*10,i))
        e.push(Watermark("right",i*10+2))
        assert e.retained == 0 and e.key_count == 0
    assert e.stats["evicted"] == 4096


def test_two_watermarks_and_duplicate_boundary_state():
    e = TemporalJoin(2,1)
    for i in range(400):
        t = i*10
        for s in ("left","right"):
            for _ in range(2): e.push(Event(s,i,t,None))
        e.push(Watermark("left",t+3))
        e.push(Watermark("right",t+3))
        assert e.retained == 4 and e.key_count == 2
        e.push(Watermark("left",t+4))
        e.push(Watermark("right",t+4))
        assert e.retained == 0 and e.key_count == 0
    assert e.stats["candidate_visits"] == 1600
    assert e.stats["evicted"] == 1600


def test_wide_output_sensitive_range_budget():
    e = TemporalJoin(500)
    for i in range(1024): e.push(Event("right",1,i*2,i))
    before = dict(e.stats)
    out = e.push(Event("left",1,1024,0))
    assert len(out) == 501
    assert e.stats["candidate_visits"] - before["candidate_visits"] == 501
    assert e.stats["range_probes"] - before["range_probes"] <= 4*(1024 .bit_length()+1)
