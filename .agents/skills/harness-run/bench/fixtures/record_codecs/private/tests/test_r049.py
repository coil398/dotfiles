"""Spec: docs/SPEC.md §§2–5 and docs/group08.md#r049."""

def test_encode_normal():
    from record_codecs.group08 import encode_r049 as encode, decode_r049 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_049': '42', 'qty_049': 'yes', 'flag_049': 'R49', 'mode_049': 22}

def test_decode_normal():
    from record_codecs.group08 import encode_r049 as encode, decode_r049 as decode
    assert decode({'v_049': '42', 'qty_049': 'yes', 'flag_049': 'R49', 'mode_049': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group08 import encode_r049 as encode, decode_r049 as decode
    with pytest.raises(KeyError) as error:
        encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_049': 'yes', 'flag_049': 'R49', 'mode_049': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_049': '42', 'flag_049': 'R49', 'mode_049': 22}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_049': '42', 'qty_049': 'yes', 'flag_049': 'H49', 'mode_049': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_049': '42', 'qty_049': 'yes', 'flag_049': None, 'mode_049': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'})
    assert error.value.args == ('amount_3',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_049': '42', 'qty_049': 'yes', 'flag_049': 'R49'}
    with pytest.raises(KeyError) as error:
        decode({'qty_049': 'yes', 'flag_049': 'R49', 'mode_049': 22})
    assert error.value.args == ('v_049',)
    assert decode({'v_049': None, 'qty_049': 'yes', 'flag_049': 'R49', 'mode_049': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_049': '42', 'flag_049': 'R49', 'mode_049': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_049': '42', 'qty_049': None, 'flag_049': 'R49', 'mode_049': 22})
    assert error.value.args == ('qty_049',)
    assert decode({'v_049': '42', 'qty_049': 'yes', 'mode_049': 22}) == {'count_0': 42, 'active_1': True, 'state_2': 'held', 'amount_3': 11}
    assert decode({'v_049': '42', 'qty_049': 'yes', 'flag_049': None, 'mode_049': 22}) == {'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_049': '42', 'qty_049': 'yes', 'flag_049': 'R49'})
    assert error.value.args == ('mode_049',)
    assert decode({'v_049': '42', 'qty_049': 'yes', 'flag_049': 'R49', 'mode_049': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group08 import encode_r049 as encode, decode_r049 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_049': '-100000000000000000003', 'qty_049': 'no', 'flag_049': 'D49', 'mode_049': -34}
    assert value == before
    assert result is not value
    value = {'v_049': '-100000000000000000003', 'qty_049': 'no', 'flag_049': 'D49', 'mode_049': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_049': '0', 'qty_049': 'no', 'flag_049': 'H49', 'mode_049': 0}
    assert decode({'v_049': '0', 'qty_049': 'no', 'flag_049': 'H49', 'mode_049': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
