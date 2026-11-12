"""Spec: docs/SPEC.md §§2–5 and docs/group31.md#r192."""

def test_encode_normal():
    from record_codecs.group31 import encode_r192 as encode, decode_r192 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_192': 'snow 雪', 'qty_192': '42', 'flag_192': 'ON', 'mode_192': 'R192'}

def test_decode_normal():
    from record_codecs.group31 import encode_r192 as encode, decode_r192 as decode
    assert decode({'v_192': 'snow 雪', 'qty_192': '42', 'flag_192': 'ON', 'mode_192': 'R192', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group31 import encode_r192 as encode, decode_r192 as decode
    with pytest.raises(KeyError) as error:
        encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    assert encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'qty_192': '42', 'flag_192': 'ON', 'mode_192': 'R192'}
    assert encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}) == {'v_192': 'snow 雪', 'flag_192': 'ON', 'mode_192': 'R192'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_192': 'snow 雪', 'qty_192': '42', 'flag_192': 'OFF', 'mode_192': 'R192'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_192': 'snow 雪', 'qty_192': '42', 'flag_192': None, 'mode_192': 'R192'}
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True})
    assert error.value.args == ('state_3',)
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None}) == {'v_192': 'snow 雪', 'qty_192': '42', 'flag_192': 'ON'}
    with pytest.raises(KeyError) as error:
        decode({'qty_192': '42', 'flag_192': 'ON', 'mode_192': 'R192'})
    assert error.value.args == ('v_192',)
    assert decode({'v_192': None, 'qty_192': '42', 'flag_192': 'ON', 'mode_192': 'R192'}) == {'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_192': 'snow 雪', 'flag_192': 'ON', 'mode_192': 'R192'}) == {'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_192': 'snow 雪', 'qty_192': None, 'flag_192': 'ON', 'mode_192': 'R192'})
    assert error.value.args == ('qty_192',)
    assert decode({'v_192': 'snow 雪', 'qty_192': '42', 'mode_192': 'R192'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': False, 'state_3': 'ready'}
    assert decode({'v_192': 'snow 雪', 'qty_192': '42', 'flag_192': None, 'mode_192': 'R192'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}
    with pytest.raises(KeyError) as error:
        decode({'v_192': 'snow 雪', 'qty_192': '42', 'flag_192': 'ON'})
    assert error.value.args == ('mode_192',)
    assert decode({'v_192': 'snow 雪', 'qty_192': '42', 'flag_192': 'ON', 'mode_192': None}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group31 import encode_r192 as encode, decode_r192 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_192': '', 'qty_192': '-100000000000000000003', 'flag_192': 'OFF', 'mode_192': 'D192'}
    assert value == before
    assert result is not value
    value = {'v_192': '', 'qty_192': '-100000000000000000003', 'flag_192': 'OFF', 'mode_192': 'D192'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_192': '', 'qty_192': '0', 'flag_192': 'OFF', 'mode_192': 'H192'}
    assert decode({'v_192': '', 'qty_192': '0', 'flag_192': 'OFF', 'mode_192': 'H192'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
