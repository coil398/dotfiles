from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r085
def encode_r085(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_085'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_085'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_085'] = 'H85'
    elif record['state_2'] is None:
        out['flag_085'] = None
    else:
        out['flag_085'] = enum_encode(record['state_2'], {'ready': 'R85', 'held': 'H85', 'done': 'D85'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_085'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r085(record: dict) -> dict:
    out = {}
    if 'v_085' not in record:
        raise KeyError('v_085')
    elif record['v_085'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_085'])
    if 'qty_085' not in record:
        pass
    elif record['qty_085'] is None:
        raise ValueError('qty_085')
    else:
        out['active_1'] = boolean_decode(record['qty_085'], ['yes', 'no'])
    if 'flag_085' not in record:
        out['state_2'] = 'held'
    elif record['flag_085'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_085'], {'ready': 'R85', 'held': 'H85', 'done': 'D85'})
    if 'mode_085' not in record:
        raise KeyError('mode_085')
    elif record['mode_085'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_085'], 2)
    return out

# unit r086
def encode_r086(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_086'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_086'] = enum_encode(record['state_1'], {'ready': 'R86', 'held': 'H86', 'done': 'D86'})
    if 'amount_2' not in record:
        out['flag_086'] = 6
    elif record['amount_2'] is None:
        out['flag_086'] = None
    else:
        out['flag_086'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_086'] = strings_encode(record['labels_3'])
    return out

def decode_r086(record: dict) -> dict:
    out = {}
    if 'v_086' not in record:
        raise KeyError('v_086')
    elif record['v_086'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_086'], ['ON', 'OFF'])
    if 'qty_086' not in record:
        pass
    elif record['qty_086'] is None:
        raise ValueError('qty_086')
    else:
        out['state_1'] = enum_decode(record['qty_086'], {'ready': 'R86', 'held': 'H86', 'done': 'D86'})
    if 'flag_086' not in record:
        out['amount_2'] = 3
    elif record['flag_086'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_086'], 2)
    if 'mode_086' not in record:
        raise KeyError('mode_086')
    elif record['mode_086'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_086'])
    return out

# unit r087
def encode_r087(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_087'] = enum_encode(record['state_0'], {'ready': 'R87', 'held': 'H87', 'done': 'D87'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_087'] = None
    else:
        out['qty_087'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        out['flag_087'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_087'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_087'] = text_encode(record['title_3'])
    return out

def decode_r087(record: dict) -> dict:
    out = {}
    if 'v_087' not in record:
        raise KeyError('v_087')
    elif record['v_087'] is None:
        raise ValueError('v_087')
    else:
        out['state_0'] = enum_decode(record['v_087'], {'ready': 'R87', 'held': 'H87', 'done': 'D87'})
    if 'qty_087' not in record:
        pass
    elif record['qty_087'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_087'], 2)
    if 'flag_087' not in record:
        out['labels_2'] = ['default']
    elif record['flag_087'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_087'])
    if 'mode_087' not in record:
        raise KeyError('mode_087')
    elif record['mode_087'] is None:
        raise ValueError('mode_087')
    else:
        out['title_3'] = text_decode(record['mode_087'])
    return out

# unit r088
def encode_r088(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_088'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_088'] = None
    else:
        out['qty_088'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_088'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_088'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_088'] = decimal_encode(record['count_3'])
    return out

def decode_r088(record: dict) -> dict:
    out = {}
    if 'v_088' not in record:
        raise KeyError('v_088')
    elif record['v_088'] is None:
        raise ValueError('v_088')
    else:
        out['amount_0'] = scale_decode(record['v_088'], 2)
    if 'qty_088' not in record:
        pass
    elif record['qty_088'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_088'])
    if 'flag_088' not in record:
        out['title_2'] = 'unset'
    elif record['flag_088'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_088'])
    if 'mode_088' not in record:
        raise KeyError('mode_088')
    elif record['mode_088'] is None:
        raise ValueError('mode_088')
    else:
        out['count_3'] = decimal_decode(record['mode_088'])
    return out

# unit r089
def encode_r089(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_089'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_089'] = None
    else:
        out['qty_089'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_089'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_089'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_089'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r089(record: dict) -> dict:
    out = {}
    if 'v_089' not in record:
        raise KeyError('v_089')
    elif record['v_089'] is None:
        raise ValueError('v_089')
    else:
        out['labels_0'] = strings_decode(record['v_089'])
    if 'qty_089' not in record:
        pass
    elif record['qty_089'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_089'])
    if 'flag_089' not in record:
        out['count_2'] = -7
    elif record['flag_089'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_089'])
    if 'mode_089' not in record:
        raise KeyError('mode_089')
    elif record['mode_089'] is None:
        raise ValueError('mode_089')
    else:
        out['active_3'] = boolean_decode(record['mode_089'], ['yes', 'no'])
    return out

# unit r090
def encode_r090(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_090'] = None
    else:
        out['v_090'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_090'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_090'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_090'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_090'] = None
    else:
        out['mode_090'] = enum_encode(record['state_3'], {'ready': 'R90', 'held': 'H90', 'done': 'D90'})
    return out

def decode_r090(record: dict) -> dict:
    out = {}
    if 'v_090' not in record:
        pass
    elif record['v_090'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_090'])
    if 'qty_090' not in record:
        out['count_1'] = -7
    elif record['qty_090'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_090'])
    if 'flag_090' not in record:
        raise KeyError('flag_090')
    elif record['flag_090'] is None:
        raise ValueError('flag_090')
    else:
        out['active_2'] = boolean_decode(record['flag_090'], ['ON', 'OFF'])
    if 'mode_090' not in record:
        pass
    elif record['mode_090'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_090'], {'ready': 'R90', 'held': 'H90', 'done': 'D90'})
    return out

