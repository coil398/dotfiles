"""Spec: docs/SPEC.md §§2–5 and docs/group02.md#r018."""

def test_encode_normal():
    from record_codecs.group02 import encode_r018 as encode, decode_r018 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_018': 'snow 雪', 'qty_018': '42', 'flag_018': 'ON', 'mode_018': 'R18'}

def test_decode_normal():
    from record_codecs.group02 import encode_r018 as encode, decode_r018 as decode
    assert decode({'v_018': 'snow 雪', 'qty_018': '42', 'flag_018': 'ON', 'mode_018': 'R18', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group02 import encode_r018 as encode, decode_r018 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_018': '42', 'flag_018': 'ON', 'mode_018': 'R18'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_018': None, 'qty_018': '42', 'flag_018': 'ON', 'mode_018': 'R18'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_018': 'snow 雪', 'qty_018': '-7', 'flag_018': 'ON', 'mode_018': 'R18'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_018': 'snow 雪', 'flag_018': 'ON', 'mode_018': 'R18'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_018': 'snow 雪', 'qty_018': '42', 'flag_018': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_018': 'snow 雪', 'qty_018': '42', 'flag_018': 'ON', 'mode_018': None}
    assert decode({'qty_018': '42', 'flag_018': 'ON', 'mode_018': 'R18'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_018': None, 'qty_018': '42', 'flag_018': 'ON', 'mode_018': 'R18'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_018': 'snow 雪', 'flag_018': 'ON', 'mode_018': 'R18'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_018': 'snow 雪', 'qty_018': None, 'flag_018': 'ON', 'mode_018': 'R18'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_018': 'snow 雪', 'qty_018': '42', 'mode_018': 'R18'})
    assert error.value.args == ('flag_018',)
    with pytest.raises(ValueError) as error:
        decode({'v_018': 'snow 雪', 'qty_018': '42', 'flag_018': None, 'mode_018': 'R18'})
    assert error.value.args == ('flag_018',)
    assert decode({'v_018': 'snow 雪', 'qty_018': '42', 'flag_018': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_018': 'snow 雪', 'qty_018': '42', 'flag_018': 'ON', 'mode_018': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group02 import encode_r018 as encode, decode_r018 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_018': '', 'qty_018': '-100000000000000000003', 'flag_018': 'OFF', 'mode_018': 'D18'}
    assert value == before
    assert result is not value
    value = {'v_018': '', 'qty_018': '-100000000000000000003', 'flag_018': 'OFF', 'mode_018': 'D18'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_018': '', 'qty_018': '0', 'flag_018': 'OFF', 'mode_018': 'H18'}
    assert decode({'v_018': '', 'qty_018': '0', 'flag_018': 'OFF', 'mode_018': 'H18'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
