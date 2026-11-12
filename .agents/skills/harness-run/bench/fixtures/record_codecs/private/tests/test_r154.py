"""Spec: docs/SPEC.md §§2–5 and docs/group25.md#r154."""

def test_encode_normal():
    from record_codecs.group25 import encode_r154 as encode, decode_r154 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_154': 110, 'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪', 'mode_154': '42'}

def test_decode_normal():
    from record_codecs.group25 import encode_r154 as encode, decode_r154 as decode
    assert decode({'v_154': 110, 'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪', 'mode_154': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group25 import encode_r154 as encode, decode_r154 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_154': 30, 'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪', 'mode_154': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'v_154': None, 'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪', 'mode_154': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_154': 110, 'flag_154': 'snow 雪', 'mode_154': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_154': 110, 'qty_154': ['red', 'blue'], 'mode_154': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_154': 110, 'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪', 'mode_154': '-7'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_154': 110, 'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪', 'mode_154': None}
    assert decode({'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪', 'mode_154': '42'}) == {'amount_0': 3, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_154': None, 'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪', 'mode_154': '42'}) == {'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_154': 110, 'flag_154': 'snow 雪', 'mode_154': '42'})
    assert error.value.args == ('qty_154',)
    assert decode({'v_154': 110, 'qty_154': None, 'flag_154': 'snow 雪', 'mode_154': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_154': 110, 'qty_154': ['red', 'blue'], 'mode_154': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_154': 110, 'qty_154': ['red', 'blue'], 'flag_154': None, 'mode_154': '42'})
    assert error.value.args == ('flag_154',)
    assert decode({'v_154': 110, 'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': -7}
    assert decode({'v_154': 110, 'qty_154': ['red', 'blue'], 'flag_154': 'snow 雪', 'mode_154': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group25 import encode_r154 as encode, decode_r154 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_154': -170, 'qty_154': ['', 'a', 'a', '雪'], 'flag_154': '', 'mode_154': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_154'] is not value['labels_1']
    result['qty_154'].append("changed")
    assert value == before
    value = {'v_154': -170, 'qty_154': ['', 'a', 'a', '雪'], 'flag_154': '', 'mode_154': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_154']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_154': 0, 'qty_154': [], 'flag_154': '', 'mode_154': '0'}
    assert decode({'v_154': 0, 'qty_154': [], 'flag_154': '', 'mode_154': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
