"""Spec: docs/SPEC.md §§2–5 and docs/group00.md#r002."""

def test_encode_normal():
    from record_codecs.group00 import encode_r002 as encode, decode_r002 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_002': 'ON', 'qty_002': 'R2', 'flag_002': 22, 'mode_002': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group00 import encode_r002 as encode, decode_r002 as decode
    assert decode({'v_002': 'ON', 'qty_002': 'R2', 'flag_002': 22, 'mode_002': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group00 import encode_r002 as encode, decode_r002 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_002': 'R2', 'flag_002': 22, 'mode_002': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_002': None, 'qty_002': 'R2', 'flag_002': 22, 'mode_002': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_002': 'ON', 'qty_002': 'H2', 'flag_002': 22, 'mode_002': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_002': 'ON', 'flag_002': 22, 'mode_002': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_002': 'ON', 'qty_002': 'R2', 'flag_002': 22}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_002': 'ON', 'qty_002': 'R2', 'flag_002': 22, 'mode_002': None}
    assert decode({'qty_002': 'R2', 'flag_002': 22, 'mode_002': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_002': None, 'qty_002': 'R2', 'flag_002': 22, 'mode_002': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_002': 'ON', 'flag_002': 22, 'mode_002': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_002': 'ON', 'qty_002': None, 'flag_002': 22, 'mode_002': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_002': 'ON', 'qty_002': 'R2', 'mode_002': ['red', 'blue']})
    assert error.value.args == ('flag_002',)
    with pytest.raises(ValueError) as error:
        decode({'v_002': 'ON', 'qty_002': 'R2', 'flag_002': None, 'mode_002': ['red', 'blue']})
    assert error.value.args == ('flag_002',)
    assert decode({'v_002': 'ON', 'qty_002': 'R2', 'flag_002': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_002': 'ON', 'qty_002': 'R2', 'flag_002': 22, 'mode_002': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group00 import encode_r002 as encode, decode_r002 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_002': 'OFF', 'qty_002': 'D2', 'flag_002': -34, 'mode_002': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_002'] is not value['labels_3']
    result['mode_002'].append("changed")
    assert value == before
    value = {'v_002': 'OFF', 'qty_002': 'D2', 'flag_002': -34, 'mode_002': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_002']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_002': 'OFF', 'qty_002': 'H2', 'flag_002': 0, 'mode_002': []}
    assert decode({'v_002': 'OFF', 'qty_002': 'H2', 'flag_002': 0, 'mode_002': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
