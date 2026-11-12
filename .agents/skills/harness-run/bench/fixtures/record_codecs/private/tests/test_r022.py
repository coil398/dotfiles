"""Spec: docs/SPEC.md §§2–5 and docs/group03.md#r022."""

def test_encode_normal():
    from record_codecs.group03 import encode_r022 as encode, decode_r022 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_022': 110, 'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪', 'mode_022': '42'}

def test_decode_normal():
    from record_codecs.group03 import encode_r022 as encode, decode_r022 as decode
    assert decode({'v_022': 110, 'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪', 'mode_022': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group03 import encode_r022 as encode, decode_r022 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪', 'mode_022': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪', 'mode_022': '42'}
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_022': 110, 'qty_022': ['default'], 'flag_022': 'snow 雪', 'mode_022': '42'}
    result = encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    result['qty_022'].append("changed")
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_022': 110, 'qty_022': ['default'], 'flag_022': 'snow 雪', 'mode_022': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_022': 110, 'qty_022': ['red', 'blue'], 'flag_022': None, 'mode_022': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_022': 110, 'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_022': 110, 'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪'}
    assert decode({'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪', 'mode_022': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_022': None, 'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪', 'mode_022': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_022': 110, 'flag_022': 'snow 雪', 'mode_022': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    result = decode({'v_022': 110, 'flag_022': 'snow 雪', 'mode_022': '42'})
    result['labels_1'].append("changed")
    assert decode({'v_022': 110, 'flag_022': 'snow 雪', 'mode_022': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_022': 110, 'qty_022': None, 'flag_022': 'snow 雪', 'mode_022': '42'})
    assert error.value.args == ('qty_022',)
    with pytest.raises(KeyError) as error:
        decode({'v_022': 110, 'qty_022': ['red', 'blue'], 'mode_022': '42'})
    assert error.value.args == ('flag_022',)
    assert decode({'v_022': 110, 'qty_022': ['red', 'blue'], 'flag_022': None, 'mode_022': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}
    assert decode({'v_022': 110, 'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}
    assert decode({'v_022': 110, 'qty_022': ['red', 'blue'], 'flag_022': 'snow 雪', 'mode_022': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group03 import encode_r022 as encode, decode_r022 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_022': -170, 'qty_022': ['', 'a', 'a', '雪'], 'flag_022': '', 'mode_022': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_022'] is not value['labels_1']
    result['qty_022'].append("changed")
    assert value == before
    value = {'v_022': -170, 'qty_022': ['', 'a', 'a', '雪'], 'flag_022': '', 'mode_022': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_022']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_022': 0, 'qty_022': [], 'flag_022': '', 'mode_022': '0'}
    assert decode({'v_022': 0, 'qty_022': [], 'flag_022': '', 'mode_022': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
