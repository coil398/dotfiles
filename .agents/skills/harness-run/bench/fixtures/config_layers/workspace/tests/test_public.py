import json
from configlayers import load, load_cli


def test_recursive_relative_include_and_merge(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "base.json").write_text('{"a":{"x":1,"items":[1,2]},"gone":true}')
    (tmp_path / "sub" / "mid.json").write_text('{"$include":"../base.json","a":{"y":2}}')
    (tmp_path / "main.json").write_text('{"$include":"sub/mid.json","a":{"items":[3]},"gone":{"$delete":true}}')
    assert load(tmp_path / "main.json") == {"a":{"x":1,"y":2,"items":[3]}}


def test_null_override_and_no_input_mutation(tmp_path):
    p = tmp_path / "c.json"
    p.write_text('{"a":{"x":1},"v":2}')
    overrides = {"a":{"x":None}, "v":{"$delete":True}}
    assert load(p, overrides=overrides) == {"a":{"x":None}}
    assert overrides == {"a":{"x":None}, "v":{"$delete":True}}


def test_cli_json_values_and_repeated_path(tmp_path):
    p = tmp_path / "c.json"
    p.write_text('{"x":1}')
    assert load_cli(["--config", str(p), "--set", "x=2", "--set", "x=null", "--set", "n.ok=true"]) == {"x":None,"n":{"ok":True}}
