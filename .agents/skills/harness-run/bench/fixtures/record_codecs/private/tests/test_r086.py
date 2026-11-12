"""Spec: docs/SPEC.md §§2–5 and docs/group14.md#r086."""

def test_encode_normal():
    from record_codecs.group14 import encode_r086 as encode, decode_r086 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_086': 'ON', 'qty_086': 'R86', 'flag_086': 22, 'mode_086': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group14 import encode_r086 as encode, decode_r086 as decode
    assert decode({'v_086': 'ON', 'qty_086': 'R86', 'flag_086': 22, 'mode_086': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group14 import encode_r086 as encode, decode_r086 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_086': 'R86', 'flag_086': 22, 'mode_086': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_086': 'ON', 'flag_086': 22, 'mode_086': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_086': 'ON', 'qty_086': 'R86', 'flag_086': 6, 'mode_086': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_086': 'ON', 'qty_086': 'R86', 'flag_086': None, 'mode_086': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_086': 'ON', 'qty_086': 'R86', 'flag_086': 22}
    with pytest.raises(KeyError) as error:
        decode({'qty_086': 'R86', 'flag_086': 22, 'mode_086': ['red', 'blue']})
    assert error.value.args == ('v_086',)
    assert decode({'v_086': None, 'qty_086': 'R86', 'flag_086': 22, 'mode_086': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_086': 'ON', 'flag_086': 22, 'mode_086': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_086': 'ON', 'qty_086': None, 'flag_086': 22, 'mode_086': ['red', 'blue']})
    assert error.value.args == ('qty_086',)
    assert decode({'v_086': 'ON', 'qty_086': 'R86', 'mode_086': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_086': 'ON', 'qty_086': 'R86', 'flag_086': None, 'mode_086': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_086': 'ON', 'qty_086': 'R86', 'flag_086': 22})
    assert error.value.args == ('mode_086',)
    assert decode({'v_086': 'ON', 'qty_086': 'R86', 'flag_086': 22, 'mode_086': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group14 import encode_r086 as encode, decode_r086 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_086': 'OFF', 'qty_086': 'D86', 'flag_086': -34, 'mode_086': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_086'] is not value['labels_3']
    result['mode_086'].append("changed")
    assert value == before
    value = {'v_086': 'OFF', 'qty_086': 'D86', 'flag_086': -34, 'mode_086': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_086']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_086': 'OFF', 'qty_086': 'H86', 'flag_086': 0, 'mode_086': []}
    assert decode({'v_086': 'OFF', 'qty_086': 'H86', 'flag_086': 0, 'mode_086': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
