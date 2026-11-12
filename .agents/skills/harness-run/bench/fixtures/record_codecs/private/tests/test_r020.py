"""Spec: docs/SPEC.md §§2–5 and docs/group03.md#r020."""

def test_encode_normal():
    from record_codecs.group03 import encode_r020 as encode, decode_r020 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_020': 'ON', 'qty_020': 'R20', 'flag_020': 110, 'mode_020': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group03 import encode_r020 as encode, decode_r020 as decode
    assert decode({'v_020': 'ON', 'qty_020': 'R20', 'flag_020': 110, 'mode_020': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group03 import encode_r020 as encode, decode_r020 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_020': 'R20', 'flag_020': 110, 'mode_020': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_020': None, 'qty_020': 'R20', 'flag_020': 110, 'mode_020': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_020': 'ON', 'qty_020': 'H20', 'flag_020': 110, 'mode_020': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_020': 'ON', 'flag_020': 110, 'mode_020': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_020': 'ON', 'qty_020': 'R20', 'flag_020': 110}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_020': 'ON', 'qty_020': 'R20', 'flag_020': 110, 'mode_020': None}
    assert decode({'qty_020': 'R20', 'flag_020': 110, 'mode_020': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_020': None, 'qty_020': 'R20', 'flag_020': 110, 'mode_020': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_020': 'ON', 'flag_020': 110, 'mode_020': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_020': 'ON', 'qty_020': None, 'flag_020': 110, 'mode_020': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_020': 'ON', 'qty_020': 'R20', 'mode_020': ['red', 'blue']})
    assert error.value.args == ('flag_020',)
    with pytest.raises(ValueError) as error:
        decode({'v_020': 'ON', 'qty_020': 'R20', 'flag_020': None, 'mode_020': ['red', 'blue']})
    assert error.value.args == ('flag_020',)
    assert decode({'v_020': 'ON', 'qty_020': 'R20', 'flag_020': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_020': 'ON', 'qty_020': 'R20', 'flag_020': 110, 'mode_020': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group03 import encode_r020 as encode, decode_r020 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_020': 'OFF', 'qty_020': 'D20', 'flag_020': -170, 'mode_020': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_020'] is not value['labels_3']
    result['mode_020'].append("changed")
    assert value == before
    value = {'v_020': 'OFF', 'qty_020': 'D20', 'flag_020': -170, 'mode_020': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_020']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_020': 'OFF', 'qty_020': 'H20', 'flag_020': 0, 'mode_020': []}
    assert decode({'v_020': 'OFF', 'qty_020': 'H20', 'flag_020': 0, 'mode_020': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
