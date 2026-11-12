"""Spec: docs/SPEC.md §§2–5 and docs/group15.md#r094."""

def test_encode_normal():
    from record_codecs.group15 import encode_r094 as encode, decode_r094 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_094': 110, 'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪', 'mode_094': '42'}

def test_decode_normal():
    from record_codecs.group15 import encode_r094 as encode, decode_r094 as decode
    assert decode({'v_094': 110, 'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪', 'mode_094': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group15 import encode_r094 as encode, decode_r094 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪', 'mode_094': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪', 'mode_094': '42'}
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_094': 110, 'qty_094': ['default'], 'flag_094': 'snow 雪', 'mode_094': '42'}
    result = encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    result['qty_094'].append("changed")
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_094': 110, 'qty_094': ['default'], 'flag_094': 'snow 雪', 'mode_094': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_094': 110, 'qty_094': ['red', 'blue'], 'flag_094': None, 'mode_094': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_094': 110, 'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_094': 110, 'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪'}
    assert decode({'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪', 'mode_094': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_094': None, 'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪', 'mode_094': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_094': 110, 'flag_094': 'snow 雪', 'mode_094': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    result = decode({'v_094': 110, 'flag_094': 'snow 雪', 'mode_094': '42'})
    result['labels_1'].append("changed")
    assert decode({'v_094': 110, 'flag_094': 'snow 雪', 'mode_094': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_094': 110, 'qty_094': None, 'flag_094': 'snow 雪', 'mode_094': '42'})
    assert error.value.args == ('qty_094',)
    with pytest.raises(KeyError) as error:
        decode({'v_094': 110, 'qty_094': ['red', 'blue'], 'mode_094': '42'})
    assert error.value.args == ('flag_094',)
    assert decode({'v_094': 110, 'qty_094': ['red', 'blue'], 'flag_094': None, 'mode_094': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}
    assert decode({'v_094': 110, 'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}
    assert decode({'v_094': 110, 'qty_094': ['red', 'blue'], 'flag_094': 'snow 雪', 'mode_094': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group15 import encode_r094 as encode, decode_r094 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_094': -170, 'qty_094': ['', 'a', 'a', '雪'], 'flag_094': '', 'mode_094': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_094'] is not value['labels_1']
    result['qty_094'].append("changed")
    assert value == before
    value = {'v_094': -170, 'qty_094': ['', 'a', 'a', '雪'], 'flag_094': '', 'mode_094': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_094']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_094': 0, 'qty_094': [], 'flag_094': '', 'mode_094': '0'}
    assert decode({'v_094': 0, 'qty_094': [], 'flag_094': '', 'mode_094': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
