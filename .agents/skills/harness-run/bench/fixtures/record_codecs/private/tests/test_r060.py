"""Spec: docs/SPEC.md §§2–5 and docs/group09.md#r060."""

def test_encode_normal():
    from record_codecs.group09 import encode_r060 as encode, decode_r060 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_060': 'snow 雪', 'qty_060': '42', 'flag_060': 'ON', 'mode_060': 'R60'}

def test_decode_normal():
    from record_codecs.group09 import encode_r060 as encode, decode_r060 as decode
    assert decode({'v_060': 'snow 雪', 'qty_060': '42', 'flag_060': 'ON', 'mode_060': 'R60', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group09 import encode_r060 as encode, decode_r060 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_060': 'unset', 'qty_060': '42', 'flag_060': 'ON', 'mode_060': 'R60'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_060': 'snow 雪', 'qty_060': None, 'flag_060': 'ON', 'mode_060': 'R60'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_060': 'snow 雪', 'qty_060': '42', 'mode_060': 'R60'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_060': 'snow 雪', 'qty_060': '42', 'mode_060': 'R60'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_060': 'snow 雪', 'qty_060': '42', 'flag_060': 'ON', 'mode_060': 'H60'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_060': '42', 'flag_060': 'ON', 'mode_060': 'R60'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_060': None, 'qty_060': '42', 'flag_060': 'ON', 'mode_060': 'R60'})
    assert error.value.args == ('v_060',)
    with pytest.raises(KeyError) as error:
        decode({'v_060': 'snow 雪', 'flag_060': 'ON', 'mode_060': 'R60'})
    assert error.value.args == ('qty_060',)
    assert decode({'v_060': 'snow 雪', 'qty_060': None, 'flag_060': 'ON', 'mode_060': 'R60'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_060': 'snow 雪', 'qty_060': '42', 'mode_060': 'R60'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_060': 'snow 雪', 'qty_060': '42', 'flag_060': None, 'mode_060': 'R60'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_060': 'snow 雪', 'qty_060': '42', 'flag_060': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_060': 'snow 雪', 'qty_060': '42', 'flag_060': 'ON', 'mode_060': None})
    assert error.value.args == ('mode_060',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group09 import encode_r060 as encode, decode_r060 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_060': '', 'qty_060': '-100000000000000000003', 'flag_060': 'OFF', 'mode_060': 'D60'}
    assert value == before
    assert result is not value
    value = {'v_060': '', 'qty_060': '-100000000000000000003', 'flag_060': 'OFF', 'mode_060': 'D60'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_060': '', 'qty_060': '0', 'flag_060': 'OFF', 'mode_060': 'H60'}
    assert decode({'v_060': '', 'qty_060': '0', 'flag_060': 'OFF', 'mode_060': 'H60'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
