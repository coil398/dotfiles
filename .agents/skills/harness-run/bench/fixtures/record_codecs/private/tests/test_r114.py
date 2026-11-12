"""Spec: docs/SPEC.md §§2–5 and docs/group18.md#r114."""

def test_encode_normal():
    from record_codecs.group18 import encode_r114 as encode, decode_r114 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_114': 'snow 雪', 'qty_114': '42', 'flag_114': 'ON', 'mode_114': 'R114'}

def test_decode_normal():
    from record_codecs.group18 import encode_r114 as encode, decode_r114 as decode
    assert decode({'v_114': 'snow 雪', 'qty_114': '42', 'flag_114': 'ON', 'mode_114': 'R114', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group18 import encode_r114 as encode, decode_r114 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_114': 'unset', 'qty_114': '42', 'flag_114': 'ON', 'mode_114': 'R114'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_114': 'snow 雪', 'qty_114': None, 'flag_114': 'ON', 'mode_114': 'R114'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_114': 'snow 雪', 'qty_114': '42', 'mode_114': 'R114'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_114': 'snow 雪', 'qty_114': '42', 'mode_114': 'R114'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_114': 'snow 雪', 'qty_114': '42', 'flag_114': 'ON', 'mode_114': 'H114'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_114': '42', 'flag_114': 'ON', 'mode_114': 'R114'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_114': None, 'qty_114': '42', 'flag_114': 'ON', 'mode_114': 'R114'})
    assert error.value.args == ('v_114',)
    with pytest.raises(KeyError) as error:
        decode({'v_114': 'snow 雪', 'flag_114': 'ON', 'mode_114': 'R114'})
    assert error.value.args == ('qty_114',)
    assert decode({'v_114': 'snow 雪', 'qty_114': None, 'flag_114': 'ON', 'mode_114': 'R114'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_114': 'snow 雪', 'qty_114': '42', 'mode_114': 'R114'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_114': 'snow 雪', 'qty_114': '42', 'flag_114': None, 'mode_114': 'R114'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_114': 'snow 雪', 'qty_114': '42', 'flag_114': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_114': 'snow 雪', 'qty_114': '42', 'flag_114': 'ON', 'mode_114': None})
    assert error.value.args == ('mode_114',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group18 import encode_r114 as encode, decode_r114 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_114': '', 'qty_114': '-100000000000000000003', 'flag_114': 'OFF', 'mode_114': 'D114'}
    assert value == before
    assert result is not value
    value = {'v_114': '', 'qty_114': '-100000000000000000003', 'flag_114': 'OFF', 'mode_114': 'D114'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_114': '', 'qty_114': '0', 'flag_114': 'OFF', 'mode_114': 'H114'}
    assert decode({'v_114': '', 'qty_114': '0', 'flag_114': 'OFF', 'mode_114': 'H114'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
