"""Spec: docs/SPEC.md §§2–5 and docs/group24.md#r150."""

def test_encode_normal():
    from record_codecs.group24 import encode_r150 as encode, decode_r150 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_150': 'snow 雪', 'qty_150': '42', 'flag_150': 'ON', 'mode_150': 'R150'}

def test_decode_normal():
    from record_codecs.group24 import encode_r150 as encode, decode_r150 as decode
    assert decode({'v_150': 'snow 雪', 'qty_150': '42', 'flag_150': 'ON', 'mode_150': 'R150', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group24 import encode_r150 as encode, decode_r150 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_150': 'unset', 'qty_150': '42', 'flag_150': 'ON', 'mode_150': 'R150'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_150': 'snow 雪', 'qty_150': None, 'flag_150': 'ON', 'mode_150': 'R150'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_150': 'snow 雪', 'qty_150': '42', 'mode_150': 'R150'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_150': 'snow 雪', 'qty_150': '42', 'mode_150': 'R150'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_150': 'snow 雪', 'qty_150': '42', 'flag_150': 'ON', 'mode_150': 'H150'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_150': '42', 'flag_150': 'ON', 'mode_150': 'R150'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_150': None, 'qty_150': '42', 'flag_150': 'ON', 'mode_150': 'R150'})
    assert error.value.args == ('v_150',)
    with pytest.raises(KeyError) as error:
        decode({'v_150': 'snow 雪', 'flag_150': 'ON', 'mode_150': 'R150'})
    assert error.value.args == ('qty_150',)
    assert decode({'v_150': 'snow 雪', 'qty_150': None, 'flag_150': 'ON', 'mode_150': 'R150'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_150': 'snow 雪', 'qty_150': '42', 'mode_150': 'R150'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_150': 'snow 雪', 'qty_150': '42', 'flag_150': None, 'mode_150': 'R150'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_150': 'snow 雪', 'qty_150': '42', 'flag_150': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_150': 'snow 雪', 'qty_150': '42', 'flag_150': 'ON', 'mode_150': None})
    assert error.value.args == ('mode_150',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group24 import encode_r150 as encode, decode_r150 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_150': '', 'qty_150': '-100000000000000000003', 'flag_150': 'OFF', 'mode_150': 'D150'}
    assert value == before
    assert result is not value
    value = {'v_150': '', 'qty_150': '-100000000000000000003', 'flag_150': 'OFF', 'mode_150': 'D150'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_150': '', 'qty_150': '0', 'flag_150': 'OFF', 'mode_150': 'H150'}
    assert decode({'v_150': '', 'qty_150': '0', 'flag_150': 'OFF', 'mode_150': 'H150'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
