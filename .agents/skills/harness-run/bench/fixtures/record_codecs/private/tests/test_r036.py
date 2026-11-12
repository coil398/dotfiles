"""Spec: docs/SPEC.md §§2–5 and docs/group05.md#r036."""

def test_encode_normal():
    from record_codecs.group05 import encode_r036 as encode, decode_r036 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_036': 'snow 雪', 'qty_036': '42', 'flag_036': 'ON', 'mode_036': 'R36'}

def test_decode_normal():
    from record_codecs.group05 import encode_r036 as encode, decode_r036 as decode
    assert decode({'v_036': 'snow 雪', 'qty_036': '42', 'flag_036': 'ON', 'mode_036': 'R36', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group05 import encode_r036 as encode, decode_r036 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_036': '42', 'flag_036': 'ON', 'mode_036': 'R36'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_036': None, 'qty_036': '42', 'flag_036': 'ON', 'mode_036': 'R36'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_036': 'snow 雪', 'qty_036': '-7', 'flag_036': 'ON', 'mode_036': 'R36'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_036': 'snow 雪', 'flag_036': 'ON', 'mode_036': 'R36'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_036': 'snow 雪', 'qty_036': '42', 'flag_036': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_036': 'snow 雪', 'qty_036': '42', 'flag_036': 'ON', 'mode_036': None}
    assert decode({'qty_036': '42', 'flag_036': 'ON', 'mode_036': 'R36'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_036': None, 'qty_036': '42', 'flag_036': 'ON', 'mode_036': 'R36'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_036': 'snow 雪', 'flag_036': 'ON', 'mode_036': 'R36'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_036': 'snow 雪', 'qty_036': None, 'flag_036': 'ON', 'mode_036': 'R36'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_036': 'snow 雪', 'qty_036': '42', 'mode_036': 'R36'})
    assert error.value.args == ('flag_036',)
    with pytest.raises(ValueError) as error:
        decode({'v_036': 'snow 雪', 'qty_036': '42', 'flag_036': None, 'mode_036': 'R36'})
    assert error.value.args == ('flag_036',)
    assert decode({'v_036': 'snow 雪', 'qty_036': '42', 'flag_036': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_036': 'snow 雪', 'qty_036': '42', 'flag_036': 'ON', 'mode_036': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group05 import encode_r036 as encode, decode_r036 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_036': '', 'qty_036': '-100000000000000000003', 'flag_036': 'OFF', 'mode_036': 'D36'}
    assert value == before
    assert result is not value
    value = {'v_036': '', 'qty_036': '-100000000000000000003', 'flag_036': 'OFF', 'mode_036': 'D36'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_036': '', 'qty_036': '0', 'flag_036': 'OFF', 'mode_036': 'H36'}
    assert decode({'v_036': '', 'qty_036': '0', 'flag_036': 'OFF', 'mode_036': 'H36'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
