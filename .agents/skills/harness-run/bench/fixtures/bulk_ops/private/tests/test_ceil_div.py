from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([7, 3], 3), ([0, 2], 0), ([-7, 3], -2), ([1000000000000000000000000000001, 10], 100000000000000000000000000001)])
def test_ceil_div(args, expected):
    from ops.m22 import ceil_div
    original = deepcopy(args)
    result = ceil_div(*args)
    assert result == expected
    assert type(result) is type(expected)
    assert args == original
    def ordered(value):
        if isinstance(value, dict):
            return [(k, ordered(v)) for k, v in value.items()]
        if isinstance(value, list):
            return [ordered(v) for v in value]
        return value
    assert ordered(result) == ordered(expected)
    assert ordered(args) == ordered(original)
    input_ids = set()
    def remember(value):
        if isinstance(value, (list, dict)):
            input_ids.add(id(value))
            for child in (value.values() if isinstance(value, dict) else value):
                remember(child)
    remember(args)
    def fresh(value):
        if isinstance(value, (list, dict)):
            assert id(value) not in input_ids
            for child in (value.values() if isinstance(value, dict) else value):
                fresh(child)
    fresh(result)
