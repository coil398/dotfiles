from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r061
def encode_r061(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_061'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_061'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_061'] = None
    else:
        out['qty_061'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_061'] = enum_encode(record['state_2'], {'ready': 'R61', 'held': 'H61', 'done': 'D61'})
    if 'amount_3' not in record:
        out['mode_061'] = 6
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_061'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r061(record: dict) -> dict:
    out = {}
    if 'v_061' not in record:
        out['count_0'] = -7
    elif record['v_061'] is None:
        raise ValueError('v_061')
    else:
        out['count_0'] = decimal_decode(record['v_061'])
    if 'qty_061' not in record:
        raise KeyError('qty_061')
    elif record['qty_061'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_061'], ['yes', 'no'])
    if 'flag_061' not in record:
        pass
    elif record['flag_061'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_061'], {'ready': 'R61', 'held': 'H61', 'done': 'D61'})
    if 'mode_061' not in record:
        out['amount_3'] = 3
    elif record['mode_061'] is None:
        raise ValueError('mode_061')
    else:
        out['amount_3'] = scale_decode(record['mode_061'], 2)
    return out

# unit r062
def encode_r062(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_062'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_062'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_062'] = None
    else:
        out['qty_062'] = enum_encode(record['state_1'], {'ready': 'R62', 'held': 'H62', 'done': 'D62'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_062'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        out['mode_062'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_062'] = strings_encode(record['labels_3'])
    return out

def decode_r062(record: dict) -> dict:
    out = {}
    if 'v_062' not in record:
        out['active_0'] = False
    elif record['v_062'] is None:
        raise ValueError('v_062')
    else:
        out['active_0'] = boolean_decode(record['v_062'], ['ON', 'OFF'])
    if 'qty_062' not in record:
        raise KeyError('qty_062')
    elif record['qty_062'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_062'], {'ready': 'R62', 'held': 'H62', 'done': 'D62'})
    if 'flag_062' not in record:
        pass
    elif record['flag_062'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_062'], 2)
    if 'mode_062' not in record:
        out['labels_3'] = ['default']
    elif record['mode_062'] is None:
        raise ValueError('mode_062')
    else:
        out['labels_3'] = strings_decode(record['mode_062'])
    return out

# unit r063
def encode_r063(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_063'] = 'H63'
    elif record['state_0'] is None:
        out['v_063'] = None
    else:
        out['v_063'] = enum_encode(record['state_0'], {'ready': 'R63', 'held': 'H63', 'done': 'D63'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_063'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_063'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_063'] = 'unset'
    elif record['title_3'] is None:
        out['mode_063'] = None
    else:
        out['mode_063'] = text_encode(record['title_3'])
    return out

def decode_r063(record: dict) -> dict:
    out = {}
    if 'v_063' not in record:
        out['state_0'] = 'held'
    elif record['v_063'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_063'], {'ready': 'R63', 'held': 'H63', 'done': 'D63'})
    if 'qty_063' not in record:
        raise KeyError('qty_063')
    elif record['qty_063'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_063'], 2)
    if 'flag_063' not in record:
        pass
    elif record['flag_063'] is None:
        raise ValueError('flag_063')
    else:
        out['labels_2'] = strings_decode(record['flag_063'])
    if 'mode_063' not in record:
        out['title_3'] = 'unset'
    elif record['mode_063'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_063'])
    return out

# unit r064
def encode_r064(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_064'] = 6
    elif record['amount_0'] is None:
        out['v_064'] = None
    else:
        out['v_064'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_064'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_064'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_064'] = '-7'
    elif record['count_3'] is None:
        out['mode_064'] = None
    else:
        out['mode_064'] = decimal_encode(record['count_3'])
    return out

def decode_r064(record: dict) -> dict:
    out = {}
    if 'v_064' not in record:
        out['amount_0'] = 3
    elif record['v_064'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_064'], 2)
    if 'qty_064' not in record:
        raise KeyError('qty_064')
    elif record['qty_064'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_064'])
    if 'flag_064' not in record:
        pass
    elif record['flag_064'] is None:
        raise ValueError('flag_064')
    else:
        out['title_2'] = text_decode(record['flag_064'])
    if 'mode_064' not in record:
        out['count_3'] = -7
    elif record['mode_064'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_064'])
    return out

# unit r065
def encode_r065(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_065'] = ['default']
    elif record['labels_0'] is None:
        out['v_065'] = None
    else:
        out['v_065'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_065'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_065'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_065'] = 'no'
    elif record['active_3'] is None:
        out['mode_065'] = None
    else:
        out['mode_065'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r065(record: dict) -> dict:
    out = {}
    if 'v_065' not in record:
        out['labels_0'] = ['default']
    elif record['v_065'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_065'])
    if 'qty_065' not in record:
        raise KeyError('qty_065')
    elif record['qty_065'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_065'])
    if 'flag_065' not in record:
        pass
    elif record['flag_065'] is None:
        raise ValueError('flag_065')
    else:
        out['count_2'] = decimal_decode(record['flag_065'])
    if 'mode_065' not in record:
        out['active_3'] = False
    elif record['mode_065'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_065'], ['yes', 'no'])
    return out

# unit r066
def encode_r066(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_066'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_066'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_066'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_066'] = None
    else:
        out['flag_066'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_066'] = enum_encode(record['state_3'], {'ready': 'R66', 'held': 'H66', 'done': 'D66'})
    return out

def decode_r066(record: dict) -> dict:
    out = {}
    if 'v_066' not in record:
        raise KeyError('v_066')
    elif record['v_066'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_066'])
    if 'qty_066' not in record:
        pass
    elif record['qty_066'] is None:
        raise ValueError('qty_066')
    else:
        out['count_1'] = decimal_decode(record['qty_066'])
    if 'flag_066' not in record:
        out['active_2'] = False
    elif record['flag_066'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_066'], ['ON', 'OFF'])
    if 'mode_066' not in record:
        raise KeyError('mode_066')
    elif record['mode_066'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_066'], {'ready': 'R66', 'held': 'H66', 'done': 'D66'})
    return out

