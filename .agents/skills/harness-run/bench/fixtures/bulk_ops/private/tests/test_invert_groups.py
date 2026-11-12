from copy import deepcopy
import pytest

@pytest.mark.parametrize("args, expected", [([{'a': 'x', 'b': 'y', 'c': 'x'}], {'x': ['a', 'c'], 'y': ['b']}), ([{}], {}), ([{'b': 'z', 'a': 'z'}], {'z': ['b', 'a']}), ([{'': '', 'x': 'x'}], {'': [''], 'x': ['x']})])
def test_invert_groups(args, expected):
    from ops.m11 import invert_groups
    original = deepcopy(args)
    result = invert_groups(*args)
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
