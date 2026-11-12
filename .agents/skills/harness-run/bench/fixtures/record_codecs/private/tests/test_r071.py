"""Spec: docs/SPEC.md §§2–5 and docs/group11.md#r071."""

def test_encode_normal():
    from record_codecs.group11 import encode_r071 as encode, decode_r071 as decode
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True, 'ignored': 'extra'}) == {'v_071': ['red', 'blue'], 'qty_071': 'snow 雪', 'flag_071': '42', 'mode_071': 'yes'}

def test_decode_normal():
    from record_codecs.group11 import encode_r071 as encode, decode_r071 as decode
    assert decode({'v_071': ['red', 'blue'], 'qty_071': 'snow 雪', 'flag_071': '42', 'mode_071': 'yes', 'ignored': 'extra'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}

def test_missing_null():
    import pytest
    from record_codecs.group11 import encode_r071 as encode, decode_r071 as decode
    with pytest.raises(KeyError) as error:
        encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    assert error.value.args == ('labels_0',)
    assert encode({'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}) == {'v_071': ['red', 'blue'], 'flag_071': '42', 'mode_071': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}) == {'v_071': ['red', 'blue'], 'qty_071': None, 'flag_071': '42', 'mode_071': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}) == {'v_071': ['red', 'blue'], 'qty_071': 'snow 雪', 'flag_071': '-7', 'mode_071': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True}) == {'v_071': ['red', 'blue'], 'qty_071': 'snow 雪', 'mode_071': 'yes'}
    with pytest.raises(KeyError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42})
    assert error.value.args == ('active_3',)
    with pytest.raises(ValueError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None})
    assert error.value.args == ('active_3',)
    with pytest.raises(KeyError) as error:
        decode({'qty_071': 'snow 雪', 'flag_071': '42', 'mode_071': 'yes'})
    assert error.value.args == ('v_071',)
    with pytest.raises(ValueError) as error:
        decode({'v_071': None, 'qty_071': 'snow 雪', 'flag_071': '42', 'mode_071': 'yes'})
    assert error.value.args == ('v_071',)
    assert decode({'v_071': ['red', 'blue'], 'flag_071': '42', 'mode_071': 'yes'}) == {'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}
    assert decode({'v_071': ['red', 'blue'], 'qty_071': None, 'flag_071': '42', 'mode_071': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}
    assert decode({'v_071': ['red', 'blue'], 'qty_071': 'snow 雪', 'mode_071': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': -7, 'active_3': True}
    assert decode({'v_071': ['red', 'blue'], 'qty_071': 'snow 雪', 'flag_071': None, 'mode_071': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}
    with pytest.raises(KeyError) as error:
        decode({'v_071': ['red', 'blue'], 'qty_071': 'snow 雪', 'flag_071': '42'})
    assert error.value.args == ('mode_071',)
    with pytest.raises(ValueError) as error:
        decode({'v_071': ['red', 'blue'], 'qty_071': 'snow 雪', 'flag_071': '42', 'mode_071': None})
    assert error.value.args == ('mode_071',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group11 import encode_r071 as encode, decode_r071 as decode
    value = {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_071': ['', 'a', 'a', '雪'], 'qty_071': '', 'flag_071': '-100000000000000000003', 'mode_071': 'no'}
    assert value == before
    assert result is not value
    assert result['v_071'] is not value['labels_0']
    result['v_071'].append("changed")
    assert value == before
    value = {'v_071': ['', 'a', 'a', '雪'], 'qty_071': '', 'flag_071': '-100000000000000000003', 'mode_071': 'no'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    assert value == before
    assert result is not value
    assert result['labels_0'] is not value['v_071']
    result['labels_0'].append("changed")
    assert value == before
    assert encode({'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}) == {'v_071': [], 'qty_071': '', 'flag_071': '0', 'mode_071': 'no'}
    assert decode({'v_071': [], 'qty_071': '', 'flag_071': '0', 'mode_071': 'no'}) == {'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}
