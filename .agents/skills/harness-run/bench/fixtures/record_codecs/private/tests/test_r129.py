"""Spec: docs/SPEC.md §§2–5 and docs/group21.md#r129."""

def test_encode_normal():
    from record_codecs.group21 import encode_r129 as encode, decode_r129 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_129': 'R129', 'qty_129': 110, 'flag_129': ['red', 'blue'], 'mode_129': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group21 import encode_r129 as encode, decode_r129 as decode
    assert decode({'v_129': 'R129', 'qty_129': 110, 'flag_129': ['red', 'blue'], 'mode_129': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group21 import encode_r129 as encode, decode_r129 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_129': 110, 'flag_129': ['red', 'blue'], 'mode_129': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_129': 110, 'flag_129': ['red', 'blue'], 'mode_129': 'snow 雪'}
    assert encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_129': 'R129', 'qty_129': 30, 'flag_129': ['red', 'blue'], 'mode_129': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}) == {'v_129': 'R129', 'qty_129': 110, 'flag_129': None, 'mode_129': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_129': 'R129', 'qty_129': 110, 'flag_129': ['red', 'blue']}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_129': 'R129', 'qty_129': 110, 'flag_129': ['red', 'blue']}
    assert decode({'qty_129': 110, 'flag_129': ['red', 'blue'], 'mode_129': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_129': None, 'qty_129': 110, 'flag_129': ['red', 'blue'], 'mode_129': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_129': 'R129', 'flag_129': ['red', 'blue'], 'mode_129': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 3, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_129': 'R129', 'qty_129': None, 'flag_129': ['red', 'blue'], 'mode_129': 'snow 雪'})
    assert error.value.args == ('qty_129',)
    with pytest.raises(KeyError) as error:
        decode({'v_129': 'R129', 'qty_129': 110, 'mode_129': 'snow 雪'})
    assert error.value.args == ('flag_129',)
    assert decode({'v_129': 'R129', 'qty_129': 110, 'flag_129': None, 'mode_129': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}
    assert decode({'v_129': 'R129', 'qty_129': 110, 'flag_129': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}
    assert decode({'v_129': 'R129', 'qty_129': 110, 'flag_129': ['red', 'blue'], 'mode_129': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group21 import encode_r129 as encode, decode_r129 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_129': 'D129', 'qty_129': -170, 'flag_129': ['', 'a', 'a', '雪'], 'mode_129': ''}
    assert value == before
    assert result is not value
    assert result['flag_129'] is not value['labels_2']
    result['flag_129'].append("changed")
    assert value == before
    value = {'v_129': 'D129', 'qty_129': -170, 'flag_129': ['', 'a', 'a', '雪'], 'mode_129': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_129']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_129': 'H129', 'qty_129': 0, 'flag_129': [], 'mode_129': ''}
    assert decode({'v_129': 'H129', 'qty_129': 0, 'flag_129': [], 'mode_129': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
