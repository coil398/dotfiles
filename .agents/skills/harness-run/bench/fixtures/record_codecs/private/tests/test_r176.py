"""Spec: docs/SPEC.md §§2–5 and docs/group29.md#r176."""

def test_encode_normal():
    from record_codecs.group29 import encode_r176 as encode, decode_r176 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_176': 'ON', 'qty_176': 'R176', 'flag_176': 110, 'mode_176': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group29 import encode_r176 as encode, decode_r176 as decode
    assert decode({'v_176': 'ON', 'qty_176': 'R176', 'flag_176': 110, 'mode_176': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group29 import encode_r176 as encode, decode_r176 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_176': 'R176', 'flag_176': 110, 'mode_176': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_176': 'ON', 'flag_176': 110, 'mode_176': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_176': 'ON', 'qty_176': 'R176', 'flag_176': 30, 'mode_176': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_176': 'ON', 'qty_176': 'R176', 'flag_176': None, 'mode_176': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_176': 'ON', 'qty_176': 'R176', 'flag_176': 110}
    with pytest.raises(KeyError) as error:
        decode({'qty_176': 'R176', 'flag_176': 110, 'mode_176': ['red', 'blue']})
    assert error.value.args == ('v_176',)
    assert decode({'v_176': None, 'qty_176': 'R176', 'flag_176': 110, 'mode_176': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_176': 'ON', 'flag_176': 110, 'mode_176': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_176': 'ON', 'qty_176': None, 'flag_176': 110, 'mode_176': ['red', 'blue']})
    assert error.value.args == ('qty_176',)
    assert decode({'v_176': 'ON', 'qty_176': 'R176', 'mode_176': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_176': 'ON', 'qty_176': 'R176', 'flag_176': None, 'mode_176': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_176': 'ON', 'qty_176': 'R176', 'flag_176': 110})
    assert error.value.args == ('mode_176',)
    assert decode({'v_176': 'ON', 'qty_176': 'R176', 'flag_176': 110, 'mode_176': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group29 import encode_r176 as encode, decode_r176 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_176': 'OFF', 'qty_176': 'D176', 'flag_176': -170, 'mode_176': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_176'] is not value['labels_3']
    result['mode_176'].append("changed")
    assert value == before
    value = {'v_176': 'OFF', 'qty_176': 'D176', 'flag_176': -170, 'mode_176': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_176']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_176': 'OFF', 'qty_176': 'H176', 'flag_176': 0, 'mode_176': []}
    assert decode({'v_176': 'OFF', 'qty_176': 'H176', 'flag_176': 0, 'mode_176': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
