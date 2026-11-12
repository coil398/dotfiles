from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r049
def encode_r049(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_049'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_049'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_049'] = 'H49'
    elif record['state_2'] is None:
        out['flag_049'] = None
    else:
        out['flag_049'] = enum_encode(record['state_2'], {'ready': 'R49', 'held': 'H49', 'done': 'D49'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_049'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r049(record: dict) -> dict:
    out = {}
    if 'v_049' not in record:
        raise KeyError('v_049')
    elif record['v_049'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_049'])
    if 'qty_049' not in record:
        pass
    elif record['qty_049'] is None:
        raise ValueError('qty_049')
    else:
        out['active_1'] = boolean_decode(record['qty_049'], ['yes', 'no'])
    if 'flag_049' not in record:
        out['state_2'] = 'held'
    elif record['flag_049'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_049'], {'ready': 'R49', 'held': 'H49', 'done': 'D49'})
    if 'mode_049' not in record:
        raise KeyError('mode_049')
    elif record['mode_049'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_049'], 2)
    return out

# unit r050
def encode_r050(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_050'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_050'] = enum_encode(record['state_1'], {'ready': 'R50', 'held': 'H50', 'done': 'D50'})
    if 'amount_2' not in record:
        out['flag_050'] = 6
    elif record['amount_2'] is None:
        out['flag_050'] = None
    else:
        out['flag_050'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_050'] = strings_encode(record['labels_3'])
    return out

def decode_r050(record: dict) -> dict:
    out = {}
    if 'v_050' not in record:
        raise KeyError('v_050')
    elif record['v_050'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_050'], ['ON', 'OFF'])
    if 'qty_050' not in record:
        pass
    elif record['qty_050'] is None:
        raise ValueError('qty_050')
    else:
        out['state_1'] = enum_decode(record['qty_050'], {'ready': 'R50', 'held': 'H50', 'done': 'D50'})
    if 'flag_050' not in record:
        out['amount_2'] = 3
    elif record['flag_050'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_050'], 2)
    if 'mode_050' not in record:
        raise KeyError('mode_050')
    elif record['mode_050'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_050'])
    return out

# unit r051
def encode_r051(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_051'] = enum_encode(record['state_0'], {'ready': 'R51', 'held': 'H51', 'done': 'D51'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_051'] = None
    else:
        out['qty_051'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        out['flag_051'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_051'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_051'] = text_encode(record['title_3'])
    return out

def decode_r051(record: dict) -> dict:
    out = {}
    if 'v_051' not in record:
        raise KeyError('v_051')
    elif record['v_051'] is None:
        raise ValueError('v_051')
    else:
        out['state_0'] = enum_decode(record['v_051'], {'ready': 'R51', 'held': 'H51', 'done': 'D51'})
    if 'qty_051' not in record:
        pass
    elif record['qty_051'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_051'], 2)
    if 'flag_051' not in record:
        out['labels_2'] = ['default']
    elif record['flag_051'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_051'])
    if 'mode_051' not in record:
        raise KeyError('mode_051')
    elif record['mode_051'] is None:
        raise ValueError('mode_051')
    else:
        out['title_3'] = text_decode(record['mode_051'])
    return out

# unit r052
def encode_r052(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_052'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_052'] = None
    else:
        out['qty_052'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_052'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_052'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_052'] = decimal_encode(record['count_3'])
    return out

def decode_r052(record: dict) -> dict:
    out = {}
    if 'v_052' not in record:
        raise KeyError('v_052')
    elif record['v_052'] is None:
        raise ValueError('v_052')
    else:
        out['amount_0'] = scale_decode(record['v_052'], 2)
    if 'qty_052' not in record:
        pass
    elif record['qty_052'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_052'])
    if 'flag_052' not in record:
        out['title_2'] = 'unset'
    elif record['flag_052'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_052'])
    if 'mode_052' not in record:
        raise KeyError('mode_052')
    elif record['mode_052'] is None:
        raise ValueError('mode_052')
    else:
        out['count_3'] = decimal_decode(record['mode_052'])
    return out

# unit r053
def encode_r053(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_053'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_053'] = None
    else:
        out['qty_053'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_053'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_053'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_053'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r053(record: dict) -> dict:
    out = {}
    if 'v_053' not in record:
        raise KeyError('v_053')
    elif record['v_053'] is None:
        raise ValueError('v_053')
    else:
        out['labels_0'] = strings_decode(record['v_053'])
    if 'qty_053' not in record:
        pass
    elif record['qty_053'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_053'])
    if 'flag_053' not in record:
        out['count_2'] = -7
    elif record['flag_053'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_053'])
    if 'mode_053' not in record:
        raise KeyError('mode_053')
    elif record['mode_053'] is None:
        raise ValueError('mode_053')
    else:
        out['active_3'] = boolean_decode(record['mode_053'], ['yes', 'no'])
    return out

# unit r054
def encode_r054(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_054'] = None
    else:
        out['v_054'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_054'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_054'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_054'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_054'] = None
    else:
        out['mode_054'] = enum_encode(record['state_3'], {'ready': 'R54', 'held': 'H54', 'done': 'D54'})
    return out

def decode_r054(record: dict) -> dict:
    out = {}
    if 'v_054' not in record:
        pass
    elif record['v_054'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_054'])
    if 'qty_054' not in record:
        out['count_1'] = -7
    elif record['qty_054'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_054'])
    if 'flag_054' not in record:
        raise KeyError('flag_054')
    elif record['flag_054'] is None:
        raise ValueError('flag_054')
    else:
        out['active_2'] = boolean_decode(record['flag_054'], ['ON', 'OFF'])
    if 'mode_054' not in record:
        pass
    elif record['mode_054'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_054'], {'ready': 'R54', 'held': 'H54', 'done': 'D54'})
    return out

