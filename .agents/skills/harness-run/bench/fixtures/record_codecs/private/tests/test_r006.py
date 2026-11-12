"""Spec: docs/SPEC.md §§2–5 and docs/group00.md#r006."""

def test_encode_normal():
    from record_codecs.group00 import encode_r006 as encode, decode_r006 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_006': 'snow 雪', 'qty_006': '42', 'flag_006': 'ON', 'mode_006': 'R6'}

def test_decode_normal():
    from record_codecs.group00 import encode_r006 as encode, decode_r006 as decode
    assert decode({'v_006': 'snow 雪', 'qty_006': '42', 'flag_006': 'ON', 'mode_006': 'R6', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group00 import encode_r006 as encode, decode_r006 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_006': 'unset', 'qty_006': '42', 'flag_006': 'ON', 'mode_006': 'R6'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_006': 'snow 雪', 'qty_006': None, 'flag_006': 'ON', 'mode_006': 'R6'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_006': 'snow 雪', 'qty_006': '42', 'mode_006': 'R6'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_006': 'snow 雪', 'qty_006': '42', 'mode_006': 'R6'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_006': 'snow 雪', 'qty_006': '42', 'flag_006': 'ON', 'mode_006': 'H6'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_006': '42', 'flag_006': 'ON', 'mode_006': 'R6'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_006': None, 'qty_006': '42', 'flag_006': 'ON', 'mode_006': 'R6'})
    assert error.value.args == ('v_006',)
    with pytest.raises(KeyError) as error:
        decode({'v_006': 'snow 雪', 'flag_006': 'ON', 'mode_006': 'R6'})
    assert error.value.args == ('qty_006',)
    assert decode({'v_006': 'snow 雪', 'qty_006': None, 'flag_006': 'ON', 'mode_006': 'R6'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_006': 'snow 雪', 'qty_006': '42', 'mode_006': 'R6'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_006': 'snow 雪', 'qty_006': '42', 'flag_006': None, 'mode_006': 'R6'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_006': 'snow 雪', 'qty_006': '42', 'flag_006': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_006': 'snow 雪', 'qty_006': '42', 'flag_006': 'ON', 'mode_006': None})
    assert error.value.args == ('mode_006',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group00 import encode_r006 as encode, decode_r006 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_006': '', 'qty_006': '-100000000000000000003', 'flag_006': 'OFF', 'mode_006': 'D6'}
    assert value == before
    assert result is not value
    value = {'v_006': '', 'qty_006': '-100000000000000000003', 'flag_006': 'OFF', 'mode_006': 'D6'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_006': '', 'qty_006': '0', 'flag_006': 'OFF', 'mode_006': 'H6'}
    assert decode({'v_006': '', 'qty_006': '0', 'flag_006': 'OFF', 'mode_006': 'H6'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
