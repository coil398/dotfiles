"""Spec: docs/SPEC.md §§2–5 and docs/group28.md#r172."""

def test_encode_normal():
    from record_codecs.group28 import encode_r172 as encode, decode_r172 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_172': 22, 'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪', 'mode_172': '42'}

def test_decode_normal():
    from record_codecs.group28 import encode_r172 as encode, decode_r172 as decode
    assert decode({'v_172': 22, 'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪', 'mode_172': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group28 import encode_r172 as encode, decode_r172 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_172': 6, 'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪', 'mode_172': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_172': None, 'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪', 'mode_172': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_172': 22, 'flag_172': 'snow 雪', 'mode_172': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_172': 22, 'qty_172': ['red', 'blue'], 'mode_172': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_172': 22, 'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪', 'mode_172': '-7'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_172': 22, 'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪', 'mode_172': None}
    assert decode({'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪', 'mode_172': '42'}) == {'amount_0': 3, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_172': None, 'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪', 'mode_172': '42'}) == {'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_172': 22, 'flag_172': 'snow 雪', 'mode_172': '42'})
    assert error.value.args == ('qty_172',)
    assert decode({'v_172': 22, 'qty_172': None, 'flag_172': 'snow 雪', 'mode_172': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_172': 22, 'qty_172': ['red', 'blue'], 'mode_172': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_172': 22, 'qty_172': ['red', 'blue'], 'flag_172': None, 'mode_172': '42'})
    assert error.value.args == ('flag_172',)
    assert decode({'v_172': 22, 'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': -7}
    assert decode({'v_172': 22, 'qty_172': ['red', 'blue'], 'flag_172': 'snow 雪', 'mode_172': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group28 import encode_r172 as encode, decode_r172 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_172': -34, 'qty_172': ['', 'a', 'a', '雪'], 'flag_172': '', 'mode_172': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_172'] is not value['labels_1']
    result['qty_172'].append("changed")
    assert value == before
    value = {'v_172': -34, 'qty_172': ['', 'a', 'a', '雪'], 'flag_172': '', 'mode_172': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_172']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_172': 0, 'qty_172': [], 'flag_172': '', 'mode_172': '0'}
    assert decode({'v_172': 0, 'qty_172': [], 'flag_172': '', 'mode_172': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
