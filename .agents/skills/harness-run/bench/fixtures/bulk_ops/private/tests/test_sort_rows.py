from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([[{'n': 2}, {'n': 1}], 'n'], [{'n': 1}, {'n': 2}]), ([[], 'n'], []), ([[{'n': 1, 'id': 'b'}, {'n': 1, 'id': 'a'}], 'n'], [{'n': 1, 'id': 'b'}, {'n': 1, 'id': 'a'}]), ([[{'n': 0}, {'n': -1}], 'n'], [{'n': -1}, {'n': 0}])])
def test_sort_rows(args, expected):
    from ops.m27 import sort_rows
    original = deepcopy(args)
    result = sort_rows(*args)
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
