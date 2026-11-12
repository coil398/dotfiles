"""Spec: docs/SPEC.md §§2–5 and docs/group15.md#r091."""

def test_encode_normal():
    from record_codecs.group15 import encode_r091 as encode, decode_r091 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_091': '42', 'qty_091': 'yes', 'flag_091': 'R91', 'mode_091': 110}

def test_decode_normal():
    from record_codecs.group15 import encode_r091 as encode, decode_r091 as decode
    assert decode({'v_091': '42', 'qty_091': 'yes', 'flag_091': 'R91', 'mode_091': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group15 import encode_r091 as encode, decode_r091 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_091': 'yes', 'flag_091': 'R91', 'mode_091': 110}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_091': None, 'qty_091': 'yes', 'flag_091': 'R91', 'mode_091': 110}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_091': '42', 'qty_091': 'no', 'flag_091': 'R91', 'mode_091': 110}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_091': '42', 'flag_091': 'R91', 'mode_091': 110}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_091': '42', 'qty_091': 'yes', 'flag_091': 'R91'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_091': '42', 'qty_091': 'yes', 'flag_091': 'R91', 'mode_091': None}
    assert decode({'qty_091': 'yes', 'flag_091': 'R91', 'mode_091': 110}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_091': None, 'qty_091': 'yes', 'flag_091': 'R91', 'mode_091': 110}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_091': '42', 'flag_091': 'R91', 'mode_091': 110}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_091': '42', 'qty_091': None, 'flag_091': 'R91', 'mode_091': 110}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_091': '42', 'qty_091': 'yes', 'mode_091': 110})
    assert error.value.args == ('flag_091',)
    with pytest.raises(ValueError) as error:
        decode({'v_091': '42', 'qty_091': 'yes', 'flag_091': None, 'mode_091': 110})
    assert error.value.args == ('flag_091',)
    assert decode({'v_091': '42', 'qty_091': 'yes', 'flag_091': 'R91'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_091': '42', 'qty_091': 'yes', 'flag_091': 'R91', 'mode_091': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group15 import encode_r091 as encode, decode_r091 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_091': '-100000000000000000003', 'qty_091': 'no', 'flag_091': 'D91', 'mode_091': -170}
    assert value == before
    assert result is not value
    value = {'v_091': '-100000000000000000003', 'qty_091': 'no', 'flag_091': 'D91', 'mode_091': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_091': '0', 'qty_091': 'no', 'flag_091': 'H91', 'mode_091': 0}
    assert decode({'v_091': '0', 'qty_091': 'no', 'flag_091': 'H91', 'mode_091': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
