"""Spec: docs/SPEC.md §§2–5 and docs/group23.md#r143."""

def test_encode_normal():
    from record_codecs.group23 import encode_r143 as encode, decode_r143 as decode
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True, 'ignored': 'extra'}) == {'v_143': ['red', 'blue'], 'qty_143': 'snow 雪', 'flag_143': '42', 'mode_143': 'yes'}

def test_decode_normal():
    from record_codecs.group23 import encode_r143 as encode, decode_r143 as decode
    assert decode({'v_143': ['red', 'blue'], 'qty_143': 'snow 雪', 'flag_143': '42', 'mode_143': 'yes', 'ignored': 'extra'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}

def test_missing_null():
    import pytest
    from record_codecs.group23 import encode_r143 as encode, decode_r143 as decode
    with pytest.raises(KeyError) as error:
        encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    assert encode({'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}) == {'v_143': ['red', 'blue'], 'flag_143': '42', 'mode_143': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}) == {'v_143': ['red', 'blue'], 'qty_143': None, 'flag_143': '42', 'mode_143': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}) == {'v_143': ['red', 'blue'], 'qty_143': 'snow 雪', 'flag_143': '-7', 'mode_143': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True}) == {'v_143': ['red', 'blue'], 'qty_143': 'snow 雪', 'mode_143': 'yes'}
    with pytest.raises(KeyError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42})
    assert error.value.args == ('active_3',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None})
    assert error.value.args == ('active_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_143': 'snow 雪', 'flag_143': '42', 'mode_143': 'yes'})
    assert error.value.args == ('v_143',)
    with pytest.raises(ValueError) as error:
        decode({'v_143': None, 'qty_143': 'snow 雪', 'flag_143': '42', 'mode_143': 'yes'})
    assert error.value.args == ('v_143',)
    assert decode({'v_143': ['red', 'blue'], 'flag_143': '42', 'mode_143': 'yes'}) == {'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}
    assert decode({'v_143': ['red', 'blue'], 'qty_143': None, 'flag_143': '42', 'mode_143': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}
    assert decode({'v_143': ['red', 'blue'], 'qty_143': 'snow 雪', 'mode_143': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': -7, 'active_3': True}
    assert decode({'v_143': ['red', 'blue'], 'qty_143': 'snow 雪', 'flag_143': None, 'mode_143': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}
    with pytest.raises(KeyError) as error:
        decode({'v_143': ['red', 'blue'], 'qty_143': 'snow 雪', 'flag_143': '42'})
    assert error.value.args == ('mode_143',)
    with pytest.raises(ValueError) as error:
        decode({'v_143': ['red', 'blue'], 'qty_143': 'snow 雪', 'flag_143': '42', 'mode_143': None})
    assert error.value.args == ('mode_143',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group23 import encode_r143 as encode, decode_r143 as decode
    value = {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_143': ['', 'a', 'a', '雪'], 'qty_143': '', 'flag_143': '-100000000000000000003', 'mode_143': 'no'}
    assert value == before
    assert result is not value
    assert result['v_143'] is not value['labels_0']
    result['v_143'].append("changed")
    assert value == before
    value = {'v_143': ['', 'a', 'a', '雪'], 'qty_143': '', 'flag_143': '-100000000000000000003', 'mode_143': 'no'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    assert value == before
    assert result is not value
    assert result['labels_0'] is not value['v_143']
    result['labels_0'].append("changed")
    assert value == before
    assert encode({'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}) == {'v_143': [], 'qty_143': '', 'flag_143': '0', 'mode_143': 'no'}
    assert decode({'v_143': [], 'qty_143': '', 'flag_143': '0', 'mode_143': 'no'}) == {'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}
