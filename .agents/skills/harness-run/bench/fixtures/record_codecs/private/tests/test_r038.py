"""Spec: docs/SPEC.md §§2–5 and docs/group06.md#r038."""

def test_encode_normal():
    from record_codecs.group06 import encode_r038 as encode, decode_r038 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_038': 'ON', 'qty_038': 'R38', 'flag_038': 22, 'mode_038': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group06 import encode_r038 as encode, decode_r038 as decode
    assert decode({'v_038': 'ON', 'qty_038': 'R38', 'flag_038': 22, 'mode_038': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group06 import encode_r038 as encode, decode_r038 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_038': 'R38', 'flag_038': 22, 'mode_038': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_038': None, 'qty_038': 'R38', 'flag_038': 22, 'mode_038': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_038': 'ON', 'qty_038': 'H38', 'flag_038': 22, 'mode_038': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_038': 'ON', 'flag_038': 22, 'mode_038': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_038': 'ON', 'qty_038': 'R38', 'flag_038': 22}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_038': 'ON', 'qty_038': 'R38', 'flag_038': 22, 'mode_038': None}
    assert decode({'qty_038': 'R38', 'flag_038': 22, 'mode_038': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_038': None, 'qty_038': 'R38', 'flag_038': 22, 'mode_038': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_038': 'ON', 'flag_038': 22, 'mode_038': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_038': 'ON', 'qty_038': None, 'flag_038': 22, 'mode_038': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_038': 'ON', 'qty_038': 'R38', 'mode_038': ['red', 'blue']})
    assert error.value.args == ('flag_038',)
    with pytest.raises(ValueError) as error:
        decode({'v_038': 'ON', 'qty_038': 'R38', 'flag_038': None, 'mode_038': ['red', 'blue']})
    assert error.value.args == ('flag_038',)
    assert decode({'v_038': 'ON', 'qty_038': 'R38', 'flag_038': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_038': 'ON', 'qty_038': 'R38', 'flag_038': 22, 'mode_038': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group06 import encode_r038 as encode, decode_r038 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_038': 'OFF', 'qty_038': 'D38', 'flag_038': -34, 'mode_038': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_038'] is not value['labels_3']
    result['mode_038'].append("changed")
    assert value == before
    value = {'v_038': 'OFF', 'qty_038': 'D38', 'flag_038': -34, 'mode_038': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_038']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_038': 'OFF', 'qty_038': 'H38', 'flag_038': 0, 'mode_038': []}
    assert decode({'v_038': 'OFF', 'qty_038': 'H38', 'flag_038': 0, 'mode_038': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
