from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r133
def encode_r133(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_133'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_133'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_133'] = None
    else:
        out['qty_133'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_133'] = enum_encode(record['state_2'], {'ready': 'R133', 'held': 'H133', 'done': 'D133'})
    if 'amount_3' not in record:
        out['mode_133'] = 6
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_133'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r133(record: dict) -> dict:
    out = {}
    if 'v_133' not in record:
        out['count_0'] = -7
    elif record['v_133'] is None:
        raise ValueError('v_133')
    else:
        out['count_0'] = decimal_decode(record['v_133'])
    if 'qty_133' not in record:
        raise KeyError('qty_133')
    elif record['qty_133'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_133'], ['yes', 'no'])
    if 'flag_133' not in record:
        pass
    elif record['flag_133'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_133'], {'ready': 'R133', 'held': 'H133', 'done': 'D133'})
    if 'mode_133' not in record:
        out['amount_3'] = 3
    elif record['mode_133'] is None:
        raise ValueError('mode_133')
    else:
        out['amount_3'] = scale_decode(record['mode_133'], 2)
    return out

# unit r134
def encode_r134(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_134'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_134'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_134'] = None
    else:
        out['qty_134'] = enum_encode(record['state_1'], {'ready': 'R134', 'held': 'H134', 'done': 'D134'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_134'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        out['mode_134'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_134'] = strings_encode(record['labels_3'])
    return out

def decode_r134(record: dict) -> dict:
    out = {}
    if 'v_134' not in record:
        out['active_0'] = False
    elif record['v_134'] is None:
        raise ValueError('v_134')
    else:
        out['active_0'] = boolean_decode(record['v_134'], ['ON', 'OFF'])
    if 'qty_134' not in record:
        raise KeyError('qty_134')
    elif record['qty_134'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_134'], {'ready': 'R134', 'held': 'H134', 'done': 'D134'})
    if 'flag_134' not in record:
        pass
    elif record['flag_134'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_134'], 2)
    if 'mode_134' not in record:
        out['labels_3'] = ['default']
    elif record['mode_134'] is None:
        raise ValueError('mode_134')
    else:
        out['labels_3'] = strings_decode(record['mode_134'])
    return out

# unit r135
def encode_r135(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_135'] = 'H135'
    elif record['state_0'] is None:
        out['v_135'] = None
    else:
        out['v_135'] = enum_encode(record['state_0'], {'ready': 'R135', 'held': 'H135', 'done': 'D135'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_135'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_135'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_135'] = 'unset'
    elif record['title_3'] is None:
        out['mode_135'] = None
    else:
        out['mode_135'] = text_encode(record['title_3'])
    return out

def decode_r135(record: dict) -> dict:
    out = {}
    if 'v_135' not in record:
        out['state_0'] = 'held'
    elif record['v_135'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_135'], {'ready': 'R135', 'held': 'H135', 'done': 'D135'})
    if 'qty_135' not in record:
        raise KeyError('qty_135')
    elif record['qty_135'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_135'], 2)
    if 'flag_135' not in record:
        pass
    elif record['flag_135'] is None:
        raise ValueError('flag_135')
    else:
        out['labels_2'] = strings_decode(record['flag_135'])
    if 'mode_135' not in record:
        out['title_3'] = 'unset'
    elif record['mode_135'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_135'])
    return out

# unit r136
def encode_r136(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_136'] = 6
    elif record['amount_0'] is None:
        out['v_136'] = None
    else:
        out['v_136'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_136'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_136'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_136'] = '-7'
    elif record['count_3'] is None:
        out['mode_136'] = None
    else:
        out['mode_136'] = decimal_encode(record['count_3'])
    return out

def decode_r136(record: dict) -> dict:
    out = {}
    if 'v_136' not in record:
        out['amount_0'] = 3
    elif record['v_136'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_136'], 2)
    if 'qty_136' not in record:
        raise KeyError('qty_136')
    elif record['qty_136'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_136'])
    if 'flag_136' not in record:
        pass
    elif record['flag_136'] is None:
        raise ValueError('flag_136')
    else:
        out['title_2'] = text_decode(record['flag_136'])
    if 'mode_136' not in record:
        out['count_3'] = -7
    elif record['mode_136'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_136'])
    return out

# unit r137
def encode_r137(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_137'] = ['default']
    elif record['labels_0'] is None:
        out['v_137'] = None
    else:
        out['v_137'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_137'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_137'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_137'] = 'no'
    elif record['active_3'] is None:
        out['mode_137'] = None
    else:
        out['mode_137'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r137(record: dict) -> dict:
    out = {}
    if 'v_137' not in record:
        out['labels_0'] = ['default']
    elif record['v_137'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_137'])
    if 'qty_137' not in record:
        raise KeyError('qty_137')
    elif record['qty_137'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_137'])
    if 'flag_137' not in record:
        pass
    elif record['flag_137'] is None:
        raise ValueError('flag_137')
    else:
        out['count_2'] = decimal_decode(record['flag_137'])
    if 'mode_137' not in record:
        out['active_3'] = False
    elif record['mode_137'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_137'], ['yes', 'no'])
    return out

# unit r138
def encode_r138(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_138'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_138'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_138'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_138'] = None
    else:
        out['flag_138'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_138'] = enum_encode(record['state_3'], {'ready': 'R138', 'held': 'H138', 'done': 'D138'})
    return out

def decode_r138(record: dict) -> dict:
    out = {}
    if 'v_138' not in record:
        raise KeyError('v_138')
    elif record['v_138'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_138'])
    if 'qty_138' not in record:
        pass
    elif record['qty_138'] is None:
        raise ValueError('qty_138')
    else:
        out['count_1'] = decimal_decode(record['qty_138'])
    if 'flag_138' not in record:
        out['active_2'] = False
    elif record['flag_138'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_138'], ['ON', 'OFF'])
    if 'mode_138' not in record:
        raise KeyError('mode_138')
    elif record['mode_138'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_138'], {'ready': 'R138', 'held': 'H138', 'done': 'D138'})
    return out

