from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r169
def encode_r169(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_169'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_169'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_169'] = None
    else:
        out['qty_169'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_169'] = enum_encode(record['state_2'], {'ready': 'R169', 'held': 'H169', 'done': 'D169'})
    if 'amount_3' not in record:
        out['mode_169'] = 6
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_169'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r169(record: dict) -> dict:
    out = {}
    if 'v_169' not in record:
        out['count_0'] = -7
    elif record['v_169'] is None:
        raise ValueError('v_169')
    else:
        out['count_0'] = decimal_decode(record['v_169'])
    if 'qty_169' not in record:
        raise KeyError('qty_169')
    elif record['qty_169'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_169'], ['yes', 'no'])
    if 'flag_169' not in record:
        pass
    elif record['flag_169'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_169'], {'ready': 'R169', 'held': 'H169', 'done': 'D169'})
    if 'mode_169' not in record:
        out['amount_3'] = 3
    elif record['mode_169'] is None:
        raise ValueError('mode_169')
    else:
        out['amount_3'] = scale_decode(record['mode_169'], 2)
    return out

# unit r170
def encode_r170(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_170'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_170'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_170'] = None
    else:
        out['qty_170'] = enum_encode(record['state_1'], {'ready': 'R170', 'held': 'H170', 'done': 'D170'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_170'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        out['mode_170'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_170'] = strings_encode(record['labels_3'])
    return out

def decode_r170(record: dict) -> dict:
    out = {}
    if 'v_170' not in record:
        out['active_0'] = False
    elif record['v_170'] is None:
        raise ValueError('v_170')
    else:
        out['active_0'] = boolean_decode(record['v_170'], ['ON', 'OFF'])
    if 'qty_170' not in record:
        raise KeyError('qty_170')
    elif record['qty_170'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_170'], {'ready': 'R170', 'held': 'H170', 'done': 'D170'})
    if 'flag_170' not in record:
        pass
    elif record['flag_170'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_170'], 2)
    if 'mode_170' not in record:
        out['labels_3'] = ['default']
    elif record['mode_170'] is None:
        raise ValueError('mode_170')
    else:
        out['labels_3'] = strings_decode(record['mode_170'])
    return out

# unit r171
def encode_r171(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_171'] = 'H171'
    elif record['state_0'] is None:
        out['v_171'] = None
    else:
        out['v_171'] = enum_encode(record['state_0'], {'ready': 'R171', 'held': 'H171', 'done': 'D171'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_171'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_171'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_171'] = 'unset'
    elif record['title_3'] is None:
        out['mode_171'] = None
    else:
        out['mode_171'] = text_encode(record['title_3'])
    return out

def decode_r171(record: dict) -> dict:
    out = {}
    if 'v_171' not in record:
        out['state_0'] = 'held'
    elif record['v_171'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_171'], {'ready': 'R171', 'held': 'H171', 'done': 'D171'})
    if 'qty_171' not in record:
        raise KeyError('qty_171')
    elif record['qty_171'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_171'], 2)
    if 'flag_171' not in record:
        pass
    elif record['flag_171'] is None:
        raise ValueError('flag_171')
    else:
        out['labels_2'] = strings_decode(record['flag_171'])
    if 'mode_171' not in record:
        out['title_3'] = 'unset'
    elif record['mode_171'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_171'])
    return out

# unit r172
def encode_r172(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_172'] = 6
    elif record['amount_0'] is None:
        out['v_172'] = None
    else:
        out['v_172'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_172'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_172'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_172'] = '-7'
    elif record['count_3'] is None:
        out['mode_172'] = None
    else:
        out['mode_172'] = decimal_encode(record['count_3'])
    return out

def decode_r172(record: dict) -> dict:
    out = {}
    if 'v_172' not in record:
        out['amount_0'] = 3
    elif record['v_172'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_172'], 2)
    if 'qty_172' not in record:
        raise KeyError('qty_172')
    elif record['qty_172'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_172'])
    if 'flag_172' not in record:
        pass
    elif record['flag_172'] is None:
        raise ValueError('flag_172')
    else:
        out['title_2'] = text_decode(record['flag_172'])
    if 'mode_172' not in record:
        out['count_3'] = -7
    elif record['mode_172'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_172'])
    return out

# unit r173
def encode_r173(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_173'] = ['default']
    elif record['labels_0'] is None:
        out['v_173'] = None
    else:
        out['v_173'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_173'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_173'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_173'] = 'no'
    elif record['active_3'] is None:
        out['mode_173'] = None
    else:
        out['mode_173'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r173(record: dict) -> dict:
    out = {}
    if 'v_173' not in record:
        out['labels_0'] = ['default']
    elif record['v_173'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_173'])
    if 'qty_173' not in record:
        raise KeyError('qty_173')
    elif record['qty_173'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_173'])
    if 'flag_173' not in record:
        pass
    elif record['flag_173'] is None:
        raise ValueError('flag_173')
    else:
        out['count_2'] = decimal_decode(record['flag_173'])
    if 'mode_173' not in record:
        out['active_3'] = False
    elif record['mode_173'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_173'], ['yes', 'no'])
    return out

# unit r174
def encode_r174(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_174'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_174'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_174'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_174'] = None
    else:
        out['flag_174'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_174'] = enum_encode(record['state_3'], {'ready': 'R174', 'held': 'H174', 'done': 'D174'})
    return out

def decode_r174(record: dict) -> dict:
    out = {}
    if 'v_174' not in record:
        raise KeyError('v_174')
    elif record['v_174'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_174'])
    if 'qty_174' not in record:
        pass
    elif record['qty_174'] is None:
        raise ValueError('qty_174')
    else:
        out['count_1'] = decimal_decode(record['qty_174'])
    if 'flag_174' not in record:
        out['active_2'] = False
    elif record['flag_174'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_174'], ['ON', 'OFF'])
    if 'mode_174' not in record:
        raise KeyError('mode_174')
    elif record['mode_174'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_174'], {'ready': 'R174', 'held': 'H174', 'done': 'D174'})
    return out

