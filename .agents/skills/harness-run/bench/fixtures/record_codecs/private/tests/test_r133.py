"""Spec: docs/SPEC.md §§2–5 and docs/group22.md#r133."""

def test_encode_normal():
    from record_codecs.group22 import encode_r133 as encode, decode_r133 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_133': '42', 'qty_133': 'yes', 'flag_133': 'R133', 'mode_133': 22}

def test_decode_normal():
    from record_codecs.group22 import encode_r133 as encode, decode_r133 as decode
    assert decode({'v_133': '42', 'qty_133': 'yes', 'flag_133': 'R133', 'mode_133': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group22 import encode_r133 as encode, decode_r133 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_133': '-7', 'qty_133': 'yes', 'flag_133': 'R133', 'mode_133': 22}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_133': '42', 'qty_133': None, 'flag_133': 'R133', 'mode_133': 22}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_133': '42', 'qty_133': 'yes', 'mode_133': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_133': '42', 'qty_133': 'yes', 'mode_133': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_133': '42', 'qty_133': 'yes', 'flag_133': 'R133', 'mode_133': 6}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_133': 'yes', 'flag_133': 'R133', 'mode_133': 22}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_133': None, 'qty_133': 'yes', 'flag_133': 'R133', 'mode_133': 22})
    assert error.value.args == ('v_133',)
    with pytest.raises(KeyError) as error:
        decode({'v_133': '42', 'flag_133': 'R133', 'mode_133': 22})
    assert error.value.args == ('qty_133',)
    assert decode({'v_133': '42', 'qty_133': None, 'flag_133': 'R133', 'mode_133': 22}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_133': '42', 'qty_133': 'yes', 'mode_133': 22}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_133': '42', 'qty_133': 'yes', 'flag_133': None, 'mode_133': 22}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_133': '42', 'qty_133': 'yes', 'flag_133': 'R133'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_133': '42', 'qty_133': 'yes', 'flag_133': 'R133', 'mode_133': None})
    assert error.value.args == ('mode_133',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group22 import encode_r133 as encode, decode_r133 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_133': '-100000000000000000003', 'qty_133': 'no', 'flag_133': 'D133', 'mode_133': -34}
    assert value == before
    assert result is not value
    value = {'v_133': '-100000000000000000003', 'qty_133': 'no', 'flag_133': 'D133', 'mode_133': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_133': '0', 'qty_133': 'no', 'flag_133': 'H133', 'mode_133': 0}
    assert decode({'v_133': '0', 'qty_133': 'no', 'flag_133': 'H133', 'mode_133': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
