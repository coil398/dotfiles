"""Spec: docs/SPEC.md §§2–5 and docs/group11.md#r072."""

def test_encode_normal():
    from record_codecs.group11 import encode_r072 as encode, decode_r072 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_072': 'snow 雪', 'qty_072': '42', 'flag_072': 'ON', 'mode_072': 'R72'}

def test_decode_normal():
    from record_codecs.group11 import encode_r072 as encode, decode_r072 as decode
    assert decode({'v_072': 'snow 雪', 'qty_072': '42', 'flag_072': 'ON', 'mode_072': 'R72', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group11 import encode_r072 as encode, decode_r072 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_072': '42', 'flag_072': 'ON', 'mode_072': 'R72'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_072': None, 'qty_072': '42', 'flag_072': 'ON', 'mode_072': 'R72'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_072': 'snow 雪', 'qty_072': '-7', 'flag_072': 'ON', 'mode_072': 'R72'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_072': 'snow 雪', 'flag_072': 'ON', 'mode_072': 'R72'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_072': 'snow 雪', 'qty_072': '42', 'flag_072': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_072': 'snow 雪', 'qty_072': '42', 'flag_072': 'ON', 'mode_072': None}
    assert decode({'qty_072': '42', 'flag_072': 'ON', 'mode_072': 'R72'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_072': None, 'qty_072': '42', 'flag_072': 'ON', 'mode_072': 'R72'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_072': 'snow 雪', 'flag_072': 'ON', 'mode_072': 'R72'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_072': 'snow 雪', 'qty_072': None, 'flag_072': 'ON', 'mode_072': 'R72'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_072': 'snow 雪', 'qty_072': '42', 'mode_072': 'R72'})
    assert error.value.args == ('flag_072',)
    with pytest.raises(ValueError) as error:
        decode({'v_072': 'snow 雪', 'qty_072': '42', 'flag_072': None, 'mode_072': 'R72'})
    assert error.value.args == ('flag_072',)
    assert decode({'v_072': 'snow 雪', 'qty_072': '42', 'flag_072': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_072': 'snow 雪', 'qty_072': '42', 'flag_072': 'ON', 'mode_072': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group11 import encode_r072 as encode, decode_r072 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_072': '', 'qty_072': '-100000000000000000003', 'flag_072': 'OFF', 'mode_072': 'D72'}
    assert value == before
    assert result is not value
    value = {'v_072': '', 'qty_072': '-100000000000000000003', 'flag_072': 'OFF', 'mode_072': 'D72'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_072': '', 'qty_072': '0', 'flag_072': 'OFF', 'mode_072': 'H72'}
    assert decode({'v_072': '', 'qty_072': '0', 'flag_072': 'OFF', 'mode_072': 'H72'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
