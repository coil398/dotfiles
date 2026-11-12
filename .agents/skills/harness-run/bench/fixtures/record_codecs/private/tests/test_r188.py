"""Spec: docs/SPEC.md §§2–5 and docs/group31.md#r188."""

def test_encode_normal():
    from record_codecs.group31 import encode_r188 as encode, decode_r188 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_188': 'ON', 'qty_188': 'R188', 'flag_188': 110, 'mode_188': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group31 import encode_r188 as encode, decode_r188 as decode
    assert decode({'v_188': 'ON', 'qty_188': 'R188', 'flag_188': 110, 'mode_188': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group31 import encode_r188 as encode, decode_r188 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_188': 'OFF', 'qty_188': 'R188', 'flag_188': 110, 'mode_188': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_188': 'ON', 'qty_188': None, 'flag_188': 110, 'mode_188': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_188': 'ON', 'qty_188': 'R188', 'mode_188': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_188': 'ON', 'qty_188': 'R188', 'mode_188': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_188': 'ON', 'qty_188': 'R188', 'flag_188': 110, 'mode_188': ['default']}
    result = encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    result['mode_188'].append("changed")
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_188': 'ON', 'qty_188': 'R188', 'flag_188': 110, 'mode_188': ['default']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None})
    assert error.value.args == ('labels_3',)
    assert decode({'qty_188': 'R188', 'flag_188': 110, 'mode_188': ['red', 'blue']}) == {'active_0': False, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_188': None, 'qty_188': 'R188', 'flag_188': 110, 'mode_188': ['red', 'blue']})
    assert error.value.args == ('v_188',)
    with pytest.raises(KeyError) as error:
        decode({'v_188': 'ON', 'flag_188': 110, 'mode_188': ['red', 'blue']})
    assert error.value.args == ('qty_188',)
    assert decode({'v_188': 'ON', 'qty_188': None, 'flag_188': 110, 'mode_188': ['red', 'blue']}) == {'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_188': 'ON', 'qty_188': 'R188', 'mode_188': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_188': 'ON', 'qty_188': 'R188', 'flag_188': None, 'mode_188': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_188': 'ON', 'qty_188': 'R188', 'flag_188': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    result = decode({'v_188': 'ON', 'qty_188': 'R188', 'flag_188': 110})
    result['labels_3'].append("changed")
    assert decode({'v_188': 'ON', 'qty_188': 'R188', 'flag_188': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    with pytest.raises(ValueError) as error:
        decode({'v_188': 'ON', 'qty_188': 'R188', 'flag_188': 110, 'mode_188': None})
    assert error.value.args == ('mode_188',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group31 import encode_r188 as encode, decode_r188 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_188': 'OFF', 'qty_188': 'D188', 'flag_188': -170, 'mode_188': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_188'] is not value['labels_3']
    result['mode_188'].append("changed")
    assert value == before
    value = {'v_188': 'OFF', 'qty_188': 'D188', 'flag_188': -170, 'mode_188': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_188']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_188': 'OFF', 'qty_188': 'H188', 'flag_188': 0, 'mode_188': []}
    assert decode({'v_188': 'OFF', 'qty_188': 'H188', 'flag_188': 0, 'mode_188': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
