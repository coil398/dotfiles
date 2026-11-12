"""Spec: docs/SPEC.md §§2–5 and docs/group10.md#r066."""

def test_encode_normal():
    from record_codecs.group10 import encode_r066 as encode, decode_r066 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_066': 'snow 雪', 'qty_066': '42', 'flag_066': 'ON', 'mode_066': 'R66'}

def test_decode_normal():
    from record_codecs.group10 import encode_r066 as encode, decode_r066 as decode
    assert decode({'v_066': 'snow 雪', 'qty_066': '42', 'flag_066': 'ON', 'mode_066': 'R66', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group10 import encode_r066 as encode, decode_r066 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_066': '42', 'flag_066': 'ON', 'mode_066': 'R66'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_066': 'snow 雪', 'flag_066': 'ON', 'mode_066': 'R66'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_066': 'snow 雪', 'qty_066': '42', 'flag_066': 'OFF', 'mode_066': 'R66'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_066': 'snow 雪', 'qty_066': '42', 'flag_066': None, 'mode_066': 'R66'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_066': 'snow 雪', 'qty_066': '42', 'flag_066': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_066': '42', 'flag_066': 'ON', 'mode_066': 'R66'})
    assert error.value.args == ('v_066',)
    assert decode({'v_066': None, 'qty_066': '42', 'flag_066': 'ON', 'mode_066': 'R66'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_066': 'snow 雪', 'flag_066': 'ON', 'mode_066': 'R66'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_066': 'snow 雪', 'qty_066': None, 'flag_066': 'ON', 'mode_066': 'R66'})
    assert error.value.args == ('qty_066',)
    assert decode({'v_066': 'snow 雪', 'qty_066': '42', 'mode_066': 'R66'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_066': 'snow 雪', 'qty_066': '42', 'flag_066': None, 'mode_066': 'R66'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_066': 'snow 雪', 'qty_066': '42', 'flag_066': 'ON'})
    assert error.value.args == ('mode_066',)
    assert decode({'v_066': 'snow 雪', 'qty_066': '42', 'flag_066': 'ON', 'mode_066': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group10 import encode_r066 as encode, decode_r066 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_066': '', 'qty_066': '-100000000000000000003', 'flag_066': 'OFF', 'mode_066': 'D66'}
    assert value == before
    assert result is not value
    value = {'v_066': '', 'qty_066': '-100000000000000000003', 'flag_066': 'OFF', 'mode_066': 'D66'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_066': '', 'qty_066': '0', 'flag_066': 'OFF', 'mode_066': 'H66'}
    assert decode({'v_066': '', 'qty_066': '0', 'flag_066': 'OFF', 'mode_066': 'H66'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
