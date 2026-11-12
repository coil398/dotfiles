"""Spec: docs/SPEC.md §§2–5 and docs/group04.md#r026."""

def test_encode_normal():
    from record_codecs.group04 import encode_r026 as encode, decode_r026 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_026': 'ON', 'qty_026': 'R26', 'flag_026': 22, 'mode_026': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group04 import encode_r026 as encode, decode_r026 as decode
    assert decode({'v_026': 'ON', 'qty_026': 'R26', 'flag_026': 22, 'mode_026': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group04 import encode_r026 as encode, decode_r026 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_026': 'OFF', 'qty_026': 'R26', 'flag_026': 22, 'mode_026': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_026': 'ON', 'qty_026': None, 'flag_026': 22, 'mode_026': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_026': 'ON', 'qty_026': 'R26', 'mode_026': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_026': 'ON', 'qty_026': 'R26', 'mode_026': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_026': 'ON', 'qty_026': 'R26', 'flag_026': 22, 'mode_026': ['default']}
    result = encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    result['mode_026'].append("changed")
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_026': 'ON', 'qty_026': 'R26', 'flag_026': 22, 'mode_026': ['default']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None})
    assert error.value.args == ('labels_3',)
    assert decode({'qty_026': 'R26', 'flag_026': 22, 'mode_026': ['red', 'blue']}) == {'active_0': False, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_026': None, 'qty_026': 'R26', 'flag_026': 22, 'mode_026': ['red', 'blue']})
    assert error.value.args == ('v_026',)
    with pytest.raises(KeyError) as error:
        decode({'v_026': 'ON', 'flag_026': 22, 'mode_026': ['red', 'blue']})
    assert error.value.args == ('qty_026',)
    assert decode({'v_026': 'ON', 'qty_026': None, 'flag_026': 22, 'mode_026': ['red', 'blue']}) == {'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_026': 'ON', 'qty_026': 'R26', 'mode_026': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_026': 'ON', 'qty_026': 'R26', 'flag_026': None, 'mode_026': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_026': 'ON', 'qty_026': 'R26', 'flag_026': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    result = decode({'v_026': 'ON', 'qty_026': 'R26', 'flag_026': 22})
    result['labels_3'].append("changed")
    assert decode({'v_026': 'ON', 'qty_026': 'R26', 'flag_026': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    with pytest.raises(ValueError) as error:
        decode({'v_026': 'ON', 'qty_026': 'R26', 'flag_026': 22, 'mode_026': None})
    assert error.value.args == ('mode_026',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group04 import encode_r026 as encode, decode_r026 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_026': 'OFF', 'qty_026': 'D26', 'flag_026': -34, 'mode_026': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_026'] is not value['labels_3']
    result['mode_026'].append("changed")
    assert value == before
    value = {'v_026': 'OFF', 'qty_026': 'D26', 'flag_026': -34, 'mode_026': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_026']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_026': 'OFF', 'qty_026': 'H26', 'flag_026': 0, 'mode_026': []}
    assert decode({'v_026': 'OFF', 'qty_026': 'H26', 'flag_026': 0, 'mode_026': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
