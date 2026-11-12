"""Spec: docs/SPEC.md §§2–5 and docs/group15.md#r096."""

def test_encode_normal():
    from record_codecs.group15 import encode_r096 as encode, decode_r096 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_096': 'snow 雪', 'qty_096': '42', 'flag_096': 'ON', 'mode_096': 'R96'}

def test_decode_normal():
    from record_codecs.group15 import encode_r096 as encode, decode_r096 as decode
    assert decode({'v_096': 'snow 雪', 'qty_096': '42', 'flag_096': 'ON', 'mode_096': 'R96', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group15 import encode_r096 as encode, decode_r096 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_096': 'unset', 'qty_096': '42', 'flag_096': 'ON', 'mode_096': 'R96'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_096': 'snow 雪', 'qty_096': None, 'flag_096': 'ON', 'mode_096': 'R96'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_096': 'snow 雪', 'qty_096': '42', 'mode_096': 'R96'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_096': 'snow 雪', 'qty_096': '42', 'mode_096': 'R96'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_096': 'snow 雪', 'qty_096': '42', 'flag_096': 'ON', 'mode_096': 'H96'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_096': '42', 'flag_096': 'ON', 'mode_096': 'R96'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_096': None, 'qty_096': '42', 'flag_096': 'ON', 'mode_096': 'R96'})
    assert error.value.args == ('v_096',)
    with pytest.raises(KeyError) as error:
        decode({'v_096': 'snow 雪', 'flag_096': 'ON', 'mode_096': 'R96'})
    assert error.value.args == ('qty_096',)
    assert decode({'v_096': 'snow 雪', 'qty_096': None, 'flag_096': 'ON', 'mode_096': 'R96'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_096': 'snow 雪', 'qty_096': '42', 'mode_096': 'R96'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_096': 'snow 雪', 'qty_096': '42', 'flag_096': None, 'mode_096': 'R96'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_096': 'snow 雪', 'qty_096': '42', 'flag_096': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_096': 'snow 雪', 'qty_096': '42', 'flag_096': 'ON', 'mode_096': None})
    assert error.value.args == ('mode_096',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group15 import encode_r096 as encode, decode_r096 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_096': '', 'qty_096': '-100000000000000000003', 'flag_096': 'OFF', 'mode_096': 'D96'}
    assert value == before
    assert result is not value
    value = {'v_096': '', 'qty_096': '-100000000000000000003', 'flag_096': 'OFF', 'mode_096': 'D96'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_096': '', 'qty_096': '0', 'flag_096': 'OFF', 'mode_096': 'H96'}
    assert decode({'v_096': '', 'qty_096': '0', 'flag_096': 'OFF', 'mode_096': 'H96'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
