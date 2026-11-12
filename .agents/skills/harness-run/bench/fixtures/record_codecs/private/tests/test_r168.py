"""Spec: docs/SPEC.md §§2–5 and docs/group27.md#r168."""

def test_encode_normal():
    from record_codecs.group27 import encode_r168 as encode, decode_r168 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_168': 'snow 雪', 'qty_168': '42', 'flag_168': 'ON', 'mode_168': 'R168'}

def test_decode_normal():
    from record_codecs.group27 import encode_r168 as encode, decode_r168 as decode
    assert decode({'v_168': 'snow 雪', 'qty_168': '42', 'flag_168': 'ON', 'mode_168': 'R168', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group27 import encode_r168 as encode, decode_r168 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_168': 'unset', 'qty_168': '42', 'flag_168': 'ON', 'mode_168': 'R168'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_168': 'snow 雪', 'qty_168': None, 'flag_168': 'ON', 'mode_168': 'R168'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_168': 'snow 雪', 'qty_168': '42', 'mode_168': 'R168'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_168': 'snow 雪', 'qty_168': '42', 'mode_168': 'R168'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_168': 'snow 雪', 'qty_168': '42', 'flag_168': 'ON', 'mode_168': 'H168'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_168': '42', 'flag_168': 'ON', 'mode_168': 'R168'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_168': None, 'qty_168': '42', 'flag_168': 'ON', 'mode_168': 'R168'})
    assert error.value.args == ('v_168',)
    with pytest.raises(KeyError) as error:
        decode({'v_168': 'snow 雪', 'flag_168': 'ON', 'mode_168': 'R168'})
    assert error.value.args == ('qty_168',)
    assert decode({'v_168': 'snow 雪', 'qty_168': None, 'flag_168': 'ON', 'mode_168': 'R168'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_168': 'snow 雪', 'qty_168': '42', 'mode_168': 'R168'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_168': 'snow 雪', 'qty_168': '42', 'flag_168': None, 'mode_168': 'R168'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_168': 'snow 雪', 'qty_168': '42', 'flag_168': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_168': 'snow 雪', 'qty_168': '42', 'flag_168': 'ON', 'mode_168': None})
    assert error.value.args == ('mode_168',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group27 import encode_r168 as encode, decode_r168 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_168': '', 'qty_168': '-100000000000000000003', 'flag_168': 'OFF', 'mode_168': 'D168'}
    assert value == before
    assert result is not value
    value = {'v_168': '', 'qty_168': '-100000000000000000003', 'flag_168': 'OFF', 'mode_168': 'D168'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_168': '', 'qty_168': '0', 'flag_168': 'OFF', 'mode_168': 'H168'}
    assert decode({'v_168': '', 'qty_168': '0', 'flag_168': 'OFF', 'mode_168': 'H168'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
