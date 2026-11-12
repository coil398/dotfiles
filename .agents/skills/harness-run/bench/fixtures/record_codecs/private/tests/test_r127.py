"""Spec: docs/SPEC.md §§2–5 and docs/group21.md#r127."""

def test_encode_normal():
    from record_codecs.group21 import encode_r127 as encode, decode_r127 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_127': '42', 'qty_127': 'yes', 'flag_127': 'R127', 'mode_127': 110}

def test_decode_normal():
    from record_codecs.group21 import encode_r127 as encode, decode_r127 as decode
    assert decode({'v_127': '42', 'qty_127': 'yes', 'flag_127': 'R127', 'mode_127': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group21 import encode_r127 as encode, decode_r127 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_127': 'yes', 'flag_127': 'R127', 'mode_127': 110}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_127': None, 'qty_127': 'yes', 'flag_127': 'R127', 'mode_127': 110}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_127': '42', 'qty_127': 'no', 'flag_127': 'R127', 'mode_127': 110}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_127': '42', 'flag_127': 'R127', 'mode_127': 110}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_127': '42', 'qty_127': 'yes', 'flag_127': 'R127'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_127': '42', 'qty_127': 'yes', 'flag_127': 'R127', 'mode_127': None}
    assert decode({'qty_127': 'yes', 'flag_127': 'R127', 'mode_127': 110}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_127': None, 'qty_127': 'yes', 'flag_127': 'R127', 'mode_127': 110}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_127': '42', 'flag_127': 'R127', 'mode_127': 110}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_127': '42', 'qty_127': None, 'flag_127': 'R127', 'mode_127': 110}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_127': '42', 'qty_127': 'yes', 'mode_127': 110})
    assert error.value.args == ('flag_127',)
    with pytest.raises(ValueError) as error:
        decode({'v_127': '42', 'qty_127': 'yes', 'flag_127': None, 'mode_127': 110})
    assert error.value.args == ('flag_127',)
    assert decode({'v_127': '42', 'qty_127': 'yes', 'flag_127': 'R127'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_127': '42', 'qty_127': 'yes', 'flag_127': 'R127', 'mode_127': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group21 import encode_r127 as encode, decode_r127 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_127': '-100000000000000000003', 'qty_127': 'no', 'flag_127': 'D127', 'mode_127': -170}
    assert value == before
    assert result is not value
    value = {'v_127': '-100000000000000000003', 'qty_127': 'no', 'flag_127': 'D127', 'mode_127': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_127': '0', 'qty_127': 'no', 'flag_127': 'H127', 'mode_127': 0}
    assert decode({'v_127': '0', 'qty_127': 'no', 'flag_127': 'H127', 'mode_127': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
