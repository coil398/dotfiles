"""Spec: docs/SPEC.md §§2–5 and docs/group30.md#r186."""

def test_encode_normal():
    from record_codecs.group30 import encode_r186 as encode, decode_r186 as decode
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready', 'ignored': 'extra'}) == {'v_186': 'snow 雪', 'qty_186': '42', 'flag_186': 'ON', 'mode_186': 'R186'}

def test_decode_normal():
    from record_codecs.group30 import encode_r186 as encode, decode_r186 as decode
    assert decode({'v_186': 'snow 雪', 'qty_186': '42', 'flag_186': 'ON', 'mode_186': 'R186', 'ignored': 'extra'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}

def test_missing_null():
    import pytest
    from record_codecs.group30 import encode_r186 as encode, decode_r186 as decode
    assert encode({'count_1': 42, 'active_2': True, 'state_3': 'ready'}) == {'v_186': 'unset', 'qty_186': '42', 'flag_186': 'ON', 'mode_186': 'R186'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': None, 'count_1': 42, 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('title_0',)
    with pytest.raises(KeyError) as error:
        encode({'title_0': 'snow 雪', 'active_2': True, 'state_3': 'ready'})
    assert error.value.args == ('count_1',)
    assert encode({'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}) == {'v_186': 'snow 雪', 'qty_186': None, 'flag_186': 'ON', 'mode_186': 'R186'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}) == {'v_186': 'snow 雪', 'qty_186': '42', 'mode_186': 'R186'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': None, 'state_3': 'ready'}) == {'v_186': 'snow 雪', 'qty_186': '42', 'mode_186': 'R186'}
    assert encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True}) == {'v_186': 'snow 雪', 'qty_186': '42', 'flag_186': 'ON', 'mode_186': 'H186'}
    with pytest.raises(ValueError) as error:
        encode({'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': None})
    assert error.value.args == ('state_3',)
    assert decode({'qty_186': '42', 'flag_186': 'ON', 'mode_186': 'R186'}) == {'title_0': 'unset', 'count_1': 42, 'active_2': True, 'state_3': 'ready'}
    with pytest.raises(ValueError) as error:
        decode({'v_186': None, 'qty_186': '42', 'flag_186': 'ON', 'mode_186': 'R186'})
    assert error.value.args == ('v_186',)
    with pytest.raises(KeyError) as error:
        decode({'v_186': 'snow 雪', 'flag_186': 'ON', 'mode_186': 'R186'})
    assert error.value.args == ('qty_186',)
    assert decode({'v_186': 'snow 雪', 'qty_186': None, 'flag_186': 'ON', 'mode_186': 'R186'}) == {'title_0': 'snow 雪', 'count_1': None, 'active_2': True, 'state_3': 'ready'}
    assert decode({'v_186': 'snow 雪', 'qty_186': '42', 'mode_186': 'R186'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_186': 'snow 雪', 'qty_186': '42', 'flag_186': None, 'mode_186': 'R186'}) == {'title_0': 'snow 雪', 'count_1': 42, 'state_3': 'ready'}
    assert decode({'v_186': 'snow 雪', 'qty_186': '42', 'flag_186': 'ON'}) == {'title_0': 'snow 雪', 'count_1': 42, 'active_2': True, 'state_3': 'held'}
    with pytest.raises(ValueError) as error:
        decode({'v_186': 'snow 雪', 'qty_186': '42', 'flag_186': 'ON', 'mode_186': None})
    assert error.value.args == ('mode_186',)

def test_boundary_nonmutation():
    from copy import deepcopy
    from record_codecs.group30 import encode_r186 as encode, decode_r186 as decode
    value = {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    before = deepcopy(value)
    result = encode(value)
    assert result == {'v_186': '', 'qty_186': '-100000000000000000003', 'flag_186': 'OFF', 'mode_186': 'D186'}
    assert value == before
    assert result is not value
    value = {'v_186': '', 'qty_186': '-100000000000000000003', 'flag_186': 'OFF', 'mode_186': 'D186'}
    before = deepcopy(value)
    result = decode(value)
    assert result == {'title_0': '', 'count_1': -100000000000000000003, 'active_2': False, 'state_3': 'done'}
    assert value == before
    assert result is not value
    assert encode({'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}) == {'v_186': '', 'qty_186': '0', 'flag_186': 'OFF', 'mode_186': 'H186'}
    assert decode({'v_186': '', 'qty_186': '0', 'flag_186': 'OFF', 'mode_186': 'H186'}) == {'title_0': '', 'count_1': 0, 'active_2': False, 'state_3': 'held'}
