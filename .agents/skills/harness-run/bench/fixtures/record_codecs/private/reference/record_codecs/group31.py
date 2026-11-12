from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r187
def encode_r187(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_187'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_187'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_187'] = None
    else:
        out['qty_187'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_187'] = enum_encode(record['state_2'], {'ready': 'R187', 'held': 'H187', 'done': 'D187'})
    if 'amount_3' not in record:
        out['mode_187'] = 30
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_187'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r187(record: dict) -> dict:
    out = {}
    if 'v_187' not in record:
        out['count_0'] = -7
    elif record['v_187'] is None:
        raise ValueError('v_187')
    else:
        out['count_0'] = decimal_decode(record['v_187'])
    if 'qty_187' not in record:
        raise KeyError('qty_187')
    elif record['qty_187'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_187'], ['yes', 'no'])
    if 'flag_187' not in record:
        pass
    elif record['flag_187'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_187'], {'ready': 'R187', 'held': 'H187', 'done': 'D187'})
    if 'mode_187' not in record:
        out['amount_3'] = 3
    elif record['mode_187'] is None:
        raise ValueError('mode_187')
    else:
        out['amount_3'] = scale_decode(record['mode_187'], 10)
    return out

# unit r188
def encode_r188(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_188'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_188'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_188'] = None
    else:
        out['qty_188'] = enum_encode(record['state_1'], {'ready': 'R188', 'held': 'H188', 'done': 'D188'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_188'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        out['mode_188'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_188'] = strings_encode(record['labels_3'])
    return out

def decode_r188(record: dict) -> dict:
    out = {}
    if 'v_188' not in record:
        out['active_0'] = False
    elif record['v_188'] is None:
        raise ValueError('v_188')
    else:
        out['active_0'] = boolean_decode(record['v_188'], ['ON', 'OFF'])
    if 'qty_188' not in record:
        raise KeyError('qty_188')
    elif record['qty_188'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_188'], {'ready': 'R188', 'held': 'H188', 'done': 'D188'})
    if 'flag_188' not in record:
        pass
    elif record['flag_188'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_188'], 10)
    if 'mode_188' not in record:
        out['labels_3'] = ['default']
    elif record['mode_188'] is None:
        raise ValueError('mode_188')
    else:
        out['labels_3'] = strings_decode(record['mode_188'])
    return out

# unit r189
def encode_r189(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_189'] = 'H189'
    elif record['state_0'] is None:
        out['v_189'] = None
    else:
        out['v_189'] = enum_encode(record['state_0'], {'ready': 'R189', 'held': 'H189', 'done': 'D189'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_189'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_189'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_189'] = 'unset'
    elif record['title_3'] is None:
        out['mode_189'] = None
    else:
        out['mode_189'] = text_encode(record['title_3'])
    return out

def decode_r189(record: dict) -> dict:
    out = {}
    if 'v_189' not in record:
        out['state_0'] = 'held'
    elif record['v_189'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_189'], {'ready': 'R189', 'held': 'H189', 'done': 'D189'})
    if 'qty_189' not in record:
        raise KeyError('qty_189')
    elif record['qty_189'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_189'], 10)
    if 'flag_189' not in record:
        pass
    elif record['flag_189'] is None:
        raise ValueError('flag_189')
    else:
        out['labels_2'] = strings_decode(record['flag_189'])
    if 'mode_189' not in record:
        out['title_3'] = 'unset'
    elif record['mode_189'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_189'])
    return out

# unit r190
def encode_r190(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_190'] = 30
    elif record['amount_0'] is None:
        out['v_190'] = None
    else:
        out['v_190'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_190'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_190'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_190'] = '-7'
    elif record['count_3'] is None:
        out['mode_190'] = None
    else:
        out['mode_190'] = decimal_encode(record['count_3'])
    return out

def decode_r190(record: dict) -> dict:
    out = {}
    if 'v_190' not in record:
        out['amount_0'] = 3
    elif record['v_190'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_190'], 10)
    if 'qty_190' not in record:
        raise KeyError('qty_190')
    elif record['qty_190'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_190'])
    if 'flag_190' not in record:
        pass
    elif record['flag_190'] is None:
        raise ValueError('flag_190')
    else:
        out['title_2'] = text_decode(record['flag_190'])
    if 'mode_190' not in record:
        out['count_3'] = -7
    elif record['mode_190'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_190'])
    return out

# unit r191
def encode_r191(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_191'] = ['default']
    elif record['labels_0'] is None:
        out['v_191'] = None
    else:
        out['v_191'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_191'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_191'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_191'] = 'no'
    elif record['active_3'] is None:
        out['mode_191'] = None
    else:
        out['mode_191'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r191(record: dict) -> dict:
    out = {}
    if 'v_191' not in record:
        out['labels_0'] = ['default']
    elif record['v_191'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_191'])
    if 'qty_191' not in record:
        raise KeyError('qty_191')
    elif record['qty_191'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_191'])
    if 'flag_191' not in record:
        pass
    elif record['flag_191'] is None:
        raise ValueError('flag_191')
    else:
        out['count_2'] = decimal_decode(record['flag_191'])
    if 'mode_191' not in record:
        out['active_3'] = False
    elif record['mode_191'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_191'], ['yes', 'no'])
    return out

# unit r192
def encode_r192(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_192'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_192'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_192'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_192'] = None
    else:
        out['flag_192'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_192'] = enum_encode(record['state_3'], {'ready': 'R192', 'held': 'H192', 'done': 'D192'})
    return out

def decode_r192(record: dict) -> dict:
    out = {}
    if 'v_192' not in record:
        raise KeyError('v_192')
    elif record['v_192'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_192'])
    if 'qty_192' not in record:
        pass
    elif record['qty_192'] is None:
        raise ValueError('qty_192')
    else:
        out['count_1'] = decimal_decode(record['qty_192'])
    if 'flag_192' not in record:
        out['active_2'] = False
    elif record['flag_192'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_192'], ['ON', 'OFF'])
    if 'mode_192' not in record:
        raise KeyError('mode_192')
    elif record['mode_192'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_192'], {'ready': 'R192', 'held': 'H192', 'done': 'D192'})
    return out

