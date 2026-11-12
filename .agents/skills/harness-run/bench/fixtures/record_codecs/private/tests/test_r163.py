"""Spec: docs/SPEC.md §§2–5 and docs/group27.md#r163."""

def test_encode_normal():
    from record_codecs.group27 import encode_r163 as encode, decode_r163 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_163': '42', 'qty_163': 'yes', 'flag_163': 'R163', 'mode_163': 110}

def test_decode_normal():
    from record_codecs.group27 import encode_r163 as encode, decode_r163 as decode
    assert decode({'v_163': '42', 'qty_163': 'yes', 'flag_163': 'R163', 'mode_163': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group27 import encode_r163 as encode, decode_r163 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_163': 'yes', 'flag_163': 'R163', 'mode_163': 110}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_163': None, 'qty_163': 'yes', 'flag_163': 'R163', 'mode_163': 110}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_163': '42', 'qty_163': 'no', 'flag_163': 'R163', 'mode_163': 110}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_163': '42', 'flag_163': 'R163', 'mode_163': 110}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_163': '42', 'qty_163': 'yes', 'flag_163': 'R163'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_163': '42', 'qty_163': 'yes', 'flag_163': 'R163', 'mode_163': None}
    assert decode({'qty_163': 'yes', 'flag_163': 'R163', 'mode_163': 110}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_163': None, 'qty_163': 'yes', 'flag_163': 'R163', 'mode_163': 110}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_163': '42', 'flag_163': 'R163', 'mode_163': 110}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_163': '42', 'qty_163': None, 'flag_163': 'R163', 'mode_163': 110}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_163': '42', 'qty_163': 'yes', 'mode_163': 110})
    assert error.value.args == ('flag_163',)
    with pytest.raises(ValueError) as error:
        decode({'v_163': '42', 'qty_163': 'yes', 'flag_163': None, 'mode_163': 110})
    assert error.value.args == ('flag_163',)
    assert decode({'v_163': '42', 'qty_163': 'yes', 'flag_163': 'R163'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_163': '42', 'qty_163': 'yes', 'flag_163': 'R163', 'mode_163': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group27 import encode_r163 as encode, decode_r163 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_163': '-100000000000000000003', 'qty_163': 'no', 'flag_163': 'D163', 'mode_163': -170}
    assert value == before
    assert result is not value
    value = {'v_163': '-100000000000000000003', 'qty_163': 'no', 'flag_163': 'D163', 'mode_163': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_163': '0', 'qty_163': 'no', 'flag_163': 'H163', 'mode_163': 0}
    assert decode({'v_163': '0', 'qty_163': 'no', 'flag_163': 'H163', 'mode_163': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
