"""Spec: docs/SPEC.md §§2–5 and docs/group25.md#r152."""

def test_encode_normal():
    from record_codecs.group25 import encode_r152 as encode, decode_r152 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_152': 'ON', 'qty_152': 'R152', 'flag_152': 110, 'mode_152': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group25 import encode_r152 as encode, decode_r152 as decode
    assert decode({'v_152': 'ON', 'qty_152': 'R152', 'flag_152': 110, 'mode_152': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group25 import encode_r152 as encode, decode_r152 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_152': 'OFF', 'qty_152': 'R152', 'flag_152': 110, 'mode_152': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_152': 'ON', 'qty_152': None, 'flag_152': 110, 'mode_152': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_152': 'ON', 'qty_152': 'R152', 'mode_152': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_152': 'ON', 'qty_152': 'R152', 'mode_152': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_152': 'ON', 'qty_152': 'R152', 'flag_152': 110, 'mode_152': ['default']}
    result = encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    result['mode_152'].append("changed")
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_152': 'ON', 'qty_152': 'R152', 'flag_152': 110, 'mode_152': ['default']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None})
    assert error.value.args == ('labels_3',)
    assert decode({'qty_152': 'R152', 'flag_152': 110, 'mode_152': ['red', 'blue']}) == {'active_0': False, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_152': None, 'qty_152': 'R152', 'flag_152': 110, 'mode_152': ['red', 'blue']})
    assert error.value.args == ('v_152',)
    with pytest.raises(KeyError) as error:
        decode({'v_152': 'ON', 'flag_152': 110, 'mode_152': ['red', 'blue']})
    assert error.value.args == ('qty_152',)
    assert decode({'v_152': 'ON', 'qty_152': None, 'flag_152': 110, 'mode_152': ['red', 'blue']}) == {'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_152': 'ON', 'qty_152': 'R152', 'mode_152': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_152': 'ON', 'qty_152': 'R152', 'flag_152': None, 'mode_152': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_152': 'ON', 'qty_152': 'R152', 'flag_152': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    result = decode({'v_152': 'ON', 'qty_152': 'R152', 'flag_152': 110})
    result['labels_3'].append("changed")
    assert decode({'v_152': 'ON', 'qty_152': 'R152', 'flag_152': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    with pytest.raises(ValueError) as error:
        decode({'v_152': 'ON', 'qty_152': 'R152', 'flag_152': 110, 'mode_152': None})
    assert error.value.args == ('mode_152',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group25 import encode_r152 as encode, decode_r152 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_152': 'OFF', 'qty_152': 'D152', 'flag_152': -170, 'mode_152': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_152'] is not value['labels_3']
    result['mode_152'].append("changed")
    assert value == before
    value = {'v_152': 'OFF', 'qty_152': 'D152', 'flag_152': -170, 'mode_152': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_152']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_152': 'OFF', 'qty_152': 'H152', 'flag_152': 0, 'mode_152': []}
    assert decode({'v_152': 'OFF', 'qty_152': 'H152', 'flag_152': 0, 'mode_152': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
