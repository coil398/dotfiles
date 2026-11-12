"""Spec: docs/SPEC.md §§2–5 and docs/group13.md#r083."""

def test_encode_normal():
    from record_codecs.group13 import encode_r083 as encode, decode_r083 as decode
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True, 'ignored': 'extra'}) == {'v_083': ['red', 'blue'], 'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'yes'}

def test_decode_normal():
    from record_codecs.group13 import encode_r083 as encode, decode_r083 as decode
    assert decode({'v_083': ['red', 'blue'], 'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'yes', 'ignored': 'extra'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}

def test_missing_null():
    import pytest
    from record_codecs.group13 import encode_r083 as encode, decode_r083 as decode
    assert encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'v_083': ['default'], 'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'yes'}
    result = encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    result['v_083'].append("changed")
    assert encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'v_083': ['default'], 'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'yes'}
    assert encode({'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'v_083': None, 'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'yes'}
    with pytest.raises(KeyError) as error:
        encode({'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True})
    assert error.value.args == ('title_1',)
    assert encode({'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}) == {'v_083': ['red', 'blue'], 'flag_083': '42', 'mode_083': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}) == {'v_083': ['red', 'blue'], 'qty_083': 'snow 雪', 'mode_083': 'yes'}
    with pytest.raises(ValueError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True})
    assert error.value.args == ('count_2',)
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42}) == {'v_083': ['red', 'blue'], 'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'no'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None}) == {'v_083': ['red', 'blue'], 'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': None}
    assert decode({'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'yes'}) == {'labels_0': ['default'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    result = decode({'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'yes'})
    result['labels_0'].append("changed")
    assert decode({'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'yes'}) == {'labels_0': ['default'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    assert decode({'v_083': None, 'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': 'yes'}) == {'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    with pytest.raises(KeyError) as error:
        decode({'v_083': ['red', 'blue'], 'flag_083': '42', 'mode_083': 'yes'})
    assert error.value.args == ('qty_083',)
    assert decode({'v_083': ['red', 'blue'], 'qty_083': None, 'flag_083': '42', 'mode_083': 'yes'}) == {'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}
    assert decode({'v_083': ['red', 'blue'], 'qty_083': 'snow 雪', 'mode_083': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}
    with pytest.raises(ValueError) as error:
        decode({'v_083': ['red', 'blue'], 'qty_083': 'snow 雪', 'flag_083': None, 'mode_083': 'yes'})
    assert error.value.args == ('flag_083',)
    assert decode({'v_083': ['red', 'blue'], 'qty_083': 'snow 雪', 'flag_083': '42'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': False}
    assert decode({'v_083': ['red', 'blue'], 'qty_083': 'snow 雪', 'flag_083': '42', 'mode_083': None}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group13 import encode_r083 as encode, decode_r083 as decode
    value = {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_083': ['', 'a', 'a', '雪'], 'qty_083': '', 'flag_083': '-100000000000000000003', 'mode_083': 'no'}
    assert value == before
    assert result is not value
    assert result['v_083'] is not value['labels_0']
    result['v_083'].append("changed")
    assert value == before
    value = {'v_083': ['', 'a', 'a', '雪'], 'qty_083': '', 'flag_083': '-100000000000000000003', 'mode_083': 'no'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    assert value == before
    assert result is not value
    assert result['labels_0'] is not value['v_083']
    result['labels_0'].append("changed")
    assert value == before
    assert encode({'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}) == {'v_083': [], 'qty_083': '', 'flag_083': '0', 'mode_083': 'no'}
    assert decode({'v_083': [], 'qty_083': '', 'flag_083': '0', 'mode_083': 'no'}) == {'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}
