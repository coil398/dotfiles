"""Spec: docs/SPEC.md §§2–5 and docs/group11.md#r070."""

def test_encode_normal():
    from record_codecs.group11 import encode_r070 as encode, decode_r070 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_070': 110, 'qty_070': ['red', 'blue'], 'flag_070': 'snow 雪', 'mode_070': '42'}

def test_decode_normal():
    from record_codecs.group11 import encode_r070 as encode, decode_r070 as decode
    assert decode({'v_070': 110, 'qty_070': ['red', 'blue'], 'flag_070': 'snow 雪', 'mode_070': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group11 import encode_r070 as encode, decode_r070 as decode
    with pytest.raises(KeyError) as error:
        encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_070': 110, 'flag_070': 'snow 雪', 'mode_070': '42'}
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_070': 110, 'qty_070': None, 'flag_070': 'snow 雪', 'mode_070': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_070': 110, 'qty_070': ['red', 'blue'], 'flag_070': 'unset', 'mode_070': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_070': 110, 'qty_070': ['red', 'blue'], 'mode_070': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'})
    assert error.value.args == ('count_3',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None})
    assert error.value.args == ('count_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_070': ['red', 'blue'], 'flag_070': 'snow 雪', 'mode_070': '42'})
    assert error.value.args == ('v_070',)
    with pytest.raises(ValueError) as error:
        decode({'v_070': None, 'qty_070': ['red', 'blue'], 'flag_070': 'snow 雪', 'mode_070': '42'})
    assert error.value.args == ('v_070',)
    assert decode({'v_070': 110, 'flag_070': 'snow 雪', 'mode_070': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_070': 110, 'qty_070': None, 'flag_070': 'snow 雪', 'mode_070': '42'}) == {'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_070': 110, 'qty_070': ['red', 'blue'], 'mode_070': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'unset', 'count_3': 42}
    assert decode({'v_070': 110, 'qty_070': ['red', 'blue'], 'flag_070': None, 'mode_070': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_070': 110, 'qty_070': ['red', 'blue'], 'flag_070': 'snow 雪'})
    assert error.value.args == ('mode_070',)
    with pytest.raises(ValueError) as error:
        decode({'v_070': 110, 'qty_070': ['red', 'blue'], 'flag_070': 'snow 雪', 'mode_070': None})
    assert error.value.args == ('mode_070',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group11 import encode_r070 as encode, decode_r070 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_070': -170, 'qty_070': ['', 'a', 'a', '雪'], 'flag_070': '', 'mode_070': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_070'] is not value['labels_1']
    result['qty_070'].append("changed")
    assert value == before
    value = {'v_070': -170, 'qty_070': ['', 'a', 'a', '雪'], 'flag_070': '', 'mode_070': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_070']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_070': 0, 'qty_070': [], 'flag_070': '', 'mode_070': '0'}
    assert decode({'v_070': 0, 'qty_070': [], 'flag_070': '', 'mode_070': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
