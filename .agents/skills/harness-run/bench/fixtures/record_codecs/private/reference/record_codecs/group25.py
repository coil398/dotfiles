from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r151
def encode_r151(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        out['v_151'] = '-7'
    elif record['count_0'] is None:
        raise ValueError('count_0')
    else:
        out['v_151'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        raise KeyError('active_1')
    elif record['active_1'] is None:
        out['qty_151'] = None
    else:
        out['qty_151'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        pass
    elif record['state_2'] is None:
        pass
    else:
        out['flag_151'] = enum_encode(record['state_2'], {'ready': 'R151', 'held': 'H151', 'done': 'D151'})
    if 'amount_3' not in record:
        out['mode_151'] = 30
    elif record['amount_3'] is None:
        raise ValueError('amount_3')
    else:
        out['mode_151'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r151(record: dict) -> dict:
    out = {}
    if 'v_151' not in record:
        out['count_0'] = -7
    elif record['v_151'] is None:
        raise ValueError('v_151')
    else:
        out['count_0'] = decimal_decode(record['v_151'])
    if 'qty_151' not in record:
        raise KeyError('qty_151')
    elif record['qty_151'] is None:
        out['active_1'] = None
    else:
        out['active_1'] = boolean_decode(record['qty_151'], ['yes', 'no'])
    if 'flag_151' not in record:
        pass
    elif record['flag_151'] is None:
        pass
    else:
        out['state_2'] = enum_decode(record['flag_151'], {'ready': 'R151', 'held': 'H151', 'done': 'D151'})
    if 'mode_151' not in record:
        out['amount_3'] = 3
    elif record['mode_151'] is None:
        raise ValueError('mode_151')
    else:
        out['amount_3'] = scale_decode(record['mode_151'], 10)
    return out

# unit r152
def encode_r152(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        out['v_152'] = 'OFF'
    elif record['active_0'] is None:
        raise ValueError('active_0')
    else:
        out['v_152'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        raise KeyError('state_1')
    elif record['state_1'] is None:
        out['qty_152'] = None
    else:
        out['qty_152'] = enum_encode(record['state_1'], {'ready': 'R152', 'held': 'H152', 'done': 'D152'})
    if 'amount_2' not in record:
        pass
    elif record['amount_2'] is None:
        pass
    else:
        out['flag_152'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        out['mode_152'] = ['default']
    elif record['labels_3'] is None:
        raise ValueError('labels_3')
    else:
        out['mode_152'] = strings_encode(record['labels_3'])
    return out

def decode_r152(record: dict) -> dict:
    out = {}
    if 'v_152' not in record:
        out['active_0'] = False
    elif record['v_152'] is None:
        raise ValueError('v_152')
    else:
        out['active_0'] = boolean_decode(record['v_152'], ['ON', 'OFF'])
    if 'qty_152' not in record:
        raise KeyError('qty_152')
    elif record['qty_152'] is None:
        out['state_1'] = None
    else:
        out['state_1'] = enum_decode(record['qty_152'], {'ready': 'R152', 'held': 'H152', 'done': 'D152'})
    if 'flag_152' not in record:
        pass
    elif record['flag_152'] is None:
        pass
    else:
        out['amount_2'] = scale_decode(record['flag_152'], 10)
    if 'mode_152' not in record:
        out['labels_3'] = ['default']
    elif record['mode_152'] is None:
        raise ValueError('mode_152')
    else:
        out['labels_3'] = strings_decode(record['mode_152'])
    return out

# unit r153
def encode_r153(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        out['v_153'] = 'H153'
    elif record['state_0'] is None:
        out['v_153'] = None
    else:
        out['v_153'] = enum_encode(record['state_0'], {'ready': 'R153', 'held': 'H153', 'done': 'D153'})
    if 'amount_1' not in record:
        raise KeyError('amount_1')
    elif record['amount_1'] is None:
        pass
    else:
        out['qty_153'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        pass
    elif record['labels_2'] is None:
        raise ValueError('labels_2')
    else:
        out['flag_153'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        out['mode_153'] = 'unset'
    elif record['title_3'] is None:
        out['mode_153'] = None
    else:
        out['mode_153'] = text_encode(record['title_3'])
    return out

def decode_r153(record: dict) -> dict:
    out = {}
    if 'v_153' not in record:
        out['state_0'] = 'held'
    elif record['v_153'] is None:
        out['state_0'] = None
    else:
        out['state_0'] = enum_decode(record['v_153'], {'ready': 'R153', 'held': 'H153', 'done': 'D153'})
    if 'qty_153' not in record:
        raise KeyError('qty_153')
    elif record['qty_153'] is None:
        pass
    else:
        out['amount_1'] = scale_decode(record['qty_153'], 10)
    if 'flag_153' not in record:
        pass
    elif record['flag_153'] is None:
        raise ValueError('flag_153')
    else:
        out['labels_2'] = strings_decode(record['flag_153'])
    if 'mode_153' not in record:
        out['title_3'] = 'unset'
    elif record['mode_153'] is None:
        out['title_3'] = None
    else:
        out['title_3'] = text_decode(record['mode_153'])
    return out

# unit r154
def encode_r154(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        out['v_154'] = 30
    elif record['amount_0'] is None:
        out['v_154'] = None
    else:
        out['v_154'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        raise KeyError('labels_1')
    elif record['labels_1'] is None:
        pass
    else:
        out['qty_154'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        pass
    elif record['title_2'] is None:
        raise ValueError('title_2')
    else:
        out['flag_154'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        out['mode_154'] = '-7'
    elif record['count_3'] is None:
        out['mode_154'] = None
    else:
        out['mode_154'] = decimal_encode(record['count_3'])
    return out

def decode_r154(record: dict) -> dict:
    out = {}
    if 'v_154' not in record:
        out['amount_0'] = 3
    elif record['v_154'] is None:
        out['amount_0'] = None
    else:
        out['amount_0'] = scale_decode(record['v_154'], 10)
    if 'qty_154' not in record:
        raise KeyError('qty_154')
    elif record['qty_154'] is None:
        pass
    else:
        out['labels_1'] = strings_decode(record['qty_154'])
    if 'flag_154' not in record:
        pass
    elif record['flag_154'] is None:
        raise ValueError('flag_154')
    else:
        out['title_2'] = text_decode(record['flag_154'])
    if 'mode_154' not in record:
        out['count_3'] = -7
    elif record['mode_154'] is None:
        out['count_3'] = None
    else:
        out['count_3'] = decimal_decode(record['mode_154'])
    return out

# unit r155
def encode_r155(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        out['v_155'] = ['default']
    elif record['labels_0'] is None:
        out['v_155'] = None
    else:
        out['v_155'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        raise KeyError('title_1')
    elif record['title_1'] is None:
        pass
    else:
        out['qty_155'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        pass
    elif record['count_2'] is None:
        raise ValueError('count_2')
    else:
        out['flag_155'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        out['mode_155'] = 'no'
    elif record['active_3'] is None:
        out['mode_155'] = None
    else:
        out['mode_155'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r155(record: dict) -> dict:
    out = {}
    if 'v_155' not in record:
        out['labels_0'] = ['default']
    elif record['v_155'] is None:
        out['labels_0'] = None
    else:
        out['labels_0'] = strings_decode(record['v_155'])
    if 'qty_155' not in record:
        raise KeyError('qty_155')
    elif record['qty_155'] is None:
        pass
    else:
        out['title_1'] = text_decode(record['qty_155'])
    if 'flag_155' not in record:
        pass
    elif record['flag_155'] is None:
        raise ValueError('flag_155')
    else:
        out['count_2'] = decimal_decode(record['flag_155'])
    if 'mode_155' not in record:
        out['active_3'] = False
    elif record['mode_155'] is None:
        out['active_3'] = None
    else:
        out['active_3'] = boolean_decode(record['mode_155'], ['yes', 'no'])
    return out

# unit r156
def encode_r156(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        raise KeyError('title_0')
    elif record['title_0'] is None:
        pass
    else:
        out['v_156'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        pass
    elif record['count_1'] is None:
        raise ValueError('count_1')
    else:
        out['qty_156'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        out['flag_156'] = 'OFF'
    elif record['active_2'] is None:
        out['flag_156'] = None
    else:
        out['flag_156'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        raise KeyError('state_3')
    elif record['state_3'] is None:
        pass
    else:
        out['mode_156'] = enum_encode(record['state_3'], {'ready': 'R156', 'held': 'H156', 'done': 'D156'})
    return out

def decode_r156(record: dict) -> dict:
    out = {}
    if 'v_156' not in record:
        raise KeyError('v_156')
    elif record['v_156'] is None:
        pass
    else:
        out['title_0'] = text_decode(record['v_156'])
    if 'qty_156' not in record:
        pass
    elif record['qty_156'] is None:
        raise ValueError('qty_156')
    else:
        out['count_1'] = decimal_decode(record['qty_156'])
    if 'flag_156' not in record:
        out['active_2'] = False
    elif record['flag_156'] is None:
        out['active_2'] = None
    else:
        out['active_2'] = boolean_decode(record['flag_156'], ['ON', 'OFF'])
    if 'mode_156' not in record:
        raise KeyError('mode_156')
    elif record['mode_156'] is None:
        pass
    else:
        out['state_3'] = enum_decode(record['mode_156'], {'ready': 'R156', 'held': 'H156', 'done': 'D156'})
    return out

