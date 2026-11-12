"""Spec: docs/SPEC.md §§2–5 and docs/group23.md#r140."""

def test_encode_normal():
    from record_codecs.group23 import encode_r140 as encode, decode_r140 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_140': 'ON', 'qty_140': 'R140', 'flag_140': 110, 'mode_140': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group23 import encode_r140 as encode, decode_r140 as decode
    assert decode({'v_140': 'ON', 'qty_140': 'R140', 'flag_140': 110, 'mode_140': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group23 import encode_r140 as encode, decode_r140 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_140': 'R140', 'flag_140': 110, 'mode_140': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_140': 'ON', 'flag_140': 110, 'mode_140': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_140': 'ON', 'qty_140': 'R140', 'flag_140': 30, 'mode_140': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_140': 'ON', 'qty_140': 'R140', 'flag_140': None, 'mode_140': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_140': 'ON', 'qty_140': 'R140', 'flag_140': 110}
    with pytest.raises(KeyError) as error:
        decode({'qty_140': 'R140', 'flag_140': 110, 'mode_140': ['red', 'blue']})
    assert error.value.args == ('v_140',)
    assert decode({'v_140': None, 'qty_140': 'R140', 'flag_140': 110, 'mode_140': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_140': 'ON', 'flag_140': 110, 'mode_140': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_140': 'ON', 'qty_140': None, 'flag_140': 110, 'mode_140': ['red', 'blue']})
    assert error.value.args == ('qty_140',)
    assert decode({'v_140': 'ON', 'qty_140': 'R140', 'mode_140': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_140': 'ON', 'qty_140': 'R140', 'flag_140': None, 'mode_140': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_140': 'ON', 'qty_140': 'R140', 'flag_140': 110})
    assert error.value.args == ('mode_140',)
    assert decode({'v_140': 'ON', 'qty_140': 'R140', 'flag_140': 110, 'mode_140': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group23 import encode_r140 as encode, decode_r140 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_140': 'OFF', 'qty_140': 'D140', 'flag_140': -170, 'mode_140': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_140'] is not value['labels_3']
    result['mode_140'].append("changed")
    assert value == before
    value = {'v_140': 'OFF', 'qty_140': 'D140', 'flag_140': -170, 'mode_140': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_140']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_140': 'OFF', 'qty_140': 'H140', 'flag_140': 0, 'mode_140': []}
    assert decode({'v_140': 'OFF', 'qty_140': 'H140', 'flag_140': 0, 'mode_140': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
