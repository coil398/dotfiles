"""Spec: docs/SPEC.md §§2–5 and docs/group12.md#r076."""

def test_encode_normal():
    from record_codecs.group12 import encode_r076 as encode, decode_r076 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_076': 22, 'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪', 'mode_076': '42'}

def test_decode_normal():
    from record_codecs.group12 import encode_r076 as encode, decode_r076 as decode
    assert decode({'v_076': 22, 'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪', 'mode_076': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group12 import encode_r076 as encode, decode_r076 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪', 'mode_076': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪', 'mode_076': '42'}
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_076': 22, 'qty_076': ['default'], 'flag_076': 'snow 雪', 'mode_076': '42'}
    result = encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    result['qty_076'].append("changed")
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_076': 22, 'qty_076': ['default'], 'flag_076': 'snow 雪', 'mode_076': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_076': 22, 'qty_076': ['red', 'blue'], 'flag_076': None, 'mode_076': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_076': 22, 'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_076': 22, 'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪'}
    assert decode({'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪', 'mode_076': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_076': None, 'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪', 'mode_076': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_076': 22, 'flag_076': 'snow 雪', 'mode_076': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    result = decode({'v_076': 22, 'flag_076': 'snow 雪', 'mode_076': '42'})
    result['labels_1'].append("changed")
    assert decode({'v_076': 22, 'flag_076': 'snow 雪', 'mode_076': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_076': 22, 'qty_076': None, 'flag_076': 'snow 雪', 'mode_076': '42'})
    assert error.value.args == ('qty_076',)
    with pytest.raises(KeyError) as error:
        decode({'v_076': 22, 'qty_076': ['red', 'blue'], 'mode_076': '42'})
    assert error.value.args == ('flag_076',)
    assert decode({'v_076': 22, 'qty_076': ['red', 'blue'], 'flag_076': None, 'mode_076': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}
    assert decode({'v_076': 22, 'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}
    assert decode({'v_076': 22, 'qty_076': ['red', 'blue'], 'flag_076': 'snow 雪', 'mode_076': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group12 import encode_r076 as encode, decode_r076 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_076': -34, 'qty_076': ['', 'a', 'a', '雪'], 'flag_076': '', 'mode_076': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_076'] is not value['labels_1']
    result['qty_076'].append("changed")
    assert value == before
    value = {'v_076': -34, 'qty_076': ['', 'a', 'a', '雪'], 'flag_076': '', 'mode_076': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_076']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_076': 0, 'qty_076': [], 'flag_076': '', 'mode_076': '0'}
    assert decode({'v_076': 0, 'qty_076': [], 'flag_076': '', 'mode_076': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
