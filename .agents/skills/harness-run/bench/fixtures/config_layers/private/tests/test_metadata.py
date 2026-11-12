from configlayers import load


def test_include_metadata_never_leaks(tmp_path):
    (tmp_path/'child.json').write_text('{"x":1}')
    (tmp_path/'root.json').write_text('{"$include":"child.json","y":2}')
    assert '$include' not in load(tmp_path/'root.json')


def test_delete_marker_with_extra_key_is_value():
    from configlayers.merge import merge
    assert merge({'x':1},{'x':{'$delete':True,'keep':2}})=={'x':{'$delete':True,'keep':2}}


def test_override_delete_marker_is_interpreted(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{"x":1}')
    assert load(p,overrides={'x':{'$delete':True}})=={}


def test_independent_loads_do_not_share_defaults(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{"a":{"x":1}}')
    first=load(p); first['a']['x']=99
    assert load(p)=={'a':{'x':1}}
