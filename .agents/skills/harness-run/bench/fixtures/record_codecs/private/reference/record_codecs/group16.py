from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r097
def encode_r097(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_097'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_097'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_097'] = None
    else:
        out['qty_097'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_097'] = enum_encode(record['state_2'], {'ready': 'R97', 'held': 'H97', 'done': 'D97'})
    if 'amount_3' not in record:
        out['mode_097'] = 6
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_097'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r097(record: dict) -> dict:
    out = {}
    if 'v_097' not in record:
        out['count_0'] = -7
    elif record['v_097'] is None:
        raise ValueError('v_097')
    else:
        out['count_0'] = decimal_decode(record['v_097'])
    if 'qty_097' not in record:
        raise KeyError('qty_097')
    elif record['qty_097'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_097'], ['yes', 'no'])
    if 'flag_097' not in record:
        pass
    elif record['flag_097'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_097'], {'ready': 'R97', 'held': 'H97', 'done': 'D97'})
    if 'mode_097' not in record:
        out['amount_3'] = 3
    elif record['mode_097'] is None:
        raise ValueError('mode_097')
    else:
        out['amount_3'] = scale_decode(record['mode_097'], 2)
    return out

# unit r098
def encode_r098(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_098'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_098'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_098'] = None
    else:
        out['qty_098'] = enum_encode(record['state_1'], {'ready': 'R98', 'held': 'H98', 'done': 'D98'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_098'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        out['mode_098'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_098'] = strings_encode(record['labels_3'])
    return out

def decode_r098(record: dict) -> dict:
    out = {}
    if 'v_098' not in record:
        out['active_0'] = False
    elif record['v_098'] is None:
        raise ValueError('v_098')
    else:
        out['active_0'] = boolean_decode(record['v_098'], ['ON', 'OFF'])
    if 'qty_098' not in record:
        raise KeyError('qty_098')
    elif record['qty_098'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_098'], {'ready': 'R98', 'held': 'H98', 'done': 'D98'})
    if 'flag_098' not in record:
        pass
    elif record['flag_098'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_098'], 2)
    if 'mode_098' not in record:
        out['labels_3'] = ['default']
    elif record['mode_098'] is None:
        raise ValueError('mode_098')
    else:
        out['labels_3'] = strings_decode(record['mode_098'])
    return out

# unit r099
def encode_r099(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_099'] = 'H99'
    elif record['state_0'] is None:
        out['v_099'] = None
    else:
        out['v_099'] = enum_encode(record['state_0'], {'ready': 'R99', 'held': 'H99', 'done': 'D99'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_099'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_099'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_099'] = 'unset'
    elif record['title_3'] is None:
        out['mode_099'] = None
    else:
        out['mode_099'] = text_encode(record['title_3'])
    return out

def decode_r099(record: dict) -> dict:
    out = {}
    if 'v_099' not in record:
        out['state_0'] = 'held'
    elif record['v_099'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_099'], {'ready': 'R99', 'held': 'H99', 'done': 'D99'})
    if 'qty_099' not in record:
        raise KeyError('qty_099')
    elif record['qty_099'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_099'], 2)
    if 'flag_099' not in record:
        pass
    elif record['flag_099'] is None:
        raise ValueError('flag_099')
    else:
        out['labels_2'] = strings_decode(record['flag_099'])
    if 'mode_099' not in record:
        out['title_3'] = 'unset'
    elif record['mode_099'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_099'])
    return out

# unit r100
def encode_r100(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_100'] = 6
    elif record['amount_0'] is None:
        out['v_100'] = None
    else:
        out['v_100'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_100'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_100'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_100'] = '-7'
    elif record['count_3'] is None:
        out['mode_100'] = None
    else:
        out['mode_100'] = decimal_encode(record['count_3'])
    return out

def decode_r100(record: dict) -> dict:
    out = {}
    if 'v_100' not in record:
        out['amount_0'] = 3
    elif record['v_100'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_100'], 2)
    if 'qty_100' not in record:
        raise KeyError('qty_100')
    elif record['qty_100'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_100'])
    if 'flag_100' not in record:
        pass
    elif record['flag_100'] is None:
        raise ValueError('flag_100')
    else:
        out['title_2'] = text_decode(record['flag_100'])
    if 'mode_100' not in record:
        out['count_3'] = -7
    elif record['mode_100'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_100'])
    return out

# unit r101
def encode_r101(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_101'] = ['default']
    elif record['labels_0'] is None:
        out['v_101'] = None
    else:
        out['v_101'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_101'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_101'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_101'] = 'no'
    elif record['active_3'] is None:
        out['mode_101'] = None
    else:
        out['mode_101'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r101(record: dict) -> dict:
    out = {}
    if 'v_101' not in record:
        out['labels_0'] = ['default']
    elif record['v_101'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_101'])
    if 'qty_101' not in record:
        raise KeyError('qty_101')
    elif record['qty_101'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_101'])
    if 'flag_101' not in record:
        pass
    elif record['flag_101'] is None:
        raise ValueError('flag_101')
    else:
        out['count_2'] = decimal_decode(record['flag_101'])
    if 'mode_101' not in record:
        out['active_3'] = False
    elif record['mode_101'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_101'], ['yes', 'no'])
    return out

# unit r102
def encode_r102(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_102'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_102'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_102'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_102'] = None
    else:
        out['flag_102'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_102'] = enum_encode(record['state_3'], {'ready': 'R102', 'held': 'H102', 'done': 'D102'})
    return out

def decode_r102(record: dict) -> dict:
    out = {}
    if 'v_102' not in record:
        raise KeyError('v_102')
    elif record['v_102'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_102'])
    if 'qty_102' not in record:
        pass
    elif record['qty_102'] is None:
        raise ValueError('qty_102')
    else:
        out['count_1'] = decimal_decode(record['qty_102'])
    if 'flag_102' not in record:
        out['active_2'] = False
    elif record['flag_102'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_102'], ['ON', 'OFF'])
    if 'mode_102' not in record:
        raise KeyError('mode_102')
    elif record['mode_102'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_102'], {'ready': 'R102', 'held': 'H102', 'done': 'D102'})
    return out

