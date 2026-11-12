from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r163
def encode_r163(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_163'] = None
    else:
        out['v_163'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_163'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_163'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_163'] = enum_encode(record['state_2'], {'ready': 'R163', 'held': 'H163', 'done': 'D163'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_163'] = None
    else:
        out['mode_163'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r163(record: dict) -> dict:
    out = {}
    if 'v_163' not in record:
        pass
    elif record['v_163'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_163'])
    if 'qty_163' not in record:
        out['active_1'] = False
    elif record['qty_163'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_163'], ['yes', 'no'])
    if 'flag_163' not in record:
        raise KeyError('flag_163')
    elif record['flag_163'] is None:
        raise ValueError('flag_163')
    else:
        out['state_2'] = enum_decode(record['flag_163'], {'ready': 'R163', 'held': 'H163', 'done': 'D163'})
    if 'mode_163' not in record:
        pass
    elif record['mode_163'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_163'], 10)
    return out

# unit r164
def encode_r164(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_164'] = None
    else:
        out['v_164'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_164'] = 'H164'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_164'] = enum_encode(record['state_1'], {'ready': 'R164', 'held': 'H164', 'done': 'D164'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_164'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_164'] = None
    else:
        out['mode_164'] = strings_encode(record['labels_3'])
    return out

def decode_r164(record: dict) -> dict:
    out = {}
    if 'v_164' not in record:
        pass
    elif record['v_164'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_164'], ['ON', 'OFF'])
    if 'qty_164' not in record:
        out['state_1'] = 'held'
    elif record['qty_164'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_164'], {'ready': 'R164', 'held': 'H164', 'done': 'D164'})
    if 'flag_164' not in record:
        raise KeyError('flag_164')
    elif record['flag_164'] is None:
        raise ValueError('flag_164')
    else:
        out['amount_2'] = scale_decode(record['flag_164'], 10)
    if 'mode_164' not in record:
        pass
    elif record['mode_164'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_164'])
    return out

# unit r165
def encode_r165(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_165'] = enum_encode(record['state_0'], {'ready': 'R165', 'held': 'H165', 'done': 'D165'})
    if 'amount_1' not in record:
        out['qty_165'] = 30
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_165'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_165'] = None
    else:
        out['flag_165'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_165'] = text_encode(record['title_3'])
    return out

def decode_r165(record: dict) -> dict:
    out = {}
    if 'v_165' not in record:
        pass
    elif record['v_165'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_165'], {'ready': 'R165', 'held': 'H165', 'done': 'D165'})
    if 'qty_165' not in record:
        out['amount_1'] = 3
    elif record['qty_165'] is None:
        raise ValueError('qty_165')
    else:
        out['amount_1'] = scale_decode(record['qty_165'], 10)
    if 'flag_165' not in record:
        raise KeyError('flag_165')
    elif record['flag_165'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_165'])
    if 'mode_165' not in record:
        pass
    elif record['mode_165'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_165'])
    return out

# unit r166
def encode_r166(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_166'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        out['qty_166'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_166'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_166'] = None
    else:
        out['flag_166'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_166'] = decimal_encode(record['count_3'])
    return out

def decode_r166(record: dict) -> dict:
    out = {}
    if 'v_166' not in record:
        pass
    elif record['v_166'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_166'], 10)
    if 'qty_166' not in record:
        out['labels_1'] = ['default']
    elif record['qty_166'] is None:
        raise ValueError('qty_166')
    else:
        out['labels_1'] = strings_decode(record['qty_166'])
    if 'flag_166' not in record:
        raise KeyError('flag_166')
    elif record['flag_166'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_166'])
    if 'mode_166' not in record:
        pass
    elif record['mode_166'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_166'])
    return out

# unit r167
def encode_r167(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_167'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_167'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_167'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_167'] = None
    else:
        out['flag_167'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_167'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r167(record: dict) -> dict:
    out = {}
    if 'v_167' not in record:
        pass
    elif record['v_167'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_167'])
    if 'qty_167' not in record:
        out['title_1'] = 'unset'
    elif record['qty_167'] is None:
        raise ValueError('qty_167')
    else:
        out['title_1'] = text_decode(record['qty_167'])
    if 'flag_167' not in record:
        raise KeyError('flag_167')
    elif record['flag_167'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_167'])
    if 'mode_167' not in record:
        pass
    elif record['mode_167'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_167'], ['yes', 'no'])
    return out

# unit r168
def encode_r168(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_168'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_168'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_168'] = None
    else:
        out['qty_168'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_168'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_168'] = 'H168'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_168'] = enum_encode(record['state_3'], {'ready': 'R168', 'held': 'H168', 'done': 'D168'})
    return out

def decode_r168(record: dict) -> dict:
    out = {}
    if 'v_168' not in record:
        out['title_0'] = 'unset'
    elif record['v_168'] is None:
        raise ValueError('v_168')
    else:
        out['title_0'] = text_decode(record['v_168'])
    if 'qty_168' not in record:
        raise KeyError('qty_168')
    elif record['qty_168'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_168'])
    if 'flag_168' not in record:
        pass
    elif record['flag_168'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_168'], ['ON', 'OFF'])
    if 'mode_168' not in record:
        out['state_3'] = 'held'
    elif record['mode_168'] is None:
        raise ValueError('mode_168')
    else:
        out['state_3'] = enum_decode(record['mode_168'], {'ready': 'R168', 'held': 'H168', 'done': 'D168'})
    return out

