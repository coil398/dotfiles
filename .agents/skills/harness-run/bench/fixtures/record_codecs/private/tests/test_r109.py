"""Spec: docs/SPEC.md §§2–5 and docs/group18.md#r109."""

def test_encode_normal():
    from record_codecs.group18 import encode_r109 as encode, decode_r109 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_109': '42', 'qty_109': 'yes', 'flag_109': 'R109', 'mode_109': 22}

def test_decode_normal():
    from record_codecs.group18 import encode_r109 as encode, decode_r109 as decode
    assert decode({'v_109': '42', 'qty_109': 'yes', 'flag_109': 'R109', 'mode_109': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group18 import encode_r109 as encode, decode_r109 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_109': 'yes', 'flag_109': 'R109', 'mode_109': 22}
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_109': None, 'qty_109': 'yes', 'flag_109': 'R109', 'mode_109': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_109': '42', 'qty_109': 'no', 'flag_109': 'R109', 'mode_109': 22}
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_109': '42', 'flag_109': 'R109', 'mode_109': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11})
    assert error.value.args == ('state_2',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_109': '42', 'qty_109': 'yes', 'flag_109': 'R109'}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_109': '42', 'qty_109': 'yes', 'flag_109': 'R109', 'mode_109': None}
    assert decode({'qty_109': 'yes', 'flag_109': 'R109', 'mode_109': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_109': None, 'qty_109': 'yes', 'flag_109': 'R109', 'mode_109': 22}) == {'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_109': '42', 'flag_109': 'R109', 'mode_109': 22}) == {'count_0': 42, 'active_1': False, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_109': '42', 'qty_109': None, 'flag_109': 'R109', 'mode_109': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_109': '42', 'qty_109': 'yes', 'mode_109': 22})
    assert error.value.args == ('flag_109',)
    with pytest.raises(ValueError) as error:
        decode({'v_109': '42', 'qty_109': 'yes', 'flag_109': None, 'mode_109': 22})
    assert error.value.args == ('flag_109',)
    assert decode({'v_109': '42', 'qty_109': 'yes', 'flag_109': 'R109'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}
    assert decode({'v_109': '42', 'qty_109': 'yes', 'flag_109': 'R109', 'mode_109': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group18 import encode_r109 as encode, decode_r109 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_109': '-100000000000000000003', 'qty_109': 'no', 'flag_109': 'D109', 'mode_109': -34}
    assert value == before
    assert result is not value
    value = {'v_109': '-100000000000000000003', 'qty_109': 'no', 'flag_109': 'D109', 'mode_109': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_109': '0', 'qty_109': 'no', 'flag_109': 'H109', 'mode_109': 0}
    assert decode({'v_109': '0', 'qty_109': 'no', 'flag_109': 'H109', 'mode_109': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
