from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r103
def encode_r103(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_103'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_103'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_103'] = 'H103'
    elif record['state_2'] is None:
        out['flag_103'] = None
    else:
        out['flag_103'] = enum_encode(record['state_2'], {'ready': 'R103', 'held': 'H103', 'done': 'D103'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_103'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r103(record: dict) -> dict:
    out = {}
    if 'v_103' not in record:
        raise KeyError('v_103')
    elif record['v_103'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_103'])
    if 'qty_103' not in record:
        pass
    elif record['qty_103'] is None:
        raise ValueError('qty_103')
    else:
        out['active_1'] = boolean_decode(record['qty_103'], ['yes', 'no'])
    if 'flag_103' not in record:
        out['state_2'] = 'held'
    elif record['flag_103'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_103'], {'ready': 'R103', 'held': 'H103', 'done': 'D103'})
    if 'mode_103' not in record:
        raise KeyError('mode_103')
    elif record['mode_103'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_103'], 10)
    return out

# unit r104
def encode_r104(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_104'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_104'] = enum_encode(record['state_1'], {'ready': 'R104', 'held': 'H104', 'done': 'D104'})
    if 'amount_2' not in record:
        out['flag_104'] = 30
    elif record['amount_2'] is None:
        out['flag_104'] = None
    else:
        out['flag_104'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_104'] = strings_encode(record['labels_3'])
    return out

def decode_r104(record: dict) -> dict:
    out = {}
    if 'v_104' not in record:
        raise KeyError('v_104')
    elif record['v_104'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_104'], ['ON', 'OFF'])
    if 'qty_104' not in record:
        pass
    elif record['qty_104'] is None:
        raise ValueError('qty_104')
    else:
        out['state_1'] = enum_decode(record['qty_104'], {'ready': 'R104', 'held': 'H104', 'done': 'D104'})
    if 'flag_104' not in record:
        out['amount_2'] = 3
    elif record['flag_104'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_104'], 10)
    if 'mode_104' not in record:
        raise KeyError('mode_104')
    elif record['mode_104'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_104'])
    return out

# unit r105
def encode_r105(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_105'] = enum_encode(record['state_0'], {'ready': 'R105', 'held': 'H105', 'done': 'D105'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_105'] = None
    else:
        out['qty_105'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        out['flag_105'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_105'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_105'] = text_encode(record['title_3'])
    return out

def decode_r105(record: dict) -> dict:
    out = {}
    if 'v_105' not in record:
        raise KeyError('v_105')
    elif record['v_105'] is None:
        raise ValueError('v_105')
    else:
        out['state_0'] = enum_decode(record['v_105'], {'ready': 'R105', 'held': 'H105', 'done': 'D105'})
    if 'qty_105' not in record:
        pass
    elif record['qty_105'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_105'], 10)
    if 'flag_105' not in record:
        out['labels_2'] = ['default']
    elif record['flag_105'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_105'])
    if 'mode_105' not in record:
        raise KeyError('mode_105')
    elif record['mode_105'] is None:
        raise ValueError('mode_105')
    else:
        out['title_3'] = text_decode(record['mode_105'])
    return out

# unit r106
def encode_r106(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_106'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_106'] = None
    else:
        out['qty_106'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_106'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_106'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_106'] = decimal_encode(record['count_3'])
    return out

def decode_r106(record: dict) -> dict:
    out = {}
    if 'v_106' not in record:
        raise KeyError('v_106')
    elif record['v_106'] is None:
        raise ValueError('v_106')
    else:
        out['amount_0'] = scale_decode(record['v_106'], 10)
    if 'qty_106' not in record:
        pass
    elif record['qty_106'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_106'])
    if 'flag_106' not in record:
        out['title_2'] = 'unset'
    elif record['flag_106'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_106'])
    if 'mode_106' not in record:
        raise KeyError('mode_106')
    elif record['mode_106'] is None:
        raise ValueError('mode_106')
    else:
        out['count_3'] = decimal_decode(record['mode_106'])
    return out

# unit r107
def encode_r107(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_107'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_107'] = None
    else:
        out['qty_107'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_107'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_107'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_107'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r107(record: dict) -> dict:
    out = {}
    if 'v_107' not in record:
        raise KeyError('v_107')
    elif record['v_107'] is None:
        raise ValueError('v_107')
    else:
        out['labels_0'] = strings_decode(record['v_107'])
    if 'qty_107' not in record:
        pass
    elif record['qty_107'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_107'])
    if 'flag_107' not in record:
        out['count_2'] = -7
    elif record['flag_107'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_107'])
    if 'mode_107' not in record:
        raise KeyError('mode_107')
    elif record['mode_107'] is None:
        raise ValueError('mode_107')
    else:
        out['active_3'] = boolean_decode(record['mode_107'], ['yes', 'no'])
    return out

# unit r108
def encode_r108(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_108'] = None
    else:
        out['v_108'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_108'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_108'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_108'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_108'] = None
    else:
        out['mode_108'] = enum_encode(record['state_3'], {'ready': 'R108', 'held': 'H108', 'done': 'D108'})
    return out

def decode_r108(record: dict) -> dict:
    out = {}
    if 'v_108' not in record:
        pass
    elif record['v_108'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_108'])
    if 'qty_108' not in record:
        out['count_1'] = -7
    elif record['qty_108'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_108'])
    if 'flag_108' not in record:
        raise KeyError('flag_108')
    elif record['flag_108'] is None:
        raise ValueError('flag_108')
    else:
        out['active_2'] = boolean_decode(record['flag_108'], ['ON', 'OFF'])
    if 'mode_108' not in record:
        pass
    elif record['mode_108'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_108'], {'ready': 'R108', 'held': 'H108', 'done': 'D108'})
    return out

