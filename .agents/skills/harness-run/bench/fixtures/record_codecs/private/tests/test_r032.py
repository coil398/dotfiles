"""Spec: docs/SPEC.md §§2–5 and docs/group05.md#r032."""

def test_encode_normal():
    from record_codecs.group05 import encode_r032 as encode, decode_r032 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_032': 'ON', 'qty_032': 'R32', 'flag_032': 110, 'mode_032': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group05 import encode_r032 as encode, decode_r032 as decode
    assert decode({'v_032': 'ON', 'qty_032': 'R32', 'flag_032': 110, 'mode_032': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group05 import encode_r032 as encode, decode_r032 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_032': 'R32', 'flag_032': 110, 'mode_032': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_032': 'ON', 'flag_032': 110, 'mode_032': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_032': 'ON', 'qty_032': 'R32', 'flag_032': 30, 'mode_032': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_032': 'ON', 'qty_032': 'R32', 'flag_032': None, 'mode_032': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_032': 'ON', 'qty_032': 'R32', 'flag_032': 110}
    with pytest.raises(KeyError) as error:
        decode({'qty_032': 'R32', 'flag_032': 110, 'mode_032': ['red', 'blue']})
    assert error.value.args == ('v_032',)
    assert decode({'v_032': None, 'qty_032': 'R32', 'flag_032': 110, 'mode_032': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_032': 'ON', 'flag_032': 110, 'mode_032': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_032': 'ON', 'qty_032': None, 'flag_032': 110, 'mode_032': ['red', 'blue']})
    assert error.value.args == ('qty_032',)
    assert decode({'v_032': 'ON', 'qty_032': 'R32', 'mode_032': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_032': 'ON', 'qty_032': 'R32', 'flag_032': None, 'mode_032': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_032': 'ON', 'qty_032': 'R32', 'flag_032': 110})
    assert error.value.args == ('mode_032',)
    assert decode({'v_032': 'ON', 'qty_032': 'R32', 'flag_032': 110, 'mode_032': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group05 import encode_r032 as encode, decode_r032 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_032': 'OFF', 'qty_032': 'D32', 'flag_032': -170, 'mode_032': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_032'] is not value['labels_3']
    result['mode_032'].append("changed")
    assert value == before
    value = {'v_032': 'OFF', 'qty_032': 'D32', 'flag_032': -170, 'mode_032': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_032']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_032': 'OFF', 'qty_032': 'H32', 'flag_032': 0, 'mode_032': []}
    assert decode({'v_032': 'OFF', 'qty_032': 'H32', 'flag_032': 0, 'mode_032': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
