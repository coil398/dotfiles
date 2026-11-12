from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r109
def encode_r109(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_109'] = None
    else:
        out['v_109'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_109'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_109'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_109'] = enum_encode(record['state_2'], {'ready': 'R109', 'held': 'H109', 'done': 'D109'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_109'] = None
    else:
        out['mode_109'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r109(record: dict) -> dict:
    out = {}
    if 'v_109' not in record:
        pass
    elif record['v_109'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_109'])
    if 'qty_109' not in record:
        out['active_1'] = False
    elif record['qty_109'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_109'], ['yes', 'no'])
    if 'flag_109' not in record:
        raise KeyError('flag_109')
    elif record['flag_109'] is None:
        raise ValueError('flag_109')
    else:
        out['state_2'] = enum_decode(record['flag_109'], {'ready': 'R109', 'held': 'H109', 'done': 'D109'})
    if 'mode_109' not in record:
        pass
    elif record['mode_109'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_109'], 2)
    return out

# unit r110
def encode_r110(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_110'] = None
    else:
        out['v_110'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_110'] = 'H110'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_110'] = enum_encode(record['state_1'], {'ready': 'R110', 'held': 'H110', 'done': 'D110'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_110'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_110'] = None
    else:
        out['mode_110'] = strings_encode(record['labels_3'])
    return out

def decode_r110(record: dict) -> dict:
    out = {}
    if 'v_110' not in record:
        pass
    elif record['v_110'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_110'], ['ON', 'OFF'])
    if 'qty_110' not in record:
        out['state_1'] = 'held'
    elif record['qty_110'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_110'], {'ready': 'R110', 'held': 'H110', 'done': 'D110'})
    if 'flag_110' not in record:
        raise KeyError('flag_110')
    elif record['flag_110'] is None:
        raise ValueError('flag_110')
    else:
        out['amount_2'] = scale_decode(record['flag_110'], 2)
    if 'mode_110' not in record:
        pass
    elif record['mode_110'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_110'])
    return out

# unit r111
def encode_r111(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_111'] = enum_encode(record['state_0'], {'ready': 'R111', 'held': 'H111', 'done': 'D111'})
    if 'amount_1' not in record:
        out['qty_111'] = 6
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_111'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_111'] = None
    else:
        out['flag_111'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_111'] = text_encode(record['title_3'])
    return out

def decode_r111(record: dict) -> dict:
    out = {}
    if 'v_111' not in record:
        pass
    elif record['v_111'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_111'], {'ready': 'R111', 'held': 'H111', 'done': 'D111'})
    if 'qty_111' not in record:
        out['amount_1'] = 3
    elif record['qty_111'] is None:
        raise ValueError('qty_111')
    else:
        out['amount_1'] = scale_decode(record['qty_111'], 2)
    if 'flag_111' not in record:
        raise KeyError('flag_111')
    elif record['flag_111'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_111'])
    if 'mode_111' not in record:
        pass
    elif record['mode_111'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_111'])
    return out

# unit r112
def encode_r112(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_112'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        out['qty_112'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_112'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_112'] = None
    else:
        out['flag_112'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_112'] = decimal_encode(record['count_3'])
    return out

def decode_r112(record: dict) -> dict:
    out = {}
    if 'v_112' not in record:
        pass
    elif record['v_112'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_112'], 2)
    if 'qty_112' not in record:
        out['labels_1'] = ['default']
    elif record['qty_112'] is None:
        raise ValueError('qty_112')
    else:
        out['labels_1'] = strings_decode(record['qty_112'])
    if 'flag_112' not in record:
        raise KeyError('flag_112')
    elif record['flag_112'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_112'])
    if 'mode_112' not in record:
        pass
    elif record['mode_112'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_112'])
    return out

# unit r113
def encode_r113(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_113'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_113'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_113'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_113'] = None
    else:
        out['flag_113'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_113'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r113(record: dict) -> dict:
    out = {}
    if 'v_113' not in record:
        pass
    elif record['v_113'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_113'])
    if 'qty_113' not in record:
        out['title_1'] = 'unset'
    elif record['qty_113'] is None:
        raise ValueError('qty_113')
    else:
        out['title_1'] = text_decode(record['qty_113'])
    if 'flag_113' not in record:
        raise KeyError('flag_113')
    elif record['flag_113'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_113'])
    if 'mode_113' not in record:
        pass
    elif record['mode_113'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_113'], ['yes', 'no'])
    return out

# unit r114
def encode_r114(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_114'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_114'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_114'] = None
    else:
        out['qty_114'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_114'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_114'] = 'H114'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_114'] = enum_encode(record['state_3'], {'ready': 'R114', 'held': 'H114', 'done': 'D114'})
    return out

def decode_r114(record: dict) -> dict:
    out = {}
    if 'v_114' not in record:
        out['title_0'] = 'unset'
    elif record['v_114'] is None:
        raise ValueError('v_114')
    else:
        out['title_0'] = text_decode(record['v_114'])
    if 'qty_114' not in record:
        raise KeyError('qty_114')
    elif record['qty_114'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_114'])
    if 'flag_114' not in record:
        pass
    elif record['flag_114'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_114'], ['ON', 'OFF'])
    if 'mode_114' not in record:
        out['state_3'] = 'held'
    elif record['mode_114'] is None:
        raise ValueError('mode_114')
    else:
        out['state_3'] = enum_decode(record['mode_114'], {'ready': 'R114', 'held': 'H114', 'done': 'D114'})
    return out

