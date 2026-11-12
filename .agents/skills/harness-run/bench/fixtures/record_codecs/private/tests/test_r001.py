"""Spec: docs/SPEC.md §§2–5 and docs/group00.md#r001."""

def test_encode_normal():
    from record_codecs.group00 import encode_r001 as encode, decode_r001 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_001': '42', 'qty_001': 'yes', 'flag_001': 'R1', 'mode_001': 22}

def test_decode_normal():
    from record_codecs.group00 import encode_r001 as encode, decode_r001 as decode
    assert decode({'v_001': '42', 'qty_001': 'yes', 'flag_001': 'R1', 'mode_001': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group00 import encode_r001 as encode, decode_r001 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_001': 'yes', 'flag_001': 'R1', 'mode_001': 22}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_001': None, 'qty_001': 'yes', 'flag_001': 'R1', 'mode_001': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_001': '42', 'qty_001': 'no', 'flag_001': 'R1', 'mode_001': 22}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_001': '42', 'flag_001': 'R1', 'mode_001': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_001': '42', 'qty_001': 'yes', 'flag_001': 'R1'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_001': '42', 'qty_001': 'yes', 'flag_001': 'R1', 'mode_001': None}
    assert decode({'qty_001': 'yes', 'flag_001': 'R1', 'mode_001': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_001': None, 'qty_001': 'yes', 'flag_001': 'R1', 'mode_001': 22}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_001': '42', 'flag_001': 'R1', 'mode_001': 22}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_001': '42', 'qty_001': None, 'flag_001': 'R1', 'mode_001': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_001': '42', 'qty_001': 'yes', 'mode_001': 22})
    assert error.value.args == ('flag_001',)
    with pytest.raises(ValueError) as error:
        decode({'v_001': '42', 'qty_001': 'yes', 'flag_001': None, 'mode_001': 22})
    assert error.value.args == ('flag_001',)
    assert decode({'v_001': '42', 'qty_001': 'yes', 'flag_001': 'R1'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_001': '42', 'qty_001': 'yes', 'flag_001': 'R1', 'mode_001': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group00 import encode_r001 as encode, decode_r001 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_001': '-100000000000000000003', 'qty_001': 'no', 'flag_001': 'D1', 'mode_001': -34}
    assert value == before
    assert result is not value
    value = {'v_001': '-100000000000000000003', 'qty_001': 'no', 'flag_001': 'D1', 'mode_001': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_001': '0', 'qty_001': 'no', 'flag_001': 'H1', 'mode_001': 0}
    assert decode({'v_001': '0', 'qty_001': 'no', 'flag_001': 'H1', 'mode_001': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
