"""Spec: docs/SPEC.md §§2–5 and docs/group29.md#r180."""

def test_encode_normal():
    from record_codecs.group29 import encode_r180 as encode, decode_r180 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_180': 'snow 雪', 'qty_180': '42', 'flag_180': 'ON', 'mode_180': 'R180'}

def test_decode_normal():
    from record_codecs.group29 import encode_r180 as encode, decode_r180 as decode
    assert decode({'v_180': 'snow 雪', 'qty_180': '42', 'flag_180': 'ON', 'mode_180': 'R180', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group29 import encode_r180 as encode, decode_r180 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_180': '42', 'flag_180': 'ON', 'mode_180': 'R180'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_180': None, 'qty_180': '42', 'flag_180': 'ON', 'mode_180': 'R180'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_180': 'snow 雪', 'qty_180': '-7', 'flag_180': 'ON', 'mode_180': 'R180'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_180': 'snow 雪', 'flag_180': 'ON', 'mode_180': 'R180'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_180': 'snow 雪', 'qty_180': '42', 'flag_180': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_180': 'snow 雪', 'qty_180': '42', 'flag_180': 'ON', 'mode_180': None}
    assert decode({'qty_180': '42', 'flag_180': 'ON', 'mode_180': 'R180'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_180': None, 'qty_180': '42', 'flag_180': 'ON', 'mode_180': 'R180'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_180': 'snow 雪', 'flag_180': 'ON', 'mode_180': 'R180'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_180': 'snow 雪', 'qty_180': None, 'flag_180': 'ON', 'mode_180': 'R180'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_180': 'snow 雪', 'qty_180': '42', 'mode_180': 'R180'})
    assert error.value.args == ('flag_180',)
    with pytest.raises(ValueError) as error:
        decode({'v_180': 'snow 雪', 'qty_180': '42', 'flag_180': None, 'mode_180': 'R180'})
    assert error.value.args == ('flag_180',)
    assert decode({'v_180': 'snow 雪', 'qty_180': '42', 'flag_180': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_180': 'snow 雪', 'qty_180': '42', 'flag_180': 'ON', 'mode_180': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group29 import encode_r180 as encode, decode_r180 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_180': '', 'qty_180': '-100000000000000000003', 'flag_180': 'OFF', 'mode_180': 'D180'}
    assert value == before
    assert result is not value
    value = {'v_180': '', 'qty_180': '-100000000000000000003', 'flag_180': 'OFF', 'mode_180': 'D180'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_180': '', 'qty_180': '0', 'flag_180': 'OFF', 'mode_180': 'H180'}
    assert decode({'v_180': '', 'qty_180': '0', 'flag_180': 'OFF', 'mode_180': 'H180'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
