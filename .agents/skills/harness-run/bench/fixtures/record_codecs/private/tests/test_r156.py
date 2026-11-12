"""Spec: docs/SPEC.md §§2–5 and docs/group25.md#r156."""

def test_encode_normal():
    from record_codecs.group25 import encode_r156 as encode, decode_r156 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_156': 'snow 雪', 'qty_156': '42', 'flag_156': 'ON', 'mode_156': 'R156'}

def test_decode_normal():
    from record_codecs.group25 import encode_r156 as encode, decode_r156 as decode
    assert decode({'v_156': 'snow 雪', 'qty_156': '42', 'flag_156': 'ON', 'mode_156': 'R156', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group25 import encode_r156 as encode, decode_r156 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_156': '42', 'flag_156': 'ON', 'mode_156': 'R156'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_156': 'snow 雪', 'flag_156': 'ON', 'mode_156': 'R156'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_156': 'snow 雪', 'qty_156': '42', 'flag_156': 'OFF', 'mode_156': 'R156'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_156': 'snow 雪', 'qty_156': '42', 'flag_156': None, 'mode_156': 'R156'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_156': 'snow 雪', 'qty_156': '42', 'flag_156': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_156': '42', 'flag_156': 'ON', 'mode_156': 'R156'})
    assert error.value.args == ('v_156',)
    assert decode({'v_156': None, 'qty_156': '42', 'flag_156': 'ON', 'mode_156': 'R156'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_156': 'snow 雪', 'flag_156': 'ON', 'mode_156': 'R156'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_156': 'snow 雪', 'qty_156': None, 'flag_156': 'ON', 'mode_156': 'R156'})
    assert error.value.args == ('qty_156',)
    assert decode({'v_156': 'snow 雪', 'qty_156': '42', 'mode_156': 'R156'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_156': 'snow 雪', 'qty_156': '42', 'flag_156': None, 'mode_156': 'R156'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_156': 'snow 雪', 'qty_156': '42', 'flag_156': 'ON'})
    assert error.value.args == ('mode_156',)
    assert decode({'v_156': 'snow 雪', 'qty_156': '42', 'flag_156': 'ON', 'mode_156': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group25 import encode_r156 as encode, decode_r156 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_156': '', 'qty_156': '-100000000000000000003', 'flag_156': 'OFF', 'mode_156': 'D156'}
    assert value == before
    assert result is not value
    value = {'v_156': '', 'qty_156': '-100000000000000000003', 'flag_156': 'OFF', 'mode_156': 'D156'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_156': '', 'qty_156': '0', 'flag_156': 'OFF', 'mode_156': 'H156'}
    assert decode({'v_156': '', 'qty_156': '0', 'flag_156': 'OFF', 'mode_156': 'H156'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
