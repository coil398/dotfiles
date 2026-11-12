"""Spec: docs/SPEC.md §§2–5 and docs/group19.md#r117."""

def test_encode_normal():
    from record_codecs.group19 import encode_r117 as encode, decode_r117 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_117': 'R117', 'qty_117': 110, 'flag_117': ['red', 'blue'], 'mode_117': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group19 import encode_r117 as encode, decode_r117 as decode
    assert decode({'v_117': 'R117', 'qty_117': 110, 'flag_117': ['red', 'blue'], 'mode_117': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group19 import encode_r117 as encode, decode_r117 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_117': 'H117', 'qty_117': 110, 'flag_117': ['red', 'blue'], 'mode_117': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_117': None, 'qty_117': 110, 'flag_117': ['red', 'blue'], 'mode_117': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_117': 'R117', 'flag_117': ['red', 'blue'], 'mode_117': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_117': 'R117', 'qty_117': 110, 'mode_117': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_117': 'R117', 'qty_117': 110, 'flag_117': ['red', 'blue'], 'mode_117': 'unset'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_117': 'R117', 'qty_117': 110, 'flag_117': ['red', 'blue'], 'mode_117': None}
    assert decode({'qty_117': 110, 'flag_117': ['red', 'blue'], 'mode_117': 'snow 雪'}) == {'state_0': 'held', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_117': None, 'qty_117': 110, 'flag_117': ['red', 'blue'], 'mode_117': 'snow 雪'}) == {'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_117': 'R117', 'flag_117': ['red', 'blue'], 'mode_117': 'snow 雪'})
    assert error.value.args == ('qty_117',)
    assert decode({'v_117': 'R117', 'qty_117': None, 'flag_117': ['red', 'blue'], 'mode_117': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_117': 'R117', 'qty_117': 110, 'mode_117': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_117': 'R117', 'qty_117': 110, 'flag_117': None, 'mode_117': 'snow 雪'})
    assert error.value.args == ('flag_117',)
    assert decode({'v_117': 'R117', 'qty_117': 110, 'flag_117': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'unset'}
    assert decode({'v_117': 'R117', 'qty_117': 110, 'flag_117': ['red', 'blue'], 'mode_117': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group19 import encode_r117 as encode, decode_r117 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_117': 'D117', 'qty_117': -170, 'flag_117': ['', 'a', 'a', '雪'], 'mode_117': ''}
    assert value == before
    assert result is not value
    assert result['flag_117'] is not value['labels_2']
    result['flag_117'].append("changed")
    assert value == before
    value = {'v_117': 'D117', 'qty_117': -170, 'flag_117': ['', 'a', 'a', '雪'], 'mode_117': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_117']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_117': 'H117', 'qty_117': 0, 'flag_117': [], 'mode_117': ''}
    assert decode({'v_117': 'H117', 'qty_117': 0, 'flag_117': [], 'mode_117': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
