"""Spec: docs/SPEC.md §§2–5 and docs/group11.md#r068."""

def test_encode_normal():
    from record_codecs.group11 import encode_r068 as encode, decode_r068 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_068': 'ON', 'qty_068': 'R68', 'flag_068': 110, 'mode_068': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group11 import encode_r068 as encode, decode_r068 as decode
    assert decode({'v_068': 'ON', 'qty_068': 'R68', 'flag_068': 110, 'mode_068': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group11 import encode_r068 as encode, decode_r068 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_068': 'R68', 'flag_068': 110, 'mode_068': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_068': 'ON', 'flag_068': 110, 'mode_068': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_068': 'ON', 'qty_068': 'R68', 'flag_068': 30, 'mode_068': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_068': 'ON', 'qty_068': 'R68', 'flag_068': None, 'mode_068': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_068': 'ON', 'qty_068': 'R68', 'flag_068': 110}
    with pytest.raises(KeyError) as error:
        decode({'qty_068': 'R68', 'flag_068': 110, 'mode_068': ['red', 'blue']})
    assert error.value.args == ('v_068',)
    assert decode({'v_068': None, 'qty_068': 'R68', 'flag_068': 110, 'mode_068': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_068': 'ON', 'flag_068': 110, 'mode_068': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_068': 'ON', 'qty_068': None, 'flag_068': 110, 'mode_068': ['red', 'blue']})
    assert error.value.args == ('qty_068',)
    assert decode({'v_068': 'ON', 'qty_068': 'R68', 'mode_068': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_068': 'ON', 'qty_068': 'R68', 'flag_068': None, 'mode_068': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_068': 'ON', 'qty_068': 'R68', 'flag_068': 110})
    assert error.value.args == ('mode_068',)
    assert decode({'v_068': 'ON', 'qty_068': 'R68', 'flag_068': 110, 'mode_068': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group11 import encode_r068 as encode, decode_r068 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_068': 'OFF', 'qty_068': 'D68', 'flag_068': -170, 'mode_068': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_068'] is not value['labels_3']
    result['mode_068'].append("changed")
    assert value == before
    value = {'v_068': 'OFF', 'qty_068': 'D68', 'flag_068': -170, 'mode_068': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_068']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_068': 'OFF', 'qty_068': 'H68', 'flag_068': 0, 'mode_068': []}
    assert decode({'v_068': 'OFF', 'qty_068': 'H68', 'flag_068': 0, 'mode_068': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
