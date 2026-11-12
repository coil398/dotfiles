from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r007
def encode_r007(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_007'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_007'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_007'] = None
    else:
        out['qty_007'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_007'] = enum_encode(record['state_2'], {'ready': 'R7', 'held': 'H7', 'done': 'D7'})
    if 'amount_3' not in record:
        out['mode_007'] = 30
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_007'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r007(record: dict) -> dict:
    out = {}
    if 'v_007' not in record:
        out['count_0'] = -7
    elif record['v_007'] is None:
        raise ValueError('v_007')
    else:
        out['count_0'] = decimal_decode(record['v_007'])
    if 'qty_007' not in record:
        raise KeyError('qty_007')
    elif record['qty_007'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_007'], ['yes', 'no'])
    if 'flag_007' not in record:
        pass
    elif record['flag_007'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_007'], {'ready': 'R7', 'held': 'H7', 'done': 'D7'})
    if 'mode_007' not in record:
        out['amount_3'] = 3
    elif record['mode_007'] is None:
        raise ValueError('mode_007')
    else:
        out['amount_3'] = scale_decode(record['mode_007'], 10)
    return out

# unit r008
def encode_r008(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_008'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_008'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_008'] = None
    else:
        out['qty_008'] = enum_encode(record['state_1'], {'ready': 'R8', 'held': 'H8', 'done': 'D8'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_008'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        out['mode_008'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_008'] = strings_encode(record['labels_3'])
    return out

def decode_r008(record: dict) -> dict:
    out = {}
    if 'v_008' not in record:
        out['active_0'] = False
    elif record['v_008'] is None:
        raise ValueError('v_008')
    else:
        out['active_0'] = boolean_decode(record['v_008'], ['ON', 'OFF'])
    if 'qty_008' not in record:
        raise KeyError('qty_008')
    elif record['qty_008'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_008'], {'ready': 'R8', 'held': 'H8', 'done': 'D8'})
    if 'flag_008' not in record:
        pass
    elif record['flag_008'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_008'], 10)
    if 'mode_008' not in record:
        out['labels_3'] = ['default']
    elif record['mode_008'] is None:
        raise ValueError('mode_008')
    else:
        out['labels_3'] = strings_decode(record['mode_008'])
    return out

# unit r009
def encode_r009(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_009'] = 'H9'
    elif record['state_0'] is None:
        out['v_009'] = None
    else:
        out['v_009'] = enum_encode(record['state_0'], {'ready': 'R9', 'held': 'H9', 'done': 'D9'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_009'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_009'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_009'] = 'unset'
    elif record['title_3'] is None:
        out['mode_009'] = None
    else:
        out['mode_009'] = text_encode(record['title_3'])
    return out

def decode_r009(record: dict) -> dict:
    out = {}
    if 'v_009' not in record:
        out['state_0'] = 'held'
    elif record['v_009'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_009'], {'ready': 'R9', 'held': 'H9', 'done': 'D9'})
    if 'qty_009' not in record:
        raise KeyError('qty_009')
    elif record['qty_009'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_009'], 10)
    if 'flag_009' not in record:
        pass
    elif record['flag_009'] is None:
        raise ValueError('flag_009')
    else:
        out['labels_2'] = strings_decode(record['flag_009'])
    if 'mode_009' not in record:
        out['title_3'] = 'unset'
    elif record['mode_009'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_009'])
    return out

# unit r010
def encode_r010(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_010'] = 30
    elif record['amount_0'] is None:
        out['v_010'] = None
    else:
        out['v_010'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_010'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_010'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_010'] = '-7'
    elif record['count_3'] is None:
        out['mode_010'] = None
    else:
        out['mode_010'] = decimal_encode(record['count_3'])
    return out

def decode_r010(record: dict) -> dict:
    out = {}
    if 'v_010' not in record:
        out['amount_0'] = 3
    elif record['v_010'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_010'], 10)
    if 'qty_010' not in record:
        raise KeyError('qty_010')
    elif record['qty_010'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_010'])
    if 'flag_010' not in record:
        pass
    elif record['flag_010'] is None:
        raise ValueError('flag_010')
    else:
        out['title_2'] = text_decode(record['flag_010'])
    if 'mode_010' not in record:
        out['count_3'] = -7
    elif record['mode_010'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_010'])
    return out

# unit r011
def encode_r011(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_011'] = ['default']
    elif record['labels_0'] is None:
        out['v_011'] = None
    else:
        out['v_011'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_011'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_011'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_011'] = 'no'
    elif record['active_3'] is None:
        out['mode_011'] = None
    else:
        out['mode_011'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r011(record: dict) -> dict:
    out = {}
    if 'v_011' not in record:
        out['labels_0'] = ['default']
    elif record['v_011'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_011'])
    if 'qty_011' not in record:
        raise KeyError('qty_011')
    elif record['qty_011'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_011'])
    if 'flag_011' not in record:
        pass
    elif record['flag_011'] is None:
        raise ValueError('flag_011')
    else:
        out['count_2'] = decimal_decode(record['flag_011'])
    if 'mode_011' not in record:
        out['active_3'] = False
    elif record['mode_011'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_011'], ['yes', 'no'])
    return out

# unit r012
def encode_r012(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_012'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_012'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_012'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_012'] = None
    else:
        out['flag_012'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_012'] = enum_encode(record['state_3'], {'ready': 'R12', 'held': 'H12', 'done': 'D12'})
    return out

def decode_r012(record: dict) -> dict:
    out = {}
    if 'v_012' not in record:
        raise KeyError('v_012')
    elif record['v_012'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_012'])
    if 'qty_012' not in record:
        pass
    elif record['qty_012'] is None:
        raise ValueError('qty_012')
    else:
        out['count_1'] = decimal_decode(record['qty_012'])
    if 'flag_012' not in record:
        out['active_2'] = False
    elif record['flag_012'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_012'], ['ON', 'OFF'])
    if 'mode_012' not in record:
        raise KeyError('mode_012')
    elif record['mode_012'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_012'], {'ready': 'R12', 'held': 'H12', 'done': 'D12'})
    return out

