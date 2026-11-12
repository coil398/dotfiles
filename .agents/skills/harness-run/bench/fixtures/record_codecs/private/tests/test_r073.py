"""Spec: docs/SPEC.md §§2–5 and docs/group12.md#r073."""

def test_encode_normal():
    from record_codecs.group12 import encode_r073 as encode, decode_r073 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_073': '42', 'qty_073': 'yes', 'flag_073': 'R73', 'mode_073': 22}

def test_decode_normal():
    from record_codecs.group12 import encode_r073 as encode, decode_r073 as decode
    assert decode({'v_073': '42', 'qty_073': 'yes', 'flag_073': 'R73', 'mode_073': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group12 import encode_r073 as encode, decode_r073 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_073': 'yes', 'flag_073': 'R73', 'mode_073': 22}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_073': None, 'qty_073': 'yes', 'flag_073': 'R73', 'mode_073': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_073': '42', 'qty_073': 'no', 'flag_073': 'R73', 'mode_073': 22}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_073': '42', 'flag_073': 'R73', 'mode_073': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_073': '42', 'qty_073': 'yes', 'flag_073': 'R73'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_073': '42', 'qty_073': 'yes', 'flag_073': 'R73', 'mode_073': None}
    assert decode({'qty_073': 'yes', 'flag_073': 'R73', 'mode_073': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_073': None, 'qty_073': 'yes', 'flag_073': 'R73', 'mode_073': 22}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_073': '42', 'flag_073': 'R73', 'mode_073': 22}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_073': '42', 'qty_073': None, 'flag_073': 'R73', 'mode_073': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_073': '42', 'qty_073': 'yes', 'mode_073': 22})
    assert error.value.args == ('flag_073',)
    with pytest.raises(ValueError) as error:
        decode({'v_073': '42', 'qty_073': 'yes', 'flag_073': None, 'mode_073': 22})
    assert error.value.args == ('flag_073',)
    assert decode({'v_073': '42', 'qty_073': 'yes', 'flag_073': 'R73'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_073': '42', 'qty_073': 'yes', 'flag_073': 'R73', 'mode_073': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group12 import encode_r073 as encode, decode_r073 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_073': '-100000000000000000003', 'qty_073': 'no', 'flag_073': 'D73', 'mode_073': -34}
    assert value == before
    assert result is not value
    value = {'v_073': '-100000000000000000003', 'qty_073': 'no', 'flag_073': 'D73', 'mode_073': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_073': '0', 'qty_073': 'no', 'flag_073': 'H73', 'mode_073': 0}
    assert decode({'v_073': '0', 'qty_073': 'no', 'flag_073': 'H73', 'mode_073': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
