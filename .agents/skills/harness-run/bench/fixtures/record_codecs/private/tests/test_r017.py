"""Spec: docs/SPEC.md §§2–5 and docs/group02.md#r017."""

def test_encode_normal():
    from record_codecs.group02 import encode_r017 as encode, decode_r017 as decode
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True, 'ignored': 'extra'}) == {'v_017': ['red', 'blue'], 'qty_017': 'snow 雪', 'flag_017': '42', 'mode_017': 'yes'}

def test_decode_normal():
    from record_codecs.group02 import encode_r017 as encode, decode_r017 as decode
    assert decode({'v_017': ['red', 'blue'], 'qty_017': 'snow 雪', 'flag_017': '42', 'mode_017': 'yes', 'ignored': 'extra'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}

def test_missing_null():
    import pytest
    from record_codecs.group02 import encode_r017 as encode, decode_r017 as decode
    with pytest.raises(KeyError) as error:
        encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    assert encode({'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}) == {'v_017': ['red', 'blue'], 'flag_017': '42', 'mode_017': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}) == {'v_017': ['red', 'blue'], 'qty_017': None, 'flag_017': '42', 'mode_017': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}) == {'v_017': ['red', 'blue'], 'qty_017': 'snow 雪', 'flag_017': '-7', 'mode_017': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True}) == {'v_017': ['red', 'blue'], 'qty_017': 'snow 雪', 'mode_017': 'yes'}
    with pytest.raises(KeyError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42})
    assert error.value.args == ('active_3',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None})
    assert error.value.args == ('active_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_017': 'snow 雪', 'flag_017': '42', 'mode_017': 'yes'})
    assert error.value.args == ('v_017',)
    with pytest.raises(ValueError) as error:
        decode({'v_017': None, 'qty_017': 'snow 雪', 'flag_017': '42', 'mode_017': 'yes'})
    assert error.value.args == ('v_017',)
    assert decode({'v_017': ['red', 'blue'], 'flag_017': '42', 'mode_017': 'yes'}) == {'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}
    assert decode({'v_017': ['red', 'blue'], 'qty_017': None, 'flag_017': '42', 'mode_017': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}
    assert decode({'v_017': ['red', 'blue'], 'qty_017': 'snow 雪', 'mode_017': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': -7, 'active_3': True}
    assert decode({'v_017': ['red', 'blue'], 'qty_017': 'snow 雪', 'flag_017': None, 'mode_017': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}
    with pytest.raises(KeyError) as error:
        decode({'v_017': ['red', 'blue'], 'qty_017': 'snow 雪', 'flag_017': '42'})
    assert error.value.args == ('mode_017',)
    with pytest.raises(ValueError) as error:
        decode({'v_017': ['red', 'blue'], 'qty_017': 'snow 雪', 'flag_017': '42', 'mode_017': None})
    assert error.value.args == ('mode_017',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group02 import encode_r017 as encode, decode_r017 as decode
    value = {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_017': ['', 'a', 'a', '雪'], 'qty_017': '', 'flag_017': '-100000000000000000003', 'mode_017': 'no'}
    assert value == before
    assert result is not value
    assert result['v_017'] is not value['labels_0']
    result['v_017'].append("changed")
    assert value == before
    value = {'v_017': ['', 'a', 'a', '雪'], 'qty_017': '', 'flag_017': '-100000000000000000003', 'mode_017': 'no'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    assert value == before
    assert result is not value
    assert result['labels_0'] is not value['v_017']
    result['labels_0'].append("changed")
    assert value == before
    assert encode({'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}) == {'v_017': [], 'qty_017': '', 'flag_017': '0', 'mode_017': 'no'}
    assert decode({'v_017': [], 'qty_017': '', 'flag_017': '0', 'mode_017': 'no'}) == {'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}
