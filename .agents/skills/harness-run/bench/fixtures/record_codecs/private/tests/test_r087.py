"""Spec: docs/SPEC.md §§2–5 and docs/group14.md#r087."""

def test_encode_normal():
    from record_codecs.group14 import encode_r087 as encode, decode_r087 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_087': 'R87', 'qty_087': 22, 'flag_087': ['red', 'blue'], 'mode_087': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group14 import encode_r087 as encode, decode_r087 as decode
    assert decode({'v_087': 'R87', 'qty_087': 22, 'flag_087': ['red', 'blue'], 'mode_087': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group14 import encode_r087 as encode, decode_r087 as decode
    with pytest.raises(KeyError) as error:
        encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('state_0',)
    with pytest.raises(ValueError) as error:
        encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('state_0',)
    assert encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_087': 'R87', 'flag_087': ['red', 'blue'], 'mode_087': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_087': 'R87', 'qty_087': None, 'flag_087': ['red', 'blue'], 'mode_087': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_087': 'R87', 'qty_087': 22, 'flag_087': ['default'], 'mode_087': 'snow 雪'}
    result = encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'})
    result['flag_087'].append("changed")
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_087': 'R87', 'qty_087': 22, 'flag_087': ['default'], 'mode_087': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}) == {'v_087': 'R87', 'qty_087': 22, 'mode_087': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']})
    assert error.value.args == ('title_3',)
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None})
    assert error.value.args == ('title_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_087': 22, 'flag_087': ['red', 'blue'], 'mode_087': 'snow 雪'})
    assert error.value.args == ('v_087',)
    with pytest.raises(ValueError) as error:
        decode({'v_087': None, 'qty_087': 22, 'flag_087': ['red', 'blue'], 'mode_087': 'snow 雪'})
    assert error.value.args == ('v_087',)
    assert decode({'v_087': 'R87', 'flag_087': ['red', 'blue'], 'mode_087': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_087': 'R87', 'qty_087': None, 'flag_087': ['red', 'blue'], 'mode_087': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_087': 'R87', 'qty_087': 22, 'mode_087': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['default'], 'title_3': 'snow 雪'}
    result = decode({'v_087': 'R87', 'qty_087': 22, 'mode_087': 'snow 雪'})
    result['labels_2'].append("changed")
    assert decode({'v_087': 'R87', 'qty_087': 22, 'mode_087': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['default'], 'title_3': 'snow 雪'}
    assert decode({'v_087': 'R87', 'qty_087': 22, 'flag_087': None, 'mode_087': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_087': 'R87', 'qty_087': 22, 'flag_087': ['red', 'blue']})
    assert error.value.args == ('mode_087',)
    with pytest.raises(ValueError) as error:
        decode({'v_087': 'R87', 'qty_087': 22, 'flag_087': ['red', 'blue'], 'mode_087': None})
    assert error.value.args == ('mode_087',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group14 import encode_r087 as encode, decode_r087 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_087': 'D87', 'qty_087': -34, 'flag_087': ['', 'a', 'a', '雪'], 'mode_087': ''}
    assert value == before
    assert result is not value
    assert result['flag_087'] is not value['labels_2']
    result['flag_087'].append("changed")
    assert value == before
    value = {'v_087': 'D87', 'qty_087': -34, 'flag_087': ['', 'a', 'a', '雪'], 'mode_087': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_087']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_087': 'H87', 'qty_087': 0, 'flag_087': [], 'mode_087': ''}
    assert decode({'v_087': 'H87', 'qty_087': 0, 'flag_087': [], 'mode_087': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
