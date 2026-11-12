from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([[{'id': 'a', 'n': 1}, {'id': 'b', 'n': 2}], 'id'], {'a': {'id': 'a', 'n': 1}, 'b': {'id': 'b', 'n': 2}}), ([[], 'id'], {}), ([[{'id': 'a', 'n': 1}, {'id': 'a', 'n': 2}], 'id'], {'a': {'id': 'a', 'n': 2}}), ([[{'id': ''}], 'id'], {'': {'id': ''}})])
def test_index_last(args, expected):
    from ops.m26 import index_last
    original = deepcopy(args)
    result = index_last(*args)
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
