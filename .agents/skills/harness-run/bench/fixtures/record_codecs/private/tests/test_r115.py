"""Spec: docs/SPEC.md §§2–5 and docs/group19.md#r115."""

def test_encode_normal():
    from record_codecs.group19 import encode_r115 as encode, decode_r115 as decode
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11, 'ignored': 'extra'}) == {'v_115': '42', 'qty_115': 'yes', 'flag_115': 'R115', 'mode_115': 110}

def test_decode_normal():
    from record_codecs.group19 import encode_r115 as encode, decode_r115 as decode
    assert decode({'v_115': '42', 'qty_115': 'yes', 'flag_115': 'R115', 'mode_115': 110, 'ignored': 'extra'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}

def test_missing_null():
    import pytest
    from record_codecs.group19 import encode_r115 as encode, decode_r115 as decode
    assert encode({'active_1': True, 'state_2': 'ready', 'amount_3': 11}) == {'v_115': '-7', 'qty_115': 'yes', 'flag_115': 'R115', 'mode_115': 110}
    with pytest.raises(ValueError) as error:
        encode({'count_0': None, 'active_1': True, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('count_0',)
    with pytest.raises(KeyError) as error:
        encode({'count_0': 42, 'state_2': 'ready', 'amount_3': 11})
    assert error.value.args == ('active_1',)
    assert encode({'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}) == {'v_115': '42', 'qty_115': None, 'flag_115': 'R115', 'mode_115': 110}
    assert encode({'count_0': 42, 'active_1': True, 'amount_3': 11}) == {'v_115': '42', 'qty_115': 'yes', 'mode_115': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': None, 'amount_3': 11}) == {'v_115': '42', 'qty_115': 'yes', 'mode_115': 110}
    assert encode({'count_0': 42, 'active_1': True, 'state_2': 'ready'}) == {'v_115': '42', 'qty_115': 'yes', 'flag_115': 'R115', 'mode_115': 30}
    with pytest.raises(ValueError) as error:
        encode({'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': None})
    assert error.value.args == ('amount_3',)
    assert decode({'qty_115': 'yes', 'flag_115': 'R115', 'mode_115': 110}) == {'count_0': -7, 'active_1': True, 'state_2': 'ready', 'amount_3': 11}
    with pytest.raises(ValueError) as error:
        decode({'v_115': None, 'qty_115': 'yes', 'flag_115': 'R115', 'mode_115': 110})
    assert error.value.args == ('v_115',)
    with pytest.raises(KeyError) as error:
        decode({'v_115': '42', 'flag_115': 'R115', 'mode_115': 110})
    assert error.value.args == ('qty_115',)
    assert decode({'v_115': '42', 'qty_115': None, 'flag_115': 'R115', 'mode_115': 110}) == {'count_0': 42, 'active_1': None, 'state_2': 'ready', 'amount_3': 11}
    assert decode({'v_115': '42', 'qty_115': 'yes', 'mode_115': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_115': '42', 'qty_115': 'yes', 'flag_115': None, 'mode_115': 110}) == {'count_0': 42, 'active_1': True, 'amount_3': 11}
    assert decode({'v_115': '42', 'qty_115': 'yes', 'flag_115': 'R115'}) == {'count_0': 42, 'active_1': True, 'state_2': 'ready', 'amount_3': 3}
    with pytest.raises(ValueError) as error:
        decode({'v_115': '42', 'qty_115': 'yes', 'flag_115': 'R115', 'mode_115': None})
    assert error.value.args == ('mode_115',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group19 import encode_r115 as encode, decode_r115 as decode
    value = {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_115': '-100000000000000000003', 'qty_115': 'no', 'flag_115': 'D115', 'mode_115': -170}
    assert value == before
    assert result is not value
    value = {'v_115': '-100000000000000000003', 'qty_115': 'no', 'flag_115': 'D115', 'mode_115': -170}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'count_0': -100000000000000000003, 'active_1': False, 'state_2': 'done', 'amount_3': -17}
    assert value == before
    assert result is not value
    assert encode({'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}) == {'v_115': '0', 'qty_115': 'no', 'flag_115': 'H115', 'mode_115': 0}
    assert decode({'v_115': '0', 'qty_115': 'no', 'flag_115': 'H115', 'mode_115': 0}) == {'count_0': 0, 'active_1': False, 'state_2': 'held', 'amount_3': 0}
