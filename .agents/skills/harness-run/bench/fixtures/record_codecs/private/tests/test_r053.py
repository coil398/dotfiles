"""Spec: docs/SPEC.md §§2–5 and docs/group08.md#r053."""

def test_encode_normal():
    from record_codecs.group08 import encode_r053 as encode, decode_r053 as decode
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True, 'ignored': 'extra'}) == {'v_053': ['red', 'blue'], 'qty_053': 'snow 雪', 'flag_053': '42', 'mode_053': 'yes'}

def test_decode_normal():
    from record_codecs.group08 import encode_r053 as encode, decode_r053 as decode
    assert decode({'v_053': ['red', 'blue'], 'qty_053': 'snow 雪', 'flag_053': '42', 'mode_053': 'yes', 'ignored': 'extra'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}

def test_missing_null():
    import pytest
    from record_codecs.group08 import encode_r053 as encode, decode_r053 as decode
    with pytest.raises(KeyError) as error:
        encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    assert encode({'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}) == {'v_053': ['red', 'blue'], 'flag_053': '42', 'mode_053': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}) == {'v_053': ['red', 'blue'], 'qty_053': None, 'flag_053': '42', 'mode_053': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}) == {'v_053': ['red', 'blue'], 'qty_053': 'snow 雪', 'flag_053': '-7', 'mode_053': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True}) == {'v_053': ['red', 'blue'], 'qty_053': 'snow 雪', 'mode_053': 'yes'}
    with pytest.raises(KeyError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42})
    assert error.value.args == ('active_3',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None})
    assert error.value.args == ('active_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_053': 'snow 雪', 'flag_053': '42', 'mode_053': 'yes'})
    assert error.value.args == ('v_053',)
    with pytest.raises(ValueError) as error:
        decode({'v_053': None, 'qty_053': 'snow 雪', 'flag_053': '42', 'mode_053': 'yes'})
    assert error.value.args == ('v_053',)
    assert decode({'v_053': ['red', 'blue'], 'flag_053': '42', 'mode_053': 'yes'}) == {'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}
    assert decode({'v_053': ['red', 'blue'], 'qty_053': None, 'flag_053': '42', 'mode_053': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}
    assert decode({'v_053': ['red', 'blue'], 'qty_053': 'snow 雪', 'mode_053': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': -7, 'active_3': True}
    assert decode({'v_053': ['red', 'blue'], 'qty_053': 'snow 雪', 'flag_053': None, 'mode_053': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}
    with pytest.raises(KeyError) as error:
        decode({'v_053': ['red', 'blue'], 'qty_053': 'snow 雪', 'flag_053': '42'})
    assert error.value.args == ('mode_053',)
    with pytest.raises(ValueError) as error:
        decode({'v_053': ['red', 'blue'], 'qty_053': 'snow 雪', 'flag_053': '42', 'mode_053': None})
    assert error.value.args == ('mode_053',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group08 import encode_r053 as encode, decode_r053 as decode
    value = {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_053': ['', 'a', 'a', '雪'], 'qty_053': '', 'flag_053': '-100000000000000000003', 'mode_053': 'no'}
    assert value == before
    assert result is not value
    assert result['v_053'] is not value['labels_0']
    result['v_053'].append("changed")
    assert value == before
    value = {'v_053': ['', 'a', 'a', '雪'], 'qty_053': '', 'flag_053': '-100000000000000000003', 'mode_053': 'no'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    assert value == before
    assert result is not value
    assert result['labels_0'] is not value['v_053']
    result['labels_0'].append("changed")
    assert value == before
    assert encode({'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}) == {'v_053': [], 'qty_053': '', 'flag_053': '0', 'mode_053': 'no'}
    assert decode({'v_053': [], 'qty_053': '', 'flag_053': '0', 'mode_053': 'no'}) == {'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}
