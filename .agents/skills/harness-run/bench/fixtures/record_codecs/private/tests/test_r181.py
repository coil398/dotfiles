"""Spec: docs/SPEC.md §§2–5 and docs/group30.md#r181."""

def test_encode_normal():
    from record_codecs.group30 import encode_r181 as encode, decode_r181 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_181': '42', 'qty_181': 'yes', 'flag_181': 'R181', 'mode_181': 22}

def test_decode_normal():
    from record_codecs.group30 import encode_r181 as encode, decode_r181 as decode
    assert decode({'v_181': '42', 'qty_181': 'yes', 'flag_181': 'R181', 'mode_181': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group30 import encode_r181 as encode, decode_r181 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_181': 'yes', 'flag_181': 'R181', 'mode_181': 22}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_181': None, 'qty_181': 'yes', 'flag_181': 'R181', 'mode_181': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_181': '42', 'qty_181': 'no', 'flag_181': 'R181', 'mode_181': 22}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_181': '42', 'flag_181': 'R181', 'mode_181': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_181': '42', 'qty_181': 'yes', 'flag_181': 'R181'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_181': '42', 'qty_181': 'yes', 'flag_181': 'R181', 'mode_181': None}
    assert decode({'qty_181': 'yes', 'flag_181': 'R181', 'mode_181': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_181': None, 'qty_181': 'yes', 'flag_181': 'R181', 'mode_181': 22}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_181': '42', 'flag_181': 'R181', 'mode_181': 22}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_181': '42', 'qty_181': None, 'flag_181': 'R181', 'mode_181': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_181': '42', 'qty_181': 'yes', 'mode_181': 22})
    assert error.value.args == ('flag_181',)
    with pytest.raises(ValueError) as error:
        decode({'v_181': '42', 'qty_181': 'yes', 'flag_181': None, 'mode_181': 22})
    assert error.value.args == ('flag_181',)
    assert decode({'v_181': '42', 'qty_181': 'yes', 'flag_181': 'R181'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_181': '42', 'qty_181': 'yes', 'flag_181': 'R181', 'mode_181': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group30 import encode_r181 as encode, decode_r181 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_181': '-100000000000000000003', 'qty_181': 'no', 'flag_181': 'D181', 'mode_181': -34}
    assert value == before
    assert result is not value
    value = {'v_181': '-100000000000000000003', 'qty_181': 'no', 'flag_181': 'D181', 'mode_181': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_181': '0', 'qty_181': 'no', 'flag_181': 'H181', 'mode_181': 0}
    assert decode({'v_181': '0', 'qty_181': 'no', 'flag_181': 'H181', 'mode_181': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
