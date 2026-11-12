"""Spec: docs/SPEC.md §§2–5 and docs/group17.md#r106."""

def test_encode_normal():
    from record_codecs.group17 import encode_r106 as encode, decode_r106 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_106': 110, 'qty_106': ['red', 'blue'], 'flag_106': 'snow 雪', 'mode_106': '42'}

def test_decode_normal():
    from record_codecs.group17 import encode_r106 as encode, decode_r106 as decode
    assert decode({'v_106': 110, 'qty_106': ['red', 'blue'], 'flag_106': 'snow 雪', 'mode_106': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group17 import encode_r106 as encode, decode_r106 as decode
    with pytest.raises(KeyError) as error:
        encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_106': 110, 'flag_106': 'snow 雪', 'mode_106': '42'}
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_106': 110, 'qty_106': None, 'flag_106': 'snow 雪', 'mode_106': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_106': 110, 'qty_106': ['red', 'blue'], 'flag_106': 'unset', 'mode_106': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_106': 110, 'qty_106': ['red', 'blue'], 'mode_106': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'})
    assert error.value.args == ('count_3',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None})
    assert error.value.args == ('count_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_106': ['red', 'blue'], 'flag_106': 'snow 雪', 'mode_106': '42'})
    assert error.value.args == ('v_106',)
    with pytest.raises(ValueError) as error:
        decode({'v_106': None, 'qty_106': ['red', 'blue'], 'flag_106': 'snow 雪', 'mode_106': '42'})
    assert error.value.args == ('v_106',)
    assert decode({'v_106': 110, 'flag_106': 'snow 雪', 'mode_106': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_106': 110, 'qty_106': None, 'flag_106': 'snow 雪', 'mode_106': '42'}) == {'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_106': 110, 'qty_106': ['red', 'blue'], 'mode_106': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'unset', 'count_3': 42}
    assert decode({'v_106': 110, 'qty_106': ['red', 'blue'], 'flag_106': None, 'mode_106': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_106': 110, 'qty_106': ['red', 'blue'], 'flag_106': 'snow 雪'})
    assert error.value.args == ('mode_106',)
    with pytest.raises(ValueError) as error:
        decode({'v_106': 110, 'qty_106': ['red', 'blue'], 'flag_106': 'snow 雪', 'mode_106': None})
    assert error.value.args == ('mode_106',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group17 import encode_r106 as encode, decode_r106 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_106': -170, 'qty_106': ['', 'a', 'a', '雪'], 'flag_106': '', 'mode_106': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_106'] is not value['labels_1']
    result['qty_106'].append("changed")
    assert value == before
    value = {'v_106': -170, 'qty_106': ['', 'a', 'a', '雪'], 'flag_106': '', 'mode_106': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_106']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_106': 0, 'qty_106': [], 'flag_106': '', 'mode_106': '0'}
    assert decode({'v_106': 0, 'qty_106': [], 'flag_106': '', 'mode_106': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
