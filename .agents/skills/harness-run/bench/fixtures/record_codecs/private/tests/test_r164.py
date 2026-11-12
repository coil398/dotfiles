"""Spec: docs/SPEC.md §§2–5 and docs/group27.md#r164."""

def test_encode_normal():
    from record_codecs.group27 import encode_r164 as encode, decode_r164 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_164': 'ON', 'qty_164': 'R164', 'flag_164': 110, 'mode_164': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group27 import encode_r164 as encode, decode_r164 as decode
    assert decode({'v_164': 'ON', 'qty_164': 'R164', 'flag_164': 110, 'mode_164': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group27 import encode_r164 as encode, decode_r164 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_164': 'R164', 'flag_164': 110, 'mode_164': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_164': None, 'qty_164': 'R164', 'flag_164': 110, 'mode_164': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_164': 'ON', 'qty_164': 'H164', 'flag_164': 110, 'mode_164': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_164': 'ON', 'flag_164': 110, 'mode_164': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_164': 'ON', 'qty_164': 'R164', 'flag_164': 110}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_164': 'ON', 'qty_164': 'R164', 'flag_164': 110, 'mode_164': None}
    assert decode({'qty_164': 'R164', 'flag_164': 110, 'mode_164': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_164': None, 'qty_164': 'R164', 'flag_164': 110, 'mode_164': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_164': 'ON', 'flag_164': 110, 'mode_164': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_164': 'ON', 'qty_164': None, 'flag_164': 110, 'mode_164': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_164': 'ON', 'qty_164': 'R164', 'mode_164': ['red', 'blue']})
    assert error.value.args == ('flag_164',)
    with pytest.raises(ValueError) as error:
        decode({'v_164': 'ON', 'qty_164': 'R164', 'flag_164': None, 'mode_164': ['red', 'blue']})
    assert error.value.args == ('flag_164',)
    assert decode({'v_164': 'ON', 'qty_164': 'R164', 'flag_164': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_164': 'ON', 'qty_164': 'R164', 'flag_164': 110, 'mode_164': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group27 import encode_r164 as encode, decode_r164 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_164': 'OFF', 'qty_164': 'D164', 'flag_164': -170, 'mode_164': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_164'] is not value['labels_3']
    result['mode_164'].append("changed")
    assert value == before
    value = {'v_164': 'OFF', 'qty_164': 'D164', 'flag_164': -170, 'mode_164': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_164']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_164': 'OFF', 'qty_164': 'H164', 'flag_164': 0, 'mode_164': []}
    assert decode({'v_164': 'OFF', 'qty_164': 'H164', 'flag_164': 0, 'mode_164': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
