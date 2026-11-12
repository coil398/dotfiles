"""Spec: docs/SPEC.md §§2–5 and docs/group10.md#r062."""

def test_encode_normal():
    from record_codecs.group10 import encode_r062 as encode, decode_r062 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_062': 'ON', 'qty_062': 'R62', 'flag_062': 22, 'mode_062': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group10 import encode_r062 as encode, decode_r062 as decode
    assert decode({'v_062': 'ON', 'qty_062': 'R62', 'flag_062': 22, 'mode_062': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group10 import encode_r062 as encode, decode_r062 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_062': 'OFF', 'qty_062': 'R62', 'flag_062': 22, 'mode_062': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_062': 'ON', 'qty_062': None, 'flag_062': 22, 'mode_062': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_062': 'ON', 'qty_062': 'R62', 'mode_062': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_062': 'ON', 'qty_062': 'R62', 'mode_062': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_062': 'ON', 'qty_062': 'R62', 'flag_062': 22, 'mode_062': ['default']}
    result = encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    result['mode_062'].append("changed")
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_062': 'ON', 'qty_062': 'R62', 'flag_062': 22, 'mode_062': ['default']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None})
    assert error.value.args == ('labels_3',)
    assert decode({'qty_062': 'R62', 'flag_062': 22, 'mode_062': ['red', 'blue']}) == {'active_0': False, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_062': None, 'qty_062': 'R62', 'flag_062': 22, 'mode_062': ['red', 'blue']})
    assert error.value.args == ('v_062',)
    with pytest.raises(KeyError) as error:
        decode({'v_062': 'ON', 'flag_062': 22, 'mode_062': ['red', 'blue']})
    assert error.value.args == ('qty_062',)
    assert decode({'v_062': 'ON', 'qty_062': None, 'flag_062': 22, 'mode_062': ['red', 'blue']}) == {'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_062': 'ON', 'qty_062': 'R62', 'mode_062': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_062': 'ON', 'qty_062': 'R62', 'flag_062': None, 'mode_062': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_062': 'ON', 'qty_062': 'R62', 'flag_062': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    result = decode({'v_062': 'ON', 'qty_062': 'R62', 'flag_062': 22})
    result['labels_3'].append("changed")
    assert decode({'v_062': 'ON', 'qty_062': 'R62', 'flag_062': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    with pytest.raises(ValueError) as error:
        decode({'v_062': 'ON', 'qty_062': 'R62', 'flag_062': 22, 'mode_062': None})
    assert error.value.args == ('mode_062',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group10 import encode_r062 as encode, decode_r062 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_062': 'OFF', 'qty_062': 'D62', 'flag_062': -34, 'mode_062': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_062'] is not value['labels_3']
    result['mode_062'].append("changed")
    assert value == before
    value = {'v_062': 'OFF', 'qty_062': 'D62', 'flag_062': -34, 'mode_062': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_062']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_062': 'OFF', 'qty_062': 'H62', 'flag_062': 0, 'mode_062': []}
    assert decode({'v_062': 'OFF', 'qty_062': 'H62', 'flag_062': 0, 'mode_062': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
