"""Spec: docs/SPEC.md §§2–5 and docs/group22.md#r136."""

def test_encode_normal():
    from record_codecs.group22 import encode_r136 as encode, decode_r136 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_136': 22, 'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪', 'mode_136': '42'}

def test_decode_normal():
    from record_codecs.group22 import encode_r136 as encode, decode_r136 as decode
    assert decode({'v_136': 22, 'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪', 'mode_136': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group22 import encode_r136 as encode, decode_r136 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_136': 6, 'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪', 'mode_136': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_136': None, 'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪', 'mode_136': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_136': 22, 'flag_136': 'snow 雪', 'mode_136': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_136': 22, 'qty_136': ['red', 'blue'], 'mode_136': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_136': 22, 'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪', 'mode_136': '-7'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_136': 22, 'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪', 'mode_136': None}
    assert decode({'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪', 'mode_136': '42'}) == {'amount_0': 3, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_136': None, 'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪', 'mode_136': '42'}) == {'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_136': 22, 'flag_136': 'snow 雪', 'mode_136': '42'})
    assert error.value.args == ('qty_136',)
    assert decode({'v_136': 22, 'qty_136': None, 'flag_136': 'snow 雪', 'mode_136': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_136': 22, 'qty_136': ['red', 'blue'], 'mode_136': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_136': 22, 'qty_136': ['red', 'blue'], 'flag_136': None, 'mode_136': '42'})
    assert error.value.args == ('flag_136',)
    assert decode({'v_136': 22, 'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': -7}
    assert decode({'v_136': 22, 'qty_136': ['red', 'blue'], 'flag_136': 'snow 雪', 'mode_136': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group22 import encode_r136 as encode, decode_r136 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_136': -34, 'qty_136': ['', 'a', 'a', '雪'], 'flag_136': '', 'mode_136': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_136'] is not value['labels_1']
    result['qty_136'].append("changed")
    assert value == before
    value = {'v_136': -34, 'qty_136': ['', 'a', 'a', '雪'], 'flag_136': '', 'mode_136': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_136']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_136': 0, 'qty_136': [], 'flag_136': '', 'mode_136': '0'}
    assert decode({'v_136': 0, 'qty_136': [], 'flag_136': '', 'mode_136': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
