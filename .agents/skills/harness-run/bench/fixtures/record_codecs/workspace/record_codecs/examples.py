from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit example_a
def encode_example_a(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_193'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_193'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_193'] = 'H193'
    elif record['state_2'] is None:
        out['flag_193'] = None
    else:
        out['flag_193'] = enum_encode(record['state_2'], {'ready': 'R193', 'held': 'H193', 'done': 'D193'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_193'] = scale_encode(record['amount_3'], 2)
    return out

def decode_example_a(record: dict) -> dict:
    out = {}
    if 'v_193' not in record:
        raise KeyError('v_193')
    elif record['v_193'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_193'])
    if 'qty_193' not in record:
        pass
    elif record['qty_193'] is None:
        raise ValueError('qty_193')
    else:
        out['active_1'] = boolean_decode(record['qty_193'], ['yes', 'no'])
    if 'flag_193' not in record:
        out['state_2'] = 'held'
    elif record['flag_193'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_193'], {'ready': 'R193', 'held': 'H193', 'done': 'D193'})
    if 'mode_193' not in record:
        raise KeyError('mode_193')
    elif record['mode_193'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_193'], 2)
    return out

# unit example_b
def encode_example_b(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_194'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_194'] = enum_encode(record['state_1'], {'ready': 'R194', 'held': 'H194', 'done': 'D194'})
    if 'amount_2' not in record:
        out['flag_194'] = 6
    elif record['amount_2'] is None:
        out['flag_194'] = None
    else:
        out['flag_194'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_194'] = strings_encode(record['labels_3'])
    return out

def decode_example_b(record: dict) -> dict:
    out = {}
    if 'v_194' not in record:
        raise KeyError('v_194')
    elif record['v_194'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_194'], ['ON', 'OFF'])
    if 'qty_194' not in record:
        pass
    elif record['qty_194'] is None:
        raise ValueError('qty_194')
    else:
        out['state_1'] = enum_decode(record['qty_194'], {'ready': 'R194', 'held': 'H194', 'done': 'D194'})
    if 'flag_194' not in record:
        out['amount_2'] = 3
    elif record['flag_194'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_194'], 2)
    if 'mode_194' not in record:
        raise KeyError('mode_194')
    elif record['mode_194'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_194'])
    return out

