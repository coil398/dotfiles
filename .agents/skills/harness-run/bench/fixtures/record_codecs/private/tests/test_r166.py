"""Spec: docs/SPEC.md §§2–5 and docs/group27.md#r166."""

def test_encode_normal():
    from record_codecs.group27 import encode_r166 as encode, decode_r166 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_166': 110, 'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪', 'mode_166': '42'}

def test_decode_normal():
    from record_codecs.group27 import encode_r166 as encode, decode_r166 as decode
    assert decode({'v_166': 110, 'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪', 'mode_166': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group27 import encode_r166 as encode, decode_r166 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪', 'mode_166': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪', 'mode_166': '42'}
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_166': 110, 'qty_166': ['default'], 'flag_166': 'snow 雪', 'mode_166': '42'}
    result = encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    result['qty_166'].append("changed")
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_166': 110, 'qty_166': ['default'], 'flag_166': 'snow 雪', 'mode_166': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_166': 110, 'qty_166': ['red', 'blue'], 'flag_166': None, 'mode_166': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_166': 110, 'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_166': 110, 'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪'}
    assert decode({'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪', 'mode_166': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_166': None, 'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪', 'mode_166': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_166': 110, 'flag_166': 'snow 雪', 'mode_166': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    result = decode({'v_166': 110, 'flag_166': 'snow 雪', 'mode_166': '42'})
    result['labels_1'].append("changed")
    assert decode({'v_166': 110, 'flag_166': 'snow 雪', 'mode_166': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_166': 110, 'qty_166': None, 'flag_166': 'snow 雪', 'mode_166': '42'})
    assert error.value.args == ('qty_166',)
    with pytest.raises(KeyError) as error:
        decode({'v_166': 110, 'qty_166': ['red', 'blue'], 'mode_166': '42'})
    assert error.value.args == ('flag_166',)
    assert decode({'v_166': 110, 'qty_166': ['red', 'blue'], 'flag_166': None, 'mode_166': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}
    assert decode({'v_166': 110, 'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}
    assert decode({'v_166': 110, 'qty_166': ['red', 'blue'], 'flag_166': 'snow 雪', 'mode_166': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group27 import encode_r166 as encode, decode_r166 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_166': -170, 'qty_166': ['', 'a', 'a', '雪'], 'flag_166': '', 'mode_166': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_166'] is not value['labels_1']
    result['qty_166'].append("changed")
    assert value == before
    value = {'v_166': -170, 'qty_166': ['', 'a', 'a', '雪'], 'flag_166': '', 'mode_166': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_166']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_166': 0, 'qty_166': [], 'flag_166': '', 'mode_166': '0'}
    assert decode({'v_166': 0, 'qty_166': [], 'flag_166': '', 'mode_166': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
