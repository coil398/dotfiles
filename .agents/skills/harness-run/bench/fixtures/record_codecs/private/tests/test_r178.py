"""Spec: docs/SPEC.md §§2–5 and docs/group29.md#r178."""

def test_encode_normal():
    from record_codecs.group29 import encode_r178 as encode, decode_r178 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_178': 110, 'qty_178': ['red', 'blue'], 'flag_178': 'snow 雪', 'mode_178': '42'}

def test_decode_normal():
    from record_codecs.group29 import encode_r178 as encode, decode_r178 as decode
    assert decode({'v_178': 110, 'qty_178': ['red', 'blue'], 'flag_178': 'snow 雪', 'mode_178': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group29 import encode_r178 as encode, decode_r178 as decode
    with pytest.raises(KeyError) as error:
        encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_178': 110, 'flag_178': 'snow 雪', 'mode_178': '42'}
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_178': 110, 'qty_178': None, 'flag_178': 'snow 雪', 'mode_178': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_178': 110, 'qty_178': ['red', 'blue'], 'flag_178': 'unset', 'mode_178': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_178': 110, 'qty_178': ['red', 'blue'], 'mode_178': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'})
    assert error.value.args == ('count_3',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None})
    assert error.value.args == ('count_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_178': ['red', 'blue'], 'flag_178': 'snow 雪', 'mode_178': '42'})
    assert error.value.args == ('v_178',)
    with pytest.raises(ValueError) as error:
        decode({'v_178': None, 'qty_178': ['red', 'blue'], 'flag_178': 'snow 雪', 'mode_178': '42'})
    assert error.value.args == ('v_178',)
    assert decode({'v_178': 110, 'flag_178': 'snow 雪', 'mode_178': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_178': 110, 'qty_178': None, 'flag_178': 'snow 雪', 'mode_178': '42'}) == {'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_178': 110, 'qty_178': ['red', 'blue'], 'mode_178': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'unset', 'count_3': 42}
    assert decode({'v_178': 110, 'qty_178': ['red', 'blue'], 'flag_178': None, 'mode_178': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_178': 110, 'qty_178': ['red', 'blue'], 'flag_178': 'snow 雪'})
    assert error.value.args == ('mode_178',)
    with pytest.raises(ValueError) as error:
        decode({'v_178': 110, 'qty_178': ['red', 'blue'], 'flag_178': 'snow 雪', 'mode_178': None})
    assert error.value.args == ('mode_178',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group29 import encode_r178 as encode, decode_r178 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_178': -170, 'qty_178': ['', 'a', 'a', '雪'], 'flag_178': '', 'mode_178': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_178'] is not value['labels_1']
    result['qty_178'].append("changed")
    assert value == before
    value = {'v_178': -170, 'qty_178': ['', 'a', 'a', '雪'], 'flag_178': '', 'mode_178': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_178']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_178': 0, 'qty_178': [], 'flag_178': '', 'mode_178': '0'}
    assert decode({'v_178': 0, 'qty_178': [], 'flag_178': '', 'mode_178': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
