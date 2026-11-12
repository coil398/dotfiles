"""Spec: docs/SPEC.md §§2–5 and docs/group24.md#r147."""

def test_encode_normal():
    from record_codecs.group24 import encode_r147 as encode, decode_r147 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_147': 'R147', 'qty_147': 22, 'flag_147': ['red', 'blue'], 'mode_147': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group24 import encode_r147 as encode, decode_r147 as decode
    assert decode({'v_147': 'R147', 'qty_147': 22, 'flag_147': ['red', 'blue'], 'mode_147': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group24 import encode_r147 as encode, decode_r147 as decode
    assert encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_147': 22, 'flag_147': ['red', 'blue'], 'mode_147': 'snow 雪'}
    assert encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'qty_147': 22, 'flag_147': ['red', 'blue'], 'mode_147': 'snow 雪'}
    assert encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_147': 'R147', 'qty_147': 6, 'flag_147': ['red', 'blue'], 'mode_147': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('amount_1',)
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'})
    assert error.value.args == ('labels_2',)
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}) == {'v_147': 'R147', 'qty_147': 22, 'flag_147': None, 'mode_147': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}) == {'v_147': 'R147', 'qty_147': 22, 'flag_147': ['red', 'blue']}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None}) == {'v_147': 'R147', 'qty_147': 22, 'flag_147': ['red', 'blue']}
    assert decode({'qty_147': 22, 'flag_147': ['red', 'blue'], 'mode_147': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_147': None, 'qty_147': 22, 'flag_147': ['red', 'blue'], 'mode_147': 'snow 雪'}) == {'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_147': 'R147', 'flag_147': ['red', 'blue'], 'mode_147': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 3, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    with pytest.raises(ValueError) as error:
        decode({'v_147': 'R147', 'qty_147': None, 'flag_147': ['red', 'blue'], 'mode_147': 'snow 雪'})
    assert error.value.args == ('qty_147',)
    with pytest.raises(KeyError) as error:
        decode({'v_147': 'R147', 'qty_147': 22, 'mode_147': 'snow 雪'})
    assert error.value.args == ('flag_147',)
    assert decode({'v_147': 'R147', 'qty_147': 22, 'flag_147': None, 'mode_147': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}
    assert decode({'v_147': 'R147', 'qty_147': 22, 'flag_147': ['red', 'blue']}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}
    assert decode({'v_147': 'R147', 'qty_147': 22, 'flag_147': ['red', 'blue'], 'mode_147': None}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group24 import encode_r147 as encode, decode_r147 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_147': 'D147', 'qty_147': -34, 'flag_147': ['', 'a', 'a', '雪'], 'mode_147': ''}
    assert value == before
    assert result is not value
    assert result['flag_147'] is not value['labels_2']
    result['flag_147'].append("changed")
    assert value == before
    value = {'v_147': 'D147', 'qty_147': -34, 'flag_147': ['', 'a', 'a', '雪'], 'mode_147': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_147']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_147': 'H147', 'qty_147': 0, 'flag_147': [], 'mode_147': ''}
    assert decode({'v_147': 'H147', 'qty_147': 0, 'flag_147': [], 'mode_147': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
