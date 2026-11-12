"""Spec: docs/SPEC.md §§2–5 and docs/group28.md#r169."""

def test_encode_normal():
    from record_codecs.group28 import encode_r169 as encode, decode_r169 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_169': '42', 'qty_169': 'yes', 'flag_169': 'R169', 'mode_169': 22}

def test_decode_normal():
    from record_codecs.group28 import encode_r169 as encode, decode_r169 as decode
    assert decode({'v_169': '42', 'qty_169': 'yes', 'flag_169': 'R169', 'mode_169': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group28 import encode_r169 as encode, decode_r169 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_169': '-7', 'qty_169': 'yes', 'flag_169': 'R169', 'mode_169': 22}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_169': '42', 'qty_169': None, 'flag_169': 'R169', 'mode_169': 22}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_169': '42', 'qty_169': 'yes', 'mode_169': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_169': '42', 'qty_169': 'yes', 'mode_169': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_169': '42', 'qty_169': 'yes', 'flag_169': 'R169', 'mode_169': 6}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_169': 'yes', 'flag_169': 'R169', 'mode_169': 22}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_169': None, 'qty_169': 'yes', 'flag_169': 'R169', 'mode_169': 22})
    assert error.value.args == ('v_169',)
    with pytest.raises(KeyError) as error:
        decode({'v_169': '42', 'flag_169': 'R169', 'mode_169': 22})
    assert error.value.args == ('qty_169',)
    assert decode({'v_169': '42', 'qty_169': None, 'flag_169': 'R169', 'mode_169': 22}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_169': '42', 'qty_169': 'yes', 'mode_169': 22}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_169': '42', 'qty_169': 'yes', 'flag_169': None, 'mode_169': 22}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_169': '42', 'qty_169': 'yes', 'flag_169': 'R169'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_169': '42', 'qty_169': 'yes', 'flag_169': 'R169', 'mode_169': None})
    assert error.value.args == ('mode_169',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group28 import encode_r169 as encode, decode_r169 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_169': '-100000000000000000003', 'qty_169': 'no', 'flag_169': 'D169', 'mode_169': -34}
    assert value == before
    assert result is not value
    value = {'v_169': '-100000000000000000003', 'qty_169': 'no', 'flag_169': 'D169', 'mode_169': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_169': '0', 'qty_169': 'no', 'flag_169': 'H169', 'mode_169': 0}
    assert decode({'v_169': '0', 'qty_169': 'no', 'flag_169': 'H169', 'mode_169': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
