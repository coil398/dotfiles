"""Spec: docs/SPEC.md §§2–5 and docs/group31.md#r187."""

def test_encode_normal():
    from record_codecs.group31 import encode_r187 as encode, decode_r187 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_187': '42', 'qty_187': 'yes', 'flag_187': 'R187', 'mode_187': 110}

def test_decode_normal():
    from record_codecs.group31 import encode_r187 as encode, decode_r187 as decode
    assert decode({'v_187': '42', 'qty_187': 'yes', 'flag_187': 'R187', 'mode_187': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group31 import encode_r187 as encode, decode_r187 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_187': '-7', 'qty_187': 'yes', 'flag_187': 'R187', 'mode_187': 110}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_187': '42', 'qty_187': None, 'flag_187': 'R187', 'mode_187': 110}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_187': '42', 'qty_187': 'yes', 'mode_187': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_187': '42', 'qty_187': 'yes', 'mode_187': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_187': '42', 'qty_187': 'yes', 'flag_187': 'R187', 'mode_187': 30}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_187': 'yes', 'flag_187': 'R187', 'mode_187': 110}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_187': None, 'qty_187': 'yes', 'flag_187': 'R187', 'mode_187': 110})
    assert error.value.args == ('v_187',)
    with pytest.raises(KeyError) as error:
        decode({'v_187': '42', 'flag_187': 'R187', 'mode_187': 110})
    assert error.value.args == ('qty_187',)
    assert decode({'v_187': '42', 'qty_187': None, 'flag_187': 'R187', 'mode_187': 110}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_187': '42', 'qty_187': 'yes', 'mode_187': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_187': '42', 'qty_187': 'yes', 'flag_187': None, 'mode_187': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_187': '42', 'qty_187': 'yes', 'flag_187': 'R187'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_187': '42', 'qty_187': 'yes', 'flag_187': 'R187', 'mode_187': None})
    assert error.value.args == ('mode_187',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group31 import encode_r187 as encode, decode_r187 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_187': '-100000000000000000003', 'qty_187': 'no', 'flag_187': 'D187', 'mode_187': -170}
    assert value == before
    assert result is not value
    value = {'v_187': '-100000000000000000003', 'qty_187': 'no', 'flag_187': 'D187', 'mode_187': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_187': '0', 'qty_187': 'no', 'flag_187': 'H187', 'mode_187': 0}
    assert decode({'v_187': '0', 'qty_187': 'no', 'flag_187': 'H187', 'mode_187': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
