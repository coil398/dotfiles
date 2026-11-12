"""Spec: docs/SPEC.md §§2–5 and docs/group12.md#r078."""

def test_encode_normal():
    from record_codecs.group12 import encode_r078 as encode, decode_r078 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_078': 'snow 雪', 'qty_078': '42', 'flag_078': 'ON', 'mode_078': 'R78'}

def test_decode_normal():
    from record_codecs.group12 import encode_r078 as encode, decode_r078 as decode
    assert decode({'v_078': 'snow 雪', 'qty_078': '42', 'flag_078': 'ON', 'mode_078': 'R78', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group12 import encode_r078 as encode, decode_r078 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_078': 'unset', 'qty_078': '42', 'flag_078': 'ON', 'mode_078': 'R78'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_078': 'snow 雪', 'qty_078': None, 'flag_078': 'ON', 'mode_078': 'R78'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_078': 'snow 雪', 'qty_078': '42', 'mode_078': 'R78'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_078': 'snow 雪', 'qty_078': '42', 'mode_078': 'R78'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_078': 'snow 雪', 'qty_078': '42', 'flag_078': 'ON', 'mode_078': 'H78'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_078': '42', 'flag_078': 'ON', 'mode_078': 'R78'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_078': None, 'qty_078': '42', 'flag_078': 'ON', 'mode_078': 'R78'})
    assert error.value.args == ('v_078',)
    with pytest.raises(KeyError) as error:
        decode({'v_078': 'snow 雪', 'flag_078': 'ON', 'mode_078': 'R78'})
    assert error.value.args == ('qty_078',)
    assert decode({'v_078': 'snow 雪', 'qty_078': None, 'flag_078': 'ON', 'mode_078': 'R78'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_078': 'snow 雪', 'qty_078': '42', 'mode_078': 'R78'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_078': 'snow 雪', 'qty_078': '42', 'flag_078': None, 'mode_078': 'R78'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_078': 'snow 雪', 'qty_078': '42', 'flag_078': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_078': 'snow 雪', 'qty_078': '42', 'flag_078': 'ON', 'mode_078': None})
    assert error.value.args == ('mode_078',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group12 import encode_r078 as encode, decode_r078 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_078': '', 'qty_078': '-100000000000000000003', 'flag_078': 'OFF', 'mode_078': 'D78'}
    assert value == before
    assert result is not value
    value = {'v_078': '', 'qty_078': '-100000000000000000003', 'flag_078': 'OFF', 'mode_078': 'D78'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_078': '', 'qty_078': '0', 'flag_078': 'OFF', 'mode_078': 'H78'}
    assert decode({'v_078': '', 'qty_078': '0', 'flag_078': 'OFF', 'mode_078': 'H78'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
