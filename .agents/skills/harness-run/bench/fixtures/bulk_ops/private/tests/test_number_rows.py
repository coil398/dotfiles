from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([[{'x': 1}, {'x': 2}], 1], [{'x': 1, '_index': 1}, {'x': 2, '_index': 2}]), ([[], 0], []), ([[{'_index': 9}, {'_index': 9}], -1], [{'_index': -1}, {'_index': 0}]), ([[{}], 0], [{'_index': 0}])])
def test_number_rows(args, expected):
    from ops.m29 import number_rows
    original = deepcopy(args)
    result = number_rows(*args)
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
