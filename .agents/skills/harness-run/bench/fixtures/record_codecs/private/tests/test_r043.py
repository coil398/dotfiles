"""Spec: docs/SPEC.md §§2–5 and docs/group07.md#r043."""

def test_encode_normal():
    from record_codecs.group07 import encode_r043 as encode, decode_r043 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_043': '42', 'qty_043': 'yes', 'flag_043': 'R43', 'mode_043': 110}

def test_decode_normal():
    from record_codecs.group07 import encode_r043 as encode, decode_r043 as decode
    assert decode({'v_043': '42', 'qty_043': 'yes', 'flag_043': 'R43', 'mode_043': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group07 import encode_r043 as encode, decode_r043 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_043': '-7', 'qty_043': 'yes', 'flag_043': 'R43', 'mode_043': 110}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_043': '42', 'qty_043': None, 'flag_043': 'R43', 'mode_043': 110}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_043': '42', 'qty_043': 'yes', 'mode_043': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_043': '42', 'qty_043': 'yes', 'mode_043': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_043': '42', 'qty_043': 'yes', 'flag_043': 'R43', 'mode_043': 30}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_043': 'yes', 'flag_043': 'R43', 'mode_043': 110}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_043': None, 'qty_043': 'yes', 'flag_043': 'R43', 'mode_043': 110})
    assert error.value.args == ('v_043',)
    with pytest.raises(KeyError) as error:
        decode({'v_043': '42', 'flag_043': 'R43', 'mode_043': 110})
    assert error.value.args == ('qty_043',)
    assert decode({'v_043': '42', 'qty_043': None, 'flag_043': 'R43', 'mode_043': 110}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_043': '42', 'qty_043': 'yes', 'mode_043': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_043': '42', 'qty_043': 'yes', 'flag_043': None, 'mode_043': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_043': '42', 'qty_043': 'yes', 'flag_043': 'R43'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_043': '42', 'qty_043': 'yes', 'flag_043': 'R43', 'mode_043': None})
    assert error.value.args == ('mode_043',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group07 import encode_r043 as encode, decode_r043 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_043': '-100000000000000000003', 'qty_043': 'no', 'flag_043': 'D43', 'mode_043': -170}
    assert value == before
    assert result is not value
    value = {'v_043': '-100000000000000000003', 'qty_043': 'no', 'flag_043': 'D43', 'mode_043': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_043': '0', 'qty_043': 'no', 'flag_043': 'H43', 'mode_043': 0}
    assert decode({'v_043': '0', 'qty_043': 'no', 'flag_043': 'H43', 'mode_043': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
