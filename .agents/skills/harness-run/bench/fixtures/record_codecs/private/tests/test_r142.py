"""Spec: docs/SPEC.md §§2–5 and docs/group23.md#r142."""

def test_encode_normal():
    from record_codecs.group23 import encode_r142 as encode, decode_r142 as decode
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42, 'ignored': 'extra'}) == {'v_142': 110, 'qty_142': ['red', 'blue'], 'flag_142': 'snow 雪', 'mode_142': '42'}

def test_decode_normal():
    from record_codecs.group23 import encode_r142 as encode, decode_r142 as decode
    assert decode({'v_142': 110, 'qty_142': ['red', 'blue'], 'flag_142': 'snow 雪', 'mode_142': '42', 'ignored': 'extra'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42}

def test_missing_null():
    import pytest
    from record_codecs.group23 import encode_r142 as encode, decode_r142 as decode
    with pytest.raises(KeyError) as error:
        encode({'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': None, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': 42})
    assert error.value.args == ('amount_0',)
    assert encode({'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_142': 110, 'flag_142': 'snow 雪', 'mode_142': '42'}
    assert encode({'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}) == {'v_142': 110, 'qty_142': None, 'flag_142': 'snow 雪', 'mode_142': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}) == {'v_142': 110, 'qty_142': ['red', 'blue'], 'flag_142': 'unset', 'mode_142': '42'}
    assert encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': None, 'count_3': 42}) == {'v_142': 110, 'qty_142': ['red', 'blue'], 'mode_142': '42'}
    with pytest.raises(KeyError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪'})
    assert error.value.args == ('count_3',)
    with pytest.raises(ValueError) as error:
        encode({'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'snow 雪', 'count_3': None})
    assert error.value.args == ('count_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_142': ['red', 'blue'], 'flag_142': 'snow 雪', 'mode_142': '42'})
    assert error.value.args == ('v_142',)
    with pytest.raises(ValueError) as error:
        decode({'v_142': None, 'qty_142': ['red', 'blue'], 'flag_142': 'snow 雪', 'mode_142': '42'})
    assert error.value.args == ('v_142',)
    assert decode({'v_142': 110, 'flag_142': 'snow 雪', 'mode_142': '42'}) == {'amount_0': 11, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_142': 110, 'qty_142': None, 'flag_142': 'snow 雪', 'mode_142': '42'}) == {'amount_0': 11, 'labels_1': None, 'title_2': 'snow 雪', 'count_3': 42}
    assert decode({'v_142': 110, 'qty_142': ['red', 'blue'], 'mode_142': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'title_2': 'unset', 'count_3': 42}
    assert decode({'v_142': 110, 'qty_142': ['red', 'blue'], 'flag_142': None, 'mode_142': '42'}) == {'amount_0': 11, 'labels_1': ['red', 'blue'], 'count_3': 42}
    with pytest.raises(KeyError) as error:
        decode({'v_142': 110, 'qty_142': ['red', 'blue'], 'flag_142': 'snow 雪'})
    assert error.value.args == ('mode_142',)
    with pytest.raises(ValueError) as error:
        decode({'v_142': 110, 'qty_142': ['red', 'blue'], 'flag_142': 'snow 雪', 'mode_142': None})
    assert error.value.args == ('mode_142',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group23 import encode_r142 as encode, decode_r142 as decode
    value = {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_142': -170, 'qty_142': ['', 'a', 'a', '雪'], 'flag_142': '', 'mode_142': '-100000000000000000003'}
    assert value == before
    assert result is not value
    assert result['qty_142'] is not value['labels_1']
    result['qty_142'].append("changed")
    assert value == before
    value = {'v_142': -170, 'qty_142': ['', 'a', 'a', '雪'], 'flag_142': '', 'mode_142': '-100000000000000000003'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'amount_0': -17, 'labels_1': ['', 'a', 'a', '雪'], 'title_2': '', 'count_3': -100000000000000000003}
    assert value == before
    assert result is not value
    assert result['labels_1'] is not value['qty_142']
    result['labels_1'].append("changed")
    assert value == before
    assert encode({'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}) == {'v_142': 0, 'qty_142': [], 'flag_142': '', 'mode_142': '0'}
    assert decode({'v_142': 0, 'qty_142': [], 'flag_142': '', 'mode_142': '0'}) == {'amount_0': 0, 'labels_1': [], 'title_2': '', 'count_3': 0}
