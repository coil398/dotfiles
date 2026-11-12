"""Spec: docs/SPEC.md §§2–5 and docs/group01.md#r012."""

def test_encode_normal():
    from record_codecs.group01 import encode_r012 as encode, decode_r012 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_012': 'snow 雪', 'qty_012': '42', 'flag_012': 'ON', 'mode_012': 'R12'}

def test_decode_normal():
    from record_codecs.group01 import encode_r012 as encode, decode_r012 as decode
    assert decode({'v_012': 'snow 雪', 'qty_012': '42', 'flag_012': 'ON', 'mode_012': 'R12', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group01 import encode_r012 as encode, decode_r012 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_012': '42', 'flag_012': 'ON', 'mode_012': 'R12'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_012': 'snow 雪', 'flag_012': 'ON', 'mode_012': 'R12'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_012': 'snow 雪', 'qty_012': '42', 'flag_012': 'OFF', 'mode_012': 'R12'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_012': 'snow 雪', 'qty_012': '42', 'flag_012': None, 'mode_012': 'R12'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_012': 'snow 雪', 'qty_012': '42', 'flag_012': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_012': '42', 'flag_012': 'ON', 'mode_012': 'R12'})
    assert error.value.args == ('v_012',)
    assert decode({'v_012': None, 'qty_012': '42', 'flag_012': 'ON', 'mode_012': 'R12'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_012': 'snow 雪', 'flag_012': 'ON', 'mode_012': 'R12'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_012': 'snow 雪', 'qty_012': None, 'flag_012': 'ON', 'mode_012': 'R12'})
    assert error.value.args == ('qty_012',)
    assert decode({'v_012': 'snow 雪', 'qty_012': '42', 'mode_012': 'R12'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_012': 'snow 雪', 'qty_012': '42', 'flag_012': None, 'mode_012': 'R12'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_012': 'snow 雪', 'qty_012': '42', 'flag_012': 'ON'})
    assert error.value.args == ('mode_012',)
    assert decode({'v_012': 'snow 雪', 'qty_012': '42', 'flag_012': 'ON', 'mode_012': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group01 import encode_r012 as encode, decode_r012 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_012': '', 'qty_012': '-100000000000000000003', 'flag_012': 'OFF', 'mode_012': 'D12'}
    assert value == before
    assert result is not value
    value = {'v_012': '', 'qty_012': '-100000000000000000003', 'flag_012': 'OFF', 'mode_012': 'D12'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_012': '', 'qty_012': '0', 'flag_012': 'OFF', 'mode_012': 'H12'}
    assert decode({'v_012': '', 'qty_012': '0', 'flag_012': 'OFF', 'mode_012': 'H12'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
