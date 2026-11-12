"""Spec: docs/SPEC.md §§2–5 and docs/group25.md#r153."""

def test_encode_normal():
    from record_codecs.group25 import encode_r153 as encode, decode_r153 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_153': 'R153', 'qty_153': 110, 'flag_153': ['red', 'blue'], 'mode_153': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group25 import encode_r153 as encode, decode_r153 as decode
    assert decode({'v_153': 'R153', 'qty_153': 110, 'flag_153': ['red', 'blue'], 'mode_153': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group25 import encode_r153 as encode, decode_r153 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_153': 'H153', 'qty_153': 110, 'flag_153': ['red', 'blue'], 'mode_153': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_153': None, 'qty_153': 110, 'flag_153': ['red', 'blue'], 'mode_153': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_153': 'R153', 'flag_153': ['red', 'blue'], 'mode_153': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_153': 'R153', 'qty_153': 110, 'mode_153': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_153': 'R153', 'qty_153': 110, 'flag_153': ['red', 'blue'], 'mode_153': 'unset'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_153': 'R153', 'qty_153': 110, 'flag_153': ['red', 'blue'], 'mode_153': None}
    assert decode({'qty_153': 110, 'flag_153': ['red', 'blue'], 'mode_153': 'snow 雪'}) == {'state_0': 'held', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_153': None, 'qty_153': 110, 'flag_153': ['red', 'blue'], 'mode_153': 'snow 雪'}) == {'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_153': 'R153', 'flag_153': ['red', 'blue'], 'mode_153': 'snow 雪'})
    assert error.value.args == ('qty_153',)
    assert decode({'v_153': 'R153', 'qty_153': None, 'flag_153': ['red', 'blue'], 'mode_153': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_153': 'R153', 'qty_153': 110, 'mode_153': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_153': 'R153', 'qty_153': 110, 'flag_153': None, 'mode_153': 'snow 雪'})
    assert error.value.args == ('flag_153',)
    assert decode({'v_153': 'R153', 'qty_153': 110, 'flag_153': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'unset'}
    assert decode({'v_153': 'R153', 'qty_153': 110, 'flag_153': ['red', 'blue'], 'mode_153': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group25 import encode_r153 as encode, decode_r153 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_153': 'D153', 'qty_153': -170, 'flag_153': ['', 'a', 'a', '雪'], 'mode_153': ''}
    assert value == before
    assert result is not value
    assert result['flag_153'] is not value['labels_2']
    result['flag_153'].append("changed")
    assert value == before
    value = {'v_153': 'D153', 'qty_153': -170, 'flag_153': ['', 'a', 'a', '雪'], 'mode_153': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_153']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_153': 'H153', 'qty_153': 0, 'flag_153': [], 'mode_153': ''}
    assert decode({'v_153': 'H153', 'qty_153': 0, 'flag_153': [], 'mode_153': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
