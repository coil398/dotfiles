"""Spec: docs/SPEC.md §§2–5 and docs/group28.md#r171."""

def test_encode_normal():
    from record_codecs.group28 import encode_r171 as encode, decode_r171 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_171': 'R171', 'qty_171': 22, 'flag_171': ['red', 'blue'], 'mode_171': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group28 import encode_r171 as encode, decode_r171 as decode
    assert decode({'v_171': 'R171', 'qty_171': 22, 'flag_171': ['red', 'blue'], 'mode_171': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group28 import encode_r171 as encode, decode_r171 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_171': 'H171', 'qty_171': 22, 'flag_171': ['red', 'blue'], 'mode_171': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_171': None, 'qty_171': 22, 'flag_171': ['red', 'blue'], 'mode_171': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_171': 'R171', 'flag_171': ['red', 'blue'], 'mode_171': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_171': 'R171', 'qty_171': 22, 'mode_171': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_171': 'R171', 'qty_171': 22, 'flag_171': ['red', 'blue'], 'mode_171': 'unset'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_171': 'R171', 'qty_171': 22, 'flag_171': ['red', 'blue'], 'mode_171': None}
    assert decode({'qty_171': 22, 'flag_171': ['red', 'blue'], 'mode_171': 'snow 雪'}) == {'state_0': 'held', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_171': None, 'qty_171': 22, 'flag_171': ['red', 'blue'], 'mode_171': 'snow 雪'}) == {'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_171': 'R171', 'flag_171': ['red', 'blue'], 'mode_171': 'snow 雪'})
    assert error.value.args == ('qty_171',)
    assert decode({'v_171': 'R171', 'qty_171': None, 'flag_171': ['red', 'blue'], 'mode_171': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_171': 'R171', 'qty_171': 22, 'mode_171': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_171': 'R171', 'qty_171': 22, 'flag_171': None, 'mode_171': 'snow 雪'})
    assert error.value.args == ('flag_171',)
    assert decode({'v_171': 'R171', 'qty_171': 22, 'flag_171': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'unset'}
    assert decode({'v_171': 'R171', 'qty_171': 22, 'flag_171': ['red', 'blue'], 'mode_171': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group28 import encode_r171 as encode, decode_r171 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_171': 'D171', 'qty_171': -34, 'flag_171': ['', 'a', 'a', '雪'], 'mode_171': ''}
    assert value == before
    assert result is not value
    assert result['flag_171'] is not value['labels_2']
    result['flag_171'].append("changed")
    assert value == before
    value = {'v_171': 'D171', 'qty_171': -34, 'flag_171': ['', 'a', 'a', '雪'], 'mode_171': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_171']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_171': 'H171', 'qty_171': 0, 'flag_171': [], 'mode_171': ''}
    assert decode({'v_171': 'H171', 'qty_171': 0, 'flag_171': [], 'mode_171': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
