"""Spec: docs/SPEC.md §§2–5 and docs/group12.md#r075."""

def test_encode_normal():
    from record_codecs.group12 import encode_r075 as encode, decode_r075 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_075': 'R75', 'qty_075': 22, 'flag_075': ['red', 'blue'], 'mode_075': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group12 import encode_r075 as encode, decode_r075 as decode
    assert decode({'v_075': 'R75', 'qty_075': 22, 'flag_075': ['red', 'blue'], 'mode_075': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group12 import encode_r075 as encode, decode_r075 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_075': 22, 'flag_075': ['red', 'blue'], 'mode_075': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_075': 22, 'flag_075': ['red', 'blue'], 'mode_075': 'snow 雪'}
    assert encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_075': 'R75', 'qty_075': 6, 'flag_075': ['red', 'blue'], 'mode_075': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}) == {'v_075': 'R75', 'qty_075': 22, 'flag_075': None, 'mode_075': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_075': 'R75', 'qty_075': 22, 'flag_075': ['red', 'blue']}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_075': 'R75', 'qty_075': 22, 'flag_075': ['red', 'blue']}
    assert decode({'qty_075': 22, 'flag_075': ['red', 'blue'], 'mode_075': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_075': None, 'qty_075': 22, 'flag_075': ['red', 'blue'], 'mode_075': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_075': 'R75', 'flag_075': ['red', 'blue'], 'mode_075': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 3, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_075': 'R75', 'qty_075': None, 'flag_075': ['red', 'blue'], 'mode_075': 'snow 雪'})
    assert error.value.args == ('qty_075',)
    with pytest.raises(KeyError) as error:
        decode({'v_075': 'R75', 'qty_075': 22, 'mode_075': 'snow 雪'})
    assert error.value.args == ('flag_075',)
    assert decode({'v_075': 'R75', 'qty_075': 22, 'flag_075': None, 'mode_075': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}
    assert decode({'v_075': 'R75', 'qty_075': 22, 'flag_075': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}
    assert decode({'v_075': 'R75', 'qty_075': 22, 'flag_075': ['red', 'blue'], 'mode_075': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group12 import encode_r075 as encode, decode_r075 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_075': 'D75', 'qty_075': -34, 'flag_075': ['', 'a', 'a', '雪'], 'mode_075': ''}
    assert value == before
    assert result is not value
    assert result['flag_075'] is not value['labels_2']
    result['flag_075'].append("changed")
    assert value == before
    value = {'v_075': 'D75', 'qty_075': -34, 'flag_075': ['', 'a', 'a', '雪'], 'mode_075': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_075']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_075': 'H75', 'qty_075': 0, 'flag_075': [], 'mode_075': ''}
    assert decode({'v_075': 'H75', 'qty_075': 0, 'flag_075': [], 'mode_075': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
