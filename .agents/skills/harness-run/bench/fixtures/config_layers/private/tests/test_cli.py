from configlayers import load_cli


def test_set_splits_at_first_equals(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{}')
    assert load_cli(['--config',str(p),'--set','x="a=b"']) == {'x':'a=b'}


def test_descending_set_replaces_scalar_and_null(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{"a":4,"b":null}')
    assert load_cli(['--config',str(p),'--set','a.x=1','--set','b.y=2']) == {'a':{'x':1},'b':{'y':2}}


def test_invalid_empty_path_component_is_rejected(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{}')
    try: load_cli(['--config',str(p),'--set','.x=1'])
    except ValueError: pass
    else: assert False, 'empty component accepted'


def test_cli_override_deletion(tmp_path):
    p=tmp_path/'c.json'; p.write_text('{"a":1}')
    assert load_cli(['--config',str(p),'--set','a={"$delete":true}']) == {}
