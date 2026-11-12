"""Spec: docs/SPEC.md §§2–5 and docs/group20.md#r121."""

def test_encode_normal():
    from record_codecs.group20 import encode_r121 as encode, decode_r121 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_121': '42', 'qty_121': 'yes', 'flag_121': 'R121', 'mode_121': 22}

def test_decode_normal():
    from record_codecs.group20 import encode_r121 as encode, decode_r121 as decode
    assert decode({'v_121': '42', 'qty_121': 'yes', 'flag_121': 'R121', 'mode_121': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group20 import encode_r121 as encode, decode_r121 as decode
    with pytest.raises(KeyError) as error:
        encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_121': 'yes', 'flag_121': 'R121', 'mode_121': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_121': '42', 'flag_121': 'R121', 'mode_121': 22}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_121': '42', 'qty_121': 'yes', 'flag_121': 'H121', 'mode_121': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_121': '42', 'qty_121': 'yes', 'flag_121': None, 'mode_121': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'})
    assert error.value.args == ('amount_3',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_121': '42', 'qty_121': 'yes', 'flag_121': 'R121'}
    with pytest.raises(KeyError) as error:
        decode({'qty_121': 'yes', 'flag_121': 'R121', 'mode_121': 22})
    assert error.value.args == ('v_121',)
    assert decode({'v_121': None, 'qty_121': 'yes', 'flag_121': 'R121', 'mode_121': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_121': '42', 'flag_121': 'R121', 'mode_121': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_121': '42', 'qty_121': None, 'flag_121': 'R121', 'mode_121': 22})
    assert error.value.args == ('qty_121',)
    assert decode({'v_121': '42', 'qty_121': 'yes', 'mode_121': 22}) == {'count_0': 42, 'active_1': True, 'state_2': 'held', 'amount_3': 11}
    assert decode({'v_121': '42', 'qty_121': 'yes', 'flag_121': None, 'mode_121': 22}) == {'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_121': '42', 'qty_121': 'yes', 'flag_121': 'R121'})
    assert error.value.args == ('mode_121',)
    assert decode({'v_121': '42', 'qty_121': 'yes', 'flag_121': 'R121', 'mode_121': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group20 import encode_r121 as encode, decode_r121 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_121': '-100000000000000000003', 'qty_121': 'no', 'flag_121': 'D121', 'mode_121': -34}
    assert value == before
    assert result is not value
    value = {'v_121': '-100000000000000000003', 'qty_121': 'no', 'flag_121': 'D121', 'mode_121': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_121': '0', 'qty_121': 'no', 'flag_121': 'H121', 'mode_121': 0}
    assert decode({'v_121': '0', 'qty_121': 'no', 'flag_121': 'H121', 'mode_121': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
