from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([[{'n': 2}, {'n': 3}, {}], 'n'], 5), ([[], 'n'], 0), ([[{'n': 2}, {'n': 2}], 'n'], 4), ([[{'n': -2}, {'n': 0}], 'n'], -2)])
def test_sum_column(args, expected):
    from ops.m28 import sum_column
    original = deepcopy(args)
    result = sum_column(*args)
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
