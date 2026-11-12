"""Spec: docs/SPEC.md §§2–5 and docs/group30.md#r182."""

def test_encode_normal():
    from record_codecs.group30 import encode_r182 as encode, decode_r182 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_182': 'ON', 'qty_182': 'R182', 'flag_182': 22, 'mode_182': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group30 import encode_r182 as encode, decode_r182 as decode
    assert decode({'v_182': 'ON', 'qty_182': 'R182', 'flag_182': 22, 'mode_182': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group30 import encode_r182 as encode, decode_r182 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_182': 'R182', 'flag_182': 22, 'mode_182': ['red', 'blue']}
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_182': None, 'qty_182': 'R182', 'flag_182': 22, 'mode_182': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_182': 'ON', 'qty_182': 'H182', 'flag_182': 22, 'mode_182': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_182': 'ON', 'flag_182': 22, 'mode_182': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('amount_2',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_182': 'ON', 'qty_182': 'R182', 'flag_182': 22}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_182': 'ON', 'qty_182': 'R182', 'flag_182': 22, 'mode_182': None}
    assert decode({'qty_182': 'R182', 'flag_182': 22, 'mode_182': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_182': None, 'qty_182': 'R182', 'flag_182': 22, 'mode_182': ['red', 'blue']}) == {'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_182': 'ON', 'flag_182': 22, 'mode_182': ['red', 'blue']}) == {'active_0': True, 'state_1': 'held', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_182': 'ON', 'qty_182': None, 'flag_182': 22, 'mode_182': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_182': 'ON', 'qty_182': 'R182', 'mode_182': ['red', 'blue']})
    assert error.value.args == ('flag_182',)
    with pytest.raises(ValueError) as error:
        decode({'v_182': 'ON', 'qty_182': 'R182', 'flag_182': None, 'mode_182': ['red', 'blue']})
    assert error.value.args == ('flag_182',)
    assert decode({'v_182': 'ON', 'qty_182': 'R182', 'flag_182': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}
    assert decode({'v_182': 'ON', 'qty_182': 'R182', 'flag_182': 22, 'mode_182': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group30 import encode_r182 as encode, decode_r182 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_182': 'OFF', 'qty_182': 'D182', 'flag_182': -34, 'mode_182': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_182'] is not value['labels_3']
    result['mode_182'].append("changed")
    assert value == before
    value = {'v_182': 'OFF', 'qty_182': 'D182', 'flag_182': -34, 'mode_182': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_182']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_182': 'OFF', 'qty_182': 'H182', 'flag_182': 0, 'mode_182': []}
    assert decode({'v_182': 'OFF', 'qty_182': 'H182', 'flag_182': 0, 'mode_182': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
