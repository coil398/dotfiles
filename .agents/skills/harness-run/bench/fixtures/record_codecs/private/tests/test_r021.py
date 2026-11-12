"""Spec: docs/SPEC.md §§2–5 and docs/group03.md#r021."""

def test_encode_normal():
    from record_codecs.group03 import encode_r021 as encode, decode_r021 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_021': 'R21', 'qty_021': 110, 'flag_021': ['red', 'blue'], 'mode_021': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group03 import encode_r021 as encode, decode_r021 as decode
    assert decode({'v_021': 'R21', 'qty_021': 110, 'flag_021': ['red', 'blue'], 'mode_021': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group03 import encode_r021 as encode, decode_r021 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_021': 110, 'flag_021': ['red', 'blue'], 'mode_021': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_021': 110, 'flag_021': ['red', 'blue'], 'mode_021': 'snow 雪'}
    assert encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_021': 'R21', 'qty_021': 30, 'flag_021': ['red', 'blue'], 'mode_021': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}) == {'v_021': 'R21', 'qty_021': 110, 'flag_021': None, 'mode_021': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_021': 'R21', 'qty_021': 110, 'flag_021': ['red', 'blue']}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_021': 'R21', 'qty_021': 110, 'flag_021': ['red', 'blue']}
    assert decode({'qty_021': 110, 'flag_021': ['red', 'blue'], 'mode_021': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_021': None, 'qty_021': 110, 'flag_021': ['red', 'blue'], 'mode_021': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_021': 'R21', 'flag_021': ['red', 'blue'], 'mode_021': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 3, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_021': 'R21', 'qty_021': None, 'flag_021': ['red', 'blue'], 'mode_021': 'snow 雪'})
    assert error.value.args == ('qty_021',)
    with pytest.raises(KeyError) as error:
        decode({'v_021': 'R21', 'qty_021': 110, 'mode_021': 'snow 雪'})
    assert error.value.args == ('flag_021',)
    assert decode({'v_021': 'R21', 'qty_021': 110, 'flag_021': None, 'mode_021': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}
    assert decode({'v_021': 'R21', 'qty_021': 110, 'flag_021': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}
    assert decode({'v_021': 'R21', 'qty_021': 110, 'flag_021': ['red', 'blue'], 'mode_021': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group03 import encode_r021 as encode, decode_r021 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_021': 'D21', 'qty_021': -170, 'flag_021': ['', 'a', 'a', '雪'], 'mode_021': ''}
    assert value == before
    assert result is not value
    assert result['flag_021'] is not value['labels_2']
    result['flag_021'].append("changed")
    assert value == before
    value = {'v_021': 'D21', 'qty_021': -170, 'flag_021': ['', 'a', 'a', '雪'], 'mode_021': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_021']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_021': 'H21', 'qty_021': 0, 'flag_021': [], 'mode_021': ''}
    assert decode({'v_021': 'H21', 'qty_021': 0, 'flag_021': [], 'mode_021': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
