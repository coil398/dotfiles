"""Spec: docs/SPEC.md §§2–5 and docs/group09.md#r058."""

def test_encode_normal():
    from record_codecs.group09 import encode_r058 as encode, decode_r058 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_058': 110, 'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪', 'mode_058': '42'}

def test_decode_normal():
    from record_codecs.group09 import encode_r058 as encode, decode_r058 as decode
    assert decode({'v_058': 110, 'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪', 'mode_058': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group09 import encode_r058 as encode, decode_r058 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪', 'mode_058': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪', 'mode_058': '42'}
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_058': 110, 'qty_058': ['default'], 'flag_058': 'snow 雪', 'mode_058': '42'}
    result = encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    result['qty_058'].append("changed")
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_058': 110, 'qty_058': ['default'], 'flag_058': 'snow 雪', 'mode_058': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_058': 110, 'qty_058': ['red', 'blue'], 'flag_058': None, 'mode_058': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_058': 110, 'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_058': 110, 'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪'}
    assert decode({'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪', 'mode_058': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_058': None, 'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪', 'mode_058': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_058': 110, 'flag_058': 'snow 雪', 'mode_058': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    result = decode({'v_058': 110, 'flag_058': 'snow 雪', 'mode_058': '42'})
    result['labels_1'].append("changed")
    assert decode({'v_058': 110, 'flag_058': 'snow 雪', 'mode_058': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_058': 110, 'qty_058': None, 'flag_058': 'snow 雪', 'mode_058': '42'})
    assert error.value.args == ('qty_058',)
    with pytest.raises(KeyError) as error:
        decode({'v_058': 110, 'qty_058': ['red', 'blue'], 'mode_058': '42'})
    assert error.value.args == ('flag_058',)
    assert decode({'v_058': 110, 'qty_058': ['red', 'blue'], 'flag_058': None, 'mode_058': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}
    assert decode({'v_058': 110, 'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}
    assert decode({'v_058': 110, 'qty_058': ['red', 'blue'], 'flag_058': 'snow 雪', 'mode_058': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group09 import encode_r058 as encode, decode_r058 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_058': -170, 'qty_058': ['', 'a', 'a', '雪'], 'flag_058': '', 'mode_058': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_058'] is not value['labels_1']
    result['qty_058'].append("changed")
    assert value == before
    value = {'v_058': -170, 'qty_058': ['', 'a', 'a', '雪'], 'flag_058': '', 'mode_058': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_058']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_058': 0, 'qty_058': [], 'flag_058': '', 'mode_058': '0'}
    assert decode({'v_058': 0, 'qty_058': [], 'flag_058': '', 'mode_058': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
