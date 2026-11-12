from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r013
def encode_r013(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_013'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_013'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_013'] = 'H13'
    elif record['state_2'] is None:
        out['flag_013'] = None
    else:
        out['flag_013'] = enum_encode(record['state_2'], {'ready': 'R13', 'held': 'H13', 'done': 'D13'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_013'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r013(record: dict) -> dict:
    out = {}
    if 'v_013' not in record:
        raise KeyError('v_013')
    elif record['v_013'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_013'])
    if 'qty_013' not in record:
        pass
    elif record['qty_013'] is None:
        raise ValueError('qty_013')
    else:
        out['active_1'] = boolean_decode(record['qty_013'], ['yes', 'no'])
    if 'flag_013' not in record:
        out['state_2'] = 'held'
    elif record['flag_013'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_013'], {'ready': 'R13', 'held': 'H13', 'done': 'D13'})
    if 'mode_013' not in record:
        raise KeyError('mode_013')
    elif record['mode_013'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_013'], 2)
    return out

# unit r014
def encode_r014(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_014'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_014'] = enum_encode(record['state_1'], {'ready': 'R14', 'held': 'H14', 'done': 'D14'})
    if 'amount_2' not in record:
        out['flag_014'] = 6
    elif record['amount_2'] is None:
        out['flag_014'] = None
    else:
        out['flag_014'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_014'] = strings_encode(record['labels_3'])
    return out

def decode_r014(record: dict) -> dict:
    out = {}
    if 'v_014' not in record:
        raise KeyError('v_014')
    elif record['v_014'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_014'], ['ON', 'OFF'])
    if 'qty_014' not in record:
        pass
    elif record['qty_014'] is None:
        raise ValueError('qty_014')
    else:
        out['state_1'] = enum_decode(record['qty_014'], {'ready': 'R14', 'held': 'H14', 'done': 'D14'})
    if 'flag_014' not in record:
        out['amount_2'] = 3
    elif record['flag_014'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_014'], 2)
    if 'mode_014' not in record:
        raise KeyError('mode_014')
    elif record['mode_014'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_014'])
    return out

# unit r015
def encode_r015(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_015'] = enum_encode(record['state_0'], {'ready': 'R15', 'held': 'H15', 'done': 'D15'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_015'] = None
    else:
        out['qty_015'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        out['flag_015'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_015'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_015'] = text_encode(record['title_3'])
    return out

def decode_r015(record: dict) -> dict:
    out = {}
    if 'v_015' not in record:
        raise KeyError('v_015')
    elif record['v_015'] is None:
        raise ValueError('v_015')
    else:
        out['state_0'] = enum_decode(record['v_015'], {'ready': 'R15', 'held': 'H15', 'done': 'D15'})
    if 'qty_015' not in record:
        pass
    elif record['qty_015'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_015'], 2)
    if 'flag_015' not in record:
        out['labels_2'] = ['default']
    elif record['flag_015'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_015'])
    if 'mode_015' not in record:
        raise KeyError('mode_015')
    elif record['mode_015'] is None:
        raise ValueError('mode_015')
    else:
        out['title_3'] = text_decode(record['mode_015'])
    return out

# unit r016
def encode_r016(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_016'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_016'] = None
    else:
        out['qty_016'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_016'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_016'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_016'] = decimal_encode(record['count_3'])
    return out

def decode_r016(record: dict) -> dict:
    out = {}
    if 'v_016' not in record:
        raise KeyError('v_016')
    elif record['v_016'] is None:
        raise ValueError('v_016')
    else:
        out['amount_0'] = scale_decode(record['v_016'], 2)
    if 'qty_016' not in record:
        pass
    elif record['qty_016'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_016'])
    if 'flag_016' not in record:
        out['title_2'] = 'unset'
    elif record['flag_016'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_016'])
    if 'mode_016' not in record:
        raise KeyError('mode_016')
    elif record['mode_016'] is None:
        raise ValueError('mode_016')
    else:
        out['count_3'] = decimal_decode(record['mode_016'])
    return out

# unit r017
def encode_r017(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_017'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_017'] = None
    else:
        out['qty_017'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_017'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_017'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_017'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r017(record: dict) -> dict:
    out = {}
    if 'v_017' not in record:
        raise KeyError('v_017')
    elif record['v_017'] is None:
        raise ValueError('v_017')
    else:
        out['labels_0'] = strings_decode(record['v_017'])
    if 'qty_017' not in record:
        pass
    elif record['qty_017'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_017'])
    if 'flag_017' not in record:
        out['count_2'] = -7
    elif record['flag_017'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_017'])
    if 'mode_017' not in record:
        raise KeyError('mode_017')
    elif record['mode_017'] is None:
        raise ValueError('mode_017')
    else:
        out['active_3'] = boolean_decode(record['mode_017'], ['yes', 'no'])
    return out

# unit r018
def encode_r018(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_018'] = None
    else:
        out['v_018'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_018'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_018'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_018'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_018'] = None
    else:
        out['mode_018'] = enum_encode(record['state_3'], {'ready': 'R18', 'held': 'H18', 'done': 'D18'})
    return out

def decode_r018(record: dict) -> dict:
    out = {}
    if 'v_018' not in record:
        pass
    elif record['v_018'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_018'])
    if 'qty_018' not in record:
        out['count_1'] = -7
    elif record['qty_018'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_018'])
    if 'flag_018' not in record:
        raise KeyError('flag_018')
    elif record['flag_018'] is None:
        raise ValueError('flag_018')
    else:
        out['active_2'] = boolean_decode(record['flag_018'], ['ON', 'OFF'])
    if 'mode_018' not in record:
        pass
    elif record['mode_018'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_018'], {'ready': 'R18', 'held': 'H18', 'done': 'D18'})
    return out

