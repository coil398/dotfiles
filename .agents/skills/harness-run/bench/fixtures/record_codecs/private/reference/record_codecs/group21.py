from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r127
def encode_r127(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_127'] = None
    else:
        out['v_127'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_127'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_127'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_127'] = enum_encode(record['state_2'], {'ready': 'R127', 'held': 'H127', 'done': 'D127'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_127'] = None
    else:
        out['mode_127'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r127(record: dict) -> dict:
    out = {}
    if 'v_127' not in record:
        pass
    elif record['v_127'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_127'])
    if 'qty_127' not in record:
        out['active_1'] = False
    elif record['qty_127'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_127'], ['yes', 'no'])
    if 'flag_127' not in record:
        raise KeyError('flag_127')
    elif record['flag_127'] is None:
        raise ValueError('flag_127')
    else:
        out['state_2'] = enum_decode(record['flag_127'], {'ready': 'R127', 'held': 'H127', 'done': 'D127'})
    if 'mode_127' not in record:
        pass
    elif record['mode_127'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_127'], 10)
    return out

# unit r128
def encode_r128(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_128'] = None
    else:
        out['v_128'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_128'] = 'H128'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_128'] = enum_encode(record['state_1'], {'ready': 'R128', 'held': 'H128', 'done': 'D128'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_128'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_128'] = None
    else:
        out['mode_128'] = strings_encode(record['labels_3'])
    return out

def decode_r128(record: dict) -> dict:
    out = {}
    if 'v_128' not in record:
        pass
    elif record['v_128'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_128'], ['ON', 'OFF'])
    if 'qty_128' not in record:
        out['state_1'] = 'held'
    elif record['qty_128'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_128'], {'ready': 'R128', 'held': 'H128', 'done': 'D128'})
    if 'flag_128' not in record:
        raise KeyError('flag_128')
    elif record['flag_128'] is None:
        raise ValueError('flag_128')
    else:
        out['amount_2'] = scale_decode(record['flag_128'], 10)
    if 'mode_128' not in record:
        pass
    elif record['mode_128'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_128'])
    return out

# unit r129
def encode_r129(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_129'] = enum_encode(record['state_0'], {'ready': 'R129', 'held': 'H129', 'done': 'D129'})
    if 'amount_1' not in record:
        out['qty_129'] = 30
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_129'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_129'] = None
    else:
        out['flag_129'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_129'] = text_encode(record['title_3'])
    return out

def decode_r129(record: dict) -> dict:
    out = {}
    if 'v_129' not in record:
        pass
    elif record['v_129'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_129'], {'ready': 'R129', 'held': 'H129', 'done': 'D129'})
    if 'qty_129' not in record:
        out['amount_1'] = 3
    elif record['qty_129'] is None:
        raise ValueError('qty_129')
    else:
        out['amount_1'] = scale_decode(record['qty_129'], 10)
    if 'flag_129' not in record:
        raise KeyError('flag_129')
    elif record['flag_129'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_129'])
    if 'mode_129' not in record:
        pass
    elif record['mode_129'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_129'])
    return out

# unit r130
def encode_r130(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_130'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        out['qty_130'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_130'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_130'] = None
    else:
        out['flag_130'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_130'] = decimal_encode(record['count_3'])
    return out

def decode_r130(record: dict) -> dict:
    out = {}
    if 'v_130' not in record:
        pass
    elif record['v_130'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_130'], 10)
    if 'qty_130' not in record:
        out['labels_1'] = ['default']
    elif record['qty_130'] is None:
        raise ValueError('qty_130')
    else:
        out['labels_1'] = strings_decode(record['qty_130'])
    if 'flag_130' not in record:
        raise KeyError('flag_130')
    elif record['flag_130'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_130'])
    if 'mode_130' not in record:
        pass
    elif record['mode_130'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_130'])
    return out

# unit r131
def encode_r131(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_131'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_131'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_131'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_131'] = None
    else:
        out['flag_131'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_131'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r131(record: dict) -> dict:
    out = {}
    if 'v_131' not in record:
        pass
    elif record['v_131'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_131'])
    if 'qty_131' not in record:
        out['title_1'] = 'unset'
    elif record['qty_131'] is None:
        raise ValueError('qty_131')
    else:
        out['title_1'] = text_decode(record['qty_131'])
    if 'flag_131' not in record:
        raise KeyError('flag_131')
    elif record['flag_131'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_131'])
    if 'mode_131' not in record:
        pass
    elif record['mode_131'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_131'], ['yes', 'no'])
    return out

# unit r132
def encode_r132(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_132'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_132'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_132'] = None
    else:
        out['qty_132'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_132'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_132'] = 'H132'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_132'] = enum_encode(record['state_3'], {'ready': 'R132', 'held': 'H132', 'done': 'D132'})
    return out

def decode_r132(record: dict) -> dict:
    out = {}
    if 'v_132' not in record:
        out['title_0'] = 'unset'
    elif record['v_132'] is None:
        raise ValueError('v_132')
    else:
        out['title_0'] = text_decode(record['v_132'])
    if 'qty_132' not in record:
        raise KeyError('qty_132')
    elif record['qty_132'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_132'])
    if 'flag_132' not in record:
        pass
    elif record['flag_132'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_132'], ['ON', 'OFF'])
    if 'mode_132' not in record:
        out['state_3'] = 'held'
    elif record['mode_132'] is None:
        raise ValueError('mode_132')
    else:
        out['state_3'] = enum_decode(record['mode_132'], {'ready': 'R132', 'held': 'H132', 'done': 'D132'})
    return out

