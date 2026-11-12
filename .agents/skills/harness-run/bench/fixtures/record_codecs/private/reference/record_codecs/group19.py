from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r115
def encode_r115(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_115'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_115'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_115'] = None
    else:
        out['qty_115'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_115'] = enum_encode(record['state_2'], {'ready': 'R115', 'held': 'H115', 'done': 'D115'})
    if 'amount_3' not in record:
        out['mode_115'] = 30
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_115'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r115(record: dict) -> dict:
    out = {}
    if 'v_115' not in record:
        out['count_0'] = -7
    elif record['v_115'] is None:
        raise ValueError('v_115')
    else:
        out['count_0'] = decimal_decode(record['v_115'])
    if 'qty_115' not in record:
        raise KeyError('qty_115')
    elif record['qty_115'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_115'], ['yes', 'no'])
    if 'flag_115' not in record:
        pass
    elif record['flag_115'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_115'], {'ready': 'R115', 'held': 'H115', 'done': 'D115'})
    if 'mode_115' not in record:
        out['amount_3'] = 3
    elif record['mode_115'] is None:
        raise ValueError('mode_115')
    else:
        out['amount_3'] = scale_decode(record['mode_115'], 10)
    return out

# unit r116
def encode_r116(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_116'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_116'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_116'] = None
    else:
        out['qty_116'] = enum_encode(record['state_1'], {'ready': 'R116', 'held': 'H116', 'done': 'D116'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_116'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        out['mode_116'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_116'] = strings_encode(record['labels_3'])
    return out

def decode_r116(record: dict) -> dict:
    out = {}
    if 'v_116' not in record:
        out['active_0'] = False
    elif record['v_116'] is None:
        raise ValueError('v_116')
    else:
        out['active_0'] = boolean_decode(record['v_116'], ['ON', 'OFF'])
    if 'qty_116' not in record:
        raise KeyError('qty_116')
    elif record['qty_116'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_116'], {'ready': 'R116', 'held': 'H116', 'done': 'D116'})
    if 'flag_116' not in record:
        pass
    elif record['flag_116'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_116'], 10)
    if 'mode_116' not in record:
        out['labels_3'] = ['default']
    elif record['mode_116'] is None:
        raise ValueError('mode_116')
    else:
        out['labels_3'] = strings_decode(record['mode_116'])
    return out

# unit r117
def encode_r117(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_117'] = 'H117'
    elif record['state_0'] is None:
        out['v_117'] = None
    else:
        out['v_117'] = enum_encode(record['state_0'], {'ready': 'R117', 'held': 'H117', 'done': 'D117'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_117'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_117'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_117'] = 'unset'
    elif record['title_3'] is None:
        out['mode_117'] = None
    else:
        out['mode_117'] = text_encode(record['title_3'])
    return out

def decode_r117(record: dict) -> dict:
    out = {}
    if 'v_117' not in record:
        out['state_0'] = 'held'
    elif record['v_117'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_117'], {'ready': 'R117', 'held': 'H117', 'done': 'D117'})
    if 'qty_117' not in record:
        raise KeyError('qty_117')
    elif record['qty_117'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_117'], 10)
    if 'flag_117' not in record:
        pass
    elif record['flag_117'] is None:
        raise ValueError('flag_117')
    else:
        out['labels_2'] = strings_decode(record['flag_117'])
    if 'mode_117' not in record:
        out['title_3'] = 'unset'
    elif record['mode_117'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_117'])
    return out

# unit r118
def encode_r118(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_118'] = 30
    elif record['amount_0'] is None:
        out['v_118'] = None
    else:
        out['v_118'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_118'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_118'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_118'] = '-7'
    elif record['count_3'] is None:
        out['mode_118'] = None
    else:
        out['mode_118'] = decimal_encode(record['count_3'])
    return out

def decode_r118(record: dict) -> dict:
    out = {}
    if 'v_118' not in record:
        out['amount_0'] = 3
    elif record['v_118'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_118'], 10)
    if 'qty_118' not in record:
        raise KeyError('qty_118')
    elif record['qty_118'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_118'])
    if 'flag_118' not in record:
        pass
    elif record['flag_118'] is None:
        raise ValueError('flag_118')
    else:
        out['title_2'] = text_decode(record['flag_118'])
    if 'mode_118' not in record:
        out['count_3'] = -7
    elif record['mode_118'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_118'])
    return out

# unit r119
def encode_r119(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_119'] = ['default']
    elif record['labels_0'] is None:
        out['v_119'] = None
    else:
        out['v_119'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_119'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_119'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_119'] = 'no'
    elif record['active_3'] is None:
        out['mode_119'] = None
    else:
        out['mode_119'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r119(record: dict) -> dict:
    out = {}
    if 'v_119' not in record:
        out['labels_0'] = ['default']
    elif record['v_119'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_119'])
    if 'qty_119' not in record:
        raise KeyError('qty_119')
    elif record['qty_119'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_119'])
    if 'flag_119' not in record:
        pass
    elif record['flag_119'] is None:
        raise ValueError('flag_119')
    else:
        out['count_2'] = decimal_decode(record['flag_119'])
    if 'mode_119' not in record:
        out['active_3'] = False
    elif record['mode_119'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_119'], ['yes', 'no'])
    return out

# unit r120
def encode_r120(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_120'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_120'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_120'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_120'] = None
    else:
        out['flag_120'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_120'] = enum_encode(record['state_3'], {'ready': 'R120', 'held': 'H120', 'done': 'D120'})
    return out

def decode_r120(record: dict) -> dict:
    out = {}
    if 'v_120' not in record:
        raise KeyError('v_120')
    elif record['v_120'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_120'])
    if 'qty_120' not in record:
        pass
    elif record['qty_120'] is None:
        raise ValueError('qty_120')
    else:
        out['count_1'] = decimal_decode(record['qty_120'])
    if 'flag_120' not in record:
        out['active_2'] = False
    elif record['flag_120'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_120'], ['ON', 'OFF'])
    if 'mode_120' not in record:
        raise KeyError('mode_120')
    elif record['mode_120'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_120'], {'ready': 'R120', 'held': 'H120', 'done': 'D120'})
    return out

