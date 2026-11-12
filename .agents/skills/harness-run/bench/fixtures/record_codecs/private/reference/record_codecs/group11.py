from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r067
def encode_r067(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_067'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_067'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_067'] = 'H67'
    elif record['state_2'] is None:
        out['flag_067'] = None
    else:
        out['flag_067'] = enum_encode(record['state_2'], {'ready': 'R67', 'held': 'H67', 'done': 'D67'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_067'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r067(record: dict) -> dict:
    out = {}
    if 'v_067' not in record:
        raise KeyError('v_067')
    elif record['v_067'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_067'])
    if 'qty_067' not in record:
        pass
    elif record['qty_067'] is None:
        raise ValueError('qty_067')
    else:
        out['active_1'] = boolean_decode(record['qty_067'], ['yes', 'no'])
    if 'flag_067' not in record:
        out['state_2'] = 'held'
    elif record['flag_067'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_067'], {'ready': 'R67', 'held': 'H67', 'done': 'D67'})
    if 'mode_067' not in record:
        raise KeyError('mode_067')
    elif record['mode_067'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_067'], 10)
    return out

# unit r068
def encode_r068(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_068'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_068'] = enum_encode(record['state_1'], {'ready': 'R68', 'held': 'H68', 'done': 'D68'})
    if 'amount_2' not in record:
        out['flag_068'] = 30
    elif record['amount_2'] is None:
        out['flag_068'] = None
    else:
        out['flag_068'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_068'] = strings_encode(record['labels_3'])
    return out

def decode_r068(record: dict) -> dict:
    out = {}
    if 'v_068' not in record:
        raise KeyError('v_068')
    elif record['v_068'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_068'], ['ON', 'OFF'])
    if 'qty_068' not in record:
        pass
    elif record['qty_068'] is None:
        raise ValueError('qty_068')
    else:
        out['state_1'] = enum_decode(record['qty_068'], {'ready': 'R68', 'held': 'H68', 'done': 'D68'})
    if 'flag_068' not in record:
        out['amount_2'] = 3
    elif record['flag_068'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_068'], 10)
    if 'mode_068' not in record:
        raise KeyError('mode_068')
    elif record['mode_068'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_068'])
    return out

# unit r069
def encode_r069(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_069'] = enum_encode(record['state_0'], {'ready': 'R69', 'held': 'H69', 'done': 'D69'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_069'] = None
    else:
        out['qty_069'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        out['flag_069'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_069'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_069'] = text_encode(record['title_3'])
    return out

def decode_r069(record: dict) -> dict:
    out = {}
    if 'v_069' not in record:
        raise KeyError('v_069')
    elif record['v_069'] is None:
        raise ValueError('v_069')
    else:
        out['state_0'] = enum_decode(record['v_069'], {'ready': 'R69', 'held': 'H69', 'done': 'D69'})
    if 'qty_069' not in record:
        pass
    elif record['qty_069'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_069'], 10)
    if 'flag_069' not in record:
        out['labels_2'] = ['default']
    elif record['flag_069'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_069'])
    if 'mode_069' not in record:
        raise KeyError('mode_069')
    elif record['mode_069'] is None:
        raise ValueError('mode_069')
    else:
        out['title_3'] = text_decode(record['mode_069'])
    return out

# unit r070
def encode_r070(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_070'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_070'] = None
    else:
        out['qty_070'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_070'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_070'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_070'] = decimal_encode(record['count_3'])
    return out

def decode_r070(record: dict) -> dict:
    out = {}
    if 'v_070' not in record:
        raise KeyError('v_070')
    elif record['v_070'] is None:
        raise ValueError('v_070')
    else:
        out['amount_0'] = scale_decode(record['v_070'], 10)
    if 'qty_070' not in record:
        pass
    elif record['qty_070'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_070'])
    if 'flag_070' not in record:
        out['title_2'] = 'unset'
    elif record['flag_070'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_070'])
    if 'mode_070' not in record:
        raise KeyError('mode_070')
    elif record['mode_070'] is None:
        raise ValueError('mode_070')
    else:
        out['count_3'] = decimal_decode(record['mode_070'])
    return out

# unit r071
def encode_r071(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_071'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_071'] = None
    else:
        out['qty_071'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_071'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_071'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_071'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r071(record: dict) -> dict:
    out = {}
    if 'v_071' not in record:
        raise KeyError('v_071')
    elif record['v_071'] is None:
        raise ValueError('v_071')
    else:
        out['labels_0'] = strings_decode(record['v_071'])
    if 'qty_071' not in record:
        pass
    elif record['qty_071'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_071'])
    if 'flag_071' not in record:
        out['count_2'] = -7
    elif record['flag_071'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_071'])
    if 'mode_071' not in record:
        raise KeyError('mode_071')
    elif record['mode_071'] is None:
        raise ValueError('mode_071')
    else:
        out['active_3'] = boolean_decode(record['mode_071'], ['yes', 'no'])
    return out

# unit r072
def encode_r072(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_072'] = None
    else:
        out['v_072'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_072'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_072'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_072'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_072'] = None
    else:
        out['mode_072'] = enum_encode(record['state_3'], {'ready': 'R72', 'held': 'H72', 'done': 'D72'})
    return out

def decode_r072(record: dict) -> dict:
    out = {}
    if 'v_072' not in record:
        pass
    elif record['v_072'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_072'])
    if 'qty_072' not in record:
        out['count_1'] = -7
    elif record['qty_072'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_072'])
    if 'flag_072' not in record:
        raise KeyError('flag_072')
    elif record['flag_072'] is None:
        raise ValueError('flag_072')
    else:
        out['active_2'] = boolean_decode(record['flag_072'], ['ON', 'OFF'])
    if 'mode_072' not in record:
        pass
    elif record['mode_072'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_072'], {'ready': 'R72', 'held': 'H72', 'done': 'D72'})
    return out

