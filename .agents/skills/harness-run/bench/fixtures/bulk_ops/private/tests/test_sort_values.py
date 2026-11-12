from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([{'a': 3, 'b': 1}], ['b', 'a']), ([{}], []), ([{'b': 2, 'a': 2, 'c': 1}], ['c', 'b', 'a']), ([{'z': -2, 'x': 0}], ['z', 'x'])])
def test_sort_values(args, expected):
    from ops.m15 import sort_values
    original = deepcopy(args)
    result = sort_values(*args)
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
