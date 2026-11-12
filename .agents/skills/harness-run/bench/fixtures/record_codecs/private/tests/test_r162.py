"""Spec: docs/SPEC.md §§2–5 and docs/group26.md#r162."""

def test_encode_normal():
    from record_codecs.group26 import encode_r162 as encode, decode_r162 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_162': 'snow 雪', 'qty_162': '42', 'flag_162': 'ON', 'mode_162': 'R162'}

def test_decode_normal():
    from record_codecs.group26 import encode_r162 as encode, decode_r162 as decode
    assert decode({'v_162': 'snow 雪', 'qty_162': '42', 'flag_162': 'ON', 'mode_162': 'R162', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group26 import encode_r162 as encode, decode_r162 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_162': '42', 'flag_162': 'ON', 'mode_162': 'R162'}
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_162': None, 'qty_162': '42', 'flag_162': 'ON', 'mode_162': 'R162'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_162': 'snow 雪', 'qty_162': '-7', 'flag_162': 'ON', 'mode_162': 'R162'}
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_162': 'snow 雪', 'flag_162': 'ON', 'mode_162': 'R162'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'})
    assert error.value.args == ('active_2',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_162': 'snow 雪', 'qty_162': '42', 'flag_162': 'ON'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_162': 'snow 雪', 'qty_162': '42', 'flag_162': 'ON', 'mode_162': None}
    assert decode({'qty_162': '42', 'flag_162': 'ON', 'mode_162': 'R162'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_162': None, 'qty_162': '42', 'flag_162': 'ON', 'mode_162': 'R162'}) == {'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_162': 'snow 雪', 'flag_162': 'ON', 'mode_162': 'R162'}) == {'title_0': 'snow 雪', 'count_1': -7, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_162': 'snow 雪', 'qty_162': None, 'flag_162': 'ON', 'mode_162': 'R162'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_162': 'snow 雪', 'qty_162': '42', 'mode_162': 'R162'})
    assert error.value.args == ('flag_162',)
    with pytest.raises(ValueError) as error:
        decode({'v_162': 'snow 雪', 'qty_162': '42', 'flag_162': None, 'mode_162': 'R162'})
    assert error.value.args == ('flag_162',)
    assert decode({'v_162': 'snow 雪', 'qty_162': '42', 'flag_162': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}
    assert decode({'v_162': 'snow 雪', 'qty_162': '42', 'flag_162': 'ON', 'mode_162': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group26 import encode_r162 as encode, decode_r162 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_162': '', 'qty_162': '-100000000000000000003', 'flag_162': 'OFF', 'mode_162': 'D162'}
    assert value == before
    assert result is not value
    value = {'v_162': '', 'qty_162': '-100000000000000000003', 'flag_162': 'OFF', 'mode_162': 'D162'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_162': '', 'qty_162': '0', 'flag_162': 'OFF', 'mode_162': 'H162'}
    assert decode({'v_162': '', 'qty_162': '0', 'flag_162': 'OFF', 'mode_162': 'H162'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
