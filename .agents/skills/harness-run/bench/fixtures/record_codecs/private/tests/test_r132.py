"""Spec: docs/SPEC.md §§2–5 and docs/group21.md#r132."""

def test_encode_normal():
    from record_codecs.group21 import encode_r132 as encode, decode_r132 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_132': 'snow 雪', 'qty_132': '42', 'flag_132': 'ON', 'mode_132': 'R132'}

def test_decode_normal():
    from record_codecs.group21 import encode_r132 as encode, decode_r132 as decode
    assert decode({'v_132': 'snow 雪', 'qty_132': '42', 'flag_132': 'ON', 'mode_132': 'R132', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group21 import encode_r132 as encode, decode_r132 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_132': 'unset', 'qty_132': '42', 'flag_132': 'ON', 'mode_132': 'R132'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_132': 'snow 雪', 'qty_132': None, 'flag_132': 'ON', 'mode_132': 'R132'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_132': 'snow 雪', 'qty_132': '42', 'mode_132': 'R132'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_132': 'snow 雪', 'qty_132': '42', 'mode_132': 'R132'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_132': 'snow 雪', 'qty_132': '42', 'flag_132': 'ON', 'mode_132': 'H132'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_132': '42', 'flag_132': 'ON', 'mode_132': 'R132'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_132': None, 'qty_132': '42', 'flag_132': 'ON', 'mode_132': 'R132'})
    assert error.value.args == ('v_132',)
    with pytest.raises(KeyError) as error:
        decode({'v_132': 'snow 雪', 'flag_132': 'ON', 'mode_132': 'R132'})
    assert error.value.args == ('qty_132',)
    assert decode({'v_132': 'snow 雪', 'qty_132': None, 'flag_132': 'ON', 'mode_132': 'R132'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_132': 'snow 雪', 'qty_132': '42', 'mode_132': 'R132'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_132': 'snow 雪', 'qty_132': '42', 'flag_132': None, 'mode_132': 'R132'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_132': 'snow 雪', 'qty_132': '42', 'flag_132': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_132': 'snow 雪', 'qty_132': '42', 'flag_132': 'ON', 'mode_132': None})
    assert error.value.args == ('mode_132',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group21 import encode_r132 as encode, decode_r132 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_132': '', 'qty_132': '-100000000000000000003', 'flag_132': 'OFF', 'mode_132': 'D132'}
    assert value == before
    assert result is not value
    value = {'v_132': '', 'qty_132': '-100000000000000000003', 'flag_132': 'OFF', 'mode_132': 'D132'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_132': '', 'qty_132': '0', 'flag_132': 'OFF', 'mode_132': 'H132'}
    assert decode({'v_132': '', 'qty_132': '0', 'flag_132': 'OFF', 'mode_132': 'H132'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
