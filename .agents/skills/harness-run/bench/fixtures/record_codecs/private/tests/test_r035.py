"""Spec: docs/SPEC.md §§2–5 and docs/group05.md#r035."""

def test_encode_normal():
    from record_codecs.group05 import encode_r035 as encode, decode_r035 as decode
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True, 'ignored': 'extra'}) == {'v_035': ['red', 'blue'], 'qty_035': 'snow 雪', 'flag_035': '42', 'mode_035': 'yes'}

def test_decode_normal():
    from record_codecs.group05 import encode_r035 as encode, decode_r035 as decode
    assert decode({'v_035': ['red', 'blue'], 'qty_035': 'snow 雪', 'flag_035': '42', 'mode_035': 'yes', 'ignored': 'extra'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}

def test_missing_null():
    import pytest
    from record_codecs.group05 import encode_r035 as encode, decode_r035 as decode
    with pytest.raises(KeyError) as error:
        encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    assert encode({'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}) == {'v_035': ['red', 'blue'], 'flag_035': '42', 'mode_035': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}) == {'v_035': ['red', 'blue'], 'qty_035': None, 'flag_035': '42', 'mode_035': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}) == {'v_035': ['red', 'blue'], 'qty_035': 'snow 雪', 'flag_035': '-7', 'mode_035': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True}) == {'v_035': ['red', 'blue'], 'qty_035': 'snow 雪', 'mode_035': 'yes'}
    with pytest.raises(KeyError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42})
    assert error.value.args == ('active_3',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None})
    assert error.value.args == ('active_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_035': 'snow 雪', 'flag_035': '42', 'mode_035': 'yes'})
    assert error.value.args == ('v_035',)
    with pytest.raises(ValueError) as error:
        decode({'v_035': None, 'qty_035': 'snow 雪', 'flag_035': '42', 'mode_035': 'yes'})
    assert error.value.args == ('v_035',)
    assert decode({'v_035': ['red', 'blue'], 'flag_035': '42', 'mode_035': 'yes'}) == {'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}
    assert decode({'v_035': ['red', 'blue'], 'qty_035': None, 'flag_035': '42', 'mode_035': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}
    assert decode({'v_035': ['red', 'blue'], 'qty_035': 'snow 雪', 'mode_035': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': -7, 'active_3': True}
    assert decode({'v_035': ['red', 'blue'], 'qty_035': 'snow 雪', 'flag_035': None, 'mode_035': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}
    with pytest.raises(KeyError) as error:
        decode({'v_035': ['red', 'blue'], 'qty_035': 'snow 雪', 'flag_035': '42'})
    assert error.value.args == ('mode_035',)
    with pytest.raises(ValueError) as error:
        decode({'v_035': ['red', 'blue'], 'qty_035': 'snow 雪', 'flag_035': '42', 'mode_035': None})
    assert error.value.args == ('mode_035',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group05 import encode_r035 as encode, decode_r035 as decode
    value = {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_035': ['', 'a', 'a', '雪'], 'qty_035': '', 'flag_035': '-100000000000000000003', 'mode_035': 'no'}
    assert value == before
    assert result is not value
    assert result['v_035'] is not value['labels_0']
    result['v_035'].append("changed")
    assert value == before
    value = {'v_035': ['', 'a', 'a', '雪'], 'qty_035': '', 'flag_035': '-100000000000000000003', 'mode_035': 'no'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    assert value == before
    assert result is not value
    assert result['labels_0'] is not value['v_035']
    result['labels_0'].append("changed")
    assert value == before
    assert encode({'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}) == {'v_035': [], 'qty_035': '', 'flag_035': '0', 'mode_035': 'no'}
    assert decode({'v_035': [], 'qty_035': '', 'flag_035': '0', 'mode_035': 'no'}) == {'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}
