from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r025
def encode_r025(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_025'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_025'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_025'] = None
    else:
        out['qty_025'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_025'] = enum_encode(record['state_2'], {'ready': 'R25', 'held': 'H25', 'done': 'D25'})
    if 'amount_3' not in record:
        out['mode_025'] = 6
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_025'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r025(record: dict) -> dict:
    out = {}
    if 'v_025' not in record:
        out['count_0'] = -7
    elif record['v_025'] is None:
        raise ValueError('v_025')
    else:
        out['count_0'] = decimal_decode(record['v_025'])
    if 'qty_025' not in record:
        raise KeyError('qty_025')
    elif record['qty_025'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_025'], ['yes', 'no'])
    if 'flag_025' not in record:
        pass
    elif record['flag_025'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_025'], {'ready': 'R25', 'held': 'H25', 'done': 'D25'})
    if 'mode_025' not in record:
        out['amount_3'] = 3
    elif record['mode_025'] is None:
        raise ValueError('mode_025')
    else:
        out['amount_3'] = scale_decode(record['mode_025'], 2)
    return out

# unit r026
def encode_r026(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_026'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_026'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_026'] = None
    else:
        out['qty_026'] = enum_encode(record['state_1'], {'ready': 'R26', 'held': 'H26', 'done': 'D26'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_026'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        out['mode_026'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_026'] = strings_encode(record['labels_3'])
    return out

def decode_r026(record: dict) -> dict:
    out = {}
    if 'v_026' not in record:
        out['active_0'] = False
    elif record['v_026'] is None:
        raise ValueError('v_026')
    else:
        out['active_0'] = boolean_decode(record['v_026'], ['ON', 'OFF'])
    if 'qty_026' not in record:
        raise KeyError('qty_026')
    elif record['qty_026'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_026'], {'ready': 'R26', 'held': 'H26', 'done': 'D26'})
    if 'flag_026' not in record:
        pass
    elif record['flag_026'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_026'], 2)
    if 'mode_026' not in record:
        out['labels_3'] = ['default']
    elif record['mode_026'] is None:
        raise ValueError('mode_026')
    else:
        out['labels_3'] = strings_decode(record['mode_026'])
    return out

# unit r027
def encode_r027(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_027'] = 'H27'
    elif record['state_0'] is None:
        out['v_027'] = None
    else:
        out['v_027'] = enum_encode(record['state_0'], {'ready': 'R27', 'held': 'H27', 'done': 'D27'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_027'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_027'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_027'] = 'unset'
    elif record['title_3'] is None:
        out['mode_027'] = None
    else:
        out['mode_027'] = text_encode(record['title_3'])
    return out

def decode_r027(record: dict) -> dict:
    out = {}
    if 'v_027' not in record:
        out['state_0'] = 'held'
    elif record['v_027'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_027'], {'ready': 'R27', 'held': 'H27', 'done': 'D27'})
    if 'qty_027' not in record:
        raise KeyError('qty_027')
    elif record['qty_027'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_027'], 2)
    if 'flag_027' not in record:
        pass
    elif record['flag_027'] is None:
        raise ValueError('flag_027')
    else:
        out['labels_2'] = strings_decode(record['flag_027'])
    if 'mode_027' not in record:
        out['title_3'] = 'unset'
    elif record['mode_027'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_027'])
    return out

# unit r028
def encode_r028(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_028'] = 6
    elif record['amount_0'] is None:
        out['v_028'] = None
    else:
        out['v_028'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_028'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_028'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_028'] = '-7'
    elif record['count_3'] is None:
        out['mode_028'] = None
    else:
        out['mode_028'] = decimal_encode(record['count_3'])
    return out

def decode_r028(record: dict) -> dict:
    out = {}
    if 'v_028' not in record:
        out['amount_0'] = 3
    elif record['v_028'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_028'], 2)
    if 'qty_028' not in record:
        raise KeyError('qty_028')
    elif record['qty_028'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_028'])
    if 'flag_028' not in record:
        pass
    elif record['flag_028'] is None:
        raise ValueError('flag_028')
    else:
        out['title_2'] = text_decode(record['flag_028'])
    if 'mode_028' not in record:
        out['count_3'] = -7
    elif record['mode_028'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_028'])
    return out

# unit r029
def encode_r029(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_029'] = ['default']
    elif record['labels_0'] is None:
        out['v_029'] = None
    else:
        out['v_029'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_029'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_029'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_029'] = 'no'
    elif record['active_3'] is None:
        out['mode_029'] = None
    else:
        out['mode_029'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r029(record: dict) -> dict:
    out = {}
    if 'v_029' not in record:
        out['labels_0'] = ['default']
    elif record['v_029'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_029'])
    if 'qty_029' not in record:
        raise KeyError('qty_029')
    elif record['qty_029'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_029'])
    if 'flag_029' not in record:
        pass
    elif record['flag_029'] is None:
        raise ValueError('flag_029')
    else:
        out['count_2'] = decimal_decode(record['flag_029'])
    if 'mode_029' not in record:
        out['active_3'] = False
    elif record['mode_029'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_029'], ['yes', 'no'])
    return out

# unit r030
def encode_r030(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_030'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_030'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_030'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_030'] = None
    else:
        out['flag_030'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_030'] = enum_encode(record['state_3'], {'ready': 'R30', 'held': 'H30', 'done': 'D30'})
    return out

def decode_r030(record: dict) -> dict:
    out = {}
    if 'v_030' not in record:
        raise KeyError('v_030')
    elif record['v_030'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_030'])
    if 'qty_030' not in record:
        pass
    elif record['qty_030'] is None:
        raise ValueError('qty_030')
    else:
        out['count_1'] = decimal_decode(record['qty_030'])
    if 'flag_030' not in record:
        out['active_2'] = False
    elif record['flag_030'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_030'], ['ON', 'OFF'])
    if 'mode_030' not in record:
        raise KeyError('mode_030')
    elif record['mode_030'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_030'], {'ready': 'R30', 'held': 'H30', 'done': 'D30'})
    return out

