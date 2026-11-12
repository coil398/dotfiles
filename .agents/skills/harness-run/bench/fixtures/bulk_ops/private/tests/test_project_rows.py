from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([[{'a': 1, 'b': 2}, {'b': 3}], ['b', 'a']], [{'b': 2, 'a': 1}, {'b': 3}]), ([[], ['x']], []), ([[{'a': 1}], ['a', 'a']], [{'a': 1}]), ([[{}], []], [{}])])
def test_project_rows(args, expected):
    from ops.m29 import project_rows
    original = deepcopy(args)
    result = project_rows(*args)
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
