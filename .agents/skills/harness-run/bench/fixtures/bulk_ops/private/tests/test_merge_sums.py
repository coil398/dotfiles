from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([{'a': 2}, {'a': 3, 'b': 1}], {'a': 5, 'b': 1}), ([{}, {}], {}), ([{'b': 0, 'a': 1}, {'a': -1, 'c': 2}], {'b': 0, 'a': 0, 'c': 2}), ([{}, {'z': -2}], {'z': -2})])
def test_merge_sums(args, expected):
    from ops.m12 import merge_sums
    original = deepcopy(args)
    result = merge_sums(*args)
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
