"""Spec: docs/SPEC.md §§2–5 and docs/group23.md#r139."""

def test_encode_normal():
    from record_codecs.group23 import encode_r139 as encode, decode_r139 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_139': '42', 'qty_139': 'yes', 'flag_139': 'R139', 'mode_139': 110}

def test_decode_normal():
    from record_codecs.group23 import encode_r139 as encode, decode_r139 as decode
    assert decode({'v_139': '42', 'qty_139': 'yes', 'flag_139': 'R139', 'mode_139': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group23 import encode_r139 as encode, decode_r139 as decode
    with pytest.raises(KeyError) as error:
        encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    assert encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'qty_139': 'yes', 'flag_139': 'R139', 'mode_139': 110}
    assert encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11}) == {'v_139': '42', 'flag_139': 'R139', 'mode_139': 110}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_139': '42', 'qty_139': 'yes', 'flag_139': 'H139', 'mode_139': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_139': '42', 'qty_139': 'yes', 'flag_139': None, 'mode_139': 110}
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'})
    assert error.value.args == ('amount_3',)
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None}) == {'v_139': '42', 'qty_139': 'yes', 'flag_139': 'R139'}
    with pytest.raises(KeyError) as error:
        decode({'qty_139': 'yes', 'flag_139': 'R139', 'mode_139': 110})
    assert error.value.args == ('v_139',)
    assert decode({'v_139': None, 'qty_139': 'yes', 'flag_139': 'R139', 'mode_139': 110}) == {'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_139': '42', 'flag_139': 'R139', 'mode_139': 110}) == {'count_0': 42, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_139': '42', 'qty_139': None, 'flag_139': 'R139', 'mode_139': 110})
    assert error.value.args == ('qty_139',)
    assert decode({'v_139': '42', 'qty_139': 'yes', 'mode_139': 110}) == {'count_0': 42, 'active_1': True, 'state_2': 'held', 'amount_3': 11}
    assert decode({'v_139': '42', 'qty_139': 'yes', 'flag_139': None, 'mode_139': 110}) == {'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}
    with pytest.raises(KeyError) as error:
        decode({'v_139': '42', 'qty_139': 'yes', 'flag_139': 'R139'})
    assert error.value.args == ('mode_139',)
    assert decode({'v_139': '42', 'qty_139': 'yes', 'flag_139': 'R139', 'mode_139': None}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group23 import encode_r139 as encode, decode_r139 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_139': '-100000000000000000003', 'qty_139': 'no', 'flag_139': 'D139', 'mode_139': -170}
    assert value == before
    assert result is not value
    value = {'v_139': '-100000000000000000003', 'qty_139': 'no', 'flag_139': 'D139', 'mode_139': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_139': '0', 'qty_139': 'no', 'flag_139': 'H139', 'mode_139': 0}
    assert decode({'v_139': '0', 'qty_139': 'no', 'flag_139': 'H139', 'mode_139': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
