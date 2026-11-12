from tests_hidden.helper import *


def test_equality_at_acceptance_frontier():
    items = [Event("left",1,8,0), Watermark("right",10), Event("right",1,8,1)]
    assert len(check(items,2,2)) == 1


def test_just_below_frontier_never_retained():
    e = TemporalJoin(20,2)
    e.push(Event("left",1,8,0))
    e.push(Watermark("right",11))
    before = (e.retained,dict(e.stats))
    assert e.push(Event("right",1,8,1)) == []
    assert (e.retained,dict(e.stats)) == before


def test_lateness_is_own_side_only():
    items = [Event("right",1,0,1), Watermark("right",100), Event("left",1,0,2)]
    assert len(check(items,0,0)) == 1


def test_unknown_own_watermark_accepts_negative_times():
    items = [Watermark("right",-10), Event("right",1,-10,1), Event("left",1,-12,2)]
    assert len(check(items,2,1)) == 1


def test_late_then_accepted_duplicate_and_advancement():
    items = [Event("left",0,9,0),Watermark("right",12),Event("right",0,8,1),Event("right",0,9,2),Watermark("right",14),Event("right",0,9,3)]
    out = check(items,5,3)
    assert [m.right.value for m in out] == [2]
