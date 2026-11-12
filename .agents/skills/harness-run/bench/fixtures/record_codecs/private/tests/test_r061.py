"""Spec: docs/SPEC.md §§2–5 and docs/group10.md#r061."""

def test_encode_normal():
    from record_codecs.group10 import encode_r061 as encode, decode_r061 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_061': '42', 'qty_061': 'yes', 'flag_061': 'R61', 'mode_061': 22}

def test_decode_normal():
    from record_codecs.group10 import encode_r061 as encode, decode_r061 as decode
    assert decode({'v_061': '42', 'qty_061': 'yes', 'flag_061': 'R61', 'mode_061': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group10 import encode_r061 as encode, decode_r061 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_061': '-7', 'qty_061': 'yes', 'flag_061': 'R61', 'mode_061': 22}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_061': '42', 'qty_061': None, 'flag_061': 'R61', 'mode_061': 22}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_061': '42', 'qty_061': 'yes', 'mode_061': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_061': '42', 'qty_061': 'yes', 'mode_061': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_061': '42', 'qty_061': 'yes', 'flag_061': 'R61', 'mode_061': 6}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_061': 'yes', 'flag_061': 'R61', 'mode_061': 22}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_061': None, 'qty_061': 'yes', 'flag_061': 'R61', 'mode_061': 22})
    assert error.value.args == ('v_061',)
    with pytest.raises(KeyError) as error:
        decode({'v_061': '42', 'flag_061': 'R61', 'mode_061': 22})
    assert error.value.args == ('qty_061',)
    assert decode({'v_061': '42', 'qty_061': None, 'flag_061': 'R61', 'mode_061': 22}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_061': '42', 'qty_061': 'yes', 'mode_061': 22}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_061': '42', 'qty_061': 'yes', 'flag_061': None, 'mode_061': 22}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_061': '42', 'qty_061': 'yes', 'flag_061': 'R61'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_061': '42', 'qty_061': 'yes', 'flag_061': 'R61', 'mode_061': None})
    assert error.value.args == ('mode_061',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group10 import encode_r061 as encode, decode_r061 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_061': '-100000000000000000003', 'qty_061': 'no', 'flag_061': 'D61', 'mode_061': -34}
    assert value == before
    assert result is not value
    value = {'v_061': '-100000000000000000003', 'qty_061': 'no', 'flag_061': 'D61', 'mode_061': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_061': '0', 'qty_061': 'no', 'flag_061': 'H61', 'mode_061': 0}
    assert decode({'v_061': '0', 'qty_061': 'no', 'flag_061': 'H61', 'mode_061': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
