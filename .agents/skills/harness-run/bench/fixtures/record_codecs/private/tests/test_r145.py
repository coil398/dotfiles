"""Spec: docs/SPEC.md §§2–5 and docs/group24.md#r145."""

def test_encode_normal():
    from record_codecs.group24 import encode_r145 as encode, decode_r145 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_145': '42', 'qty_145': 'yes', 'flag_145': 'R145', 'mode_145': 22}

def test_decode_normal():
    from record_codecs.group24 import encode_r145 as encode, decode_r145 as decode
    assert decode({'v_145': '42', 'qty_145': 'yes', 'flag_145': 'R145', 'mode_145': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group24 import encode_r145 as encode, decode_r145 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_145': 'yes', 'flag_145': 'R145', 'mode_145': 22}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_145': None, 'qty_145': 'yes', 'flag_145': 'R145', 'mode_145': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_145': '42', 'qty_145': 'no', 'flag_145': 'R145', 'mode_145': 22}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_145': '42', 'flag_145': 'R145', 'mode_145': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_145': '42', 'qty_145': 'yes', 'flag_145': 'R145'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_145': '42', 'qty_145': 'yes', 'flag_145': 'R145', 'mode_145': None}
    assert decode({'qty_145': 'yes', 'flag_145': 'R145', 'mode_145': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_145': None, 'qty_145': 'yes', 'flag_145': 'R145', 'mode_145': 22}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_145': '42', 'flag_145': 'R145', 'mode_145': 22}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_145': '42', 'qty_145': None, 'flag_145': 'R145', 'mode_145': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_145': '42', 'qty_145': 'yes', 'mode_145': 22})
    assert error.value.args == ('flag_145',)
    with pytest.raises(ValueError) as error:
        decode({'v_145': '42', 'qty_145': 'yes', 'flag_145': None, 'mode_145': 22})
    assert error.value.args == ('flag_145',)
    assert decode({'v_145': '42', 'qty_145': 'yes', 'flag_145': 'R145'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_145': '42', 'qty_145': 'yes', 'flag_145': 'R145', 'mode_145': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group24 import encode_r145 as encode, decode_r145 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_145': '-100000000000000000003', 'qty_145': 'no', 'flag_145': 'D145', 'mode_145': -34}
    assert value == before
    assert result is not value
    value = {'v_145': '-100000000000000000003', 'qty_145': 'no', 'flag_145': 'D145', 'mode_145': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_145': '0', 'qty_145': 'no', 'flag_145': 'H145', 'mode_145': 0}
    assert decode({'v_145': '0', 'qty_145': 'no', 'flag_145': 'H145', 'mode_145': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
