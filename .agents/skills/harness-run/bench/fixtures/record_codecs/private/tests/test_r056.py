"""Spec: docs/SPEC.md §§2–5 and docs/group09.md#r056."""

def test_encode_normal():
    from record_codecs.group09 import encode_r056 as encode, decode_r056 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_056': 'ON', 'qty_056': 'R56', 'flag_056': 110, 'mode_056': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group09 import encode_r056 as encode, decode_r056 as decode
    assert decode({'v_056': 'ON', 'qty_056': 'R56', 'flag_056': 110, 'mode_056': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group09 import encode_r056 as encode, decode_r056 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_056': 'R56', 'flag_056': 110, 'mode_056': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_056': None, 'qty_056': 'R56', 'flag_056': 110, 'mode_056': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_056': 'ON', 'qty_056': 'H56', 'flag_056': 110, 'mode_056': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_056': 'ON', 'flag_056': 110, 'mode_056': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_056': 'ON', 'qty_056': 'R56', 'flag_056': 110}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_056': 'ON', 'qty_056': 'R56', 'flag_056': 110, 'mode_056': None}
    assert decode({'qty_056': 'R56', 'flag_056': 110, 'mode_056': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_056': None, 'qty_056': 'R56', 'flag_056': 110, 'mode_056': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_056': 'ON', 'flag_056': 110, 'mode_056': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_056': 'ON', 'qty_056': None, 'flag_056': 110, 'mode_056': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_056': 'ON', 'qty_056': 'R56', 'mode_056': ['red', 'blue']})
    assert error.value.args == ('flag_056',)
    with pytest.raises(ValueError) as error:
        decode({'v_056': 'ON', 'qty_056': 'R56', 'flag_056': None, 'mode_056': ['red', 'blue']})
    assert error.value.args == ('flag_056',)
    assert decode({'v_056': 'ON', 'qty_056': 'R56', 'flag_056': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_056': 'ON', 'qty_056': 'R56', 'flag_056': 110, 'mode_056': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group09 import encode_r056 as encode, decode_r056 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_056': 'OFF', 'qty_056': 'D56', 'flag_056': -170, 'mode_056': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_056'] is not value['labels_3']
    result['mode_056'].append("changed")
    assert value == before
    value = {'v_056': 'OFF', 'qty_056': 'D56', 'flag_056': -170, 'mode_056': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_056']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_056': 'OFF', 'qty_056': 'H56', 'flag_056': 0, 'mode_056': []}
    assert decode({'v_056': 'OFF', 'qty_056': 'H56', 'flag_056': 0, 'mode_056': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
