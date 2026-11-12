"""Spec: docs/SPEC.md §§2–5 and docs/group26.md#r157."""

def test_encode_normal():
    from record_codecs.group26 import encode_r157 as encode, decode_r157 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_157': '42', 'qty_157': 'yes', 'flag_157': 'R157', 'mode_157': 22}

def test_decode_normal():
    from record_codecs.group26 import encode_r157 as encode, decode_r157 as decode
    assert decode({'v_157': '42', 'qty_157': 'yes', 'flag_157': 'R157', 'mode_157': 22, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group26 import encode_r157 as encode, decode_r157 as decode
    with pytest.raises(KeyError) as error:
        encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_157': 'yes', 'flag_157': 'R157', 'mode_157': 22}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_157': '42', 'flag_157': 'R157', 'mode_157': 22}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_157': '42', 'qty_157': 'yes', 'flag_157': 'H157', 'mode_157': 22}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_157': '42', 'qty_157': 'yes', 'flag_157': None, 'mode_157': 22}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'})
    assert error.value.args == ('amount_3',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_157': '42', 'qty_157': 'yes', 'flag_157': 'R157'}
    with pytest.raises(KeyError) as error:
        decode({'qty_157': 'yes', 'flag_157': 'R157', 'mode_157': 22})
    assert error.value.args == ('v_157',)
    assert decode({'v_157': None, 'qty_157': 'yes', 'flag_157': 'R157', 'mode_157': 22}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_157': '42', 'flag_157': 'R157', 'mode_157': 22}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_157': '42', 'qty_157': None, 'flag_157': 'R157', 'mode_157': 22})
    assert error.value.args == ('qty_157',)
    assert decode({'v_157': '42', 'qty_157': 'yes', 'mode_157': 22}) == {'count_0': 42, 'active_1': True, 'state_2': 'held', 'amount_3': 11}
    assert decode({'v_157': '42', 'qty_157': 'yes', 'flag_157': None, 'mode_157': 22}) == {'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_157': '42', 'qty_157': 'yes', 'flag_157': 'R157'})
    assert error.value.args == ('mode_157',)
    assert decode({'v_157': '42', 'qty_157': 'yes', 'flag_157': 'R157', 'mode_157': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group26 import encode_r157 as encode, decode_r157 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_157': '-100000000000000000003', 'qty_157': 'no', 'flag_157': 'D157', 'mode_157': -34}
    assert value == before
    assert result is not value
    value = {'v_157': '-100000000000000000003', 'qty_157': 'no', 'flag_157': 'D157', 'mode_157': -34}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_157': '0', 'qty_157': 'no', 'flag_157': 'H157', 'mode_157': 0}
    assert decode({'v_157': '0', 'qty_157': 'no', 'flag_157': 'H157', 'mode_157': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
