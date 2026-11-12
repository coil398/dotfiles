"""Spec: docs/SPEC.md §§2–5 and docs/group28.md#r174."""

def test_encode_normal():
    from record_codecs.group28 import encode_r174 as encode, decode_r174 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_174': 'snow 雪', 'qty_174': '42', 'flag_174': 'ON', 'mode_174': 'R174'}

def test_decode_normal():
    from record_codecs.group28 import encode_r174 as encode, decode_r174 as decode
    assert decode({'v_174': 'snow 雪', 'qty_174': '42', 'flag_174': 'ON', 'mode_174': 'R174', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group28 import encode_r174 as encode, decode_r174 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_174': '42', 'flag_174': 'ON', 'mode_174': 'R174'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_174': 'snow 雪', 'flag_174': 'ON', 'mode_174': 'R174'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_174': 'snow 雪', 'qty_174': '42', 'flag_174': 'OFF', 'mode_174': 'R174'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_174': 'snow 雪', 'qty_174': '42', 'flag_174': None, 'mode_174': 'R174'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_174': 'snow 雪', 'qty_174': '42', 'flag_174': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_174': '42', 'flag_174': 'ON', 'mode_174': 'R174'})
    assert error.value.args == ('v_174',)
    assert decode({'v_174': None, 'qty_174': '42', 'flag_174': 'ON', 'mode_174': 'R174'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_174': 'snow 雪', 'flag_174': 'ON', 'mode_174': 'R174'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_174': 'snow 雪', 'qty_174': None, 'flag_174': 'ON', 'mode_174': 'R174'})
    assert error.value.args == ('qty_174',)
    assert decode({'v_174': 'snow 雪', 'qty_174': '42', 'mode_174': 'R174'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_174': 'snow 雪', 'qty_174': '42', 'flag_174': None, 'mode_174': 'R174'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_174': 'snow 雪', 'qty_174': '42', 'flag_174': 'ON'})
    assert error.value.args == ('mode_174',)
    assert decode({'v_174': 'snow 雪', 'qty_174': '42', 'flag_174': 'ON', 'mode_174': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group28 import encode_r174 as encode, decode_r174 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_174': '', 'qty_174': '-100000000000000000003', 'flag_174': 'OFF', 'mode_174': 'D174'}
    assert value == before
    assert result is not value
    value = {'v_174': '', 'qty_174': '-100000000000000000003', 'flag_174': 'OFF', 'mode_174': 'D174'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_174': '', 'qty_174': '0', 'flag_174': 'OFF', 'mode_174': 'H174'}
    assert decode({'v_174': '', 'qty_174': '0', 'flag_174': 'OFF', 'mode_174': 'H174'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
