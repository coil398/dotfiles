"""Spec: docs/SPEC.md §§2–5 and docs/group06.md#r040."""

def test_encode_normal():
    from record_codecs.group06 import encode_r040 as encode, decode_r040 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_040': 22, 'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪', 'mode_040': '42'}

def test_decode_normal():
    from record_codecs.group06 import encode_r040 as encode, decode_r040 as decode
    assert decode({'v_040': 22, 'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪', 'mode_040': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group06 import encode_r040 as encode, decode_r040 as decode
    assert encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪', 'mode_040': '42'}
    assert encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}) == {'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪', 'mode_040': '42'}
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_040': 22, 'qty_040': ['default'], 'flag_040': 'snow 雪', 'mode_040': '42'}
    result = encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42})
    result['qty_040'].append("changed")
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_040': 22, 'qty_040': ['default'], 'flag_040': 'snow 雪', 'mode_040': '42'}
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('labels_1',)
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42})
    assert error.value.args == ('title_2',)
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_040': 22, 'qty_040': ['red', 'blue'], 'flag_040': None, 'mode_040': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}) == {'v_040': 22, 'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None}) == {'v_040': 22, 'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪'}
    assert decode({'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪', 'mode_040': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_040': None, 'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪', 'mode_040': '42'}) == {'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_040': 22, 'flag_040': 'snow 雪', 'mode_040': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    result = decode({'v_040': 22, 'flag_040': 'snow 雪', 'mode_040': '42'})
    result['labels_1'].append("changed")
    assert decode({'v_040': 22, 'flag_040': 'snow 雪', 'mode_040': '42'}) == {'amount_0': 11, 'labels_1': ['default'], 'title_2': 'snow 雪', 'count_3': 42}
    with pytest.raises(ValueError) as error:
        decode({'v_040': 22, 'qty_040': None, 'flag_040': 'snow 雪', 'mode_040': '42'})
    assert error.value.args == ('qty_040',)
    with pytest.raises(KeyError) as error:
        decode({'v_040': 22, 'qty_040': ['red', 'blue'], 'mode_040': '42'})
    assert error.value.args == ('flag_040',)
    assert decode({'v_040': 22, 'qty_040': ['red', 'blue'], 'flag_040': None, 'mode_040': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}
    assert decode({'v_040': 22, 'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}
    assert decode({'v_040': 22, 'qty_040': ['red', 'blue'], 'flag_040': 'snow 雪', 'mode_040': None}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group06 import encode_r040 as encode, decode_r040 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_040': -34, 'qty_040': ['', 'a', 'a', '雪'], 'flag_040': '', 'mode_040': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_040'] is not value['labels_1']
    result['qty_040'].append("changed")
    assert value == before
    value = {'v_040': -34, 'qty_040': ['', 'a', 'a', '雪'], 'flag_040': '', 'mode_040': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_040']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_040': 0, 'qty_040': [], 'flag_040': '', 'mode_040': '0'}
    assert decode({'v_040': 0, 'qty_040': [], 'flag_040': '', 'mode_040': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
