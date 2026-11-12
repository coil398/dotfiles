"""Spec: docs/SPEC.md §§2–5 and docs/group04.md#r027."""

def test_encode_normal():
    from record_codecs.group04 import encode_r027 as encode, decode_r027 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_027': 'R27', 'qty_027': 22, 'flag_027': ['red', 'blue'], 'mode_027': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group04 import encode_r027 as encode, decode_r027 as decode
    assert decode({'v_027': 'R27', 'qty_027': 22, 'flag_027': ['red', 'blue'], 'mode_027': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group04 import encode_r027 as encode, decode_r027 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_027': 'H27', 'qty_027': 22, 'flag_027': ['red', 'blue'], 'mode_027': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_027': None, 'qty_027': 22, 'flag_027': ['red', 'blue'], 'mode_027': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_027': 'R27', 'flag_027': ['red', 'blue'], 'mode_027': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_027': 'R27', 'qty_027': 22, 'mode_027': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_027': 'R27', 'qty_027': 22, 'flag_027': ['red', 'blue'], 'mode_027': 'unset'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_027': 'R27', 'qty_027': 22, 'flag_027': ['red', 'blue'], 'mode_027': None}
    assert decode({'qty_027': 22, 'flag_027': ['red', 'blue'], 'mode_027': 'snow 雪'}) == {'state_0': 'held', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_027': None, 'qty_027': 22, 'flag_027': ['red', 'blue'], 'mode_027': 'snow 雪'}) == {'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_027': 'R27', 'flag_027': ['red', 'blue'], 'mode_027': 'snow 雪'})
    assert error.value.args == ('qty_027',)
    assert decode({'v_027': 'R27', 'qty_027': None, 'flag_027': ['red', 'blue'], 'mode_027': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_027': 'R27', 'qty_027': 22, 'mode_027': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_027': 'R27', 'qty_027': 22, 'flag_027': None, 'mode_027': 'snow 雪'})
    assert error.value.args == ('flag_027',)
    assert decode({'v_027': 'R27', 'qty_027': 22, 'flag_027': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'unset'}
    assert decode({'v_027': 'R27', 'qty_027': 22, 'flag_027': ['red', 'blue'], 'mode_027': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group04 import encode_r027 as encode, decode_r027 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_027': 'D27', 'qty_027': -34, 'flag_027': ['', 'a', 'a', '雪'], 'mode_027': ''}
    assert value == before
    assert result is not value
    assert result['flag_027'] is not value['labels_2']
    result['flag_027'].append("changed")
    assert value == before
    value = {'v_027': 'D27', 'qty_027': -34, 'flag_027': ['', 'a', 'a', '雪'], 'mode_027': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_027']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_027': 'H27', 'qty_027': 0, 'flag_027': [], 'mode_027': ''}
    assert decode({'v_027': 'H27', 'qty_027': 0, 'flag_027': [], 'mode_027': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
