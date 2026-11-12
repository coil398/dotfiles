"""Spec: docs/SPEC.md §§2–5 and docs/group02.md#r014."""

def test_encode_normal():
    from record_codecs.group02 import encode_r014 as encode, decode_r014 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_014': 'ON', 'qty_014': 'R14', 'flag_014': 22, 'mode_014': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group02 import encode_r014 as encode, decode_r014 as decode
    assert decode({'v_014': 'ON', 'qty_014': 'R14', 'flag_014': 22, 'mode_014': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group02 import encode_r014 as encode, decode_r014 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_014': 'R14', 'flag_014': 22, 'mode_014': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_014': 'ON', 'flag_014': 22, 'mode_014': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_014': 'ON', 'qty_014': 'R14', 'flag_014': 6, 'mode_014': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_014': 'ON', 'qty_014': 'R14', 'flag_014': None, 'mode_014': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_014': 'ON', 'qty_014': 'R14', 'flag_014': 22}
    with pytest.raises(KeyError) as error:
        decode({'qty_014': 'R14', 'flag_014': 22, 'mode_014': ['red', 'blue']})
    assert error.value.args == ('v_014',)
    assert decode({'v_014': None, 'qty_014': 'R14', 'flag_014': 22, 'mode_014': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_014': 'ON', 'flag_014': 22, 'mode_014': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_014': 'ON', 'qty_014': None, 'flag_014': 22, 'mode_014': ['red', 'blue']})
    assert error.value.args == ('qty_014',)
    assert decode({'v_014': 'ON', 'qty_014': 'R14', 'mode_014': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_014': 'ON', 'qty_014': 'R14', 'flag_014': None, 'mode_014': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_014': 'ON', 'qty_014': 'R14', 'flag_014': 22})
    assert error.value.args == ('mode_014',)
    assert decode({'v_014': 'ON', 'qty_014': 'R14', 'flag_014': 22, 'mode_014': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group02 import encode_r014 as encode, decode_r014 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_014': 'OFF', 'qty_014': 'D14', 'flag_014': -34, 'mode_014': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_014'] is not value['labels_3']
    result['mode_014'].append("changed")
    assert value == before
    value = {'v_014': 'OFF', 'qty_014': 'D14', 'flag_014': -34, 'mode_014': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_014']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_014': 'OFF', 'qty_014': 'H14', 'flag_014': 0, 'mode_014': []}
    assert decode({'v_014': 'OFF', 'qty_014': 'H14', 'flag_014': 0, 'mode_014': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
