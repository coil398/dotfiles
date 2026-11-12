"""Spec: docs/SPEC.md §§2–5 and docs/group24.md#r146."""

def test_encode_normal():
    from record_codecs.group24 import encode_r146 as encode, decode_r146 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_146': 'ON', 'qty_146': 'R146', 'flag_146': 22, 'mode_146': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group24 import encode_r146 as encode, decode_r146 as decode
    assert decode({'v_146': 'ON', 'qty_146': 'R146', 'flag_146': 22, 'mode_146': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group24 import encode_r146 as encode, decode_r146 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_146': 'R146', 'flag_146': 22, 'mode_146': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_146': None, 'qty_146': 'R146', 'flag_146': 22, 'mode_146': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_146': 'ON', 'qty_146': 'H146', 'flag_146': 22, 'mode_146': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_146': 'ON', 'flag_146': 22, 'mode_146': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_146': 'ON', 'qty_146': 'R146', 'flag_146': 22}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_146': 'ON', 'qty_146': 'R146', 'flag_146': 22, 'mode_146': None}
    assert decode({'qty_146': 'R146', 'flag_146': 22, 'mode_146': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_146': None, 'qty_146': 'R146', 'flag_146': 22, 'mode_146': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_146': 'ON', 'flag_146': 22, 'mode_146': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_146': 'ON', 'qty_146': None, 'flag_146': 22, 'mode_146': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_146': 'ON', 'qty_146': 'R146', 'mode_146': ['red', 'blue']})
    assert error.value.args == ('flag_146',)
    with pytest.raises(ValueError) as error:
        decode({'v_146': 'ON', 'qty_146': 'R146', 'flag_146': None, 'mode_146': ['red', 'blue']})
    assert error.value.args == ('flag_146',)
    assert decode({'v_146': 'ON', 'qty_146': 'R146', 'flag_146': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_146': 'ON', 'qty_146': 'R146', 'flag_146': 22, 'mode_146': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group24 import encode_r146 as encode, decode_r146 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_146': 'OFF', 'qty_146': 'D146', 'flag_146': -34, 'mode_146': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_146'] is not value['labels_3']
    result['mode_146'].append("changed")
    assert value == before
    value = {'v_146': 'OFF', 'qty_146': 'D146', 'flag_146': -34, 'mode_146': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_146']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_146': 'OFF', 'qty_146': 'H146', 'flag_146': 0, 'mode_146': []}
    assert decode({'v_146': 'OFF', 'qty_146': 'H146', 'flag_146': 0, 'mode_146': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
