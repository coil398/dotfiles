"""Spec: docs/SPEC.md §§2–5 and docs/group17.md#r108."""

def test_encode_normal():
    from record_codecs.group17 import encode_r108 as encode, decode_r108 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_108': 'snow 雪', 'qty_108': '42', 'flag_108': 'ON', 'mode_108': 'R108'}

def test_decode_normal():
    from record_codecs.group17 import encode_r108 as encode, decode_r108 as decode
    assert decode({'v_108': 'snow 雪', 'qty_108': '42', 'flag_108': 'ON', 'mode_108': 'R108', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group17 import encode_r108 as encode, decode_r108 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_108': '42', 'flag_108': 'ON', 'mode_108': 'R108'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_108': None, 'qty_108': '42', 'flag_108': 'ON', 'mode_108': 'R108'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_108': 'snow 雪', 'qty_108': '-7', 'flag_108': 'ON', 'mode_108': 'R108'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_108': 'snow 雪', 'flag_108': 'ON', 'mode_108': 'R108'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_108': 'snow 雪', 'qty_108': '42', 'flag_108': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_108': 'snow 雪', 'qty_108': '42', 'flag_108': 'ON', 'mode_108': None}
    assert decode({'qty_108': '42', 'flag_108': 'ON', 'mode_108': 'R108'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_108': None, 'qty_108': '42', 'flag_108': 'ON', 'mode_108': 'R108'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_108': 'snow 雪', 'flag_108': 'ON', 'mode_108': 'R108'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_108': 'snow 雪', 'qty_108': None, 'flag_108': 'ON', 'mode_108': 'R108'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_108': 'snow 雪', 'qty_108': '42', 'mode_108': 'R108'})
    assert error.value.args == ('flag_108',)
    with pytest.raises(ValueError) as error:
        decode({'v_108': 'snow 雪', 'qty_108': '42', 'flag_108': None, 'mode_108': 'R108'})
    assert error.value.args == ('flag_108',)
    assert decode({'v_108': 'snow 雪', 'qty_108': '42', 'flag_108': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_108': 'snow 雪', 'qty_108': '42', 'flag_108': 'ON', 'mode_108': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group17 import encode_r108 as encode, decode_r108 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_108': '', 'qty_108': '-100000000000000000003', 'flag_108': 'OFF', 'mode_108': 'D108'}
    assert value == before
    assert result is not value
    value = {'v_108': '', 'qty_108': '-100000000000000000003', 'flag_108': 'OFF', 'mode_108': 'D108'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_108': '', 'qty_108': '0', 'flag_108': 'OFF', 'mode_108': 'H108'}
    assert decode({'v_108': '', 'qty_108': '0', 'flag_108': 'OFF', 'mode_108': 'H108'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
