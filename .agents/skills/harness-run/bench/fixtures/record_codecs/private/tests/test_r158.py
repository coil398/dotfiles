"""Spec: docs/SPEC.md §§2–5 and docs/group26.md#r158."""

def test_encode_normal():
    from record_codecs.group26 import encode_r158 as encode, decode_r158 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_158': 'ON', 'qty_158': 'R158', 'flag_158': 22, 'mode_158': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group26 import encode_r158 as encode, decode_r158 as decode
    assert decode({'v_158': 'ON', 'qty_158': 'R158', 'flag_158': 22, 'mode_158': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group26 import encode_r158 as encode, decode_r158 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_158': 'R158', 'flag_158': 22, 'mode_158': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_158': 'ON', 'flag_158': 22, 'mode_158': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_158': 'ON', 'qty_158': 'R158', 'flag_158': 6, 'mode_158': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_158': 'ON', 'qty_158': 'R158', 'flag_158': None, 'mode_158': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_158': 'ON', 'qty_158': 'R158', 'flag_158': 22}
    with pytest.raises(KeyError) as error:
        decode({'qty_158': 'R158', 'flag_158': 22, 'mode_158': ['red', 'blue']})
    assert error.value.args == ('v_158',)
    assert decode({'v_158': None, 'qty_158': 'R158', 'flag_158': 22, 'mode_158': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_158': 'ON', 'flag_158': 22, 'mode_158': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_158': 'ON', 'qty_158': None, 'flag_158': 22, 'mode_158': ['red', 'blue']})
    assert error.value.args == ('qty_158',)
    assert decode({'v_158': 'ON', 'qty_158': 'R158', 'mode_158': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_158': 'ON', 'qty_158': 'R158', 'flag_158': None, 'mode_158': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_158': 'ON', 'qty_158': 'R158', 'flag_158': 22})
    assert error.value.args == ('mode_158',)
    assert decode({'v_158': 'ON', 'qty_158': 'R158', 'flag_158': 22, 'mode_158': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group26 import encode_r158 as encode, decode_r158 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_158': 'OFF', 'qty_158': 'D158', 'flag_158': -34, 'mode_158': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_158'] is not value['labels_3']
    result['mode_158'].append("changed")
    assert value == before
    value = {'v_158': 'OFF', 'qty_158': 'D158', 'flag_158': -34, 'mode_158': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_158']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_158': 'OFF', 'qty_158': 'H158', 'flag_158': 0, 'mode_158': []}
    assert decode({'v_158': 'OFF', 'qty_158': 'H158', 'flag_158': 0, 'mode_158': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
