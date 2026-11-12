from configlayers import load


def test_nested_relative_to_declaring_file(tmp_path):
    (tmp_path / "a").mkdir(); (tmp_path / "b").mkdir()
    (tmp_path / "a" / "base.json").write_text('{"a":1}')
    (tmp_path / "b" / "mid.json").write_text('{"$include":"../a/base.json","b":2}')
    (tmp_path / "root.json").write_text('{"$include":"b/mid.json"}')
    assert load(tmp_path / "root.json") == {"a":1,"b":2}


def test_same_relative_names_in_different_directories(tmp_path):
    for d, v in [("left", 1), ("right", 2)]:
        (tmp_path / d).mkdir(); (tmp_path / d / "common.json").write_text('{"v":%d}' % v)
    (tmp_path / "root.json").write_text('{"$include":["left/common.json","right/common.json"]}')
    assert load(tmp_path / "root.json")["v"] == 2


def test_diamond_include_is_allowed(tmp_path):
    (tmp_path / "leaf.json").write_text('{"v":1}')
    (tmp_path / "a.json").write_text('{"$include":"leaf.json","a":1}')
    (tmp_path / "b.json").write_text('{"$include":"leaf.json","b":1}')
    (tmp_path / "root.json").write_text('{"$include":["a.json","b.json"]}')
    assert load(tmp_path / "root.json") == {"v":1,"a":1,"b":1}


def test_active_cycle_reports_value_error(tmp_path):
    (tmp_path / "a.json").write_text('{"$include":"b.json"}')
    (tmp_path / "b.json").write_text('{"$include":"a.json"}')
    try: load(tmp_path / "a.json")
    except ValueError as exc: assert "cycle" in str(exc).lower()
    else: assert False, "cycle accepted"
