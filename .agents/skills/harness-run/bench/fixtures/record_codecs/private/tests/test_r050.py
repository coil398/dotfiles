"""Spec: docs/SPEC.md §§2–5 and docs/group08.md#r050."""

def test_encode_normal():
    from record_codecs.group08 import encode_r050 as encode, decode_r050 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_050': 'ON', 'qty_050': 'R50', 'flag_050': 22, 'mode_050': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group08 import encode_r050 as encode, decode_r050 as decode
    assert decode({'v_050': 'ON', 'qty_050': 'R50', 'flag_050': 22, 'mode_050': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group08 import encode_r050 as encode, decode_r050 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_050': 'R50', 'flag_050': 22, 'mode_050': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_050': 'ON', 'flag_050': 22, 'mode_050': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_050': 'ON', 'qty_050': 'R50', 'flag_050': 6, 'mode_050': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_050': 'ON', 'qty_050': 'R50', 'flag_050': None, 'mode_050': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_050': 'ON', 'qty_050': 'R50', 'flag_050': 22}
    with pytest.raises(KeyError) as error:
        decode({'qty_050': 'R50', 'flag_050': 22, 'mode_050': ['red', 'blue']})
    assert error.value.args == ('v_050',)
    assert decode({'v_050': None, 'qty_050': 'R50', 'flag_050': 22, 'mode_050': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_050': 'ON', 'flag_050': 22, 'mode_050': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_050': 'ON', 'qty_050': None, 'flag_050': 22, 'mode_050': ['red', 'blue']})
    assert error.value.args == ('qty_050',)
    assert decode({'v_050': 'ON', 'qty_050': 'R50', 'mode_050': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_050': 'ON', 'qty_050': 'R50', 'flag_050': None, 'mode_050': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_050': 'ON', 'qty_050': 'R50', 'flag_050': 22})
    assert error.value.args == ('mode_050',)
    assert decode({'v_050': 'ON', 'qty_050': 'R50', 'flag_050': 22, 'mode_050': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group08 import encode_r050 as encode, decode_r050 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_050': 'OFF', 'qty_050': 'D50', 'flag_050': -34, 'mode_050': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_050'] is not value['labels_3']
    result['mode_050'].append("changed")
    assert value == before
    value = {'v_050': 'OFF', 'qty_050': 'D50', 'flag_050': -34, 'mode_050': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_050']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_050': 'OFF', 'qty_050': 'H50', 'flag_050': 0, 'mode_050': []}
    assert decode({'v_050': 'OFF', 'qty_050': 'H50', 'flag_050': 0, 'mode_050': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
