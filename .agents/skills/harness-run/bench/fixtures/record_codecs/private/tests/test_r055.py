"""Spec: docs/SPEC.md §§2–5 and docs/group09.md#r055."""

def test_encode_normal():
    from record_codecs.group09 import encode_r055 as encode, decode_r055 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_055': '42', 'qty_055': 'yes', 'flag_055': 'R55', 'mode_055': 110}

def test_decode_normal():
    from record_codecs.group09 import encode_r055 as encode, decode_r055 as decode
    assert decode({'v_055': '42', 'qty_055': 'yes', 'flag_055': 'R55', 'mode_055': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group09 import encode_r055 as encode, decode_r055 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_055': 'yes', 'flag_055': 'R55', 'mode_055': 110}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_055': None, 'qty_055': 'yes', 'flag_055': 'R55', 'mode_055': 110}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_055': '42', 'qty_055': 'no', 'flag_055': 'R55', 'mode_055': 110}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_055': '42', 'flag_055': 'R55', 'mode_055': 110}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_055': '42', 'qty_055': 'yes', 'flag_055': 'R55'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_055': '42', 'qty_055': 'yes', 'flag_055': 'R55', 'mode_055': None}
    assert decode({'qty_055': 'yes', 'flag_055': 'R55', 'mode_055': 110}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_055': None, 'qty_055': 'yes', 'flag_055': 'R55', 'mode_055': 110}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_055': '42', 'flag_055': 'R55', 'mode_055': 110}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_055': '42', 'qty_055': None, 'flag_055': 'R55', 'mode_055': 110}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_055': '42', 'qty_055': 'yes', 'mode_055': 110})
    assert error.value.args == ('flag_055',)
    with pytest.raises(ValueError) as error:
        decode({'v_055': '42', 'qty_055': 'yes', 'flag_055': None, 'mode_055': 110})
    assert error.value.args == ('flag_055',)
    assert decode({'v_055': '42', 'qty_055': 'yes', 'flag_055': 'R55'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_055': '42', 'qty_055': 'yes', 'flag_055': 'R55', 'mode_055': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group09 import encode_r055 as encode, decode_r055 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_055': '-100000000000000000003', 'qty_055': 'no', 'flag_055': 'D55', 'mode_055': -170}
    assert value == before
    assert result is not value
    value = {'v_055': '-100000000000000000003', 'qty_055': 'no', 'flag_055': 'D55', 'mode_055': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_055': '0', 'qty_055': 'no', 'flag_055': 'H55', 'mode_055': 0}
    assert decode({'v_055': '0', 'qty_055': 'no', 'flag_055': 'H55', 'mode_055': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
