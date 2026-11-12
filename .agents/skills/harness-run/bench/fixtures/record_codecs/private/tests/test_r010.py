"""Spec: docs/SPEC.md §§2–5 and docs/group01.md#r010."""

def test_encode_normal():
    from record_codecs.group01 import encode_r010 as encode, decode_r010 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_010': 110, 'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪', 'mode_010': '42'}

def test_decode_normal():
    from record_codecs.group01 import encode_r010 as encode, decode_r010 as decode
    assert decode({'v_010': 110, 'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪', 'mode_010': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group01 import encode_r010 as encode, decode_r010 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_010': 30, 'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪', 'mode_010': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_010': None, 'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪', 'mode_010': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_010': 110, 'flag_010': 'snow 雪', 'mode_010': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_010': 110, 'qty_010': ['red', 'blue'], 'mode_010': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_010': 110, 'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪', 'mode_010': '-7'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_010': 110, 'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪', 'mode_010': None}
    assert decode({'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪', 'mode_010': '42'}) == {'amount_0': 3, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_010': None, 'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪', 'mode_010': '42'}) == {'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_010': 110, 'flag_010': 'snow 雪', 'mode_010': '42'})
    assert error.value.args == ('qty_010',)
    assert decode({'v_010': 110, 'qty_010': None, 'flag_010': 'snow 雪', 'mode_010': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_010': 110, 'qty_010': ['red', 'blue'], 'mode_010': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_010': 110, 'qty_010': ['red', 'blue'], 'flag_010': None, 'mode_010': '42'})
    assert error.value.args == ('flag_010',)
    assert decode({'v_010': 110, 'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': -7}
    assert decode({'v_010': 110, 'qty_010': ['red', 'blue'], 'flag_010': 'snow 雪', 'mode_010': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group01 import encode_r010 as encode, decode_r010 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_010': -170, 'qty_010': ['', 'a', 'a', '雪'], 'flag_010': '', 'mode_010': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_010'] is not value['labels_1']
    result['qty_010'].append("changed")
    assert value == before
    value = {'v_010': -170, 'qty_010': ['', 'a', 'a', '雪'], 'flag_010': '', 'mode_010': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_010']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_010': 0, 'qty_010': [], 'flag_010': '', 'mode_010': '0'}
    assert decode({'v_010': 0, 'qty_010': [], 'flag_010': '', 'mode_010': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
