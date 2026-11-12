"""Spec: docs/SPEC.md §§2–5 and docs/group13.md#r084."""

def test_encode_normal():
    from record_codecs.group13 import encode_r084 as encode, decode_r084 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_084': 'snow 雪', 'qty_084': '42', 'flag_084': 'ON', 'mode_084': 'R84'}

def test_decode_normal():
    from record_codecs.group13 import encode_r084 as encode, decode_r084 as decode
    assert decode({'v_084': 'snow 雪', 'qty_084': '42', 'flag_084': 'ON', 'mode_084': 'R84', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group13 import encode_r084 as encode, decode_r084 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_084': '42', 'flag_084': 'ON', 'mode_084': 'R84'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_084': 'snow 雪', 'flag_084': 'ON', 'mode_084': 'R84'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_084': 'snow 雪', 'qty_084': '42', 'flag_084': 'OFF', 'mode_084': 'R84'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_084': 'snow 雪', 'qty_084': '42', 'flag_084': None, 'mode_084': 'R84'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_084': 'snow 雪', 'qty_084': '42', 'flag_084': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_084': '42', 'flag_084': 'ON', 'mode_084': 'R84'})
    assert error.value.args == ('v_084',)
    assert decode({'v_084': None, 'qty_084': '42', 'flag_084': 'ON', 'mode_084': 'R84'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_084': 'snow 雪', 'flag_084': 'ON', 'mode_084': 'R84'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_084': 'snow 雪', 'qty_084': None, 'flag_084': 'ON', 'mode_084': 'R84'})
    assert error.value.args == ('qty_084',)
    assert decode({'v_084': 'snow 雪', 'qty_084': '42', 'mode_084': 'R84'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_084': 'snow 雪', 'qty_084': '42', 'flag_084': None, 'mode_084': 'R84'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_084': 'snow 雪', 'qty_084': '42', 'flag_084': 'ON'})
    assert error.value.args == ('mode_084',)
    assert decode({'v_084': 'snow 雪', 'qty_084': '42', 'flag_084': 'ON', 'mode_084': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group13 import encode_r084 as encode, decode_r084 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_084': '', 'qty_084': '-100000000000000000003', 'flag_084': 'OFF', 'mode_084': 'D84'}
    assert value == before
    assert result is not value
    value = {'v_084': '', 'qty_084': '-100000000000000000003', 'flag_084': 'OFF', 'mode_084': 'D84'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_084': '', 'qty_084': '0', 'flag_084': 'OFF', 'mode_084': 'H84'}
    assert decode({'v_084': '', 'qty_084': '0', 'flag_084': 'OFF', 'mode_084': 'H84'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
