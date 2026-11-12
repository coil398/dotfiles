from tests_hidden.helper import *
import random


def test_closed_both_endpoints_and_keys():
    items = [Event("left", k, t, (k,t)) for k in ("a", "b") for t in (-5, 0, 5)]
    items += [Event("right", "a", 0, None), Event("right", "b", 10, None)]
    assert len(check(items, 5)) == 4


def test_zero_window_negative_and_large_integers():
    for t in (-10**40, -1, 0, 10**40):
        items = [Event("right", "k", t+1, 0), Event("right", "k", t, 1), Event("left", "k", t, 2)]
        assert len(check(items, 0)) == 1


def test_heterogeneous_keys_are_not_sorted():
    keys = [None, "x", (1,2), frozenset({3}), 42]
    items = [Event(s, k, 0, object()) for s in ("left", "right") for k in keys]
    assert len(check(items, 1)) == 5


def test_same_side_isolation_and_no_transitive_match():
    items = [Event("left", "k", t, t) for t in (0, 2, 4)]
    items += [Event("right", "k", 6, 6), Event("right", "other", 4, 4)]
    assert len(check(items, 2)) == 1


def test_seeded_out_of_order_oracle():
    rng = random.Random(921)
    items = [Event(rng.choice(("left", "right")), rng.randrange(4), rng.randrange(-20,21), i) for i in range(180)]
    assert check(items, 3)
