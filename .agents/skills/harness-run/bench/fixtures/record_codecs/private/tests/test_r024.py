"""Spec: docs/SPEC.md §§2–5 and docs/group03.md#r024."""

def test_encode_normal():
    from record_codecs.group03 import encode_r024 as encode, decode_r024 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_024': 'snow 雪', 'qty_024': '42', 'flag_024': 'ON', 'mode_024': 'R24'}

def test_decode_normal():
    from record_codecs.group03 import encode_r024 as encode, decode_r024 as decode
    assert decode({'v_024': 'snow 雪', 'qty_024': '42', 'flag_024': 'ON', 'mode_024': 'R24', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group03 import encode_r024 as encode, decode_r024 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_024': 'unset', 'qty_024': '42', 'flag_024': 'ON', 'mode_024': 'R24'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_024': 'snow 雪', 'qty_024': None, 'flag_024': 'ON', 'mode_024': 'R24'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_024': 'snow 雪', 'qty_024': '42', 'mode_024': 'R24'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_024': 'snow 雪', 'qty_024': '42', 'mode_024': 'R24'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_024': 'snow 雪', 'qty_024': '42', 'flag_024': 'ON', 'mode_024': 'H24'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_024': '42', 'flag_024': 'ON', 'mode_024': 'R24'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_024': None, 'qty_024': '42', 'flag_024': 'ON', 'mode_024': 'R24'})
    assert error.value.args == ('v_024',)
    with pytest.raises(KeyError) as error:
        decode({'v_024': 'snow 雪', 'flag_024': 'ON', 'mode_024': 'R24'})
    assert error.value.args == ('qty_024',)
    assert decode({'v_024': 'snow 雪', 'qty_024': None, 'flag_024': 'ON', 'mode_024': 'R24'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_024': 'snow 雪', 'qty_024': '42', 'mode_024': 'R24'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_024': 'snow 雪', 'qty_024': '42', 'flag_024': None, 'mode_024': 'R24'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_024': 'snow 雪', 'qty_024': '42', 'flag_024': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_024': 'snow 雪', 'qty_024': '42', 'flag_024': 'ON', 'mode_024': None})
    assert error.value.args == ('mode_024',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group03 import encode_r024 as encode, decode_r024 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_024': '', 'qty_024': '-100000000000000000003', 'flag_024': 'OFF', 'mode_024': 'D24'}
    assert value == before
    assert result is not value
    value = {'v_024': '', 'qty_024': '-100000000000000000003', 'flag_024': 'OFF', 'mode_024': 'D24'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_024': '', 'qty_024': '0', 'flag_024': 'OFF', 'mode_024': 'H24'}
    assert decode({'v_024': '', 'qty_024': '0', 'flag_024': 'OFF', 'mode_024': 'H24'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
