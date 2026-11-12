from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r175
def encode_r175(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        raise KeyError('count_0')
    elif record['count_0'] is None:
        pass
    else:
        out['v_175'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        pass
    elif record['active_1'] is None:
        raise ValueError('active_1')
    else:
        out['qty_175'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        out['flag_175'] = 'H175'
    elif record['state_2'] is None:
        out['flag_175'] = None
    else:
        out['flag_175'] = enum_encode(record['state_2'], {'ready': 'R175', 'held': 'H175', 'done': 'D175'})
    if 'amount_3' not in record:
        raise KeyError('amount_3')
    elif record['amount_3'] is None:
        pass
    else:
        out['mode_175'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r175(record: dict) -> dict:
    out = {}
    if 'v_175' not in record:
        raise KeyError('v_175')
    elif record['v_175'] is None:
        pass
    else:
        out['count_0'] = decimal_decode(record['v_175'])
    if 'qty_175' not in record:
        pass
    elif record['qty_175'] is None:
        raise ValueError('qty_175')
    else:
        out['active_1'] = boolean_decode(record['qty_175'], ['yes', 'no'])
    if 'flag_175' not in record:
        out['state_2'] = 'held'
    elif record['flag_175'] is None:
        out['state_2'] = None
    else:
        out['state_2'] = enum_decode(record['flag_175'], {'ready': 'R175', 'held': 'H175', 'done': 'D175'})
    if 'mode_175' not in record:
        raise KeyError('mode_175')
    elif record['mode_175'] is None:
        pass
    else:
        out['amount_3'] = scale_decode(record['mode_175'], 10)
    return out

# unit r176
def encode_r176(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        raise KeyError('active_0')
    elif record['active_0'] is None:
        pass
    else:
        out['v_176'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        pass
    elif record['state_1'] is None:
        raise ValueError('state_1')
    else:
        out['qty_176'] = enum_encode(record['state_1'], {'ready': 'R176', 'held': 'H176', 'done': 'D176'})
    if 'amount_2' not in record:
        out['flag_176'] = 30
    elif record['amount_2'] is None:
        out['flag_176'] = None
    else:
        out['flag_176'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        raise KeyError('labels_3')
    elif record['labels_3'] is None:
        pass
    else:
        out['mode_176'] = strings_encode(record['labels_3'])
    return out

def decode_r176(record: dict) -> dict:
    out = {}
    if 'v_176' not in record:
        raise KeyError('v_176')
    elif record['v_176'] is None:
        pass
    else:
        out['active_0'] = boolean_decode(record['v_176'], ['ON', 'OFF'])
    if 'qty_176' not in record:
        pass
    elif record['qty_176'] is None:
        raise ValueError('qty_176')
    else:
        out['state_1'] = enum_decode(record['qty_176'], {'ready': 'R176', 'held': 'H176', 'done': 'D176'})
    if 'flag_176' not in record:
        out['amount_2'] = 3
    elif record['flag_176'] is None:
        out['amount_2'] = None
    else:
        out['amount_2'] = scale_decode(record['flag_176'], 10)
    if 'mode_176' not in record:
        raise KeyError('mode_176')
    elif record['mode_176'] is None:
        pass
    else:
        out['labels_3'] = strings_decode(record['mode_176'])
    return out

# unit r177
def encode_r177(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        raise KeyError('state_0')
    elif record['state_0'] is None:
        raise ValueError('state_0')
    else:
        out['v_177'] = enum_encode(record['state_0'], {'ready': 'R177', 'held': 'H177', 'done': 'D177'})
    if 'amount_1' not in record:
        pass
    elif record['amount_1'] is None:
        out['qty_177'] = None
    else:
        out['qty_177'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        out['flag_177'] = ['default']
    elif record['labels_2'] is None:
        pass
    else:
        out['flag_177'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        raise KeyError('title_3')
    elif record['title_3'] is None:
        raise ValueError('title_3')
    else:
        out['mode_177'] = text_encode(record['title_3'])
    return out

def decode_r177(record: dict) -> dict:
    out = {}
    if 'v_177' not in record:
        raise KeyError('v_177')
    elif record['v_177'] is None:
        raise ValueError('v_177')
    else:
        out['state_0'] = enum_decode(record['v_177'], {'ready': 'R177', 'held': 'H177', 'done': 'D177'})
    if 'qty_177' not in record:
        pass
    elif record['qty_177'] is None:
        out['amount_1'] = None
    else:
        out['amount_1'] = scale_decode(record['qty_177'], 10)
    if 'flag_177' not in record:
        out['labels_2'] = ['default']
    elif record['flag_177'] is None:
        pass
    else:
        out['labels_2'] = strings_decode(record['flag_177'])
    if 'mode_177' not in record:
        raise KeyError('mode_177')
    elif record['mode_177'] is None:
        raise ValueError('mode_177')
    else:
        out['title_3'] = text_decode(record['mode_177'])
    return out

# unit r178
def encode_r178(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        raise KeyError('amount_0')
    elif record['amount_0'] is None:
        raise ValueError('amount_0')
    else:
        out['v_178'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        pass
    elif record['labels_1'] is None:
        out['qty_178'] = None
    else:
        out['qty_178'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        out['flag_178'] = 'unset'
    elif record['title_2'] is None:
        pass
    else:
        out['flag_178'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        raise KeyError('count_3')
    elif record['count_3'] is None:
        raise ValueError('count_3')
    else:
        out['mode_178'] = decimal_encode(record['count_3'])
    return out

def decode_r178(record: dict) -> dict:
    out = {}
    if 'v_178' not in record:
        raise KeyError('v_178')
    elif record['v_178'] is None:
        raise ValueError('v_178')
    else:
        out['amount_0'] = scale_decode(record['v_178'], 10)
    if 'qty_178' not in record:
        pass
    elif record['qty_178'] is None:
        out['labels_1'] = None
    else:
        out['labels_1'] = strings_decode(record['qty_178'])
    if 'flag_178' not in record:
        out['title_2'] = 'unset'
    elif record['flag_178'] is None:
        pass
    else:
        out['title_2'] = text_decode(record['flag_178'])
    if 'mode_178' not in record:
        raise KeyError('mode_178')
    elif record['mode_178'] is None:
        raise ValueError('mode_178')
    else:
        out['count_3'] = decimal_decode(record['mode_178'])
    return out

# unit r179
def encode_r179(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        raise KeyError('labels_0')
    elif record['labels_0'] is None:
        raise ValueError('labels_0')
    else:
        out['v_179'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        pass
    elif record['title_1'] is None:
        out['qty_179'] = None
    else:
        out['qty_179'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        out['flag_179'] = '-7'
    elif record['count_2'] is None:
        pass
    else:
        out['flag_179'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        raise KeyError('active_3')
    elif record['active_3'] is None:
        raise ValueError('active_3')
    else:
        out['mode_179'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r179(record: dict) -> dict:
    out = {}
    if 'v_179' not in record:
        raise KeyError('v_179')
    elif record['v_179'] is None:
        raise ValueError('v_179')
    else:
        out['labels_0'] = strings_decode(record['v_179'])
    if 'qty_179' not in record:
        pass
    elif record['qty_179'] is None:
        out['title_1'] = None
    else:
        out['title_1'] = text_decode(record['qty_179'])
    if 'flag_179' not in record:
        out['count_2'] = -7
    elif record['flag_179'] is None:
        pass
    else:
        out['count_2'] = decimal_decode(record['flag_179'])
    if 'mode_179' not in record:
        raise KeyError('mode_179')
    elif record['mode_179'] is None:
        raise ValueError('mode_179')
    else:
        out['active_3'] = boolean_decode(record['mode_179'], ['yes', 'no'])
    return out

# unit r180
def encode_r180(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        pass
    elif record['title_0'] is None:
        out['v_180'] = None
    else:
        out['v_180'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        out['qty_180'] = '-7'
    elif record['count_1'] is None:
        pass
    else:
        out['qty_180'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        raise KeyError('active_2')
    elif record['active_2'] is None:
        raise ValueError('active_2')
    else:
        out['flag_180'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        pass
    elif record['state_3'] is None:
        out['mode_180'] = None
    else:
        out['mode_180'] = enum_encode(record['state_3'], {'ready': 'R180', 'held': 'H180', 'done': 'D180'})
    return out

def decode_r180(record: dict) -> dict:
    out = {}
    if 'v_180' not in record:
        pass
    elif record['v_180'] is None:
        out['title_0'] = None
    else:
        out['title_0'] = text_decode(record['v_180'])
    if 'qty_180' not in record:
        out['count_1'] = -7
    elif record['qty_180'] is None:
        pass
    else:
        out['count_1'] = decimal_decode(record['qty_180'])
    if 'flag_180' not in record:
        raise KeyError('flag_180')
    elif record['flag_180'] is None:
        raise ValueError('flag_180')
    else:
        out['active_2'] = boolean_decode(record['flag_180'], ['ON', 'OFF'])
    if 'mode_180' not in record:
        pass
    elif record['mode_180'] is None:
        out['state_3'] = None
    else:
        out['state_3'] = enum_decode(record['mode_180'], {'ready': 'R180', 'held': 'H180', 'done': 'D180'})
    return out

