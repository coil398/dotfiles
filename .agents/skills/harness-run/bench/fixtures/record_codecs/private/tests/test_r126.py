"""Spec: docs/SPEC.md §§2–5 and docs/group20.md#r126."""

def test_encode_normal():
    from record_codecs.group20 import encode_r126 as encode, decode_r126 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_126': 'snow 雪', 'qty_126': '42', 'flag_126': 'ON', 'mode_126': 'R126'}

def test_decode_normal():
    from record_codecs.group20 import encode_r126 as encode, decode_r126 as decode
    assert decode({'v_126': 'snow 雪', 'qty_126': '42', 'flag_126': 'ON', 'mode_126': 'R126', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group20 import encode_r126 as encode, decode_r126 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_126': '42', 'flag_126': 'ON', 'mode_126': 'R126'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_126': None, 'qty_126': '42', 'flag_126': 'ON', 'mode_126': 'R126'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_126': 'snow 雪', 'qty_126': '-7', 'flag_126': 'ON', 'mode_126': 'R126'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_126': 'snow 雪', 'flag_126': 'ON', 'mode_126': 'R126'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_126': 'snow 雪', 'qty_126': '42', 'flag_126': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_126': 'snow 雪', 'qty_126': '42', 'flag_126': 'ON', 'mode_126': None}
    assert decode({'qty_126': '42', 'flag_126': 'ON', 'mode_126': 'R126'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_126': None, 'qty_126': '42', 'flag_126': 'ON', 'mode_126': 'R126'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_126': 'snow 雪', 'flag_126': 'ON', 'mode_126': 'R126'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_126': 'snow 雪', 'qty_126': None, 'flag_126': 'ON', 'mode_126': 'R126'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_126': 'snow 雪', 'qty_126': '42', 'mode_126': 'R126'})
    assert error.value.args == ('flag_126',)
    with pytest.raises(ValueError) as error:
        decode({'v_126': 'snow 雪', 'qty_126': '42', 'flag_126': None, 'mode_126': 'R126'})
    assert error.value.args == ('flag_126',)
    assert decode({'v_126': 'snow 雪', 'qty_126': '42', 'flag_126': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_126': 'snow 雪', 'qty_126': '42', 'flag_126': 'ON', 'mode_126': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group20 import encode_r126 as encode, decode_r126 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_126': '', 'qty_126': '-100000000000000000003', 'flag_126': 'OFF', 'mode_126': 'D126'}
    assert value == before
    assert result is not value
    value = {'v_126': '', 'qty_126': '-100000000000000000003', 'flag_126': 'OFF', 'mode_126': 'D126'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_126': '', 'qty_126': '0', 'flag_126': 'OFF', 'mode_126': 'H126'}
    assert decode({'v_126': '', 'qty_126': '0', 'flag_126': 'OFF', 'mode_126': 'H126'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
