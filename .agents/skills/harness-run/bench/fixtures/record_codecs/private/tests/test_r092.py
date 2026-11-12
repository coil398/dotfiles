"""Spec: docs/SPEC.md §§2–5 and docs/group15.md#r092."""

def test_encode_normal():
    from record_codecs.group15 import encode_r092 as encode, decode_r092 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_092': 'ON', 'qty_092': 'R92', 'flag_092': 110, 'mode_092': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group15 import encode_r092 as encode, decode_r092 as decode
    assert decode({'v_092': 'ON', 'qty_092': 'R92', 'flag_092': 110, 'mode_092': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group15 import encode_r092 as encode, decode_r092 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_092': 'R92', 'flag_092': 110, 'mode_092': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_092': None, 'qty_092': 'R92', 'flag_092': 110, 'mode_092': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_092': 'ON', 'qty_092': 'H92', 'flag_092': 110, 'mode_092': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_092': 'ON', 'flag_092': 110, 'mode_092': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_092': 'ON', 'qty_092': 'R92', 'flag_092': 110}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_092': 'ON', 'qty_092': 'R92', 'flag_092': 110, 'mode_092': None}
    assert decode({'qty_092': 'R92', 'flag_092': 110, 'mode_092': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_092': None, 'qty_092': 'R92', 'flag_092': 110, 'mode_092': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_092': 'ON', 'flag_092': 110, 'mode_092': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_092': 'ON', 'qty_092': None, 'flag_092': 110, 'mode_092': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_092': 'ON', 'qty_092': 'R92', 'mode_092': ['red', 'blue']})
    assert error.value.args == ('flag_092',)
    with pytest.raises(ValueError) as error:
        decode({'v_092': 'ON', 'qty_092': 'R92', 'flag_092': None, 'mode_092': ['red', 'blue']})
    assert error.value.args == ('flag_092',)
    assert decode({'v_092': 'ON', 'qty_092': 'R92', 'flag_092': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_092': 'ON', 'qty_092': 'R92', 'flag_092': 110, 'mode_092': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group15 import encode_r092 as encode, decode_r092 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_092': 'OFF', 'qty_092': 'D92', 'flag_092': -170, 'mode_092': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_092'] is not value['labels_3']
    result['mode_092'].append("changed")
    assert value == before
    value = {'v_092': 'OFF', 'qty_092': 'D92', 'flag_092': -170, 'mode_092': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_092']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_092': 'OFF', 'qty_092': 'H92', 'flag_092': 0, 'mode_092': []}
    assert decode({'v_092': 'OFF', 'qty_092': 'H92', 'flag_092': 0, 'mode_092': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
