"""Spec: docs/SPEC.md §§2–5 and docs/group20.md#r122."""

def test_encode_normal():
    from record_codecs.group20 import encode_r122 as encode, decode_r122 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_122': 'ON', 'qty_122': 'R122', 'flag_122': 22, 'mode_122': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group20 import encode_r122 as encode, decode_r122 as decode
    assert decode({'v_122': 'ON', 'qty_122': 'R122', 'flag_122': 22, 'mode_122': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group20 import encode_r122 as encode, decode_r122 as decode
    with pytest.raises(KeyError) as error:
        encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    assert encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'qty_122': 'R122', 'flag_122': 22, 'mode_122': ['red', 'blue']}
    assert encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_122': 'ON', 'flag_122': 22, 'mode_122': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_122': 'ON', 'qty_122': 'R122', 'flag_122': 6, 'mode_122': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_122': 'ON', 'qty_122': 'R122', 'flag_122': None, 'mode_122': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    assert error.value.args == ('labels_3',)
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None}) == {'v_122': 'ON', 'qty_122': 'R122', 'flag_122': 22}
    with pytest.raises(KeyError) as error:
        decode({'qty_122': 'R122', 'flag_122': 22, 'mode_122': ['red', 'blue']})
    assert error.value.args == ('v_122',)
    assert decode({'v_122': None, 'qty_122': 'R122', 'flag_122': 22, 'mode_122': ['red', 'blue']}) == {'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_122': 'ON', 'flag_122': 22, 'mode_122': ['red', 'blue']}) == {'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_122': 'ON', 'qty_122': None, 'flag_122': 22, 'mode_122': ['red', 'blue']})
    assert error.value.args == ('qty_122',)
    assert decode({'v_122': 'ON', 'qty_122': 'R122', 'mode_122': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 3, 'labels_3': ['red', 'blue']}
    assert decode({'v_122': 'ON', 'qty_122': 'R122', 'flag_122': None, 'mode_122': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}
    with pytest.raises(KeyError) as error:
        decode({'v_122': 'ON', 'qty_122': 'R122', 'flag_122': 22})
    assert error.value.args == ('mode_122',)
    assert decode({'v_122': 'ON', 'qty_122': 'R122', 'flag_122': 22, 'mode_122': None}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group20 import encode_r122 as encode, decode_r122 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_122': 'OFF', 'qty_122': 'D122', 'flag_122': -34, 'mode_122': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_122'] is not value['labels_3']
    result['mode_122'].append("changed")
    assert value == before
    value = {'v_122': 'OFF', 'qty_122': 'D122', 'flag_122': -34, 'mode_122': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_122']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_122': 'OFF', 'qty_122': 'H122', 'flag_122': 0, 'mode_122': []}
    assert decode({'v_122': 'OFF', 'qty_122': 'H122', 'flag_122': 0, 'mode_122': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
