"""Spec: docs/SPEC.md §§2–5 and docs/group10.md#r065."""

def test_encode_normal():
    from record_codecs.group10 import encode_r065 as encode, decode_r065 as decode
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True, 'ignored': 'extra'}) == {'v_065': ['red', 'blue'], 'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'yes'}

def test_decode_normal():
    from record_codecs.group10 import encode_r065 as encode, decode_r065 as decode
    assert decode({'v_065': ['red', 'blue'], 'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'yes', 'ignored': 'extra'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}

def test_missing_null():
    import pytest
    from record_codecs.group10 import encode_r065 as encode, decode_r065 as decode
    assert encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'v_065': ['default'], 'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'yes'}
    result = encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    result['v_065'].append("changed")
    assert encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'v_065': ['default'], 'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'yes'}
    assert encode({'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'v_065': None, 'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'yes'}
    with pytest.raises(KeyError) as error:
        encode({'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True})
    assert error.value.args == ('title_1',)
    assert encode({'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}) == {'v_065': ['red', 'blue'], 'flag_065': '42', 'mode_065': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}) == {'v_065': ['red', 'blue'], 'qty_065': 'snow 雪', 'mode_065': 'yes'}
    with pytest.raises(ValueError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True})
    assert error.value.args == ('count_2',)
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42}) == {'v_065': ['red', 'blue'], 'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'no'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None}) == {'v_065': ['red', 'blue'], 'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': None}
    assert decode({'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'yes'}) == {'labels_0': ['default'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    result = decode({'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'yes'})
    result['labels_0'].append("changed")
    assert decode({'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'yes'}) == {'labels_0': ['default'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    assert decode({'v_065': None, 'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': 'yes'}) == {'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    with pytest.raises(KeyError) as error:
        decode({'v_065': ['red', 'blue'], 'flag_065': '42', 'mode_065': 'yes'})
    assert error.value.args == ('qty_065',)
    assert decode({'v_065': ['red', 'blue'], 'qty_065': None, 'flag_065': '42', 'mode_065': 'yes'}) == {'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}
    assert decode({'v_065': ['red', 'blue'], 'qty_065': 'snow 雪', 'mode_065': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}
    with pytest.raises(ValueError) as error:
        decode({'v_065': ['red', 'blue'], 'qty_065': 'snow 雪', 'flag_065': None, 'mode_065': 'yes'})
    assert error.value.args == ('flag_065',)
    assert decode({'v_065': ['red', 'blue'], 'qty_065': 'snow 雪', 'flag_065': '42'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': False}
    assert decode({'v_065': ['red', 'blue'], 'qty_065': 'snow 雪', 'flag_065': '42', 'mode_065': None}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group10 import encode_r065 as encode, decode_r065 as decode
    value = {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_065': ['', 'a', 'a', '雪'], 'qty_065': '', 'flag_065': '-100000000000000000003', 'mode_065': 'no'}
    assert value == before
    assert result is not value
    assert result['v_065'] is not value['labels_0']
    result['v_065'].append("changed")
    assert value == before
    value = {'v_065': ['', 'a', 'a', '雪'], 'qty_065': '', 'flag_065': '-100000000000000000003', 'mode_065': 'no'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    assert value == before
    assert result is not value
    assert result['labels_0'] is not value['v_065']
    result['labels_0'].append("changed")
    assert value == before
    assert encode({'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}) == {'v_065': [], 'qty_065': '', 'flag_065': '0', 'mode_065': 'no'}
    assert decode({'v_065': [], 'qty_065': '', 'flag_065': '0', 'mode_065': 'no'}) == {'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}
