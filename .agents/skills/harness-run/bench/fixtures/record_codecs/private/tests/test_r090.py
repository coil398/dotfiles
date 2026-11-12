"""Spec: docs/SPEC.md §§2–5 and docs/group14.md#r090."""

def test_encode_normal():
    from record_codecs.group14 import encode_r090 as encode, decode_r090 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_090': 'snow 雪', 'qty_090': '42', 'flag_090': 'ON', 'mode_090': 'R90'}

def test_decode_normal():
    from record_codecs.group14 import encode_r090 as encode, decode_r090 as decode
    assert decode({'v_090': 'snow 雪', 'qty_090': '42', 'flag_090': 'ON', 'mode_090': 'R90', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group14 import encode_r090 as encode, decode_r090 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_090': '42', 'flag_090': 'ON', 'mode_090': 'R90'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_090': None, 'qty_090': '42', 'flag_090': 'ON', 'mode_090': 'R90'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_090': 'snow 雪', 'qty_090': '-7', 'flag_090': 'ON', 'mode_090': 'R90'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_090': 'snow 雪', 'flag_090': 'ON', 'mode_090': 'R90'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_090': 'snow 雪', 'qty_090': '42', 'flag_090': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_090': 'snow 雪', 'qty_090': '42', 'flag_090': 'ON', 'mode_090': None}
    assert decode({'qty_090': '42', 'flag_090': 'ON', 'mode_090': 'R90'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_090': None, 'qty_090': '42', 'flag_090': 'ON', 'mode_090': 'R90'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_090': 'snow 雪', 'flag_090': 'ON', 'mode_090': 'R90'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_090': 'snow 雪', 'qty_090': None, 'flag_090': 'ON', 'mode_090': 'R90'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_090': 'snow 雪', 'qty_090': '42', 'mode_090': 'R90'})
    assert error.value.args == ('flag_090',)
    with pytest.raises(ValueError) as error:
        decode({'v_090': 'snow 雪', 'qty_090': '42', 'flag_090': None, 'mode_090': 'R90'})
    assert error.value.args == ('flag_090',)
    assert decode({'v_090': 'snow 雪', 'qty_090': '42', 'flag_090': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_090': 'snow 雪', 'qty_090': '42', 'flag_090': 'ON', 'mode_090': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group14 import encode_r090 as encode, decode_r090 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_090': '', 'qty_090': '-100000000000000000003', 'flag_090': 'OFF', 'mode_090': 'D90'}
    assert value == before
    assert result is not value
    value = {'v_090': '', 'qty_090': '-100000000000000000003', 'flag_090': 'OFF', 'mode_090': 'D90'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_090': '', 'qty_090': '0', 'flag_090': 'OFF', 'mode_090': 'H90'}
    assert decode({'v_090': '', 'qty_090': '0', 'flag_090': 'OFF', 'mode_090': 'H90'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
