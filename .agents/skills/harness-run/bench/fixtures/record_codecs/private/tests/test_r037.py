"""Spec: docs/SPEC.md §§2–5 and docs/group06.md#r037."""

def test_encode_normal():
    from record_codecs.group06 import encode_r037 as encode, decode_r037 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_037': '42', 'qty_037': 'yes', 'flag_037': 'R37', 'mode_037': 22}

def test_decode_normal():
    from record_codecs.group06 import encode_r037 as encode, decode_r037 as decode
    assert decode({'v_037': '42', 'qty_037': 'yes', 'flag_037': 'R37', 'mode_037': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group06 import encode_r037 as encode, decode_r037 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_037': 'yes', 'flag_037': 'R37', 'mode_037': 22}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_037': None, 'qty_037': 'yes', 'flag_037': 'R37', 'mode_037': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_037': '42', 'qty_037': 'no', 'flag_037': 'R37', 'mode_037': 22}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_037': '42', 'flag_037': 'R37', 'mode_037': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_037': '42', 'qty_037': 'yes', 'flag_037': 'R37'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_037': '42', 'qty_037': 'yes', 'flag_037': 'R37', 'mode_037': None}
    assert decode({'qty_037': 'yes', 'flag_037': 'R37', 'mode_037': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_037': None, 'qty_037': 'yes', 'flag_037': 'R37', 'mode_037': 22}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_037': '42', 'flag_037': 'R37', 'mode_037': 22}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_037': '42', 'qty_037': None, 'flag_037': 'R37', 'mode_037': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_037': '42', 'qty_037': 'yes', 'mode_037': 22})
    assert error.value.args == ('flag_037',)
    with pytest.raises(ValueError) as error:
        decode({'v_037': '42', 'qty_037': 'yes', 'flag_037': None, 'mode_037': 22})
    assert error.value.args == ('flag_037',)
    assert decode({'v_037': '42', 'qty_037': 'yes', 'flag_037': 'R37'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_037': '42', 'qty_037': 'yes', 'flag_037': 'R37', 'mode_037': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group06 import encode_r037 as encode, decode_r037 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_037': '-100000000000000000003', 'qty_037': 'no', 'flag_037': 'D37', 'mode_037': -34}
    assert value == before
    assert result is not value
    value = {'v_037': '-100000000000000000003', 'qty_037': 'no', 'flag_037': 'D37', 'mode_037': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_037': '0', 'qty_037': 'no', 'flag_037': 'H37', 'mode_037': 0}
    assert decode({'v_037': '0', 'qty_037': 'no', 'flag_037': 'H37', 'mode_037': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
