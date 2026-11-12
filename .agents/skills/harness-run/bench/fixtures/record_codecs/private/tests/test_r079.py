"""Spec: docs/SPEC.md §§2–5 and docs/group13.md#r079."""

def test_encode_normal():
    from record_codecs.group13 import encode_r079 as encode, decode_r079 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_079': '42', 'qty_079': 'yes', 'flag_079': 'R79', 'mode_079': 110}

def test_decode_normal():
    from record_codecs.group13 import encode_r079 as encode, decode_r079 as decode
    assert decode({'v_079': '42', 'qty_079': 'yes', 'flag_079': 'R79', 'mode_079': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group13 import encode_r079 as encode, decode_r079 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_079': '-7', 'qty_079': 'yes', 'flag_079': 'R79', 'mode_079': 110}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_079': '42', 'qty_079': None, 'flag_079': 'R79', 'mode_079': 110}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_079': '42', 'qty_079': 'yes', 'mode_079': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_079': '42', 'qty_079': 'yes', 'mode_079': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_079': '42', 'qty_079': 'yes', 'flag_079': 'R79', 'mode_079': 30}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_079': 'yes', 'flag_079': 'R79', 'mode_079': 110}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_079': None, 'qty_079': 'yes', 'flag_079': 'R79', 'mode_079': 110})
    assert error.value.args == ('v_079',)
    with pytest.raises(KeyError) as error:
        decode({'v_079': '42', 'flag_079': 'R79', 'mode_079': 110})
    assert error.value.args == ('qty_079',)
    assert decode({'v_079': '42', 'qty_079': None, 'flag_079': 'R79', 'mode_079': 110}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_079': '42', 'qty_079': 'yes', 'mode_079': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_079': '42', 'qty_079': 'yes', 'flag_079': None, 'mode_079': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_079': '42', 'qty_079': 'yes', 'flag_079': 'R79'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_079': '42', 'qty_079': 'yes', 'flag_079': 'R79', 'mode_079': None})
    assert error.value.args == ('mode_079',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group13 import encode_r079 as encode, decode_r079 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_079': '-100000000000000000003', 'qty_079': 'no', 'flag_079': 'D79', 'mode_079': -170}
    assert value == before
    assert result is not value
    value = {'v_079': '-100000000000000000003', 'qty_079': 'no', 'flag_079': 'D79', 'mode_079': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_079': '0', 'qty_079': 'no', 'flag_079': 'H79', 'mode_079': 0}
    assert decode({'v_079': '0', 'qty_079': 'no', 'flag_079': 'H79', 'mode_079': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
