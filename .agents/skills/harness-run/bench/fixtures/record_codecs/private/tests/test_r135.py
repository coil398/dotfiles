"""Spec: docs/SPEC.md §§2–5 and docs/group22.md#r135."""

def test_encode_normal():
    from record_codecs.group22 import encode_r135 as encode, decode_r135 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_135': 'R135', 'qty_135': 22, 'flag_135': ['red', 'blue'], 'mode_135': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group22 import encode_r135 as encode, decode_r135 as decode
    assert decode({'v_135': 'R135', 'qty_135': 22, 'flag_135': ['red', 'blue'], 'mode_135': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group22 import encode_r135 as encode, decode_r135 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_135': 'H135', 'qty_135': 22, 'flag_135': ['red', 'blue'], 'mode_135': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_135': None, 'qty_135': 22, 'flag_135': ['red', 'blue'], 'mode_135': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_135': 'R135', 'flag_135': ['red', 'blue'], 'mode_135': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_135': 'R135', 'qty_135': 22, 'mode_135': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_135': 'R135', 'qty_135': 22, 'flag_135': ['red', 'blue'], 'mode_135': 'unset'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_135': 'R135', 'qty_135': 22, 'flag_135': ['red', 'blue'], 'mode_135': None}
    assert decode({'qty_135': 22, 'flag_135': ['red', 'blue'], 'mode_135': 'snow 雪'}) == {'state_0': 'held', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_135': None, 'qty_135': 22, 'flag_135': ['red', 'blue'], 'mode_135': 'snow 雪'}) == {'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_135': 'R135', 'flag_135': ['red', 'blue'], 'mode_135': 'snow 雪'})
    assert error.value.args == ('qty_135',)
    assert decode({'v_135': 'R135', 'qty_135': None, 'flag_135': ['red', 'blue'], 'mode_135': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_135': 'R135', 'qty_135': 22, 'mode_135': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_135': 'R135', 'qty_135': 22, 'flag_135': None, 'mode_135': 'snow 雪'})
    assert error.value.args == ('flag_135',)
    assert decode({'v_135': 'R135', 'qty_135': 22, 'flag_135': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'unset'}
    assert decode({'v_135': 'R135', 'qty_135': 22, 'flag_135': ['red', 'blue'], 'mode_135': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group22 import encode_r135 as encode, decode_r135 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_135': 'D135', 'qty_135': -34, 'flag_135': ['', 'a', 'a', '雪'], 'mode_135': ''}
    assert value == before
    assert result is not value
    assert result['flag_135'] is not value['labels_2']
    result['flag_135'].append("changed")
    assert value == before
    value = {'v_135': 'D135', 'qty_135': -34, 'flag_135': ['', 'a', 'a', '雪'], 'mode_135': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_135']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_135': 'H135', 'qty_135': 0, 'flag_135': [], 'mode_135': ''}
    assert decode({'v_135': 'H135', 'qty_135': 0, 'flag_135': [], 'mode_135': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
