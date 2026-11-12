from tests_hidden.helper import *


def test_right_arrival_sorts_left_timestamp():
    items = [Event("left",1,t,i) for i,t in enumerate((5,1,3,1))]
    items += [Event("right",1,3,0)]
    out = check(items,5)
    assert [m.left.value for m in out] == [1,3,2,0]


def test_left_arrival_sorts_right_timestamp():
    items = [Event("right",1,t,i) for i,t in enumerate((4,-1,4,0))]
    items += [Event("left",1,0,0)]
    assert [m.right.value for m in check(items,5)] == [1,3,0,2]


def test_equal_time_uses_arrival_not_payload():
    values = [object(), {}, [], None]
    items = [Event("left","k",2,v) for v in values] + [Event("right","k",2,0)]
    assert all(m.left.value is v for m,v in zip(check(items,1), values))


def test_batches_are_not_globally_sorted():
    items = [Event("left",0,t,t) for t in (10,0)]
    items += [Event("right",0,t,t) for t in (10,0)]
    assert [m.timestamp for m in check(items,0)] == [10,0]


def test_order_after_eviction_and_new_ties():
    items = [Event("left",0,t,i) for i,t in enumerate((1,9,5,9))]
    items += [Watermark("right",8), Event("left",0,9,4), Event("right",0,9,5)]
    assert [m.left.value for m in check(items,2)] == [1,3,4]
