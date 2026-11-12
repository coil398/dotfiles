"""Spec: docs/SPEC.md §§2–5 and docs/group01.md#r008."""

def test_encode_normal():
    from record_codecs.group01 import encode_r008 as encode, decode_r008 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_008': 'ON', 'qty_008': 'R8', 'flag_008': 110, 'mode_008': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group01 import encode_r008 as encode, decode_r008 as decode
    assert decode({'v_008': 'ON', 'qty_008': 'R8', 'flag_008': 110, 'mode_008': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group01 import encode_r008 as encode, decode_r008 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_008': 'OFF', 'qty_008': 'R8', 'flag_008': 110, 'mode_008': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_008': 'ON', 'qty_008': None, 'flag_008': 110, 'mode_008': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_008': 'ON', 'qty_008': 'R8', 'mode_008': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_008': 'ON', 'qty_008': 'R8', 'mode_008': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_008': 'ON', 'qty_008': 'R8', 'flag_008': 110, 'mode_008': ['default']}
    result = encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    result['mode_008'].append("changed")
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_008': 'ON', 'qty_008': 'R8', 'flag_008': 110, 'mode_008': ['default']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None})
    assert error.value.args == ('labels_3',)
    assert decode({'qty_008': 'R8', 'flag_008': 110, 'mode_008': ['red', 'blue']}) == {'active_0': False, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_008': None, 'qty_008': 'R8', 'flag_008': 110, 'mode_008': ['red', 'blue']})
    assert error.value.args == ('v_008',)
    with pytest.raises(KeyError) as error:
        decode({'v_008': 'ON', 'flag_008': 110, 'mode_008': ['red', 'blue']})
    assert error.value.args == ('qty_008',)
    assert decode({'v_008': 'ON', 'qty_008': None, 'flag_008': 110, 'mode_008': ['red', 'blue']}) == {'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_008': 'ON', 'qty_008': 'R8', 'mode_008': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_008': 'ON', 'qty_008': 'R8', 'flag_008': None, 'mode_008': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_008': 'ON', 'qty_008': 'R8', 'flag_008': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    result = decode({'v_008': 'ON', 'qty_008': 'R8', 'flag_008': 110})
    result['labels_3'].append("changed")
    assert decode({'v_008': 'ON', 'qty_008': 'R8', 'flag_008': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    with pytest.raises(ValueError) as error:
        decode({'v_008': 'ON', 'qty_008': 'R8', 'flag_008': 110, 'mode_008': None})
    assert error.value.args == ('mode_008',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group01 import encode_r008 as encode, decode_r008 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_008': 'OFF', 'qty_008': 'D8', 'flag_008': -170, 'mode_008': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_008'] is not value['labels_3']
    result['mode_008'].append("changed")
    assert value == before
    value = {'v_008': 'OFF', 'qty_008': 'D8', 'flag_008': -170, 'mode_008': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_008']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_008': 'OFF', 'qty_008': 'H8', 'flag_008': 0, 'mode_008': []}
    assert decode({'v_008': 'OFF', 'qty_008': 'H8', 'flag_008': 0, 'mode_008': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
