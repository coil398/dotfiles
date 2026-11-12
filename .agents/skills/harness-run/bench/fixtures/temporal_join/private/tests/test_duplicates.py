from tests_hidden.helper import *


def test_same_object_is_multiple_occurrences():
    a, b = Event("left", "x", 0, []), Event("right", "x", 0, {})
    out = check([a,a,b,b], 0)
    assert len(out) == 4
    assert all(m.left is a and m.right is b for m in out)


def test_cartesian_multiplicity_across_keys():
    items = [Event(s,k,1,v) for s,n in (("left",3),("right",4)) for k in ("a","b") for v in range(n)]
    assert len(check(items, 0)) == 24


def test_duplicate_timestamps_with_distinct_payloads():
    items = [Event("right", 1, 9, v) for v in ([], {}, None)]
    items += [Event("left", 1, 9, object())]
    out = check(items, 0)
    assert [m.right.value for m in out] == [[], {}, None]


def test_duplicates_survive_equal_watermark():
    items = [Event("left", "k", 7, 1)] * 3
    items += [Watermark("left",7), Watermark("right",7)] * 2
    items += [Event("right","k",7,2)] * 2
    assert len(check(items,0)) == 6


def test_pair_emitted_only_on_second_arrival():
    e = TemporalJoin(2)
    a,b,c = Event("left","k",1,1),Event("right","k",2,2),Event("left","k",3,3)
    assert e.push(a) == []
    assert e.push(b) == [Match(a,b,2)]
    assert e.push(c) == [Match(c,b,3)]
    assert e.push(Watermark("left",5)) == []
    assert e.push(Flush()) == []
