from configlayers import load


def test_nested_override_keeps_siblings(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{"a":{"x":1,"y":2}}')
    assert load(p,overrides={'a':{'x':3}})=={'a':{'x':3,'y':2}}


def test_explicit_none_means_no_layer(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{"a":1}')
    assert load(p,overrides=None)=={'a':1}


def test_override_array_replaces(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{"a":[1,2]}')
    assert load(p,overrides={'a':[3]})=={'a':[3]}


def test_override_cannot_mutate_caller_nested_values(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{}'); o={'a':{'b':[1]}}
    load(p,overrides=o); assert o=={'a':{'b':[1]}}
