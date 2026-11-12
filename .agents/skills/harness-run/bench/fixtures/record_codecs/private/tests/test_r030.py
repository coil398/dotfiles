"""Spec: docs/SPEC.md §§2–5 and docs/group04.md#r030."""

def test_encode_normal():
    from record_codecs.group04 import encode_r030 as encode, decode_r030 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_030': 'snow 雪', 'qty_030': '42', 'flag_030': 'ON', 'mode_030': 'R30'}

def test_decode_normal():
    from record_codecs.group04 import encode_r030 as encode, decode_r030 as decode
    assert decode({'v_030': 'snow 雪', 'qty_030': '42', 'flag_030': 'ON', 'mode_030': 'R30', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group04 import encode_r030 as encode, decode_r030 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_030': '42', 'flag_030': 'ON', 'mode_030': 'R30'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_030': 'snow 雪', 'flag_030': 'ON', 'mode_030': 'R30'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_030': 'snow 雪', 'qty_030': '42', 'flag_030': 'OFF', 'mode_030': 'R30'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_030': 'snow 雪', 'qty_030': '42', 'flag_030': None, 'mode_030': 'R30'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_030': 'snow 雪', 'qty_030': '42', 'flag_030': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_030': '42', 'flag_030': 'ON', 'mode_030': 'R30'})
    assert error.value.args == ('v_030',)
    assert decode({'v_030': None, 'qty_030': '42', 'flag_030': 'ON', 'mode_030': 'R30'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_030': 'snow 雪', 'flag_030': 'ON', 'mode_030': 'R30'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_030': 'snow 雪', 'qty_030': None, 'flag_030': 'ON', 'mode_030': 'R30'})
    assert error.value.args == ('qty_030',)
    assert decode({'v_030': 'snow 雪', 'qty_030': '42', 'mode_030': 'R30'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_030': 'snow 雪', 'qty_030': '42', 'flag_030': None, 'mode_030': 'R30'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_030': 'snow 雪', 'qty_030': '42', 'flag_030': 'ON'})
    assert error.value.args == ('mode_030',)
    assert decode({'v_030': 'snow 雪', 'qty_030': '42', 'flag_030': 'ON', 'mode_030': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group04 import encode_r030 as encode, decode_r030 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_030': '', 'qty_030': '-100000000000000000003', 'flag_030': 'OFF', 'mode_030': 'D30'}
    assert value == before
    assert result is not value
    value = {'v_030': '', 'qty_030': '-100000000000000000003', 'flag_030': 'OFF', 'mode_030': 'D30'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_030': '', 'qty_030': '0', 'flag_030': 'OFF', 'mode_030': 'H30'}
    assert decode({'v_030': '', 'qty_030': '0', 'flag_030': 'OFF', 'mode_030': 'H30'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
