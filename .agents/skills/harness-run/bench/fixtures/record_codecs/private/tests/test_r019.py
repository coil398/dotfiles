"""Spec: docs/SPEC.md §§2–5 and docs/group03.md#r019."""

def test_encode_normal():
    from record_codecs.group03 import encode_r019 as encode, decode_r019 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_019': '42', 'qty_019': 'yes', 'flag_019': 'R19', 'mode_019': 110}

def test_decode_normal():
    from record_codecs.group03 import encode_r019 as encode, decode_r019 as decode
    assert decode({'v_019': '42', 'qty_019': 'yes', 'flag_019': 'R19', 'mode_019': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group03 import encode_r019 as encode, decode_r019 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_019': 'yes', 'flag_019': 'R19', 'mode_019': 110}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_019': None, 'qty_019': 'yes', 'flag_019': 'R19', 'mode_019': 110}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_019': '42', 'qty_019': 'no', 'flag_019': 'R19', 'mode_019': 110}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_019': '42', 'flag_019': 'R19', 'mode_019': 110}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_019': '42', 'qty_019': 'yes', 'flag_019': 'R19'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_019': '42', 'qty_019': 'yes', 'flag_019': 'R19', 'mode_019': None}
    assert decode({'qty_019': 'yes', 'flag_019': 'R19', 'mode_019': 110}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_019': None, 'qty_019': 'yes', 'flag_019': 'R19', 'mode_019': 110}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_019': '42', 'flag_019': 'R19', 'mode_019': 110}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_019': '42', 'qty_019': None, 'flag_019': 'R19', 'mode_019': 110}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_019': '42', 'qty_019': 'yes', 'mode_019': 110})
    assert error.value.args == ('flag_019',)
    with pytest.raises(ValueError) as error:
        decode({'v_019': '42', 'qty_019': 'yes', 'flag_019': None, 'mode_019': 110})
    assert error.value.args == ('flag_019',)
    assert decode({'v_019': '42', 'qty_019': 'yes', 'flag_019': 'R19'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_019': '42', 'qty_019': 'yes', 'flag_019': 'R19', 'mode_019': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group03 import encode_r019 as encode, decode_r019 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_019': '-100000000000000000003', 'qty_019': 'no', 'flag_019': 'D19', 'mode_019': -170}
    assert value == before
    assert result is not value
    value = {'v_019': '-100000000000000000003', 'qty_019': 'no', 'flag_019': 'D19', 'mode_019': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_019': '0', 'qty_019': 'no', 'flag_019': 'H19', 'mode_019': 0}
    assert decode({'v_019': '0', 'qty_019': 'no', 'flag_019': 'H19', 'mode_019': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
