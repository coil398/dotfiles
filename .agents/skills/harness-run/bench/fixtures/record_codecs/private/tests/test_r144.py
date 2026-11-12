"""Spec: docs/SPEC.md §§2–5 and docs/group23.md#r144."""

def test_encode_normal():
    from record_codecs.group23 import encode_r144 as encode, decode_r144 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_144': 'snow 雪', 'qty_144': '42', 'flag_144': 'ON', 'mode_144': 'R144'}

def test_decode_normal():
    from record_codecs.group23 import encode_r144 as encode, decode_r144 as decode
    assert decode({'v_144': 'snow 雪', 'qty_144': '42', 'flag_144': 'ON', 'mode_144': 'R144', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group23 import encode_r144 as encode, decode_r144 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_144': '42', 'flag_144': 'ON', 'mode_144': 'R144'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_144': None, 'qty_144': '42', 'flag_144': 'ON', 'mode_144': 'R144'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_144': 'snow 雪', 'qty_144': '-7', 'flag_144': 'ON', 'mode_144': 'R144'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_144': 'snow 雪', 'flag_144': 'ON', 'mode_144': 'R144'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_144': 'snow 雪', 'qty_144': '42', 'flag_144': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_144': 'snow 雪', 'qty_144': '42', 'flag_144': 'ON', 'mode_144': None}
    assert decode({'qty_144': '42', 'flag_144': 'ON', 'mode_144': 'R144'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_144': None, 'qty_144': '42', 'flag_144': 'ON', 'mode_144': 'R144'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_144': 'snow 雪', 'flag_144': 'ON', 'mode_144': 'R144'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_144': 'snow 雪', 'qty_144': None, 'flag_144': 'ON', 'mode_144': 'R144'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_144': 'snow 雪', 'qty_144': '42', 'mode_144': 'R144'})
    assert error.value.args == ('flag_144',)
    with pytest.raises(ValueError) as error:
        decode({'v_144': 'snow 雪', 'qty_144': '42', 'flag_144': None, 'mode_144': 'R144'})
    assert error.value.args == ('flag_144',)
    assert decode({'v_144': 'snow 雪', 'qty_144': '42', 'flag_144': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_144': 'snow 雪', 'qty_144': '42', 'flag_144': 'ON', 'mode_144': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group23 import encode_r144 as encode, decode_r144 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_144': '', 'qty_144': '-100000000000000000003', 'flag_144': 'OFF', 'mode_144': 'D144'}
    assert value == before
    assert result is not value
    value = {'v_144': '', 'qty_144': '-100000000000000000003', 'flag_144': 'OFF', 'mode_144': 'D144'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_144': '', 'qty_144': '0', 'flag_144': 'OFF', 'mode_144': 'H144'}
    assert decode({'v_144': '', 'qty_144': '0', 'flag_144': 'OFF', 'mode_144': 'H144'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
