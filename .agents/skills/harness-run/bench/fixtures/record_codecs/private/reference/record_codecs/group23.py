from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r139
def encode_r139(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_139'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_139'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_139'] = 'H139'
    elif record['state_2'] is None:
        out['flag_139'] = None
    else:
        out['flag_139'] = enum_encode(record['state_2'], {'ready': 'R139', 'held': 'H139', 'done': 'D139'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_139'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r139(record: dict) -> dict:
    out = {}
    if 'v_139' not in record:
        raise KeyError('v_139')
    elif record['v_139'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_139'])
    if 'qty_139' not in record:
        pass
    elif record['qty_139'] is None:
        raise ValueError('qty_139')
    else:
        out['active_1'] = boolean_decode(record['qty_139'], ['yes', 'no'])
    if 'flag_139' not in record:
        out['state_2'] = 'held'
    elif record['flag_139'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_139'], {'ready': 'R139', 'held': 'H139', 'done': 'D139'})
    if 'mode_139' not in record:
        raise KeyError('mode_139')
    elif record['mode_139'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_139'], 10)
    return out

# unit r140
def encode_r140(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_140'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_140'] = enum_encode(record['state_1'], {'ready': 'R140', 'held': 'H140', 'done': 'D140'})
    if 'amount_2' not in record:
        out['flag_140'] = 30
    elif record['amount_2'] is None:
        out['flag_140'] = None
    else:
        out['flag_140'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_140'] = strings_encode(record['labels_3'])
    return out

def decode_r140(record: dict) -> dict:
    out = {}
    if 'v_140' not in record:
        raise KeyError('v_140')
    elif record['v_140'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_140'], ['ON', 'OFF'])
    if 'qty_140' not in record:
        pass
    elif record['qty_140'] is None:
        raise ValueError('qty_140')
    else:
        out['state_1'] = enum_decode(record['qty_140'], {'ready': 'R140', 'held': 'H140', 'done': 'D140'})
    if 'flag_140' not in record:
        out['amount_2'] = 3
    elif record['flag_140'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_140'], 10)
    if 'mode_140' not in record:
        raise KeyError('mode_140')
    elif record['mode_140'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_140'])
    return out

# unit r141
def encode_r141(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_141'] = enum_encode(record['state_0'], {'ready': 'R141', 'held': 'H141', 'done': 'D141'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_141'] = None
    else:
        out['qty_141'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        out['flag_141'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_141'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_141'] = text_encode(record['title_3'])
    return out

def decode_r141(record: dict) -> dict:
    out = {}
    if 'v_141' not in record:
        raise KeyError('v_141')
    elif record['v_141'] is None:
        raise ValueError('v_141')
    else:
        out['state_0'] = enum_decode(record['v_141'], {'ready': 'R141', 'held': 'H141', 'done': 'D141'})
    if 'qty_141' not in record:
        pass
    elif record['qty_141'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_141'], 10)
    if 'flag_141' not in record:
        out['labels_2'] = ['default']
    elif record['flag_141'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_141'])
    if 'mode_141' not in record:
        raise KeyError('mode_141')
    elif record['mode_141'] is None:
        raise ValueError('mode_141')
    else:
        out['title_3'] = text_decode(record['mode_141'])
    return out

# unit r142
def encode_r142(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_142'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_142'] = None
    else:
        out['qty_142'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_142'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_142'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_142'] = decimal_encode(record['count_3'])
    return out

def decode_r142(record: dict) -> dict:
    out = {}
    if 'v_142' not in record:
        raise KeyError('v_142')
    elif record['v_142'] is None:
        raise ValueError('v_142')
    else:
        out['amount_0'] = scale_decode(record['v_142'], 10)
    if 'qty_142' not in record:
        pass
    elif record['qty_142'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_142'])
    if 'flag_142' not in record:
        out['title_2'] = 'unset'
    elif record['flag_142'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_142'])
    if 'mode_142' not in record:
        raise KeyError('mode_142')
    elif record['mode_142'] is None:
        raise ValueError('mode_142')
    else:
        out['count_3'] = decimal_decode(record['mode_142'])
    return out

# unit r143
def encode_r143(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_143'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_143'] = None
    else:
        out['qty_143'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_143'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_143'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_143'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r143(record: dict) -> dict:
    out = {}
    if 'v_143' not in record:
        raise KeyError('v_143')
    elif record['v_143'] is None:
        raise ValueError('v_143')
    else:
        out['labels_0'] = strings_decode(record['v_143'])
    if 'qty_143' not in record:
        pass
    elif record['qty_143'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_143'])
    if 'flag_143' not in record:
        out['count_2'] = -7
    elif record['flag_143'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_143'])
    if 'mode_143' not in record:
        raise KeyError('mode_143')
    elif record['mode_143'] is None:
        raise ValueError('mode_143')
    else:
        out['active_3'] = boolean_decode(record['mode_143'], ['yes', 'no'])
    return out

# unit r144
def encode_r144(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_144'] = None
    else:
        out['v_144'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_144'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_144'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_144'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_144'] = None
    else:
        out['mode_144'] = enum_encode(record['state_3'], {'ready': 'R144', 'held': 'H144', 'done': 'D144'})
    return out

def decode_r144(record: dict) -> dict:
    out = {}
    if 'v_144' not in record:
        pass
    elif record['v_144'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_144'])
    if 'qty_144' not in record:
        out['count_1'] = -7
    elif record['qty_144'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_144'])
    if 'flag_144' not in record:
        raise KeyError('flag_144')
    elif record['flag_144'] is None:
        raise ValueError('flag_144')
    else:
        out['active_2'] = boolean_decode(record['flag_144'], ['ON', 'OFF'])
    if 'mode_144' not in record:
        pass
    elif record['mode_144'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_144'], {'ready': 'R144', 'held': 'H144', 'done': 'D144'})
    return out

