"""Spec: docs/SPEC.md §§2–5 and docs/group07.md#r044."""

def test_encode_normal():
    from record_codecs.group07 import encode_r044 as encode, decode_r044 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_044': 'ON', 'qty_044': 'R44', 'flag_044': 110, 'mode_044': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group07 import encode_r044 as encode, decode_r044 as decode
    assert decode({'v_044': 'ON', 'qty_044': 'R44', 'flag_044': 110, 'mode_044': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group07 import encode_r044 as encode, decode_r044 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_044': 'OFF', 'qty_044': 'R44', 'flag_044': 110, 'mode_044': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_044': 'ON', 'qty_044': None, 'flag_044': 110, 'mode_044': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_044': 'ON', 'qty_044': 'R44', 'mode_044': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_044': 'ON', 'qty_044': 'R44', 'mode_044': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_044': 'ON', 'qty_044': 'R44', 'flag_044': 110, 'mode_044': ['default']}
    result = encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    result['mode_044'].append("changed")
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_044': 'ON', 'qty_044': 'R44', 'flag_044': 110, 'mode_044': ['default']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None})
    assert error.value.args == ('labels_3',)
    assert decode({'qty_044': 'R44', 'flag_044': 110, 'mode_044': ['red', 'blue']}) == {'active_0': False, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_044': None, 'qty_044': 'R44', 'flag_044': 110, 'mode_044': ['red', 'blue']})
    assert error.value.args == ('v_044',)
    with pytest.raises(KeyError) as error:
        decode({'v_044': 'ON', 'flag_044': 110, 'mode_044': ['red', 'blue']})
    assert error.value.args == ('qty_044',)
    assert decode({'v_044': 'ON', 'qty_044': None, 'flag_044': 110, 'mode_044': ['red', 'blue']}) == {'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_044': 'ON', 'qty_044': 'R44', 'mode_044': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_044': 'ON', 'qty_044': 'R44', 'flag_044': None, 'mode_044': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_044': 'ON', 'qty_044': 'R44', 'flag_044': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    result = decode({'v_044': 'ON', 'qty_044': 'R44', 'flag_044': 110})
    result['labels_3'].append("changed")
    assert decode({'v_044': 'ON', 'qty_044': 'R44', 'flag_044': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    with pytest.raises(ValueError) as error:
        decode({'v_044': 'ON', 'qty_044': 'R44', 'flag_044': 110, 'mode_044': None})
    assert error.value.args == ('mode_044',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group07 import encode_r044 as encode, decode_r044 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_044': 'OFF', 'qty_044': 'D44', 'flag_044': -170, 'mode_044': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_044'] is not value['labels_3']
    result['mode_044'].append("changed")
    assert value == before
    value = {'v_044': 'OFF', 'qty_044': 'D44', 'flag_044': -170, 'mode_044': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_044']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_044': 'OFF', 'qty_044': 'H44', 'flag_044': 0, 'mode_044': []}
    assert decode({'v_044': 'OFF', 'qty_044': 'H44', 'flag_044': 0, 'mode_044': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
