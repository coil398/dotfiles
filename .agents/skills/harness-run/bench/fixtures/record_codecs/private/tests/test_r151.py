"""Spec: docs/SPEC.md §§2–5 and docs/group25.md#r151."""

def test_encode_normal():
    from record_codecs.group25 import encode_r151 as encode, decode_r151 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_151': '42', 'qty_151': 'yes', 'flag_151': 'R151', 'mode_151': 110}

def test_decode_normal():
    from record_codecs.group25 import encode_r151 as encode, decode_r151 as decode
    assert decode({'v_151': '42', 'qty_151': 'yes', 'flag_151': 'R151', 'mode_151': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group25 import encode_r151 as encode, decode_r151 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_151': '-7', 'qty_151': 'yes', 'flag_151': 'R151', 'mode_151': 110}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_151': '42', 'qty_151': None, 'flag_151': 'R151', 'mode_151': 110}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_151': '42', 'qty_151': 'yes', 'mode_151': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_151': '42', 'qty_151': 'yes', 'mode_151': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_151': '42', 'qty_151': 'yes', 'flag_151': 'R151', 'mode_151': 30}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_151': 'yes', 'flag_151': 'R151', 'mode_151': 110}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_151': None, 'qty_151': 'yes', 'flag_151': 'R151', 'mode_151': 110})
    assert error.value.args == ('v_151',)
    with pytest.raises(KeyError) as error:
        decode({'v_151': '42', 'flag_151': 'R151', 'mode_151': 110})
    assert error.value.args == ('qty_151',)
    assert decode({'v_151': '42', 'qty_151': None, 'flag_151': 'R151', 'mode_151': 110}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_151': '42', 'qty_151': 'yes', 'mode_151': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_151': '42', 'qty_151': 'yes', 'flag_151': None, 'mode_151': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_151': '42', 'qty_151': 'yes', 'flag_151': 'R151'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_151': '42', 'qty_151': 'yes', 'flag_151': 'R151', 'mode_151': None})
    assert error.value.args == ('mode_151',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group25 import encode_r151 as encode, decode_r151 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_151': '-100000000000000000003', 'qty_151': 'no', 'flag_151': 'D151', 'mode_151': -170}
    assert value == before
    assert result is not value
    value = {'v_151': '-100000000000000000003', 'qty_151': 'no', 'flag_151': 'D151', 'mode_151': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_151': '0', 'qty_151': 'no', 'flag_151': 'H151', 'mode_151': 0}
    assert decode({'v_151': '0', 'qty_151': 'no', 'flag_151': 'H151', 'mode_151': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
