from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r019
def encode_r019(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_019'] = None
    else:
        out['v_019'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_019'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_019'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_019'] = enum_encode(record['state_2'], {'ready': 'R19', 'held': 'H19', 'done': 'D19'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_019'] = None
    else:
        out['mode_019'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r019(record: dict) -> dict:
    out = {}
    if 'v_019' not in record:
        pass
    elif record['v_019'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_019'])
    if 'qty_019' not in record:
        out['active_1'] = False
    elif record['qty_019'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_019'], ['yes', 'no'])
    if 'flag_019' not in record:
        raise KeyError('flag_019')
    elif record['flag_019'] is None:
        raise ValueError('flag_019')
    else:
        out['state_2'] = enum_decode(record['flag_019'], {'ready': 'R19', 'held': 'H19', 'done': 'D19'})
    if 'mode_019' not in record:
        pass
    elif record['mode_019'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_019'], 10)
    return out

# unit r020
def encode_r020(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_020'] = None
    else:
        out['v_020'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_020'] = 'H20'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_020'] = enum_encode(record['state_1'], {'ready': 'R20', 'held': 'H20', 'done': 'D20'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_020'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_020'] = None
    else:
        out['mode_020'] = strings_encode(record['labels_3'])
    return out

def decode_r020(record: dict) -> dict:
    out = {}
    if 'v_020' not in record:
        pass
    elif record['v_020'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_020'], ['ON', 'OFF'])
    if 'qty_020' not in record:
        out['state_1'] = 'held'
    elif record['qty_020'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_020'], {'ready': 'R20', 'held': 'H20', 'done': 'D20'})
    if 'flag_020' not in record:
        raise KeyError('flag_020')
    elif record['flag_020'] is None:
        raise ValueError('flag_020')
    else:
        out['amount_2'] = scale_decode(record['flag_020'], 10)
    if 'mode_020' not in record:
        pass
    elif record['mode_020'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_020'])
    return out

# unit r021
def encode_r021(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_021'] = enum_encode(record['state_0'], {'ready': 'R21', 'held': 'H21', 'done': 'D21'})
    if 'amount_1' not in record:
        out['qty_021'] = 30
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_021'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_021'] = None
    else:
        out['flag_021'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_021'] = text_encode(record['title_3'])
    return out

def decode_r021(record: dict) -> dict:
    out = {}
    if 'v_021' not in record:
        pass
    elif record['v_021'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_021'], {'ready': 'R21', 'held': 'H21', 'done': 'D21'})
    if 'qty_021' not in record:
        out['amount_1'] = 3
    elif record['qty_021'] is None:
        raise ValueError('qty_021')
    else:
        out['amount_1'] = scale_decode(record['qty_021'], 10)
    if 'flag_021' not in record:
        raise KeyError('flag_021')
    elif record['flag_021'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_021'])
    if 'mode_021' not in record:
        pass
    elif record['mode_021'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_021'])
    return out

# unit r022
def encode_r022(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_022'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        out['qty_022'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_022'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_022'] = None
    else:
        out['flag_022'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_022'] = decimal_encode(record['count_3'])
    return out

def decode_r022(record: dict) -> dict:
    out = {}
    if 'v_022' not in record:
        pass
    elif record['v_022'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_022'], 10)
    if 'qty_022' not in record:
        out['labels_1'] = ['default']
    elif record['qty_022'] is None:
        raise ValueError('qty_022')
    else:
        out['labels_1'] = strings_decode(record['qty_022'])
    if 'flag_022' not in record:
        raise KeyError('flag_022')
    elif record['flag_022'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_022'])
    if 'mode_022' not in record:
        pass
    elif record['mode_022'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_022'])
    return out

# unit r023
def encode_r023(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_023'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_023'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_023'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_023'] = None
    else:
        out['flag_023'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_023'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r023(record: dict) -> dict:
    out = {}
    if 'v_023' not in record:
        pass
    elif record['v_023'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_023'])
    if 'qty_023' not in record:
        out['title_1'] = 'unset'
    elif record['qty_023'] is None:
        raise ValueError('qty_023')
    else:
        out['title_1'] = text_decode(record['qty_023'])
    if 'flag_023' not in record:
        raise KeyError('flag_023')
    elif record['flag_023'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_023'])
    if 'mode_023' not in record:
        pass
    elif record['mode_023'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_023'], ['yes', 'no'])
    return out

# unit r024
def encode_r024(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_024'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_024'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_024'] = None
    else:
        out['qty_024'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_024'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_024'] = 'H24'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_024'] = enum_encode(record['state_3'], {'ready': 'R24', 'held': 'H24', 'done': 'D24'})
    return out

def decode_r024(record: dict) -> dict:
    out = {}
    if 'v_024' not in record:
        out['title_0'] = 'unset'
    elif record['v_024'] is None:
        raise ValueError('v_024')
    else:
        out['title_0'] = text_decode(record['v_024'])
    if 'qty_024' not in record:
        raise KeyError('qty_024')
    elif record['qty_024'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_024'])
    if 'flag_024' not in record:
        pass
    elif record['flag_024'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_024'], ['ON', 'OFF'])
    if 'mode_024' not in record:
        out['state_3'] = 'held'
    elif record['mode_024'] is None:
        raise ValueError('mode_024')
    else:
        out['state_3'] = enum_decode(record['mode_024'], {'ready': 'R24', 'held': 'H24', 'done': 'D24'})
    return out

