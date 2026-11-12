"""Spec: docs/SPEC.md §§2–5 and docs/group02.md#r013."""

def test_encode_normal():
    from record_codecs.group02 import encode_r013 as encode, decode_r013 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_013': '42', 'qty_013': 'yes', 'flag_013': 'R13', 'mode_013': 22}

def test_decode_normal():
    from record_codecs.group02 import encode_r013 as encode, decode_r013 as decode
    assert decode({'v_013': '42', 'qty_013': 'yes', 'flag_013': 'R13', 'mode_013': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group02 import encode_r013 as encode, decode_r013 as decode
    with pytest.raises(KeyError) as error:
        encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_013': 'yes', 'flag_013': 'R13', 'mode_013': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_013': '42', 'flag_013': 'R13', 'mode_013': 22}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_013': '42', 'qty_013': 'yes', 'flag_013': 'H13', 'mode_013': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_013': '42', 'qty_013': 'yes', 'flag_013': None, 'mode_013': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'})
    assert error.value.args == ('amount_3',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_013': '42', 'qty_013': 'yes', 'flag_013': 'R13'}
    with pytest.raises(KeyError) as error:
        decode({'qty_013': 'yes', 'flag_013': 'R13', 'mode_013': 22})
    assert error.value.args == ('v_013',)
    assert decode({'v_013': None, 'qty_013': 'yes', 'flag_013': 'R13', 'mode_013': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_013': '42', 'flag_013': 'R13', 'mode_013': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_013': '42', 'qty_013': None, 'flag_013': 'R13', 'mode_013': 22})
    assert error.value.args == ('qty_013',)
    assert decode({'v_013': '42', 'qty_013': 'yes', 'mode_013': 22}) == {'count_0': 42, 'active_1': True, 'state_2': 'held', 'amount_3': 11}
    assert decode({'v_013': '42', 'qty_013': 'yes', 'flag_013': None, 'mode_013': 22}) == {'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_013': '42', 'qty_013': 'yes', 'flag_013': 'R13'})
    assert error.value.args == ('mode_013',)
    assert decode({'v_013': '42', 'qty_013': 'yes', 'flag_013': 'R13', 'mode_013': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group02 import encode_r013 as encode, decode_r013 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_013': '-100000000000000000003', 'qty_013': 'no', 'flag_013': 'D13', 'mode_013': -34}
    assert value == before
    assert result is not value
    value = {'v_013': '-100000000000000000003', 'qty_013': 'no', 'flag_013': 'D13', 'mode_013': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_013': '0', 'qty_013': 'no', 'flag_013': 'H13', 'mode_013': 0}
    assert decode({'v_013': '0', 'qty_013': 'no', 'flag_013': 'H13', 'mode_013': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
