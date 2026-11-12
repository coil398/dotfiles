from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([[{'a': 1}, {'b': 2}], ['b', 'a'], 0], {'b': [0, 2], 'a': [1, 0]}), ([[], ['a'], 0], {'a': []}), ([[{'a': 2}, {'a': 2}], ['a', 'a'], 0], {'a': [2, 2]}), ([[{}], [], -1], {})])
def test_transpose_records(args, expected):
    from ops.m30 import transpose_records
    original = deepcopy(args)
    result = transpose_records(*args)
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
