"""Spec: docs/SPEC.md §§2–5 and docs/group16.md#r097."""

def test_encode_normal():
    from record_codecs.group16 import encode_r097 as encode, decode_r097 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_097': '42', 'qty_097': 'yes', 'flag_097': 'R97', 'mode_097': 22}

def test_decode_normal():
    from record_codecs.group16 import encode_r097 as encode, decode_r097 as decode
    assert decode({'v_097': '42', 'qty_097': 'yes', 'flag_097': 'R97', 'mode_097': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group16 import encode_r097 as encode, decode_r097 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_097': '-7', 'qty_097': 'yes', 'flag_097': 'R97', 'mode_097': 22}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_097': '42', 'qty_097': None, 'flag_097': 'R97', 'mode_097': 22}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_097': '42', 'qty_097': 'yes', 'mode_097': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_097': '42', 'qty_097': 'yes', 'mode_097': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_097': '42', 'qty_097': 'yes', 'flag_097': 'R97', 'mode_097': 6}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_097': 'yes', 'flag_097': 'R97', 'mode_097': 22}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_097': None, 'qty_097': 'yes', 'flag_097': 'R97', 'mode_097': 22})
    assert error.value.args == ('v_097',)
    with pytest.raises(KeyError) as error:
        decode({'v_097': '42', 'flag_097': 'R97', 'mode_097': 22})
    assert error.value.args == ('qty_097',)
    assert decode({'v_097': '42', 'qty_097': None, 'flag_097': 'R97', 'mode_097': 22}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_097': '42', 'qty_097': 'yes', 'mode_097': 22}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_097': '42', 'qty_097': 'yes', 'flag_097': None, 'mode_097': 22}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_097': '42', 'qty_097': 'yes', 'flag_097': 'R97'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_097': '42', 'qty_097': 'yes', 'flag_097': 'R97', 'mode_097': None})
    assert error.value.args == ('mode_097',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group16 import encode_r097 as encode, decode_r097 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_097': '-100000000000000000003', 'qty_097': 'no', 'flag_097': 'D97', 'mode_097': -34}
    assert value == before
    assert result is not value
    value = {'v_097': '-100000000000000000003', 'qty_097': 'no', 'flag_097': 'D97', 'mode_097': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_097': '0', 'qty_097': 'no', 'flag_097': 'H97', 'mode_097': 0}
    assert decode({'v_097': '0', 'qty_097': 'no', 'flag_097': 'H97', 'mode_097': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
