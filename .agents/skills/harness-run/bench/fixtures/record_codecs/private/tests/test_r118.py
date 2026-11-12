"""Spec: docs/SPEC.md §§2–5 and docs/group19.md#r118."""

def test_encode_normal():
    from record_codecs.group19 import encode_r118 as encode, decode_r118 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_118': 110, 'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪', 'mode_118': '42'}

def test_decode_normal():
    from record_codecs.group19 import encode_r118 as encode, decode_r118 as decode
    assert decode({'v_118': 110, 'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪', 'mode_118': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group19 import encode_r118 as encode, decode_r118 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_118': 30, 'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪', 'mode_118': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_118': None, 'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪', 'mode_118': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_118': 110, 'flag_118': 'snow 雪', 'mode_118': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_118': 110, 'qty_118': ['red', 'blue'], 'mode_118': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_118': 110, 'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪', 'mode_118': '-7'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_118': 110, 'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪', 'mode_118': None}
    assert decode({'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪', 'mode_118': '42'}) == {'amount_0': 3, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_118': None, 'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪', 'mode_118': '42'}) == {'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_118': 110, 'flag_118': 'snow 雪', 'mode_118': '42'})
    assert error.value.args == ('qty_118',)
    assert decode({'v_118': 110, 'qty_118': None, 'flag_118': 'snow 雪', 'mode_118': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_118': 110, 'qty_118': ['red', 'blue'], 'mode_118': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_118': 110, 'qty_118': ['red', 'blue'], 'flag_118': None, 'mode_118': '42'})
    assert error.value.args == ('flag_118',)
    assert decode({'v_118': 110, 'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': -7}
    assert decode({'v_118': 110, 'qty_118': ['red', 'blue'], 'flag_118': 'snow 雪', 'mode_118': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group19 import encode_r118 as encode, decode_r118 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_118': -170, 'qty_118': ['', 'a', 'a', '雪'], 'flag_118': '', 'mode_118': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_118'] is not value['labels_1']
    result['qty_118'].append("changed")
    assert value == before
    value = {'v_118': -170, 'qty_118': ['', 'a', 'a', '雪'], 'flag_118': '', 'mode_118': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_118']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_118': 0, 'qty_118': [], 'flag_118': '', 'mode_118': '0'}
    assert decode({'v_118': 0, 'qty_118': [], 'flag_118': '', 'mode_118': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
