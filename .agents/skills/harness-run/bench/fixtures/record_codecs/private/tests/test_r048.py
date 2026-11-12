"""Spec: docs/SPEC.md §§2–5 and docs/group07.md#r048."""

def test_encode_normal():
    from record_codecs.group07 import encode_r048 as encode, decode_r048 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_048': 'snow 雪', 'qty_048': '42', 'flag_048': 'ON', 'mode_048': 'R48'}

def test_decode_normal():
    from record_codecs.group07 import encode_r048 as encode, decode_r048 as decode
    assert decode({'v_048': 'snow 雪', 'qty_048': '42', 'flag_048': 'ON', 'mode_048': 'R48', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group07 import encode_r048 as encode, decode_r048 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_048': '42', 'flag_048': 'ON', 'mode_048': 'R48'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_048': 'snow 雪', 'flag_048': 'ON', 'mode_048': 'R48'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_048': 'snow 雪', 'qty_048': '42', 'flag_048': 'OFF', 'mode_048': 'R48'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_048': 'snow 雪', 'qty_048': '42', 'flag_048': None, 'mode_048': 'R48'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_048': 'snow 雪', 'qty_048': '42', 'flag_048': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_048': '42', 'flag_048': 'ON', 'mode_048': 'R48'})
    assert error.value.args == ('v_048',)
    assert decode({'v_048': None, 'qty_048': '42', 'flag_048': 'ON', 'mode_048': 'R48'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_048': 'snow 雪', 'flag_048': 'ON', 'mode_048': 'R48'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_048': 'snow 雪', 'qty_048': None, 'flag_048': 'ON', 'mode_048': 'R48'})
    assert error.value.args == ('qty_048',)
    assert decode({'v_048': 'snow 雪', 'qty_048': '42', 'mode_048': 'R48'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_048': 'snow 雪', 'qty_048': '42', 'flag_048': None, 'mode_048': 'R48'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_048': 'snow 雪', 'qty_048': '42', 'flag_048': 'ON'})
    assert error.value.args == ('mode_048',)
    assert decode({'v_048': 'snow 雪', 'qty_048': '42', 'flag_048': 'ON', 'mode_048': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group07 import encode_r048 as encode, decode_r048 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_048': '', 'qty_048': '-100000000000000000003', 'flag_048': 'OFF', 'mode_048': 'D48'}
    assert value == before
    assert result is not value
    value = {'v_048': '', 'qty_048': '-100000000000000000003', 'flag_048': 'OFF', 'mode_048': 'D48'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_048': '', 'qty_048': '0', 'flag_048': 'OFF', 'mode_048': 'H48'}
    assert decode({'v_048': '', 'qty_048': '0', 'flag_048': 'OFF', 'mode_048': 'H48'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
