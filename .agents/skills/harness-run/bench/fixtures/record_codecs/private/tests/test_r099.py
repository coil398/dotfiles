"""Spec: docs/SPEC.md §§2–5 and docs/group16.md#r099."""

def test_encode_normal():
    from record_codecs.group16 import encode_r099 as encode, decode_r099 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_099': 'R99', 'qty_099': 22, 'flag_099': ['red', 'blue'], 'mode_099': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group16 import encode_r099 as encode, decode_r099 as decode
    assert decode({'v_099': 'R99', 'qty_099': 22, 'flag_099': ['red', 'blue'], 'mode_099': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group16 import encode_r099 as encode, decode_r099 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_099': 'H99', 'qty_099': 22, 'flag_099': ['red', 'blue'], 'mode_099': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_099': None, 'qty_099': 22, 'flag_099': ['red', 'blue'], 'mode_099': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_099': 'R99', 'flag_099': ['red', 'blue'], 'mode_099': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_099': 'R99', 'qty_099': 22, 'mode_099': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_099': 'R99', 'qty_099': 22, 'flag_099': ['red', 'blue'], 'mode_099': 'unset'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_099': 'R99', 'qty_099': 22, 'flag_099': ['red', 'blue'], 'mode_099': None}
    assert decode({'qty_099': 22, 'flag_099': ['red', 'blue'], 'mode_099': 'snow 雪'}) == {'state_0': 'held', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_099': None, 'qty_099': 22, 'flag_099': ['red', 'blue'], 'mode_099': 'snow 雪'}) == {'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_099': 'R99', 'flag_099': ['red', 'blue'], 'mode_099': 'snow 雪'})
    assert error.value.args == ('qty_099',)
    assert decode({'v_099': 'R99', 'qty_099': None, 'flag_099': ['red', 'blue'], 'mode_099': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_099': 'R99', 'qty_099': 22, 'mode_099': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_099': 'R99', 'qty_099': 22, 'flag_099': None, 'mode_099': 'snow 雪'})
    assert error.value.args == ('flag_099',)
    assert decode({'v_099': 'R99', 'qty_099': 22, 'flag_099': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'unset'}
    assert decode({'v_099': 'R99', 'qty_099': 22, 'flag_099': ['red', 'blue'], 'mode_099': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group16 import encode_r099 as encode, decode_r099 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_099': 'D99', 'qty_099': -34, 'flag_099': ['', 'a', 'a', '雪'], 'mode_099': ''}
    assert value == before
    assert result is not value
    assert result['flag_099'] is not value['labels_2']
    result['flag_099'].append("changed")
    assert value == before
    value = {'v_099': 'D99', 'qty_099': -34, 'flag_099': ['', 'a', 'a', '雪'], 'mode_099': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_099']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_099': 'H99', 'qty_099': 0, 'flag_099': [], 'mode_099': ''}
    assert decode({'v_099': 'H99', 'qty_099': 0, 'flag_099': [], 'mode_099': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
