from configlayers.merge import merge


def test_arrays_replace_and_null_is_present():
    assert merge({"a":[1,2],"n":1},{"a":[3],"n":None}) == {"a":[3],"n":None}


def test_delete_nested_key():
    assert merge({"a":{"x":1,"y":2}},{"a":{"x":{"$delete":True}}}) == {"a":{"y":2}}


def test_delete_then_readd():
    assert merge(merge({"a":1},{"a":{"$delete":True}}),{"a":2}) == {"a":2}


def test_delete_absent_is_harmless():
    assert merge({}, {"x":{"$delete":True}}) == {}
