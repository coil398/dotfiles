import pytest
import tomlkit


def test_export_and_existing_parser():
    assert "apply_edits" in tomlkit.__all__
    assert tomlkit.parse('a = 1 # hi\n').as_string() == 'a = 1 # hi\n'


def test_ordered_set_delete():
    d = tomlkit.parse('a = 1\nb = [2, 3]\n')
    out = tomlkit.apply_edits(d, [{"op":"set", "path":["a"], "value":4}, {"op":"delete", "path":["b",0]}])
    assert out.unwrap() == {"a":4,"b":[3]}
    assert d.unwrap() == {"a":1,"b":[2,3]}


def test_rename_example():
    out = tomlkit.apply_edits(tomlkit.parse('a  = 1 # keep\nb=2\n'), [{"op":"rename", "path":["a"], "new_key":"x.y"}])
    assert out.as_string() == '"x.y"  = 1 # keep\nb=2\n'


def test_dotted_example():
    out = tomlkit.apply_edits(tomlkit.parse('a.b = 1\na.c = 2\n'), [{"op":"rename", "path":["a"], "new_key":"z"}])
    assert out.as_string() == 'z.b = 1\nz.c = 2\n'


def test_failure_isolation():
    d = tomlkit.parse('a=1\n')
    with pytest.raises(KeyError):
        tomlkit.apply_edits(d, [{"op":"set", "path":["a"], "value":2},{"op":"delete", "path":["missing"]}])
    assert d.as_string() == 'a=1\n'
