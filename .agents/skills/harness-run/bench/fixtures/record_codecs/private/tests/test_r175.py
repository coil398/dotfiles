"""Spec: docs/SPEC.md §§2–5 and docs/group29.md#r175."""

def test_encode_normal():
    from record_codecs.group29 import encode_r175 as encode, decode_r175 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_175': '42', 'qty_175': 'yes', 'flag_175': 'R175', 'mode_175': 110}

def test_decode_normal():
    from record_codecs.group29 import encode_r175 as encode, decode_r175 as decode
    assert decode({'v_175': '42', 'qty_175': 'yes', 'flag_175': 'R175', 'mode_175': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group29 import encode_r175 as encode, decode_r175 as decode
    with pytest.raises(KeyError) as error:
        encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_175': 'yes', 'flag_175': 'R175', 'mode_175': 110}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_175': '42', 'flag_175': 'R175', 'mode_175': 110}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_175': '42', 'qty_175': 'yes', 'flag_175': 'H175', 'mode_175': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_175': '42', 'qty_175': 'yes', 'flag_175': None, 'mode_175': 110}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'})
    assert error.value.args == ('amount_3',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_175': '42', 'qty_175': 'yes', 'flag_175': 'R175'}
    with pytest.raises(KeyError) as error:
        decode({'qty_175': 'yes', 'flag_175': 'R175', 'mode_175': 110})
    assert error.value.args == ('v_175',)
    assert decode({'v_175': None, 'qty_175': 'yes', 'flag_175': 'R175', 'mode_175': 110}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_175': '42', 'flag_175': 'R175', 'mode_175': 110}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_175': '42', 'qty_175': None, 'flag_175': 'R175', 'mode_175': 110})
    assert error.value.args == ('qty_175',)
    assert decode({'v_175': '42', 'qty_175': 'yes', 'mode_175': 110}) == {'count_0': 42, 'active_1': True, 'state_2': 'held', 'amount_3': 11}
    assert decode({'v_175': '42', 'qty_175': 'yes', 'flag_175': None, 'mode_175': 110}) == {'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_175': '42', 'qty_175': 'yes', 'flag_175': 'R175'})
    assert error.value.args == ('mode_175',)
    assert decode({'v_175': '42', 'qty_175': 'yes', 'flag_175': 'R175', 'mode_175': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group29 import encode_r175 as encode, decode_r175 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_175': '-100000000000000000003', 'qty_175': 'no', 'flag_175': 'D175', 'mode_175': -170}
    assert value == before
    assert result is not value
    value = {'v_175': '-100000000000000000003', 'qty_175': 'no', 'flag_175': 'D175', 'mode_175': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_175': '0', 'qty_175': 'no', 'flag_175': 'H175', 'mode_175': 0}
    assert decode({'v_175': '0', 'qty_175': 'no', 'flag_175': 'H175', 'mode_175': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
