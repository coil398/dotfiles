from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r001
def encode_r001(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_001'] = None
    else:
        out['v_001'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_001'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_001'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_001'] = enum_encode(record['state_2'], {'ready': 'R1', 'held': 'H1', 'done': 'D1'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_001'] = None
    else:
        out['mode_001'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r001(record: dict) -> dict:
    out = {}
    if 'v_001' not in record:
        pass
    elif record['v_001'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_001'])
    if 'qty_001' not in record:
        out['active_1'] = False
    elif record['qty_001'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_001'], ['yes', 'no'])
    if 'flag_001' not in record:
        raise KeyError('flag_001')
    elif record['flag_001'] is None:
        raise ValueError('flag_001')
    else:
        out['state_2'] = enum_decode(record['flag_001'], {'ready': 'R1', 'held': 'H1', 'done': 'D1'})
    if 'mode_001' not in record:
        pass
    elif record['mode_001'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_001'], 2)
    return out

# unit r002
def encode_r002(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_002'] = None
    else:
        out['v_002'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_002'] = 'H2'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_002'] = enum_encode(record['state_1'], {'ready': 'R2', 'held': 'H2', 'done': 'D2'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_002'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_002'] = None
    else:
        out['mode_002'] = strings_encode(record['labels_3'])
    return out

def decode_r002(record: dict) -> dict:
    out = {}
    if 'v_002' not in record:
        pass
    elif record['v_002'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_002'], ['ON', 'OFF'])
    if 'qty_002' not in record:
        out['state_1'] = 'held'
    elif record['qty_002'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_002'], {'ready': 'R2', 'held': 'H2', 'done': 'D2'})
    if 'flag_002' not in record:
        raise KeyError('flag_002')
    elif record['flag_002'] is None:
        raise ValueError('flag_002')
    else:
        out['amount_2'] = scale_decode(record['flag_002'], 2)
    if 'mode_002' not in record:
        pass
    elif record['mode_002'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_002'])
    return out

# unit r003
def encode_r003(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_003'] = enum_encode(record['state_0'], {'ready': 'R3', 'held': 'H3', 'done': 'D3'})
    if 'amount_1' not in record:
        out['qty_003'] = 6
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_003'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_003'] = None
    else:
        out['flag_003'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_003'] = text_encode(record['title_3'])
    return out

def decode_r003(record: dict) -> dict:
    out = {}
    if 'v_003' not in record:
        pass
    elif record['v_003'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_003'], {'ready': 'R3', 'held': 'H3', 'done': 'D3'})
    if 'qty_003' not in record:
        out['amount_1'] = 3
    elif record['qty_003'] is None:
        raise ValueError('qty_003')
    else:
        out['amount_1'] = scale_decode(record['qty_003'], 2)
    if 'flag_003' not in record:
        raise KeyError('flag_003')
    elif record['flag_003'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_003'])
    if 'mode_003' not in record:
        pass
    elif record['mode_003'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_003'])
    return out

# unit r004
def encode_r004(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_004'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        out['qty_004'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_004'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_004'] = None
    else:
        out['flag_004'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_004'] = decimal_encode(record['count_3'])
    return out

def decode_r004(record: dict) -> dict:
    out = {}
    if 'v_004' not in record:
        pass
    elif record['v_004'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_004'], 2)
    if 'qty_004' not in record:
        out['labels_1'] = ['default']
    elif record['qty_004'] is None:
        raise ValueError('qty_004')
    else:
        out['labels_1'] = strings_decode(record['qty_004'])
    if 'flag_004' not in record:
        raise KeyError('flag_004')
    elif record['flag_004'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_004'])
    if 'mode_004' not in record:
        pass
    elif record['mode_004'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_004'])
    return out

# unit r005
def encode_r005(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_005'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_005'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_005'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_005'] = None
    else:
        out['flag_005'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_005'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r005(record: dict) -> dict:
    out = {}
    if 'v_005' not in record:
        pass
    elif record['v_005'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_005'])
    if 'qty_005' not in record:
        out['title_1'] = 'unset'
    elif record['qty_005'] is None:
        raise ValueError('qty_005')
    else:
        out['title_1'] = text_decode(record['qty_005'])
    if 'flag_005' not in record:
        raise KeyError('flag_005')
    elif record['flag_005'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_005'])
    if 'mode_005' not in record:
        pass
    elif record['mode_005'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_005'], ['yes', 'no'])
    return out

# unit r006
def encode_r006(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_006'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_006'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_006'] = None
    else:
        out['qty_006'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_006'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_006'] = 'H6'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_006'] = enum_encode(record['state_3'], {'ready': 'R6', 'held': 'H6', 'done': 'D6'})
    return out

def decode_r006(record: dict) -> dict:
    out = {}
    if 'v_006' not in record:
        out['title_0'] = 'unset'
    elif record['v_006'] is None:
        raise ValueError('v_006')
    else:
        out['title_0'] = text_decode(record['v_006'])
    if 'qty_006' not in record:
        raise KeyError('qty_006')
    elif record['qty_006'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_006'])
    if 'flag_006' not in record:
        pass
    elif record['flag_006'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_006'], ['ON', 'OFF'])
    if 'mode_006' not in record:
        out['state_3'] = 'held'
    elif record['mode_006'] is None:
        raise ValueError('mode_006')
    else:
        out['state_3'] = enum_decode(record['mode_006'], {'ready': 'R6', 'held': 'H6', 'done': 'D6'})
    return out

