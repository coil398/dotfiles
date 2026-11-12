"""Spec: docs/SPEC.md §§2–5 and docs/group18.md#r111."""

def test_encode_normal():
    from record_codecs.group18 import encode_r111 as encode, decode_r111 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_111': 'R111', 'qty_111': 22, 'flag_111': ['red', 'blue'], 'mode_111': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group18 import encode_r111 as encode, decode_r111 as decode
    assert decode({'v_111': 'R111', 'qty_111': 22, 'flag_111': ['red', 'blue'], 'mode_111': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group18 import encode_r111 as encode, decode_r111 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_111': 22, 'flag_111': ['red', 'blue'], 'mode_111': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_111': 22, 'flag_111': ['red', 'blue'], 'mode_111': 'snow 雪'}
    assert encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_111': 'R111', 'qty_111': 6, 'flag_111': ['red', 'blue'], 'mode_111': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}) == {'v_111': 'R111', 'qty_111': 22, 'flag_111': None, 'mode_111': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_111': 'R111', 'qty_111': 22, 'flag_111': ['red', 'blue']}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_111': 'R111', 'qty_111': 22, 'flag_111': ['red', 'blue']}
    assert decode({'qty_111': 22, 'flag_111': ['red', 'blue'], 'mode_111': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_111': None, 'qty_111': 22, 'flag_111': ['red', 'blue'], 'mode_111': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_111': 'R111', 'flag_111': ['red', 'blue'], 'mode_111': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 3, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_111': 'R111', 'qty_111': None, 'flag_111': ['red', 'blue'], 'mode_111': 'snow 雪'})
    assert error.value.args == ('qty_111',)
    with pytest.raises(KeyError) as error:
        decode({'v_111': 'R111', 'qty_111': 22, 'mode_111': 'snow 雪'})
    assert error.value.args == ('flag_111',)
    assert decode({'v_111': 'R111', 'qty_111': 22, 'flag_111': None, 'mode_111': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}
    assert decode({'v_111': 'R111', 'qty_111': 22, 'flag_111': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}
    assert decode({'v_111': 'R111', 'qty_111': 22, 'flag_111': ['red', 'blue'], 'mode_111': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group18 import encode_r111 as encode, decode_r111 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_111': 'D111', 'qty_111': -34, 'flag_111': ['', 'a', 'a', '雪'], 'mode_111': ''}
    assert value == before
    assert result is not value
    assert result['flag_111'] is not value['labels_2']
    result['flag_111'].append("changed")
    assert value == before
    value = {'v_111': 'D111', 'qty_111': -34, 'flag_111': ['', 'a', 'a', '雪'], 'mode_111': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_111']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_111': 'H111', 'qty_111': 0, 'flag_111': [], 'mode_111': ''}
    assert decode({'v_111': 'H111', 'qty_111': 0, 'flag_111': [], 'mode_111': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
