from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r145
def encode_r145(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_145'] = None
    else:
        out['v_145'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_145'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_145'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_145'] = enum_encode(record['state_2'], {'ready': 'R145', 'held': 'H145', 'done': 'D145'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_145'] = None
    else:
        out['mode_145'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r145(record: dict) -> dict:
    out = {}
    if 'v_145' not in record:
        pass
    elif record['v_145'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_145'])
    if 'qty_145' not in record:
        out['active_1'] = False
    elif record['qty_145'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_145'], ['yes', 'no'])
    if 'flag_145' not in record:
        raise KeyError('flag_145')
    elif record['flag_145'] is None:
        raise ValueError('flag_145')
    else:
        out['state_2'] = enum_decode(record['flag_145'], {'ready': 'R145', 'held': 'H145', 'done': 'D145'})
    if 'mode_145' not in record:
        pass
    elif record['mode_145'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_145'], 2)
    return out

# unit r146
def encode_r146(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_146'] = None
    else:
        out['v_146'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_146'] = 'H146'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_146'] = enum_encode(record['state_1'], {'ready': 'R146', 'held': 'H146', 'done': 'D146'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_146'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_146'] = None
    else:
        out['mode_146'] = strings_encode(record['labels_3'])
    return out

def decode_r146(record: dict) -> dict:
    out = {}
    if 'v_146' not in record:
        pass
    elif record['v_146'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_146'], ['ON', 'OFF'])
    if 'qty_146' not in record:
        out['state_1'] = 'held'
    elif record['qty_146'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_146'], {'ready': 'R146', 'held': 'H146', 'done': 'D146'})
    if 'flag_146' not in record:
        raise KeyError('flag_146')
    elif record['flag_146'] is None:
        raise ValueError('flag_146')
    else:
        out['amount_2'] = scale_decode(record['flag_146'], 2)
    if 'mode_146' not in record:
        pass
    elif record['mode_146'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_146'])
    return out

# unit r147
def encode_r147(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_147'] = enum_encode(record['state_0'], {'ready': 'R147', 'held': 'H147', 'done': 'D147'})
    if 'amount_1' not in record:
        out['qty_147'] = 6
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_147'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_147'] = None
    else:
        out['flag_147'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_147'] = text_encode(record['title_3'])
    return out

def decode_r147(record: dict) -> dict:
    out = {}
    if 'v_147' not in record:
        pass
    elif record['v_147'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_147'], {'ready': 'R147', 'held': 'H147', 'done': 'D147'})
    if 'qty_147' not in record:
        out['amount_1'] = 3
    elif record['qty_147'] is None:
        raise ValueError('qty_147')
    else:
        out['amount_1'] = scale_decode(record['qty_147'], 2)
    if 'flag_147' not in record:
        raise KeyError('flag_147')
    elif record['flag_147'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_147'])
    if 'mode_147' not in record:
        pass
    elif record['mode_147'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_147'])
    return out

# unit r148
def encode_r148(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_148'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        out['qty_148'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_148'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_148'] = None
    else:
        out['flag_148'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_148'] = decimal_encode(record['count_3'])
    return out

def decode_r148(record: dict) -> dict:
    out = {}
    if 'v_148' not in record:
        pass
    elif record['v_148'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_148'], 2)
    if 'qty_148' not in record:
        out['labels_1'] = ['default']
    elif record['qty_148'] is None:
        raise ValueError('qty_148')
    else:
        out['labels_1'] = strings_decode(record['qty_148'])
    if 'flag_148' not in record:
        raise KeyError('flag_148')
    elif record['flag_148'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_148'])
    if 'mode_148' not in record:
        pass
    elif record['mode_148'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_148'])
    return out

# unit r149
def encode_r149(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_149'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_149'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_149'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_149'] = None
    else:
        out['flag_149'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_149'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r149(record: dict) -> dict:
    out = {}
    if 'v_149' not in record:
        pass
    elif record['v_149'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_149'])
    if 'qty_149' not in record:
        out['title_1'] = 'unset'
    elif record['qty_149'] is None:
        raise ValueError('qty_149')
    else:
        out['title_1'] = text_decode(record['qty_149'])
    if 'flag_149' not in record:
        raise KeyError('flag_149')
    elif record['flag_149'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_149'])
    if 'mode_149' not in record:
        pass
    elif record['mode_149'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_149'], ['yes', 'no'])
    return out

# unit r150
def encode_r150(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_150'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_150'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_150'] = None
    else:
        out['qty_150'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_150'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_150'] = 'H150'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_150'] = enum_encode(record['state_3'], {'ready': 'R150', 'held': 'H150', 'done': 'D150'})
    return out

def decode_r150(record: dict) -> dict:
    out = {}
    if 'v_150' not in record:
        out['title_0'] = 'unset'
    elif record['v_150'] is None:
        raise ValueError('v_150')
    else:
        out['title_0'] = text_decode(record['v_150'])
    if 'qty_150' not in record:
        raise KeyError('qty_150')
    elif record['qty_150'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_150'])
    if 'flag_150' not in record:
        pass
    elif record['flag_150'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_150'], ['ON', 'OFF'])
    if 'mode_150' not in record:
        out['state_3'] = 'held'
    elif record['mode_150'] is None:
        raise ValueError('mode_150')
    else:
        out['state_3'] = enum_decode(record['mode_150'], {'ready': 'R150', 'held': 'H150', 'done': 'D150'})
    return out

