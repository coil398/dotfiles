"""Spec: docs/SPEC.md §§2–5 and docs/group19.md#r120."""

def test_encode_normal():
    from record_codecs.group19 import encode_r120 as encode, decode_r120 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_120': 'snow 雪', 'qty_120': '42', 'flag_120': 'ON', 'mode_120': 'R120'}

def test_decode_normal():
    from record_codecs.group19 import encode_r120 as encode, decode_r120 as decode
    assert decode({'v_120': 'snow 雪', 'qty_120': '42', 'flag_120': 'ON', 'mode_120': 'R120', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group19 import encode_r120 as encode, decode_r120 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_120': '42', 'flag_120': 'ON', 'mode_120': 'R120'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_120': 'snow 雪', 'flag_120': 'ON', 'mode_120': 'R120'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_120': 'snow 雪', 'qty_120': '42', 'flag_120': 'OFF', 'mode_120': 'R120'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_120': 'snow 雪', 'qty_120': '42', 'flag_120': None, 'mode_120': 'R120'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_120': 'snow 雪', 'qty_120': '42', 'flag_120': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_120': '42', 'flag_120': 'ON', 'mode_120': 'R120'})
    assert error.value.args == ('v_120',)
    assert decode({'v_120': None, 'qty_120': '42', 'flag_120': 'ON', 'mode_120': 'R120'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_120': 'snow 雪', 'flag_120': 'ON', 'mode_120': 'R120'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_120': 'snow 雪', 'qty_120': None, 'flag_120': 'ON', 'mode_120': 'R120'})
    assert error.value.args == ('qty_120',)
    assert decode({'v_120': 'snow 雪', 'qty_120': '42', 'mode_120': 'R120'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_120': 'snow 雪', 'qty_120': '42', 'flag_120': None, 'mode_120': 'R120'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_120': 'snow 雪', 'qty_120': '42', 'flag_120': 'ON'})
    assert error.value.args == ('mode_120',)
    assert decode({'v_120': 'snow 雪', 'qty_120': '42', 'flag_120': 'ON', 'mode_120': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group19 import encode_r120 as encode, decode_r120 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_120': '', 'qty_120': '-100000000000000000003', 'flag_120': 'OFF', 'mode_120': 'D120'}
    assert value == before
    assert result is not value
    value = {'v_120': '', 'qty_120': '-100000000000000000003', 'flag_120': 'OFF', 'mode_120': 'D120'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_120': '', 'qty_120': '0', 'flag_120': 'OFF', 'mode_120': 'H120'}
    assert decode({'v_120': '', 'qty_120': '0', 'flag_120': 'OFF', 'mode_120': 'H120'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
