"""Spec: docs/SPEC.md §§2–5 and docs/group08.md#r054."""

def test_encode_normal():
    from record_codecs.group08 import encode_r054 as encode, decode_r054 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_054': 'snow 雪', 'qty_054': '42', 'flag_054': 'ON', 'mode_054': 'R54'}

def test_decode_normal():
    from record_codecs.group08 import encode_r054 as encode, decode_r054 as decode
    assert decode({'v_054': 'snow 雪', 'qty_054': '42', 'flag_054': 'ON', 'mode_054': 'R54', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group08 import encode_r054 as encode, decode_r054 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_054': '42', 'flag_054': 'ON', 'mode_054': 'R54'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_054': None, 'qty_054': '42', 'flag_054': 'ON', 'mode_054': 'R54'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_054': 'snow 雪', 'qty_054': '-7', 'flag_054': 'ON', 'mode_054': 'R54'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_054': 'snow 雪', 'flag_054': 'ON', 'mode_054': 'R54'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_054': 'snow 雪', 'qty_054': '42', 'flag_054': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_054': 'snow 雪', 'qty_054': '42', 'flag_054': 'ON', 'mode_054': None}
    assert decode({'qty_054': '42', 'flag_054': 'ON', 'mode_054': 'R54'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_054': None, 'qty_054': '42', 'flag_054': 'ON', 'mode_054': 'R54'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_054': 'snow 雪', 'flag_054': 'ON', 'mode_054': 'R54'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_054': 'snow 雪', 'qty_054': None, 'flag_054': 'ON', 'mode_054': 'R54'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_054': 'snow 雪', 'qty_054': '42', 'mode_054': 'R54'})
    assert error.value.args == ('flag_054',)
    with pytest.raises(ValueError) as error:
        decode({'v_054': 'snow 雪', 'qty_054': '42', 'flag_054': None, 'mode_054': 'R54'})
    assert error.value.args == ('flag_054',)
    assert decode({'v_054': 'snow 雪', 'qty_054': '42', 'flag_054': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_054': 'snow 雪', 'qty_054': '42', 'flag_054': 'ON', 'mode_054': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group08 import encode_r054 as encode, decode_r054 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_054': '', 'qty_054': '-100000000000000000003', 'flag_054': 'OFF', 'mode_054': 'D54'}
    assert value == before
    assert result is not value
    value = {'v_054': '', 'qty_054': '-100000000000000000003', 'flag_054': 'OFF', 'mode_054': 'D54'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_054': '', 'qty_054': '0', 'flag_054': 'OFF', 'mode_054': 'H54'}
    assert decode({'v_054': '', 'qty_054': '0', 'flag_054': 'OFF', 'mode_054': 'H54'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
