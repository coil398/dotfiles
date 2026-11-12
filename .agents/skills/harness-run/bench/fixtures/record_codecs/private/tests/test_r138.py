"""Spec: docs/SPEC.md §§2–5 and docs/group22.md#r138."""

def test_encode_normal():
    from record_codecs.group22 import encode_r138 as encode, decode_r138 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_138': 'snow 雪', 'qty_138': '42', 'flag_138': 'ON', 'mode_138': 'R138'}

def test_decode_normal():
    from record_codecs.group22 import encode_r138 as encode, decode_r138 as decode
    assert decode({'v_138': 'snow 雪', 'qty_138': '42', 'flag_138': 'ON', 'mode_138': 'R138', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group22 import encode_r138 as encode, decode_r138 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_138': '42', 'flag_138': 'ON', 'mode_138': 'R138'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_138': 'snow 雪', 'flag_138': 'ON', 'mode_138': 'R138'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_138': 'snow 雪', 'qty_138': '42', 'flag_138': 'OFF', 'mode_138': 'R138'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_138': 'snow 雪', 'qty_138': '42', 'flag_138': None, 'mode_138': 'R138'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_138': 'snow 雪', 'qty_138': '42', 'flag_138': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_138': '42', 'flag_138': 'ON', 'mode_138': 'R138'})
    assert error.value.args == ('v_138',)
    assert decode({'v_138': None, 'qty_138': '42', 'flag_138': 'ON', 'mode_138': 'R138'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_138': 'snow 雪', 'flag_138': 'ON', 'mode_138': 'R138'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_138': 'snow 雪', 'qty_138': None, 'flag_138': 'ON', 'mode_138': 'R138'})
    assert error.value.args == ('qty_138',)
    assert decode({'v_138': 'snow 雪', 'qty_138': '42', 'mode_138': 'R138'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_138': 'snow 雪', 'qty_138': '42', 'flag_138': None, 'mode_138': 'R138'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_138': 'snow 雪', 'qty_138': '42', 'flag_138': 'ON'})
    assert error.value.args == ('mode_138',)
    assert decode({'v_138': 'snow 雪', 'qty_138': '42', 'flag_138': 'ON', 'mode_138': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group22 import encode_r138 as encode, decode_r138 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_138': '', 'qty_138': '-100000000000000000003', 'flag_138': 'OFF', 'mode_138': 'D138'}
    assert value == before
    assert result is not value
    value = {'v_138': '', 'qty_138': '-100000000000000000003', 'flag_138': 'OFF', 'mode_138': 'D138'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_138': '', 'qty_138': '0', 'flag_138': 'OFF', 'mode_138': 'H138'}
    assert decode({'v_138': '', 'qty_138': '0', 'flag_138': 'OFF', 'mode_138': 'H138'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
