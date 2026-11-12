"""Spec: docs/SPEC.md §§2–5 and docs/group31.md#r189."""

def test_encode_normal():
    from record_codecs.group31 import encode_r189 as encode, decode_r189 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_189': 'R189', 'qty_189': 110, 'flag_189': ['red', 'blue'], 'mode_189': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group31 import encode_r189 as encode, decode_r189 as decode
    assert decode({'v_189': 'R189', 'qty_189': 110, 'flag_189': ['red', 'blue'], 'mode_189': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group31 import encode_r189 as encode, decode_r189 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_189': 'H189', 'qty_189': 110, 'flag_189': ['red', 'blue'], 'mode_189': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_189': None, 'qty_189': 110, 'flag_189': ['red', 'blue'], 'mode_189': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_189': 'R189', 'flag_189': ['red', 'blue'], 'mode_189': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_189': 'R189', 'qty_189': 110, 'mode_189': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_189': 'R189', 'qty_189': 110, 'flag_189': ['red', 'blue'], 'mode_189': 'unset'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_189': 'R189', 'qty_189': 110, 'flag_189': ['red', 'blue'], 'mode_189': None}
    assert decode({'qty_189': 110, 'flag_189': ['red', 'blue'], 'mode_189': 'snow 雪'}) == {'state_0': 'held', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_189': None, 'qty_189': 110, 'flag_189': ['red', 'blue'], 'mode_189': 'snow 雪'}) == {'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_189': 'R189', 'flag_189': ['red', 'blue'], 'mode_189': 'snow 雪'})
    assert error.value.args == ('qty_189',)
    assert decode({'v_189': 'R189', 'qty_189': None, 'flag_189': ['red', 'blue'], 'mode_189': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_189': 'R189', 'qty_189': 110, 'mode_189': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_189': 'R189', 'qty_189': 110, 'flag_189': None, 'mode_189': 'snow 雪'})
    assert error.value.args == ('flag_189',)
    assert decode({'v_189': 'R189', 'qty_189': 110, 'flag_189': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'unset'}
    assert decode({'v_189': 'R189', 'qty_189': 110, 'flag_189': ['red', 'blue'], 'mode_189': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group31 import encode_r189 as encode, decode_r189 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_189': 'D189', 'qty_189': -170, 'flag_189': ['', 'a', 'a', '雪'], 'mode_189': ''}
    assert value == before
    assert result is not value
    assert result['flag_189'] is not value['labels_2']
    result['flag_189'].append("changed")
    assert value == before
    value = {'v_189': 'D189', 'qty_189': -170, 'flag_189': ['', 'a', 'a', '雪'], 'mode_189': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_189']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_189': 'H189', 'qty_189': 0, 'flag_189': [], 'mode_189': ''}
    assert decode({'v_189': 'H189', 'qty_189': 0, 'flag_189': [], 'mode_189': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
