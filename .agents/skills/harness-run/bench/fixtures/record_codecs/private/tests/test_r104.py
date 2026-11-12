"""Spec: docs/SPEC.md §§2–5 and docs/group17.md#r104."""

def test_encode_normal():
    from record_codecs.group17 import encode_r104 as encode, decode_r104 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_104': 'ON', 'qty_104': 'R104', 'flag_104': 110, 'mode_104': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group17 import encode_r104 as encode, decode_r104 as decode
    assert decode({'v_104': 'ON', 'qty_104': 'R104', 'flag_104': 110, 'mode_104': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group17 import encode_r104 as encode, decode_r104 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_104': 'R104', 'flag_104': 110, 'mode_104': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_104': 'ON', 'flag_104': 110, 'mode_104': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_104': 'ON', 'qty_104': 'R104', 'flag_104': 30, 'mode_104': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_104': 'ON', 'qty_104': 'R104', 'flag_104': None, 'mode_104': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_104': 'ON', 'qty_104': 'R104', 'flag_104': 110}
    with pytest.raises(KeyError) as error:
        decode({'qty_104': 'R104', 'flag_104': 110, 'mode_104': ['red', 'blue']})
    assert error.value.args == ('v_104',)
    assert decode({'v_104': None, 'qty_104': 'R104', 'flag_104': 110, 'mode_104': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_104': 'ON', 'flag_104': 110, 'mode_104': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_104': 'ON', 'qty_104': None, 'flag_104': 110, 'mode_104': ['red', 'blue']})
    assert error.value.args == ('qty_104',)
    assert decode({'v_104': 'ON', 'qty_104': 'R104', 'mode_104': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_104': 'ON', 'qty_104': 'R104', 'flag_104': None, 'mode_104': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_104': 'ON', 'qty_104': 'R104', 'flag_104': 110})
    assert error.value.args == ('mode_104',)
    assert decode({'v_104': 'ON', 'qty_104': 'R104', 'flag_104': 110, 'mode_104': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group17 import encode_r104 as encode, decode_r104 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_104': 'OFF', 'qty_104': 'D104', 'flag_104': -170, 'mode_104': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_104'] is not value['labels_3']
    result['mode_104'].append("changed")
    assert value == before
    value = {'v_104': 'OFF', 'qty_104': 'D104', 'flag_104': -170, 'mode_104': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_104']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_104': 'OFF', 'qty_104': 'H104', 'flag_104': 0, 'mode_104': []}
    assert decode({'v_104': 'OFF', 'qty_104': 'H104', 'flag_104': 0, 'mode_104': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
