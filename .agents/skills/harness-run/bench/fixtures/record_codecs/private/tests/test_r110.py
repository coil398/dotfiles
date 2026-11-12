"""Spec: docs/SPEC.md §§2–5 and docs/group18.md#r110."""

def test_encode_normal():
    from record_codecs.group18 import encode_r110 as encode, decode_r110 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_110': 'ON', 'qty_110': 'R110', 'flag_110': 22, 'mode_110': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group18 import encode_r110 as encode, decode_r110 as decode
    assert decode({'v_110': 'ON', 'qty_110': 'R110', 'flag_110': 22, 'mode_110': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group18 import encode_r110 as encode, decode_r110 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_110': 'R110', 'flag_110': 22, 'mode_110': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_110': None, 'qty_110': 'R110', 'flag_110': 22, 'mode_110': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_110': 'ON', 'qty_110': 'H110', 'flag_110': 22, 'mode_110': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_110': 'ON', 'flag_110': 22, 'mode_110': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_110': 'ON', 'qty_110': 'R110', 'flag_110': 22}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_110': 'ON', 'qty_110': 'R110', 'flag_110': 22, 'mode_110': None}
    assert decode({'qty_110': 'R110', 'flag_110': 22, 'mode_110': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_110': None, 'qty_110': 'R110', 'flag_110': 22, 'mode_110': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_110': 'ON', 'flag_110': 22, 'mode_110': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_110': 'ON', 'qty_110': None, 'flag_110': 22, 'mode_110': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_110': 'ON', 'qty_110': 'R110', 'mode_110': ['red', 'blue']})
    assert error.value.args == ('flag_110',)
    with pytest.raises(ValueError) as error:
        decode({'v_110': 'ON', 'qty_110': 'R110', 'flag_110': None, 'mode_110': ['red', 'blue']})
    assert error.value.args == ('flag_110',)
    assert decode({'v_110': 'ON', 'qty_110': 'R110', 'flag_110': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_110': 'ON', 'qty_110': 'R110', 'flag_110': 22, 'mode_110': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group18 import encode_r110 as encode, decode_r110 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_110': 'OFF', 'qty_110': 'D110', 'flag_110': -34, 'mode_110': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_110'] is not value['labels_3']
    result['mode_110'].append("changed")
    assert value == before
    value = {'v_110': 'OFF', 'qty_110': 'D110', 'flag_110': -34, 'mode_110': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_110']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_110': 'OFF', 'qty_110': 'H110', 'flag_110': 0, 'mode_110': []}
    assert decode({'v_110': 'OFF', 'qty_110': 'H110', 'flag_110': 0, 'mode_110': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
