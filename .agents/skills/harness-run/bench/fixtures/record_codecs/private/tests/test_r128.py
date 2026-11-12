"""Spec: docs/SPEC.md §§2–5 and docs/group21.md#r128."""

def test_encode_normal():
    from record_codecs.group21 import encode_r128 as encode, decode_r128 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_128': 'ON', 'qty_128': 'R128', 'flag_128': 110, 'mode_128': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group21 import encode_r128 as encode, decode_r128 as decode
    assert decode({'v_128': 'ON', 'qty_128': 'R128', 'flag_128': 110, 'mode_128': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group21 import encode_r128 as encode, decode_r128 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_128': 'R128', 'flag_128': 110, 'mode_128': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_128': None, 'qty_128': 'R128', 'flag_128': 110, 'mode_128': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_128': 'ON', 'qty_128': 'H128', 'flag_128': 110, 'mode_128': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_128': 'ON', 'flag_128': 110, 'mode_128': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_128': 'ON', 'qty_128': 'R128', 'flag_128': 110}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_128': 'ON', 'qty_128': 'R128', 'flag_128': 110, 'mode_128': None}
    assert decode({'qty_128': 'R128', 'flag_128': 110, 'mode_128': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_128': None, 'qty_128': 'R128', 'flag_128': 110, 'mode_128': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_128': 'ON', 'flag_128': 110, 'mode_128': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_128': 'ON', 'qty_128': None, 'flag_128': 110, 'mode_128': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_128': 'ON', 'qty_128': 'R128', 'mode_128': ['red', 'blue']})
    assert error.value.args == ('flag_128',)
    with pytest.raises(ValueError) as error:
        decode({'v_128': 'ON', 'qty_128': 'R128', 'flag_128': None, 'mode_128': ['red', 'blue']})
    assert error.value.args == ('flag_128',)
    assert decode({'v_128': 'ON', 'qty_128': 'R128', 'flag_128': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_128': 'ON', 'qty_128': 'R128', 'flag_128': 110, 'mode_128': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group21 import encode_r128 as encode, decode_r128 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_128': 'OFF', 'qty_128': 'D128', 'flag_128': -170, 'mode_128': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_128'] is not value['labels_3']
    result['mode_128'].append("changed")
    assert value == before
    value = {'v_128': 'OFF', 'qty_128': 'D128', 'flag_128': -170, 'mode_128': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_128']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_128': 'OFF', 'qty_128': 'H128', 'flag_128': 0, 'mode_128': []}
    assert decode({'v_128': 'OFF', 'qty_128': 'H128', 'flag_128': 0, 'mode_128': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
