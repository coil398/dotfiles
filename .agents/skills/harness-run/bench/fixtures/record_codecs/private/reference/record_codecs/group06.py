from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r037
def encode_r037(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_037'] = None
    else:
        out['v_037'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_037'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_037'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_037'] = enum_encode(record['state_2'], {'ready': 'R37', 'held': 'H37', 'done': 'D37'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_037'] = None
    else:
        out['mode_037'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r037(record: dict) -> dict:
    out = {}
    if 'v_037' not in record:
        pass
    elif record['v_037'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_037'])
    if 'qty_037' not in record:
        out['active_1'] = False
    elif record['qty_037'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_037'], ['yes', 'no'])
    if 'flag_037' not in record:
        raise KeyError('flag_037')
    elif record['flag_037'] is None:
        raise ValueError('flag_037')
    else:
        out['state_2'] = enum_decode(record['flag_037'], {'ready': 'R37', 'held': 'H37', 'done': 'D37'})
    if 'mode_037' not in record:
        pass
    elif record['mode_037'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_037'], 2)
    return out

# unit r038
def encode_r038(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_038'] = None
    else:
        out['v_038'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_038'] = 'H38'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_038'] = enum_encode(record['state_1'], {'ready': 'R38', 'held': 'H38', 'done': 'D38'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_038'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_038'] = None
    else:
        out['mode_038'] = strings_encode(record['labels_3'])
    return out

def decode_r038(record: dict) -> dict:
    out = {}
    if 'v_038' not in record:
        pass
    elif record['v_038'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_038'], ['ON', 'OFF'])
    if 'qty_038' not in record:
        out['state_1'] = 'held'
    elif record['qty_038'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_038'], {'ready': 'R38', 'held': 'H38', 'done': 'D38'})
    if 'flag_038' not in record:
        raise KeyError('flag_038')
    elif record['flag_038'] is None:
        raise ValueError('flag_038')
    else:
        out['amount_2'] = scale_decode(record['flag_038'], 2)
    if 'mode_038' not in record:
        pass
    elif record['mode_038'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_038'])
    return out

# unit r039
def encode_r039(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_039'] = enum_encode(record['state_0'], {'ready': 'R39', 'held': 'H39', 'done': 'D39'})
    if 'amount_1' not in record:
        out['qty_039'] = 6
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_039'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_039'] = None
    else:
        out['flag_039'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_039'] = text_encode(record['title_3'])
    return out

def decode_r039(record: dict) -> dict:
    out = {}
    if 'v_039' not in record:
        pass
    elif record['v_039'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_039'], {'ready': 'R39', 'held': 'H39', 'done': 'D39'})
    if 'qty_039' not in record:
        out['amount_1'] = 3
    elif record['qty_039'] is None:
        raise ValueError('qty_039')
    else:
        out['amount_1'] = scale_decode(record['qty_039'], 2)
    if 'flag_039' not in record:
        raise KeyError('flag_039')
    elif record['flag_039'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_039'])
    if 'mode_039' not in record:
        pass
    elif record['mode_039'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_039'])
    return out

# unit r040
def encode_r040(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_040'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        out['qty_040'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_040'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_040'] = None
    else:
        out['flag_040'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_040'] = decimal_encode(record['count_3'])
    return out

def decode_r040(record: dict) -> dict:
    out = {}
    if 'v_040' not in record:
        pass
    elif record['v_040'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_040'], 2)
    if 'qty_040' not in record:
        out['labels_1'] = ['default']
    elif record['qty_040'] is None:
        raise ValueError('qty_040')
    else:
        out['labels_1'] = strings_decode(record['qty_040'])
    if 'flag_040' not in record:
        raise KeyError('flag_040')
    elif record['flag_040'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_040'])
    if 'mode_040' not in record:
        pass
    elif record['mode_040'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_040'])
    return out

# unit r041
def encode_r041(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_041'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_041'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_041'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_041'] = None
    else:
        out['flag_041'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_041'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r041(record: dict) -> dict:
    out = {}
    if 'v_041' not in record:
        pass
    elif record['v_041'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_041'])
    if 'qty_041' not in record:
        out['title_1'] = 'unset'
    elif record['qty_041'] is None:
        raise ValueError('qty_041')
    else:
        out['title_1'] = text_decode(record['qty_041'])
    if 'flag_041' not in record:
        raise KeyError('flag_041')
    elif record['flag_041'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_041'])
    if 'mode_041' not in record:
        pass
    elif record['mode_041'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_041'], ['yes', 'no'])
    return out

# unit r042
def encode_r042(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_042'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_042'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_042'] = None
    else:
        out['qty_042'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_042'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_042'] = 'H42'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_042'] = enum_encode(record['state_3'], {'ready': 'R42', 'held': 'H42', 'done': 'D42'})
    return out

def decode_r042(record: dict) -> dict:
    out = {}
    if 'v_042' not in record:
        out['title_0'] = 'unset'
    elif record['v_042'] is None:
        raise ValueError('v_042')
    else:
        out['title_0'] = text_decode(record['v_042'])
    if 'qty_042' not in record:
        raise KeyError('qty_042')
    elif record['qty_042'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_042'])
    if 'flag_042' not in record:
        pass
    elif record['flag_042'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_042'], ['ON', 'OFF'])
    if 'mode_042' not in record:
        out['state_3'] = 'held'
    elif record['mode_042'] is None:
        raise ValueError('mode_042')
    else:
        out['state_3'] = enum_decode(record['mode_042'], {'ready': 'R42', 'held': 'H42', 'done': 'D42'})
    return out

