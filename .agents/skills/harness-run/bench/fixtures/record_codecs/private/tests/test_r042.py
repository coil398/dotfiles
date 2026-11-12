"""Spec: docs/SPEC.md §§2–5 and docs/group06.md#r042."""

def test_encode_normal():
    from record_codecs.group06 import encode_r042 as encode, decode_r042 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_042': 'snow 雪', 'qty_042': '42', 'flag_042': 'ON', 'mode_042': 'R42'}

def test_decode_normal():
    from record_codecs.group06 import encode_r042 as encode, decode_r042 as decode
    assert decode({'v_042': 'snow 雪', 'qty_042': '42', 'flag_042': 'ON', 'mode_042': 'R42', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group06 import encode_r042 as encode, decode_r042 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_042': 'unset', 'qty_042': '42', 'flag_042': 'ON', 'mode_042': 'R42'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_042': 'snow 雪', 'qty_042': None, 'flag_042': 'ON', 'mode_042': 'R42'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_042': 'snow 雪', 'qty_042': '42', 'mode_042': 'R42'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_042': 'snow 雪', 'qty_042': '42', 'mode_042': 'R42'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_042': 'snow 雪', 'qty_042': '42', 'flag_042': 'ON', 'mode_042': 'H42'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_042': '42', 'flag_042': 'ON', 'mode_042': 'R42'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_042': None, 'qty_042': '42', 'flag_042': 'ON', 'mode_042': 'R42'})
    assert error.value.args == ('v_042',)
    with pytest.raises(KeyError) as error:
        decode({'v_042': 'snow 雪', 'flag_042': 'ON', 'mode_042': 'R42'})
    assert error.value.args == ('qty_042',)
    assert decode({'v_042': 'snow 雪', 'qty_042': None, 'flag_042': 'ON', 'mode_042': 'R42'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_042': 'snow 雪', 'qty_042': '42', 'mode_042': 'R42'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_042': 'snow 雪', 'qty_042': '42', 'flag_042': None, 'mode_042': 'R42'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_042': 'snow 雪', 'qty_042': '42', 'flag_042': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_042': 'snow 雪', 'qty_042': '42', 'flag_042': 'ON', 'mode_042': None})
    assert error.value.args == ('mode_042',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group06 import encode_r042 as encode, decode_r042 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_042': '', 'qty_042': '-100000000000000000003', 'flag_042': 'OFF', 'mode_042': 'D42'}
    assert value == before
    assert result is not value
    value = {'v_042': '', 'qty_042': '-100000000000000000003', 'flag_042': 'OFF', 'mode_042': 'D42'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_042': '', 'qty_042': '0', 'flag_042': 'OFF', 'mode_042': 'H42'}
    assert decode({'v_042': '', 'qty_042': '0', 'flag_042': 'OFF', 'mode_042': 'H42'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
