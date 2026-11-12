"""Spec: docs/SPEC.md §§2–5 and docs/group01.md#r007."""

def test_encode_normal():
    from record_codecs.group01 import encode_r007 as encode, decode_r007 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_007': '42', 'qty_007': 'yes', 'flag_007': 'R7', 'mode_007': 110}

def test_decode_normal():
    from record_codecs.group01 import encode_r007 as encode, decode_r007 as decode
    assert decode({'v_007': '42', 'qty_007': 'yes', 'flag_007': 'R7', 'mode_007': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group01 import encode_r007 as encode, decode_r007 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_007': '-7', 'qty_007': 'yes', 'flag_007': 'R7', 'mode_007': 110}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_007': '42', 'qty_007': None, 'flag_007': 'R7', 'mode_007': 110}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_007': '42', 'qty_007': 'yes', 'mode_007': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_007': '42', 'qty_007': 'yes', 'mode_007': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_007': '42', 'qty_007': 'yes', 'flag_007': 'R7', 'mode_007': 30}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_007': 'yes', 'flag_007': 'R7', 'mode_007': 110}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_007': None, 'qty_007': 'yes', 'flag_007': 'R7', 'mode_007': 110})
    assert error.value.args == ('v_007',)
    with pytest.raises(KeyError) as error:
        decode({'v_007': '42', 'flag_007': 'R7', 'mode_007': 110})
    assert error.value.args == ('qty_007',)
    assert decode({'v_007': '42', 'qty_007': None, 'flag_007': 'R7', 'mode_007': 110}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_007': '42', 'qty_007': 'yes', 'mode_007': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_007': '42', 'qty_007': 'yes', 'flag_007': None, 'mode_007': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_007': '42', 'qty_007': 'yes', 'flag_007': 'R7'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_007': '42', 'qty_007': 'yes', 'flag_007': 'R7', 'mode_007': None})
    assert error.value.args == ('mode_007',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group01 import encode_r007 as encode, decode_r007 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_007': '-100000000000000000003', 'qty_007': 'no', 'flag_007': 'D7', 'mode_007': -170}
    assert value == before
    assert result is not value
    value = {'v_007': '-100000000000000000003', 'qty_007': 'no', 'flag_007': 'D7', 'mode_007': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_007': '0', 'qty_007': 'no', 'flag_007': 'H7', 'mode_007': 0}
    assert decode({'v_007': '0', 'qty_007': 'no', 'flag_007': 'H7', 'mode_007': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
