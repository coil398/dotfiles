from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r079
def encode_r079(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_079'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_079'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_079'] = None
    else:
        out['qty_079'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_079'] = enum_encode(record['state_2'], {'ready': 'R79', 'held': 'H79', 'done': 'D79'})
    if 'amount_3' not in record:
        out['mode_079'] = 30
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_079'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r079(record: dict) -> dict:
    out = {}
    if 'v_079' not in record:
        out['count_0'] = -7
    elif record['v_079'] is None:
        raise ValueError('v_079')
    else:
        out['count_0'] = decimal_decode(record['v_079'])
    if 'qty_079' not in record:
        raise KeyError('qty_079')
    elif record['qty_079'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_079'], ['yes', 'no'])
    if 'flag_079' not in record:
        pass
    elif record['flag_079'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_079'], {'ready': 'R79', 'held': 'H79', 'done': 'D79'})
    if 'mode_079' not in record:
        out['amount_3'] = 3
    elif record['mode_079'] is None:
        raise ValueError('mode_079')
    else:
        out['amount_3'] = scale_decode(record['mode_079'], 10)
    return out

# unit r080
def encode_r080(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_080'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_080'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_080'] = None
    else:
        out['qty_080'] = enum_encode(record['state_1'], {'ready': 'R80', 'held': 'H80', 'done': 'D80'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_080'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        out['mode_080'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_080'] = strings_encode(record['labels_3'])
    return out

def decode_r080(record: dict) -> dict:
    out = {}
    if 'v_080' not in record:
        out['active_0'] = False
    elif record['v_080'] is None:
        raise ValueError('v_080')
    else:
        out['active_0'] = boolean_decode(record['v_080'], ['ON', 'OFF'])
    if 'qty_080' not in record:
        raise KeyError('qty_080')
    elif record['qty_080'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_080'], {'ready': 'R80', 'held': 'H80', 'done': 'D80'})
    if 'flag_080' not in record:
        pass
    elif record['flag_080'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_080'], 10)
    if 'mode_080' not in record:
        out['labels_3'] = ['default']
    elif record['mode_080'] is None:
        raise ValueError('mode_080')
    else:
        out['labels_3'] = strings_decode(record['mode_080'])
    return out

# unit r081
def encode_r081(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_081'] = 'H81'
    elif record['state_0'] is None:
        out['v_081'] = None
    else:
        out['v_081'] = enum_encode(record['state_0'], {'ready': 'R81', 'held': 'H81', 'done': 'D81'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_081'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_081'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_081'] = 'unset'
    elif record['title_3'] is None:
        out['mode_081'] = None
    else:
        out['mode_081'] = text_encode(record['title_3'])
    return out

def decode_r081(record: dict) -> dict:
    out = {}
    if 'v_081' not in record:
        out['state_0'] = 'held'
    elif record['v_081'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_081'], {'ready': 'R81', 'held': 'H81', 'done': 'D81'})
    if 'qty_081' not in record:
        raise KeyError('qty_081')
    elif record['qty_081'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_081'], 10)
    if 'flag_081' not in record:
        pass
    elif record['flag_081'] is None:
        raise ValueError('flag_081')
    else:
        out['labels_2'] = strings_decode(record['flag_081'])
    if 'mode_081' not in record:
        out['title_3'] = 'unset'
    elif record['mode_081'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_081'])
    return out

# unit r082
def encode_r082(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_082'] = 30
    elif record['amount_0'] is None:
        out['v_082'] = None
    else:
        out['v_082'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_082'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_082'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_082'] = '-7'
    elif record['count_3'] is None:
        out['mode_082'] = None
    else:
        out['mode_082'] = decimal_encode(record['count_3'])
    return out

def decode_r082(record: dict) -> dict:
    out = {}
    if 'v_082' not in record:
        out['amount_0'] = 3
    elif record['v_082'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_082'], 10)
    if 'qty_082' not in record:
        raise KeyError('qty_082')
    elif record['qty_082'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_082'])
    if 'flag_082' not in record:
        pass
    elif record['flag_082'] is None:
        raise ValueError('flag_082')
    else:
        out['title_2'] = text_decode(record['flag_082'])
    if 'mode_082' not in record:
        out['count_3'] = -7
    elif record['mode_082'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_082'])
    return out

# unit r083
def encode_r083(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_083'] = ['default']
    elif record['labels_0'] is None:
        out['v_083'] = None
    else:
        out['v_083'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_083'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_083'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_083'] = 'no'
    elif record['active_3'] is None:
        out['mode_083'] = None
    else:
        out['mode_083'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r083(record: dict) -> dict:
    out = {}
    if 'v_083' not in record:
        out['labels_0'] = ['default']
    elif record['v_083'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_083'])
    if 'qty_083' not in record:
        raise KeyError('qty_083')
    elif record['qty_083'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_083'])
    if 'flag_083' not in record:
        pass
    elif record['flag_083'] is None:
        raise ValueError('flag_083')
    else:
        out['count_2'] = decimal_decode(record['flag_083'])
    if 'mode_083' not in record:
        out['active_3'] = False
    elif record['mode_083'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_083'], ['yes', 'no'])
    return out

# unit r084
def encode_r084(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_084'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_084'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_084'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_084'] = None
    else:
        out['flag_084'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_084'] = enum_encode(record['state_3'], {'ready': 'R84', 'held': 'H84', 'done': 'D84'})
    return out

def decode_r084(record: dict) -> dict:
    out = {}
    if 'v_084' not in record:
        raise KeyError('v_084')
    elif record['v_084'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_084'])
    if 'qty_084' not in record:
        pass
    elif record['qty_084'] is None:
        raise ValueError('qty_084')
    else:
        out['count_1'] = decimal_decode(record['qty_084'])
    if 'flag_084' not in record:
        out['active_2'] = False
    elif record['flag_084'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_084'], ['ON', 'OFF'])
    if 'mode_084' not in record:
        raise KeyError('mode_084')
    elif record['mode_084'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_084'], {'ready': 'R84', 'held': 'H84', 'done': 'D84'})
    return out

