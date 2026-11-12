"""Spec: docs/SPEC.md §§2–5 and docs/group16.md#r098."""

def test_encode_normal():
    from record_codecs.group16 import encode_r098 as encode, decode_r098 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_098': 'ON', 'qty_098': 'R98', 'flag_098': 22, 'mode_098': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group16 import encode_r098 as encode, decode_r098 as decode
    assert decode({'v_098': 'ON', 'qty_098': 'R98', 'flag_098': 22, 'mode_098': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group16 import encode_r098 as encode, decode_r098 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_098': 'OFF', 'qty_098': 'R98', 'flag_098': 22, 'mode_098': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_098': 'ON', 'qty_098': None, 'flag_098': 22, 'mode_098': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_098': 'ON', 'qty_098': 'R98', 'mode_098': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_098': 'ON', 'qty_098': 'R98', 'mode_098': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_098': 'ON', 'qty_098': 'R98', 'flag_098': 22, 'mode_098': ['default']}
    result = encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    result['mode_098'].append("changed")
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_098': 'ON', 'qty_098': 'R98', 'flag_098': 22, 'mode_098': ['default']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None})
    assert error.value.args == ('labels_3',)
    assert decode({'qty_098': 'R98', 'flag_098': 22, 'mode_098': ['red', 'blue']}) == {'active_0': False, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_098': None, 'qty_098': 'R98', 'flag_098': 22, 'mode_098': ['red', 'blue']})
    assert error.value.args == ('v_098',)
    with pytest.raises(KeyError) as error:
        decode({'v_098': 'ON', 'flag_098': 22, 'mode_098': ['red', 'blue']})
    assert error.value.args == ('qty_098',)
    assert decode({'v_098': 'ON', 'qty_098': None, 'flag_098': 22, 'mode_098': ['red', 'blue']}) == {'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_098': 'ON', 'qty_098': 'R98', 'mode_098': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_098': 'ON', 'qty_098': 'R98', 'flag_098': None, 'mode_098': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_098': 'ON', 'qty_098': 'R98', 'flag_098': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    result = decode({'v_098': 'ON', 'qty_098': 'R98', 'flag_098': 22})
    result['labels_3'].append("changed")
    assert decode({'v_098': 'ON', 'qty_098': 'R98', 'flag_098': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    with pytest.raises(ValueError) as error:
        decode({'v_098': 'ON', 'qty_098': 'R98', 'flag_098': 22, 'mode_098': None})
    assert error.value.args == ('mode_098',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group16 import encode_r098 as encode, decode_r098 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_098': 'OFF', 'qty_098': 'D98', 'flag_098': -34, 'mode_098': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_098'] is not value['labels_3']
    result['mode_098'].append("changed")
    assert value == before
    value = {'v_098': 'OFF', 'qty_098': 'D98', 'flag_098': -34, 'mode_098': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_098']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_098': 'OFF', 'qty_098': 'H98', 'flag_098': 0, 'mode_098': []}
    assert decode({'v_098': 'OFF', 'qty_098': 'H98', 'flag_098': 0, 'mode_098': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
