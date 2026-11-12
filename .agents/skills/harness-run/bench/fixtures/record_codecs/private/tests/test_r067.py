"""Spec: docs/SPEC.md §§2–5 and docs/group11.md#r067."""

def test_encode_normal():
    from record_codecs.group11 import encode_r067 as encode, decode_r067 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_067': '42', 'qty_067': 'yes', 'flag_067': 'R67', 'mode_067': 110}

def test_decode_normal():
    from record_codecs.group11 import encode_r067 as encode, decode_r067 as decode
    assert decode({'v_067': '42', 'qty_067': 'yes', 'flag_067': 'R67', 'mode_067': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group11 import encode_r067 as encode, decode_r067 as decode
    with pytest.raises(KeyError) as error:
        encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_067': 'yes', 'flag_067': 'R67', 'mode_067': 110}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_067': '42', 'flag_067': 'R67', 'mode_067': 110}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_067': '42', 'qty_067': 'yes', 'flag_067': 'H67', 'mode_067': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_067': '42', 'qty_067': 'yes', 'flag_067': None, 'mode_067': 110}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'})
    assert error.value.args == ('amount_3',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_067': '42', 'qty_067': 'yes', 'flag_067': 'R67'}
    with pytest.raises(KeyError) as error:
        decode({'qty_067': 'yes', 'flag_067': 'R67', 'mode_067': 110})
    assert error.value.args == ('v_067',)
    assert decode({'v_067': None, 'qty_067': 'yes', 'flag_067': 'R67', 'mode_067': 110}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_067': '42', 'flag_067': 'R67', 'mode_067': 110}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_067': '42', 'qty_067': None, 'flag_067': 'R67', 'mode_067': 110})
    assert error.value.args == ('qty_067',)
    assert decode({'v_067': '42', 'qty_067': 'yes', 'mode_067': 110}) == {'count_0': 42, 'active_1': True, 'state_2': 'held', 'amount_3': 11}
    assert decode({'v_067': '42', 'qty_067': 'yes', 'flag_067': None, 'mode_067': 110}) == {'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_067': '42', 'qty_067': 'yes', 'flag_067': 'R67'})
    assert error.value.args == ('mode_067',)
    assert decode({'v_067': '42', 'qty_067': 'yes', 'flag_067': 'R67', 'mode_067': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group11 import encode_r067 as encode, decode_r067 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_067': '-100000000000000000003', 'qty_067': 'no', 'flag_067': 'D67', 'mode_067': -170}
    assert value == before
    assert result is not value
    value = {'v_067': '-100000000000000000003', 'qty_067': 'no', 'flag_067': 'D67', 'mode_067': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_067': '0', 'qty_067': 'no', 'flag_067': 'H67', 'mode_067': 0}
    assert decode({'v_067': '0', 'qty_067': 'no', 'flag_067': 'H67', 'mode_067': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
