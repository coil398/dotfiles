"""Spec: docs/SPEC.md §§2–5 and docs/group26.md#r159."""

def test_encode_normal():
    from record_codecs.group26 import encode_r159 as encode, decode_r159 as decode
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪', 'ignored': 'extra'}) == {'v_159': 'R159', 'qty_159': 22, 'flag_159': ['red', 'blue'], 'mode_159': 'snow 雪'}

def test_decode_normal():
    from record_codecs.group26 import encode_r159 as encode, decode_r159 as decode
    assert decode({'v_159': 'R159', 'qty_159': 22, 'flag_159': ['red', 'blue'], 'mode_159': 'snow 雪', 'ignored': 'extra'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}

def test_missing_null():
    import pytest
    from record_codecs.group26 import encode_r159 as encode, decode_r159 as decode
    with pytest.raises(KeyError) as error:
        encode({'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('state_0',)
    with pytest.raises(ValueError) as error:
        encode({'state_0': None, 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'})
    assert error.value.args == ('state_0',)
    assert encode({'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_159': 'R159', 'flag_159': ['red', 'blue'], 'mode_159': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}) == {'v_159': 'R159', 'qty_159': None, 'flag_159': ['red', 'blue'], 'mode_159': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_159': 'R159', 'qty_159': 22, 'flag_159': ['default'], 'mode_159': 'snow 雪'}
    result = encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'})
    result['flag_159'].append("changed")
    assert encode({'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}) == {'v_159': 'R159', 'qty_159': 22, 'flag_159': ['default'], 'mode_159': 'snow 雪'}
    assert encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': None, 'title_3': 'snow 雪'}) == {'v_159': 'R159', 'qty_159': 22, 'mode_159': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue']})
    assert error.value.args == ('title_3',)
    with pytest.raises(ValueError) as error:
        encode({'state_0': 'ready', 'amount_1': 11, 'labels_2': ['red', 'blue'], 'title_3': None})
    assert error.value.args == ('title_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_159': 22, 'flag_159': ['red', 'blue'], 'mode_159': 'snow 雪'})
    assert error.value.args == ('v_159',)
    with pytest.raises(ValueError) as error:
        decode({'v_159': None, 'qty_159': 22, 'flag_159': ['red', 'blue'], 'mode_159': 'snow 雪'})
    assert error.value.args == ('v_159',)
    assert decode({'v_159': 'R159', 'flag_159': ['red', 'blue'], 'mode_159': 'snow 雪'}) == {'state_0': 'ready', 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_159': 'R159', 'qty_159': None, 'flag_159': ['red', 'blue'], 'mode_159': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': None, 'labels_2': ['red', 'blue'], 'title_3': 'snow 雪'}
    assert decode({'v_159': 'R159', 'qty_159': 22, 'mode_159': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['default'], 'title_3': 'snow 雪'}
    result = decode({'v_159': 'R159', 'qty_159': 22, 'mode_159': 'snow 雪'})
    result['labels_2'].append("changed")
    assert decode({'v_159': 'R159', 'qty_159': 22, 'mode_159': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'labels_2': ['default'], 'title_3': 'snow 雪'}
    assert decode({'v_159': 'R159', 'qty_159': 22, 'flag_159': None, 'mode_159': 'snow 雪'}) == {'state_0': 'ready', 'amount_1': 11, 'title_3': 'snow 雪'}
    with pytest.raises(KeyError) as error:
        decode({'v_159': 'R159', 'qty_159': 22, 'flag_159': ['red', 'blue']})
    assert error.value.args == ('mode_159',)
    with pytest.raises(ValueError) as error:
        decode({'v_159': 'R159', 'qty_159': 22, 'flag_159': ['red', 'blue'], 'mode_159': None})
    assert error.value.args == ('mode_159',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group26 import encode_r159 as encode, decode_r159 as decode
    value = {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_159': 'D159', 'qty_159': -34, 'flag_159': ['', 'a', 'a', '雪'], 'mode_159': ''}
    assert value == before
    assert result is not value
    assert result['flag_159'] is not value['labels_2']
    result['flag_159'].append("changed")
    assert value == before
    value = {'v_159': 'D159', 'qty_159': -34, 'flag_159': ['', 'a', 'a', '雪'], 'mode_159': ''}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'state_0': 'done', 'amount_1': -17, 'labels_2': ['', 'a', 'a', '雪'], 'title_3': ''}
    assert value == before
    assert result is not value
    assert result['labels_2'] is not value['flag_159']
    result['labels_2'].append("changed")
    assert value == before
    assert encode({'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}) == {'v_159': 'H159', 'qty_159': 0, 'flag_159': [], 'mode_159': ''}
    assert decode({'v_159': 'H159', 'qty_159': 0, 'flag_159': [], 'mode_159': ''}) == {'state_0': 'held', 'amount_1': 0, 'labels_2': [], 'title_3': ''}
