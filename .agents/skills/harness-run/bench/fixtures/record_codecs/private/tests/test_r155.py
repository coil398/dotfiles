"""Spec: docs/SPEC.md §§2–5 and docs/group25.md#r155."""

def test_encode_normal():
    from record_codecs.group25 import encode_r155 as encode, decode_r155 as decode
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True, 'ignored': 'extra'}) == {'v_155': ['red', 'blue'], 'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'yes'}

def test_decode_normal():
    from record_codecs.group25 import encode_r155 as encode, decode_r155 as decode
    assert decode({'v_155': ['red', 'blue'], 'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'yes', 'ignored': 'extra'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}

def test_missing_null():
    import pytest
    from record_codecs.group25 import encode_r155 as encode, decode_r155 as decode
    assert encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'v_155': ['default'], 'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'yes'}
    result = encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True})
    result['v_155'].append("changed")
    assert encode({'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'v_155': ['default'], 'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'yes'}
    assert encode({'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}) == {'v_155': None, 'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'yes'}
    with pytest.raises(KeyError) as error:
        encode({'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True})
    assert error.value.args == ('title_1',)
    assert encode({'labels_0': ['red', 'blue'], 'title_1': None, 'count_2': 42, 'active_3': True}) == {'v_155': ['red', 'blue'], 'flag_155': '42', 'mode_155': 'yes'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}) == {'v_155': ['red', 'blue'], 'qty_155': 'snow 雪', 'mode_155': 'yes'}
    with pytest.raises(ValueError) as error:
        encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': None, 'active_3': True})
    assert error.value.args == ('count_2',)
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42}) == {'v_155': ['red', 'blue'], 'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'no'}
    assert encode({'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None}) == {'v_155': ['red', 'blue'], 'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': None}
    assert decode({'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'yes'}) == {'labels_0': ['default'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    result = decode({'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'yes'})
    result['labels_0'].append("changed")
    assert decode({'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'yes'}) == {'labels_0': ['default'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    assert decode({'v_155': None, 'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': 'yes'}) == {'labels_0': None, 'title_1': 'snow 雪', 'count_2': 42, 'active_3': True}
    with pytest.raises(KeyError) as error:
        decode({'v_155': ['red', 'blue'], 'flag_155': '42', 'mode_155': 'yes'})
    assert error.value.args == ('qty_155',)
    assert decode({'v_155': ['red', 'blue'], 'qty_155': None, 'flag_155': '42', 'mode_155': 'yes'}) == {'labels_0': ['red', 'blue'], 'count_2': 42, 'active_3': True}
    assert decode({'v_155': ['red', 'blue'], 'qty_155': 'snow 雪', 'mode_155': 'yes'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'active_3': True}
    with pytest.raises(ValueError) as error:
        decode({'v_155': ['red', 'blue'], 'qty_155': 'snow 雪', 'flag_155': None, 'mode_155': 'yes'})
    assert error.value.args == ('flag_155',)
    assert decode({'v_155': ['red', 'blue'], 'qty_155': 'snow 雪', 'flag_155': '42'}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': False}
    assert decode({'v_155': ['red', 'blue'], 'qty_155': 'snow 雪', 'flag_155': '42', 'mode_155': None}) == {'labels_0': ['red', 'blue'], 'title_1': 'snow 雪', 'count_2': 42, 'active_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group25 import encode_r155 as encode, decode_r155 as decode
    value = {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_155': ['', 'a', 'a', '雪'], 'qty_155': '', 'flag_155': '-100000000000000000003', 'mode_155': 'no'}
    assert value == before
    assert result is not value
    assert result['v_155'] is not value['labels_0']
    result['v_155'].append("changed")
    assert value == before
    value = {'v_155': ['', 'a', 'a', '雪'], 'qty_155': '', 'flag_155': '-100000000000000000003', 'mode_155': 'no'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'labels_0': ['', 'a', 'a', '雪'], 'title_1': '', 'count_2': -100000000000000000003, 'active_3': False}
    assert value == before
    assert result is not value
    assert result['labels_0'] is not value['v_155']
    result['labels_0'].append("changed")
    assert value == before
    assert encode({'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}) == {'v_155': [], 'qty_155': '', 'flag_155': '0', 'mode_155': 'no'}
    assert decode({'v_155': [], 'qty_155': '', 'flag_155': '0', 'mode_155': 'no'}) == {'labels_0': [], 'title_1': '', 'count_2': 0, 'active_3': False}
