from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([[{'x': 1}, {'x': 2}, {}], 'x', 1], [{'x': 1}]), ([[], 'x', 0], []), ([[{'x': 2}, {'x': 2}], 'x', 2], [{'x': 2}, {'x': 2}]), ([[{}, {'x': 0}], 'x', 0], [{'x': 0}])])
def test_filter_rows(args, expected):
    from ops.m28 import filter_rows
    original = deepcopy(args)
    result = filter_rows(*args)
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
