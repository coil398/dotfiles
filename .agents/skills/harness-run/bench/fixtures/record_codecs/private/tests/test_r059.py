"""Spec: docs/SPEC.md §§2–5 and docs/group09.md#r059."""

def test_encode_normal():
    from record_codecs.group09 import encode_r059 as encode, decode_r059 as decode
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True, 'ignored': 'extra'}) == {'v_059': ['red', 'blue'], 'qty_059': 'snow 雪', 'flag_059': '42', 'mode_059': 'yes'}

def test_decode_normal():
    from record_codecs.group09 import encode_r059 as encode, decode_r059 as decode
    assert decode({'v_059': ['red', 'blue'], 'qty_059': 'snow 雪', 'flag_059': '42', 'mode_059': 'yes', 'ignored': 'extra'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}

def test_missing_null():
    import pytest
    from record_codecs.group09 import encode_r059 as encode, decode_r059 as decode
    assert encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'qty_059': 'snow 雪', 'flag_059': '42', 'mode_059': 'yes'}
    assert encode({'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'qty_059': 'snow 雪', 'flag_059': '42', 'mode_059': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}) == {'v_059': ['red', 'blue'], 'qty_059': 'unset', 'flag_059': '42', 'mode_059': 'yes'}
    with pytest.raises(ValueError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True})
    assert error.value.args == ('title_1',)
    with pytest.raises(KeyError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True})
    assert error.value.args == ('count_2',)
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True}) == {'v_059': ['red', 'blue'], 'qty_059': 'snow 雪', 'flag_059': None, 'mode_059': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42}) == {'v_059': ['red', 'blue'], 'qty_059': 'snow 雪', 'flag_059': '42'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None}) == {'v_059': ['red', 'blue'], 'qty_059': 'snow 雪', 'flag_059': '42'}
    assert decode({'qty_059': 'snow 雪', 'flag_059': '42', 'mode_059': 'yes'}) == {'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    assert decode({'v_059': None, 'qty_059': 'snow 雪', 'flag_059': '42', 'mode_059': 'yes'}) == {'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    assert decode({'v_059': ['red', 'blue'], 'flag_059': '42', 'mode_059': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'unset', 'count_2': 42, 'active_3': True}
    with pytest.raises(ValueError) as error:
        decode({'v_059': ['red', 'blue'], 'qty_059': None, 'flag_059': '42', 'mode_059': 'yes'})
    assert error.value.args == ('qty_059',)
    with pytest.raises(KeyError) as error:
        decode({'v_059': ['red', 'blue'], 'qty_059': 'snow 雪', 'mode_059': 'yes'})
    assert error.value.args == ('flag_059',)
    assert decode({'v_059': ['red', 'blue'], 'qty_059': 'snow 雪', 'flag_059': None, 'mode_059': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True}
    assert decode({'v_059': ['red', 'blue'], 'qty_059': 'snow 雪', 'flag_059': '42'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42}
    assert decode({'v_059': ['red', 'blue'], 'qty_059': 'snow 雪', 'flag_059': '42', 'mode_059': None}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group09 import encode_r059 as encode, decode_r059 as decode
    value = {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_059': ['', 'a', 'a', '雪'], 'qty_059': '', 'flag_059': '-100000000000000000003', 'mode_059': 'no'}
    assert value == before
    assert result is not value
    assert result['v_059'] is not value['labels_0']
    result['v_059'].append("changed")
    assert value == before
    value = {'v_059': ['', 'a', 'a', '雪'], 'qty_059': '', 'flag_059': '-100000000000000000003', 'mode_059': 'no'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    assert value == before
    assert result is not value
    assert result['labels_0'] is not value['v_059']
    result['labels_0'].append("changed")
    assert value == before
    assert encode({'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}) == {'v_059': [], 'qty_059': '', 'flag_059': '0', 'mode_059': 'no'}
    assert decode({'v_059': [], 'qty_059': '', 'flag_059': '0', 'mode_059': 'no'}) == {'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}
