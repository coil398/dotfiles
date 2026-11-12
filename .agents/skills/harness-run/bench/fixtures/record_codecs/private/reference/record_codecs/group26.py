from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r157
def encode_r157(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_157'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_157'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_157'] = 'H157'
    elif record['state_2'] is None:
        out['flag_157'] = None
    else:
        out['flag_157'] = enum_encode(record['state_2'], {'ready': 'R157', 'held': 'H157', 'done': 'D157'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_157'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r157(record: dict) -> dict:
    out = {}
    if 'v_157' not in record:
        raise KeyError('v_157')
    elif record['v_157'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_157'])
    if 'qty_157' not in record:
        pass
    elif record['qty_157'] is None:
        raise ValueError('qty_157')
    else:
        out['active_1'] = boolean_decode(record['qty_157'], ['yes', 'no'])
    if 'flag_157' not in record:
        out['state_2'] = 'held'
    elif record['flag_157'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_157'], {'ready': 'R157', 'held': 'H157', 'done': 'D157'})
    if 'mode_157' not in record:
        raise KeyError('mode_157')
    elif record['mode_157'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_157'], 2)
    return out

# unit r158
def encode_r158(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_158'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_158'] = enum_encode(record['state_1'], {'ready': 'R158', 'held': 'H158', 'done': 'D158'})
    if 'amount_2' not in record:
        out['flag_158'] = 6
    elif record['amount_2'] is None:
        out['flag_158'] = None
    else:
        out['flag_158'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_158'] = strings_encode(record['labels_3'])
    return out

def decode_r158(record: dict) -> dict:
    out = {}
    if 'v_158' not in record:
        raise KeyError('v_158')
    elif record['v_158'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_158'], ['ON', 'OFF'])
    if 'qty_158' not in record:
        pass
    elif record['qty_158'] is None:
        raise ValueError('qty_158')
    else:
        out['state_1'] = enum_decode(record['qty_158'], {'ready': 'R158', 'held': 'H158', 'done': 'D158'})
    if 'flag_158' not in record:
        out['amount_2'] = 3
    elif record['flag_158'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_158'], 2)
    if 'mode_158' not in record:
        raise KeyError('mode_158')
    elif record['mode_158'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_158'])
    return out

# unit r159
def encode_r159(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_159'] = enum_encode(record['state_0'], {'ready': 'R159', 'held': 'H159', 'done': 'D159'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_159'] = None
    else:
        out['qty_159'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        out['flag_159'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_159'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_159'] = text_encode(record['title_3'])
    return out

def decode_r159(record: dict) -> dict:
    out = {}
    if 'v_159' not in record:
        raise KeyError('v_159')
    elif record['v_159'] is None:
        raise ValueError('v_159')
    else:
        out['state_0'] = enum_decode(record['v_159'], {'ready': 'R159', 'held': 'H159', 'done': 'D159'})
    if 'qty_159' not in record:
        pass
    elif record['qty_159'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_159'], 2)
    if 'flag_159' not in record:
        out['labels_2'] = ['default']
    elif record['flag_159'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_159'])
    if 'mode_159' not in record:
        raise KeyError('mode_159')
    elif record['mode_159'] is None:
        raise ValueError('mode_159')
    else:
        out['title_3'] = text_decode(record['mode_159'])
    return out

# unit r160
def encode_r160(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_160'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_160'] = None
    else:
        out['qty_160'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_160'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_160'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_160'] = decimal_encode(record['count_3'])
    return out

def decode_r160(record: dict) -> dict:
    out = {}
    if 'v_160' not in record:
        raise KeyError('v_160')
    elif record['v_160'] is None:
        raise ValueError('v_160')
    else:
        out['amount_0'] = scale_decode(record['v_160'], 2)
    if 'qty_160' not in record:
        pass
    elif record['qty_160'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_160'])
    if 'flag_160' not in record:
        out['title_2'] = 'unset'
    elif record['flag_160'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_160'])
    if 'mode_160' not in record:
        raise KeyError('mode_160')
    elif record['mode_160'] is None:
        raise ValueError('mode_160')
    else:
        out['count_3'] = decimal_decode(record['mode_160'])
    return out

# unit r161
def encode_r161(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_161'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_161'] = None
    else:
        out['qty_161'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_161'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_161'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_161'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r161(record: dict) -> dict:
    out = {}
    if 'v_161' not in record:
        raise KeyError('v_161')
    elif record['v_161'] is None:
        raise ValueError('v_161')
    else:
        out['labels_0'] = strings_decode(record['v_161'])
    if 'qty_161' not in record:
        pass
    elif record['qty_161'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_161'])
    if 'flag_161' not in record:
        out['count_2'] = -7
    elif record['flag_161'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_161'])
    if 'mode_161' not in record:
        raise KeyError('mode_161')
    elif record['mode_161'] is None:
        raise ValueError('mode_161')
    else:
        out['active_3'] = boolean_decode(record['mode_161'], ['yes', 'no'])
    return out

# unit r162
def encode_r162(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_162'] = None
    else:
        out['v_162'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_162'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_162'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_162'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_162'] = None
    else:
        out['mode_162'] = enum_encode(record['state_3'], {'ready': 'R162', 'held': 'H162', 'done': 'D162'})
    return out

def decode_r162(record: dict) -> dict:
    out = {}
    if 'v_162' not in record:
        pass
    elif record['v_162'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_162'])
    if 'qty_162' not in record:
        out['count_1'] = -7
    elif record['qty_162'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_162'])
    if 'flag_162' not in record:
        raise KeyError('flag_162')
    elif record['flag_162'] is None:
        raise ValueError('flag_162')
    else:
        out['active_2'] = boolean_decode(record['flag_162'], ['ON', 'OFF'])
    if 'mode_162' not in record:
        pass
    elif record['mode_162'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_162'], {'ready': 'R162', 'held': 'H162', 'done': 'D162'})
    return out

