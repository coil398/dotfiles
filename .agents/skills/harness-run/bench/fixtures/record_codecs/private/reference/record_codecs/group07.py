from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r043
def encode_r043(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_043'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_043'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_043'] = None
    else:
        out['qty_043'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_043'] = enum_encode(record['state_2'], {'ready': 'R43', 'held': 'H43', 'done': 'D43'})
    if 'amount_3' not in record:
        out['mode_043'] = 30
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_043'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r043(record: dict) -> dict:
    out = {}
    if 'v_043' not in record:
        out['count_0'] = -7
    elif record['v_043'] is None:
        raise ValueError('v_043')
    else:
        out['count_0'] = decimal_decode(record['v_043'])
    if 'qty_043' not in record:
        raise KeyError('qty_043')
    elif record['qty_043'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_043'], ['yes', 'no'])
    if 'flag_043' not in record:
        pass
    elif record['flag_043'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_043'], {'ready': 'R43', 'held': 'H43', 'done': 'D43'})
    if 'mode_043' not in record:
        out['amount_3'] = 3
    elif record['mode_043'] is None:
        raise ValueError('mode_043')
    else:
        out['amount_3'] = scale_decode(record['mode_043'], 10)
    return out

# unit r044
def encode_r044(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_044'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_044'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_044'] = None
    else:
        out['qty_044'] = enum_encode(record['state_1'], {'ready': 'R44', 'held': 'H44', 'done': 'D44'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_044'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        out['mode_044'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_044'] = strings_encode(record['labels_3'])
    return out

def decode_r044(record: dict) -> dict:
    out = {}
    if 'v_044' not in record:
        out['active_0'] = False
    elif record['v_044'] is None:
        raise ValueError('v_044')
    else:
        out['active_0'] = boolean_decode(record['v_044'], ['ON', 'OFF'])
    if 'qty_044' not in record:
        raise KeyError('qty_044')
    elif record['qty_044'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_044'], {'ready': 'R44', 'held': 'H44', 'done': 'D44'})
    if 'flag_044' not in record:
        pass
    elif record['flag_044'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_044'], 10)
    if 'mode_044' not in record:
        out['labels_3'] = ['default']
    elif record['mode_044'] is None:
        raise ValueError('mode_044')
    else:
        out['labels_3'] = strings_decode(record['mode_044'])
    return out

# unit r045
def encode_r045(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_045'] = 'H45'
    elif record['state_0'] is None:
        out['v_045'] = None
    else:
        out['v_045'] = enum_encode(record['state_0'], {'ready': 'R45', 'held': 'H45', 'done': 'D45'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_045'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_045'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_045'] = 'unset'
    elif record['title_3'] is None:
        out['mode_045'] = None
    else:
        out['mode_045'] = text_encode(record['title_3'])
    return out

def decode_r045(record: dict) -> dict:
    out = {}
    if 'v_045' not in record:
        out['state_0'] = 'held'
    elif record['v_045'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_045'], {'ready': 'R45', 'held': 'H45', 'done': 'D45'})
    if 'qty_045' not in record:
        raise KeyError('qty_045')
    elif record['qty_045'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_045'], 10)
    if 'flag_045' not in record:
        pass
    elif record['flag_045'] is None:
        raise ValueError('flag_045')
    else:
        out['labels_2'] = strings_decode(record['flag_045'])
    if 'mode_045' not in record:
        out['title_3'] = 'unset'
    elif record['mode_045'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_045'])
    return out

# unit r046
def encode_r046(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_046'] = 30
    elif record['amount_0'] is None:
        out['v_046'] = None
    else:
        out['v_046'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_046'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_046'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_046'] = '-7'
    elif record['count_3'] is None:
        out['mode_046'] = None
    else:
        out['mode_046'] = decimal_encode(record['count_3'])
    return out

def decode_r046(record: dict) -> dict:
    out = {}
    if 'v_046' not in record:
        out['amount_0'] = 3
    elif record['v_046'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_046'], 10)
    if 'qty_046' not in record:
        raise KeyError('qty_046')
    elif record['qty_046'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_046'])
    if 'flag_046' not in record:
        pass
    elif record['flag_046'] is None:
        raise ValueError('flag_046')
    else:
        out['title_2'] = text_decode(record['flag_046'])
    if 'mode_046' not in record:
        out['count_3'] = -7
    elif record['mode_046'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_046'])
    return out

# unit r047
def encode_r047(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_047'] = ['default']
    elif record['labels_0'] is None:
        out['v_047'] = None
    else:
        out['v_047'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_047'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_047'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_047'] = 'no'
    elif record['active_3'] is None:
        out['mode_047'] = None
    else:
        out['mode_047'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r047(record: dict) -> dict:
    out = {}
    if 'v_047' not in record:
        out['labels_0'] = ['default']
    elif record['v_047'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_047'])
    if 'qty_047' not in record:
        raise KeyError('qty_047')
    elif record['qty_047'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_047'])
    if 'flag_047' not in record:
        pass
    elif record['flag_047'] is None:
        raise ValueError('flag_047')
    else:
        out['count_2'] = decimal_decode(record['flag_047'])
    if 'mode_047' not in record:
        out['active_3'] = False
    elif record['mode_047'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_047'], ['yes', 'no'])
    return out

# unit r048
def encode_r048(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_048'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_048'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_048'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_048'] = None
    else:
        out['flag_048'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_048'] = enum_encode(record['state_3'], {'ready': 'R48', 'held': 'H48', 'done': 'D48'})
    return out

def decode_r048(record: dict) -> dict:
    out = {}
    if 'v_048' not in record:
        raise KeyError('v_048')
    elif record['v_048'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_048'])
    if 'qty_048' not in record:
        pass
    elif record['qty_048'] is None:
        raise ValueError('qty_048')
    else:
        out['count_1'] = decimal_decode(record['qty_048'])
    if 'flag_048' not in record:
        out['active_2'] = False
    elif record['flag_048'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_048'], ['ON', 'OFF'])
    if 'mode_048' not in record:
        raise KeyError('mode_048')
    elif record['mode_048'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_048'], {'ready': 'R48', 'held': 'H48', 'done': 'D48'})
    return out

