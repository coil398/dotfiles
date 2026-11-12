"""Spec: docs/SPEC.md §§2–5 and docs/group19.md#r116."""

def test_encode_normal():
    from record_codecs.group19 import encode_r116 as encode, decode_r116 as decode
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue'], 'ignored': 'extra'}) == {'v_116': 'ON', 'qty_116': 'R116', 'flag_116': 110, 'mode_116': ['red', 'blue']}

def test_decode_normal():
    from record_codecs.group19 import encode_r116 as encode, decode_r116 as decode
    assert decode({'v_116': 'ON', 'qty_116': 'R116', 'flag_116': 110, 'mode_116': ['red', 'blue'], 'ignored': 'extra'}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}

def test_missing_null():
    import pytest
    from record_codecs.group19 import encode_r116 as encode, decode_r116 as decode
    assert encode({'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_116': 'OFF', 'qty_116': 'R116', 'flag_116': 110, 'mode_116': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': None, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('active_0',)
    with pytest.raises(KeyError) as error:
        encode({'active_0': True, 'amount_2': 11, 'labels_3': ['red', 'blue']})
    assert error.value.args == ('state_1',)
    assert encode({'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}) == {'v_116': 'ON', 'qty_116': None, 'flag_116': 110, 'mode_116': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}) == {'v_116': 'ON', 'qty_116': 'R116', 'mode_116': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': None, 'labels_3': ['red', 'blue']}) == {'v_116': 'ON', 'qty_116': 'R116', 'mode_116': ['red', 'blue']}
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_116': 'ON', 'qty_116': 'R116', 'flag_116': 110, 'mode_116': ['default']}
    result = encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11})
    result['mode_116'].append("changed")
    assert encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11}) == {'v_116': 'ON', 'qty_116': 'R116', 'flag_116': 110, 'mode_116': ['default']}
    with pytest.raises(ValueError) as error:
        encode({'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': None})
    assert error.value.args == ('labels_3',)
    assert decode({'qty_116': 'R116', 'flag_116': 110, 'mode_116': ['red', 'blue']}) == {'active_0': False, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['red', 'blue']}
    with pytest.raises(ValueError) as error:
        decode({'v_116': None, 'qty_116': 'R116', 'flag_116': 110, 'mode_116': ['red', 'blue']})
    assert error.value.args == ('v_116',)
    with pytest.raises(KeyError) as error:
        decode({'v_116': 'ON', 'flag_116': 110, 'mode_116': ['red', 'blue']})
    assert error.value.args == ('qty_116',)
    assert decode({'v_116': 'ON', 'qty_116': None, 'flag_116': 110, 'mode_116': ['red', 'blue']}) == {'active_0': True, 'state_1': None, 'amount_2': 11, 'labels_3': ['red', 'blue']}
    assert decode({'v_116': 'ON', 'qty_116': 'R116', 'mode_116': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_116': 'ON', 'qty_116': 'R116', 'flag_116': None, 'mode_116': ['red', 'blue']}) == {'active_0': True, 'state_1': 'ready', 'labels_3': ['red', 'blue']}
    assert decode({'v_116': 'ON', 'qty_116': 'R116', 'flag_116': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    result = decode({'v_116': 'ON', 'qty_116': 'R116', 'flag_116': 110})
    result['labels_3'].append("changed")
    assert decode({'v_116': 'ON', 'qty_116': 'R116', 'flag_116': 110}) == {'active_0': True, 'state_1': 'ready', 'amount_2': 11, 'labels_3': ['default']}
    with pytest.raises(ValueError) as error:
        decode({'v_116': 'ON', 'qty_116': 'R116', 'flag_116': 110, 'mode_116': None})
    assert error.value.args == ('mode_116',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group19 import encode_r116 as encode, decode_r116 as decode
    value = {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_116': 'OFF', 'qty_116': 'D116', 'flag_116': -170, 'mode_116': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['mode_116'] is not value['labels_3']
    result['mode_116'].append("changed")
    assert value == before
    value = {'v_116': 'OFF', 'qty_116': 'D116', 'flag_116': -170, 'mode_116': ['', 'a', 'a', '雪']}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'active_0': False, 'state_1': 'done', 'amount_2': -17, 'labels_3': ['', 'a', 'a', '雪']}
    assert value == before
    assert result is not value
    assert result['labels_3'] is not value['mode_116']
    result['labels_3'].append("changed")
    assert value == before
    assert encode({'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}) == {'v_116': 'OFF', 'qty_116': 'H116', 'flag_116': 0, 'mode_116': []}
    assert decode({'v_116': 'OFF', 'qty_116': 'H116', 'flag_116': 0, 'mode_116': []}) == {'active_0': False, 'state_1': 'held', 'amount_2': 0, 'labels_3': []}
