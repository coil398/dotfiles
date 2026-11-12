"""Spec: docs/SPEC.md §§2–5 and docs/group10.md#r063."""

def test_encode_normal():
    from record_codecs.group10 import encode_r063 as encode, decode_r063 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_063': 'R63', 'qty_063': 22, 'flag_063': ['red', 'blue'], 'mode_063': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group10 import encode_r063 as encode, decode_r063 as decode
    assert decode({'v_063': 'R63', 'qty_063': 22, 'flag_063': ['red', 'blue'], 'mode_063': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group10 import encode_r063 as encode, decode_r063 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_063': 'H63', 'qty_063': 22, 'flag_063': ['red', 'blue'], 'mode_063': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_063': None, 'qty_063': 22, 'flag_063': ['red', 'blue'], 'mode_063': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_063': 'R63', 'flag_063': ['red', 'blue'], 'mode_063': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_063': 'R63', 'qty_063': 22, 'mode_063': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_063': 'R63', 'qty_063': 22, 'flag_063': ['red', 'blue'], 'mode_063': 'unset'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_063': 'R63', 'qty_063': 22, 'flag_063': ['red', 'blue'], 'mode_063': None}
    assert decode({'qty_063': 22, 'flag_063': ['red', 'blue'], 'mode_063': 'snow 雪'}) == {'state_0': 'held', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_063': None, 'qty_063': 22, 'flag_063': ['red', 'blue'], 'mode_063': 'snow 雪'}) == {'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_063': 'R63', 'flag_063': ['red', 'blue'], 'mode_063': 'snow 雪'})
    assert error.value.args == ('qty_063',)
    assert decode({'v_063': 'R63', 'qty_063': None, 'flag_063': ['red', 'blue'], 'mode_063': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_063': 'R63', 'qty_063': 22, 'mode_063': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_063': 'R63', 'qty_063': 22, 'flag_063': None, 'mode_063': 'snow 雪'})
    assert error.value.args == ('flag_063',)
    assert decode({'v_063': 'R63', 'qty_063': 22, 'flag_063': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'unset'}
    assert decode({'v_063': 'R63', 'qty_063': 22, 'flag_063': ['red', 'blue'], 'mode_063': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group10 import encode_r063 as encode, decode_r063 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_063': 'D63', 'qty_063': -34, 'flag_063': ['', 'a', 'a', '雪'], 'mode_063': ''}
    assert value == before
    assert result is not value
    assert result['flag_063'] is not value['labels_2']
    result['flag_063'].append("changed")
    assert value == before
    value = {'v_063': 'D63', 'qty_063': -34, 'flag_063': ['', 'a', 'a', '雪'], 'mode_063': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_063']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_063': 'H63', 'qty_063': 0, 'flag_063': [], 'mode_063': ''}
    assert decode({'v_063': 'H63', 'qty_063': 0, 'flag_063': [], 'mode_063': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
