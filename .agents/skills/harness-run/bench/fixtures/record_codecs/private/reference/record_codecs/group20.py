from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r121
def encode_r121(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_121'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_121'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_121'] = 'H121'
    elif record['state_2'] is None:
        out['flag_121'] = None
    else:
        out['flag_121'] = enum_encode(record['state_2'], {'ready': 'R121', 'held': 'H121', 'done': 'D121'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_121'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r121(record: dict) -> dict:
    out = {}
    if 'v_121' not in record:
        raise KeyError('v_121')
    elif record['v_121'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_121'])
    if 'qty_121' not in record:
        pass
    elif record['qty_121'] is None:
        raise ValueError('qty_121')
    else:
        out['active_1'] = boolean_decode(record['qty_121'], ['yes', 'no'])
    if 'flag_121' not in record:
        out['state_2'] = 'held'
    elif record['flag_121'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_121'], {'ready': 'R121', 'held': 'H121', 'done': 'D121'})
    if 'mode_121' not in record:
        raise KeyError('mode_121')
    elif record['mode_121'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_121'], 2)
    return out

# unit r122
def encode_r122(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_122'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_122'] = enum_encode(record['state_1'], {'ready': 'R122', 'held': 'H122', 'done': 'D122'})
    if 'amount_2' not in record:
        out['flag_122'] = 6
    elif record['amount_2'] is None:
        out['flag_122'] = None
    else:
        out['flag_122'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_122'] = strings_encode(record['labels_3'])
    return out

def decode_r122(record: dict) -> dict:
    out = {}
    if 'v_122' not in record:
        raise KeyError('v_122')
    elif record['v_122'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_122'], ['ON', 'OFF'])
    if 'qty_122' not in record:
        pass
    elif record['qty_122'] is None:
        raise ValueError('qty_122')
    else:
        out['state_1'] = enum_decode(record['qty_122'], {'ready': 'R122', 'held': 'H122', 'done': 'D122'})
    if 'flag_122' not in record:
        out['amount_2'] = 3
    elif record['flag_122'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_122'], 2)
    if 'mode_122' not in record:
        raise KeyError('mode_122')
    elif record['mode_122'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_122'])
    return out

# unit r123
def encode_r123(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_123'] = enum_encode(record['state_0'], {'ready': 'R123', 'held': 'H123', 'done': 'D123'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_123'] = None
    else:
        out['qty_123'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        out['flag_123'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_123'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_123'] = text_encode(record['title_3'])
    return out

def decode_r123(record: dict) -> dict:
    out = {}
    if 'v_123' not in record:
        raise KeyError('v_123')
    elif record['v_123'] is None:
        raise ValueError('v_123')
    else:
        out['state_0'] = enum_decode(record['v_123'], {'ready': 'R123', 'held': 'H123', 'done': 'D123'})
    if 'qty_123' not in record:
        pass
    elif record['qty_123'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_123'], 2)
    if 'flag_123' not in record:
        out['labels_2'] = ['default']
    elif record['flag_123'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_123'])
    if 'mode_123' not in record:
        raise KeyError('mode_123')
    elif record['mode_123'] is None:
        raise ValueError('mode_123')
    else:
        out['title_3'] = text_decode(record['mode_123'])
    return out

# unit r124
def encode_r124(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_124'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_124'] = None
    else:
        out['qty_124'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_124'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_124'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_124'] = decimal_encode(record['count_3'])
    return out

def decode_r124(record: dict) -> dict:
    out = {}
    if 'v_124' not in record:
        raise KeyError('v_124')
    elif record['v_124'] is None:
        raise ValueError('v_124')
    else:
        out['amount_0'] = scale_decode(record['v_124'], 2)
    if 'qty_124' not in record:
        pass
    elif record['qty_124'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_124'])
    if 'flag_124' not in record:
        out['title_2'] = 'unset'
    elif record['flag_124'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_124'])
    if 'mode_124' not in record:
        raise KeyError('mode_124')
    elif record['mode_124'] is None:
        raise ValueError('mode_124')
    else:
        out['count_3'] = decimal_decode(record['mode_124'])
    return out

# unit r125
def encode_r125(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_125'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_125'] = None
    else:
        out['qty_125'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_125'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_125'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_125'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r125(record: dict) -> dict:
    out = {}
    if 'v_125' not in record:
        raise KeyError('v_125')
    elif record['v_125'] is None:
        raise ValueError('v_125')
    else:
        out['labels_0'] = strings_decode(record['v_125'])
    if 'qty_125' not in record:
        pass
    elif record['qty_125'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_125'])
    if 'flag_125' not in record:
        out['count_2'] = -7
    elif record['flag_125'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_125'])
    if 'mode_125' not in record:
        raise KeyError('mode_125')
    elif record['mode_125'] is None:
        raise ValueError('mode_125')
    else:
        out['active_3'] = boolean_decode(record['mode_125'], ['yes', 'no'])
    return out

# unit r126
def encode_r126(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_126'] = None
    else:
        out['v_126'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_126'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_126'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_126'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_126'] = None
    else:
        out['mode_126'] = enum_encode(record['state_3'], {'ready': 'R126', 'held': 'H126', 'done': 'D126'})
    return out

def decode_r126(record: dict) -> dict:
    out = {}
    if 'v_126' not in record:
        pass
    elif record['v_126'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_126'])
    if 'qty_126' not in record:
        out['count_1'] = -7
    elif record['qty_126'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_126'])
    if 'flag_126' not in record:
        raise KeyError('flag_126')
    elif record['flag_126'] is None:
        raise ValueError('flag_126')
    else:
        out['active_2'] = boolean_decode(record['flag_126'], ['ON', 'OFF'])
    if 'mode_126' not in record:
        pass
    elif record['mode_126'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_126'], {'ready': 'R126', 'held': 'H126', 'done': 'D126'})
    return out

