"""Spec: docs/SPEC.md §§2–5 and docs/group16.md#r102."""

def test_encode_normal():
    from record_codecs.group16 import encode_r102 as encode, decode_r102 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_102': 'snow 雪', 'qty_102': '42', 'flag_102': 'ON', 'mode_102': 'R102'}

def test_decode_normal():
    from record_codecs.group16 import encode_r102 as encode, decode_r102 as decode
    assert decode({'v_102': 'snow 雪', 'qty_102': '42', 'flag_102': 'ON', 'mode_102': 'R102', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group16 import encode_r102 as encode, decode_r102 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_102': '42', 'flag_102': 'ON', 'mode_102': 'R102'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_102': 'snow 雪', 'flag_102': 'ON', 'mode_102': 'R102'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_102': 'snow 雪', 'qty_102': '42', 'flag_102': 'OFF', 'mode_102': 'R102'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_102': 'snow 雪', 'qty_102': '42', 'flag_102': None, 'mode_102': 'R102'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_102': 'snow 雪', 'qty_102': '42', 'flag_102': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_102': '42', 'flag_102': 'ON', 'mode_102': 'R102'})
    assert error.value.args == ('v_102',)
    assert decode({'v_102': None, 'qty_102': '42', 'flag_102': 'ON', 'mode_102': 'R102'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_102': 'snow 雪', 'flag_102': 'ON', 'mode_102': 'R102'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_102': 'snow 雪', 'qty_102': None, 'flag_102': 'ON', 'mode_102': 'R102'})
    assert error.value.args == ('qty_102',)
    assert decode({'v_102': 'snow 雪', 'qty_102': '42', 'mode_102': 'R102'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_102': 'snow 雪', 'qty_102': '42', 'flag_102': None, 'mode_102': 'R102'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_102': 'snow 雪', 'qty_102': '42', 'flag_102': 'ON'})
    assert error.value.args == ('mode_102',)
    assert decode({'v_102': 'snow 雪', 'qty_102': '42', 'flag_102': 'ON', 'mode_102': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group16 import encode_r102 as encode, decode_r102 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_102': '', 'qty_102': '-100000000000000000003', 'flag_102': 'OFF', 'mode_102': 'D102'}
    assert value == before
    assert result is not value
    value = {'v_102': '', 'qty_102': '-100000000000000000003', 'flag_102': 'OFF', 'mode_102': 'D102'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_102': '', 'qty_102': '0', 'flag_102': 'OFF', 'mode_102': 'H102'}
    assert decode({'v_102': '', 'qty_102': '0', 'flag_102': 'OFF', 'mode_102': 'H102'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
