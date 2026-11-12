"""Spec: docs/SPEC.md §§2–5 and docs/group28.md#r170."""

def test_encode_normal():
    from record_codecs.group28 import encode_r170 as encode, decode_r170 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_170': 'ON', 'qty_170': 'R170', 'flag_170': 22, 'mode_170': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group28 import encode_r170 as encode, decode_r170 as decode
    assert decode({'v_170': 'ON', 'qty_170': 'R170', 'flag_170': 22, 'mode_170': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group28 import encode_r170 as encode, decode_r170 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_170': 'OFF', 'qty_170': 'R170', 'flag_170': 22, 'mode_170': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_170': 'ON', 'qty_170': None, 'flag_170': 22, 'mode_170': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_170': 'ON', 'qty_170': 'R170', 'mode_170': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_170': 'ON', 'qty_170': 'R170', 'mode_170': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_170': 'ON', 'qty_170': 'R170', 'flag_170': 22, 'mode_170': ['default']}
    result = encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    result['mode_170'].append("changed")
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_170': 'ON', 'qty_170': 'R170', 'flag_170': 22, 'mode_170': ['default']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None})
    assert error.value.args == ('labels_3',)
    assert decode({'qty_170': 'R170', 'flag_170': 22, 'mode_170': ['red', 'blue']}) == {'active_0': False, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_170': None, 'qty_170': 'R170', 'flag_170': 22, 'mode_170': ['red', 'blue']})
    assert error.value.args == ('v_170',)
    with pytest.raises(KeyError) as error:
        decode({'v_170': 'ON', 'flag_170': 22, 'mode_170': ['red', 'blue']})
    assert error.value.args == ('qty_170',)
    assert decode({'v_170': 'ON', 'qty_170': None, 'flag_170': 22, 'mode_170': ['red', 'blue']}) == {'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_170': 'ON', 'qty_170': 'R170', 'mode_170': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_170': 'ON', 'qty_170': 'R170', 'flag_170': None, 'mode_170': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_170': 'ON', 'qty_170': 'R170', 'flag_170': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    result = decode({'v_170': 'ON', 'qty_170': 'R170', 'flag_170': 22})
    result['labels_3'].append("changed")
    assert decode({'v_170': 'ON', 'qty_170': 'R170', 'flag_170': 22}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    with pytest.raises(ValueError) as error:
        decode({'v_170': 'ON', 'qty_170': 'R170', 'flag_170': 22, 'mode_170': None})
    assert error.value.args == ('mode_170',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group28 import encode_r170 as encode, decode_r170 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_170': 'OFF', 'qty_170': 'D170', 'flag_170': -34, 'mode_170': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_170'] is not value['labels_3']
    result['mode_170'].append("changed")
    assert value == before
    value = {'v_170': 'OFF', 'qty_170': 'D170', 'flag_170': -34, 'mode_170': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_170']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_170': 'OFF', 'qty_170': 'H170', 'flag_170': 0, 'mode_170': []}
    assert decode({'v_170': 'OFF', 'qty_170': 'H170', 'flag_170': 0, 'mode_170': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
