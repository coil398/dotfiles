from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r031
def encode_r031(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_031'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_031'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_031'] = 'H31'
    elif record['state_2'] is None:
        out['flag_031'] = None
    else:
        out['flag_031'] = enum_encode(record['state_2'], {'ready': 'R31', 'held': 'H31', 'done': 'D31'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_031'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r031(record: dict) -> dict:
    out = {}
    if 'v_031' not in record:
        raise KeyError('v_031')
    elif record['v_031'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_031'])
    if 'qty_031' not in record:
        pass
    elif record['qty_031'] is None:
        raise ValueError('qty_031')
    else:
        out['active_1'] = boolean_decode(record['qty_031'], ['yes', 'no'])
    if 'flag_031' not in record:
        out['state_2'] = 'held'
    elif record['flag_031'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_031'], {'ready': 'R31', 'held': 'H31', 'done': 'D31'})
    if 'mode_031' not in record:
        raise KeyError('mode_031')
    elif record['mode_031'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_031'], 10)
    return out

# unit r032
def encode_r032(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_032'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_032'] = enum_encode(record['state_1'], {'ready': 'R32', 'held': 'H32', 'done': 'D32'})
    if 'amount_2' not in record:
        out['flag_032'] = 30
    elif record['amount_2'] is None:
        out['flag_032'] = None
    else:
        out['flag_032'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_032'] = strings_encode(record['labels_3'])
    return out

def decode_r032(record: dict) -> dict:
    out = {}
    if 'v_032' not in record:
        raise KeyError('v_032')
    elif record['v_032'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_032'], ['ON', 'OFF'])
    if 'qty_032' not in record:
        pass
    elif record['qty_032'] is None:
        raise ValueError('qty_032')
    else:
        out['state_1'] = enum_decode(record['qty_032'], {'ready': 'R32', 'held': 'H32', 'done': 'D32'})
    if 'flag_032' not in record:
        out['amount_2'] = 3
    elif record['flag_032'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_032'], 10)
    if 'mode_032' not in record:
        raise KeyError('mode_032')
    elif record['mode_032'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_032'])
    return out

# unit r033
def encode_r033(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_033'] = enum_encode(record['state_0'], {'ready': 'R33', 'held': 'H33', 'done': 'D33'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_033'] = None
    else:
        out['qty_033'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        out['flag_033'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_033'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_033'] = text_encode(record['title_3'])
    return out

def decode_r033(record: dict) -> dict:
    out = {}
    if 'v_033' not in record:
        raise KeyError('v_033')
    elif record['v_033'] is None:
        raise ValueError('v_033')
    else:
        out['state_0'] = enum_decode(record['v_033'], {'ready': 'R33', 'held': 'H33', 'done': 'D33'})
    if 'qty_033' not in record:
        pass
    elif record['qty_033'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_033'], 10)
    if 'flag_033' not in record:
        out['labels_2'] = ['default']
    elif record['flag_033'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_033'])
    if 'mode_033' not in record:
        raise KeyError('mode_033')
    elif record['mode_033'] is None:
        raise ValueError('mode_033')
    else:
        out['title_3'] = text_decode(record['mode_033'])
    return out

# unit r034
def encode_r034(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_034'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_034'] = None
    else:
        out['qty_034'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_034'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_034'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_034'] = decimal_encode(record['count_3'])
    return out

def decode_r034(record: dict) -> dict:
    out = {}
    if 'v_034' not in record:
        raise KeyError('v_034')
    elif record['v_034'] is None:
        raise ValueError('v_034')
    else:
        out['amount_0'] = scale_decode(record['v_034'], 10)
    if 'qty_034' not in record:
        pass
    elif record['qty_034'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_034'])
    if 'flag_034' not in record:
        out['title_2'] = 'unset'
    elif record['flag_034'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_034'])
    if 'mode_034' not in record:
        raise KeyError('mode_034')
    elif record['mode_034'] is None:
        raise ValueError('mode_034')
    else:
        out['count_3'] = decimal_decode(record['mode_034'])
    return out

# unit r035
def encode_r035(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_035'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_035'] = None
    else:
        out['qty_035'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_035'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_035'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_035'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r035(record: dict) -> dict:
    out = {}
    if 'v_035' not in record:
        raise KeyError('v_035')
    elif record['v_035'] is None:
        raise ValueError('v_035')
    else:
        out['labels_0'] = strings_decode(record['v_035'])
    if 'qty_035' not in record:
        pass
    elif record['qty_035'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_035'])
    if 'flag_035' not in record:
        out['count_2'] = -7
    elif record['flag_035'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_035'])
    if 'mode_035' not in record:
        raise KeyError('mode_035')
    elif record['mode_035'] is None:
        raise ValueError('mode_035')
    else:
        out['active_3'] = boolean_decode(record['mode_035'], ['yes', 'no'])
    return out

# unit r036
def encode_r036(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_036'] = None
    else:
        out['v_036'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_036'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_036'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_036'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_036'] = None
    else:
        out['mode_036'] = enum_encode(record['state_3'], {'ready': 'R36', 'held': 'H36', 'done': 'D36'})
    return out

def decode_r036(record: dict) -> dict:
    out = {}
    if 'v_036' not in record:
        pass
    elif record['v_036'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_036'])
    if 'qty_036' not in record:
        out['count_1'] = -7
    elif record['qty_036'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_036'])
    if 'flag_036' not in record:
        raise KeyError('flag_036')
    elif record['flag_036'] is None:
        raise ValueError('flag_036')
    else:
        out['active_2'] = boolean_decode(record['flag_036'], ['ON', 'OFF'])
    if 'mode_036' not in record:
        pass
    elif record['mode_036'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_036'], {'ready': 'R36', 'held': 'H36', 'done': 'D36'})
    return out

