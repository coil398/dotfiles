from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r055
def encode_r055(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_055'] = None
    else:
        out['v_055'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_055'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_055'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_055'] = enum_encode(record['state_2'], {'ready': 'R55', 'held': 'H55', 'done': 'D55'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_055'] = None
    else:
        out['mode_055'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r055(record: dict) -> dict:
    out = {}
    if 'v_055' not in record:
        pass
    elif record['v_055'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_055'])
    if 'qty_055' not in record:
        out['active_1'] = False
    elif record['qty_055'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_055'], ['yes', 'no'])
    if 'flag_055' not in record:
        raise KeyError('flag_055')
    elif record['flag_055'] is None:
        raise ValueError('flag_055')
    else:
        out['state_2'] = enum_decode(record['flag_055'], {'ready': 'R55', 'held': 'H55', 'done': 'D55'})
    if 'mode_055' not in record:
        pass
    elif record['mode_055'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_055'], 10)
    return out

# unit r056
def encode_r056(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_056'] = None
    else:
        out['v_056'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_056'] = 'H56'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_056'] = enum_encode(record['state_1'], {'ready': 'R56', 'held': 'H56', 'done': 'D56'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_056'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_056'] = None
    else:
        out['mode_056'] = strings_encode(record['labels_3'])
    return out

def decode_r056(record: dict) -> dict:
    out = {}
    if 'v_056' not in record:
        pass
    elif record['v_056'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_056'], ['ON', 'OFF'])
    if 'qty_056' not in record:
        out['state_1'] = 'held'
    elif record['qty_056'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_056'], {'ready': 'R56', 'held': 'H56', 'done': 'D56'})
    if 'flag_056' not in record:
        raise KeyError('flag_056')
    elif record['flag_056'] is None:
        raise ValueError('flag_056')
    else:
        out['amount_2'] = scale_decode(record['flag_056'], 10)
    if 'mode_056' not in record:
        pass
    elif record['mode_056'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_056'])
    return out

# unit r057
def encode_r057(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_057'] = enum_encode(record['state_0'], {'ready': 'R57', 'held': 'H57', 'done': 'D57'})
    if 'amount_1' not in record:
        out['qty_057'] = 30
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_057'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_057'] = None
    else:
        out['flag_057'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_057'] = text_encode(record['title_3'])
    return out

def decode_r057(record: dict) -> dict:
    out = {}
    if 'v_057' not in record:
        pass
    elif record['v_057'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_057'], {'ready': 'R57', 'held': 'H57', 'done': 'D57'})
    if 'qty_057' not in record:
        out['amount_1'] = 3
    elif record['qty_057'] is None:
        raise ValueError('qty_057')
    else:
        out['amount_1'] = scale_decode(record['qty_057'], 10)
    if 'flag_057' not in record:
        raise KeyError('flag_057')
    elif record['flag_057'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_057'])
    if 'mode_057' not in record:
        pass
    elif record['mode_057'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_057'])
    return out

# unit r058
def encode_r058(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_058'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        out['qty_058'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_058'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_058'] = None
    else:
        out['flag_058'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_058'] = decimal_encode(record['count_3'])
    return out

def decode_r058(record: dict) -> dict:
    out = {}
    if 'v_058' not in record:
        pass
    elif record['v_058'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_058'], 10)
    if 'qty_058' not in record:
        out['labels_1'] = ['default']
    elif record['qty_058'] is None:
        raise ValueError('qty_058')
    else:
        out['labels_1'] = strings_decode(record['qty_058'])
    if 'flag_058' not in record:
        raise KeyError('flag_058')
    elif record['flag_058'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_058'])
    if 'mode_058' not in record:
        pass
    elif record['mode_058'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_058'])
    return out

# unit r059
def encode_r059(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_059'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_059'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_059'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_059'] = None
    else:
        out['flag_059'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_059'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r059(record: dict) -> dict:
    out = {}
    if 'v_059' not in record:
        pass
    elif record['v_059'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_059'])
    if 'qty_059' not in record:
        out['title_1'] = 'unset'
    elif record['qty_059'] is None:
        raise ValueError('qty_059')
    else:
        out['title_1'] = text_decode(record['qty_059'])
    if 'flag_059' not in record:
        raise KeyError('flag_059')
    elif record['flag_059'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_059'])
    if 'mode_059' not in record:
        pass
    elif record['mode_059'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_059'], ['yes', 'no'])
    return out

# unit r060
def encode_r060(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_060'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_060'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_060'] = None
    else:
        out['qty_060'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_060'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_060'] = 'H60'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_060'] = enum_encode(record['state_3'], {'ready': 'R60', 'held': 'H60', 'done': 'D60'})
    return out

def decode_r060(record: dict) -> dict:
    out = {}
    if 'v_060' not in record:
        out['title_0'] = 'unset'
    elif record['v_060'] is None:
        raise ValueError('v_060')
    else:
        out['title_0'] = text_decode(record['v_060'])
    if 'qty_060' not in record:
        raise KeyError('qty_060')
    elif record['qty_060'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_060'])
    if 'flag_060' not in record:
        pass
    elif record['flag_060'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_060'], ['ON', 'OFF'])
    if 'mode_060' not in record:
        out['state_3'] = 'held'
    elif record['mode_060'] is None:
        raise ValueError('mode_060')
    else:
        out['state_3'] = enum_decode(record['mode_060'], {'ready': 'R60', 'held': 'H60', 'done': 'D60'})
    return out

