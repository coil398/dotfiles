"""Spec: docs/SPEC.md §§2–5 and docs/group05.md#r034."""

def test_encode_normal():
    from record_codecs.group05 import encode_r034 as encode, decode_r034 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_034': 110, 'qty_034': ['red', 'blue'], 'flag_034': 'snow 雪', 'mode_034': '42'}

def test_decode_normal():
    from record_codecs.group05 import encode_r034 as encode, decode_r034 as decode
    assert decode({'v_034': 110, 'qty_034': ['red', 'blue'], 'flag_034': 'snow 雪', 'mode_034': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group05 import encode_r034 as encode, decode_r034 as decode
    with pytest.raises(KeyError) as error:
        encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_034': 110, 'flag_034': 'snow 雪', 'mode_034': '42'}
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_034': 110, 'qty_034': None, 'flag_034': 'snow 雪', 'mode_034': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_034': 110, 'qty_034': ['red', 'blue'], 'flag_034': 'unset', 'mode_034': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_034': 110, 'qty_034': ['red', 'blue'], 'mode_034': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'})
    assert error.value.args == ('count_3',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None})
    assert error.value.args == ('count_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_034': ['red', 'blue'], 'flag_034': 'snow 雪', 'mode_034': '42'})
    assert error.value.args == ('v_034',)
    with pytest.raises(ValueError) as error:
        decode({'v_034': None, 'qty_034': ['red', 'blue'], 'flag_034': 'snow 雪', 'mode_034': '42'})
    assert error.value.args == ('v_034',)
    assert decode({'v_034': 110, 'flag_034': 'snow 雪', 'mode_034': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_034': 110, 'qty_034': None, 'flag_034': 'snow 雪', 'mode_034': '42'}) == {'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_034': 110, 'qty_034': ['red', 'blue'], 'mode_034': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'unset', 'count_3': 42}
    assert decode({'v_034': 110, 'qty_034': ['red', 'blue'], 'flag_034': None, 'mode_034': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_034': 110, 'qty_034': ['red', 'blue'], 'flag_034': 'snow 雪'})
    assert error.value.args == ('mode_034',)
    with pytest.raises(ValueError) as error:
        decode({'v_034': 110, 'qty_034': ['red', 'blue'], 'flag_034': 'snow 雪', 'mode_034': None})
    assert error.value.args == ('mode_034',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group05 import encode_r034 as encode, decode_r034 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_034': -170, 'qty_034': ['', 'a', 'a', '雪'], 'flag_034': '', 'mode_034': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_034'] is not value['labels_1']
    result['qty_034'].append("changed")
    assert value == before
    value = {'v_034': -170, 'qty_034': ['', 'a', 'a', '雪'], 'flag_034': '', 'mode_034': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_034']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_034': 0, 'qty_034': [], 'flag_034': '', 'mode_034': '0'}
    assert decode({'v_034': 0, 'qty_034': [], 'flag_034': '', 'mode_034': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
