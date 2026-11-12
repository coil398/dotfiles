"""Spec: docs/SPEC.md §§2–5 and docs/group13.md#r081."""

def test_encode_normal():
    from record_codecs.group13 import encode_r081 as encode, decode_r081 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_081': 'R81', 'qty_081': 110, 'flag_081': ['red', 'blue'], 'mode_081': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group13 import encode_r081 as encode, decode_r081 as decode
    assert decode({'v_081': 'R81', 'qty_081': 110, 'flag_081': ['red', 'blue'], 'mode_081': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group13 import encode_r081 as encode, decode_r081 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_081': 'H81', 'qty_081': 110, 'flag_081': ['red', 'blue'], 'mode_081': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_081': None, 'qty_081': 110, 'flag_081': ['red', 'blue'], 'mode_081': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_081': 'R81', 'flag_081': ['red', 'blue'], 'mode_081': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_081': 'R81', 'qty_081': 110, 'mode_081': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_081': 'R81', 'qty_081': 110, 'flag_081': ['red', 'blue'], 'mode_081': 'unset'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_081': 'R81', 'qty_081': 110, 'flag_081': ['red', 'blue'], 'mode_081': None}
    assert decode({'qty_081': 110, 'flag_081': ['red', 'blue'], 'mode_081': 'snow 雪'}) == {'state_0': 'held', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_081': None, 'qty_081': 110, 'flag_081': ['red', 'blue'], 'mode_081': 'snow 雪'}) == {'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_081': 'R81', 'flag_081': ['red', 'blue'], 'mode_081': 'snow 雪'})
    assert error.value.args == ('qty_081',)
    assert decode({'v_081': 'R81', 'qty_081': None, 'flag_081': ['red', 'blue'], 'mode_081': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_081': 'R81', 'qty_081': 110, 'mode_081': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_081': 'R81', 'qty_081': 110, 'flag_081': None, 'mode_081': 'snow 雪'})
    assert error.value.args == ('flag_081',)
    assert decode({'v_081': 'R81', 'qty_081': 110, 'flag_081': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'unset'}
    assert decode({'v_081': 'R81', 'qty_081': 110, 'flag_081': ['red', 'blue'], 'mode_081': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group13 import encode_r081 as encode, decode_r081 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_081': 'D81', 'qty_081': -170, 'flag_081': ['', 'a', 'a', '雪'], 'mode_081': ''}
    assert value == before
    assert result is not value
    assert result['flag_081'] is not value['labels_2']
    result['flag_081'].append("changed")
    assert value == before
    value = {'v_081': 'D81', 'qty_081': -170, 'flag_081': ['', 'a', 'a', '雪'], 'mode_081': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_081']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_081': 'H81', 'qty_081': 0, 'flag_081': [], 'mode_081': ''}
    assert decode({'v_081': 'H81', 'qty_081': 0, 'flag_081': [], 'mode_081': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
