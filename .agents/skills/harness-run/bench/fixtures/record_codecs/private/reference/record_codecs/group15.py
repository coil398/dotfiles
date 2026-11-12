from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r091
def encode_r091(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_091'] = None
    else:
        out['v_091'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_091'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_091'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_091'] = enum_encode(record['state_2'], {'ready': 'R91', 'held': 'H91', 'done': 'D91'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_091'] = None
    else:
        out['mode_091'] = scale_encode(record['amount_3'], 10)
    return out

def decode_r091(record: dict) -> dict:
    out = {}
    if 'v_091' not in record:
        pass
    elif record['v_091'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_091'])
    if 'qty_091' not in record:
        out['active_1'] = False
    elif record['qty_091'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_091'], ['yes', 'no'])
    if 'flag_091' not in record:
        raise KeyError('flag_091')
    elif record['flag_091'] is None:
        raise ValueError('flag_091')
    else:
        out['state_2'] = enum_decode(record['flag_091'], {'ready': 'R91', 'held': 'H91', 'done': 'D91'})
    if 'mode_091' not in record:
        pass
    elif record['mode_091'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_091'], 10)
    return out

# unit r092
def encode_r092(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_092'] = None
    else:
        out['v_092'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_092'] = 'H92'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_092'] = enum_encode(record['state_1'], {'ready': 'R92', 'held': 'H92', 'done': 'D92'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_092'] = scale_encode(record['amount_2'], 10)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_092'] = None
    else:
        out['mode_092'] = strings_encode(record['labels_3'])
    return out

def decode_r092(record: dict) -> dict:
    out = {}
    if 'v_092' not in record:
        pass
    elif record['v_092'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_092'], ['ON', 'OFF'])
    if 'qty_092' not in record:
        out['state_1'] = 'held'
    elif record['qty_092'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_092'], {'ready': 'R92', 'held': 'H92', 'done': 'D92'})
    if 'flag_092' not in record:
        raise KeyError('flag_092')
    elif record['flag_092'] is None:
        raise ValueError('flag_092')
    else:
        out['amount_2'] = scale_decode(record['flag_092'], 10)
    if 'mode_092' not in record:
        pass
    elif record['mode_092'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_092'])
    return out

# unit r093
def encode_r093(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_093'] = enum_encode(record['state_0'], {'ready': 'R93', 'held': 'H93', 'done': 'D93'})
    if 'amount_1' not in record:
        out['qty_093'] = 30
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_093'] = scale_encode(record['amount_1'], 10)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_093'] = None
    else:
        out['flag_093'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_093'] = text_encode(record['title_3'])
    return out

def decode_r093(record: dict) -> dict:
    out = {}
    if 'v_093' not in record:
        pass
    elif record['v_093'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_093'], {'ready': 'R93', 'held': 'H93', 'done': 'D93'})
    if 'qty_093' not in record:
        out['amount_1'] = 3
    elif record['qty_093'] is None:
        raise ValueError('qty_093')
    else:
        out['amount_1'] = scale_decode(record['qty_093'], 10)
    if 'flag_093' not in record:
        raise KeyError('flag_093')
    elif record['flag_093'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_093'])
    if 'mode_093' not in record:
        pass
    elif record['mode_093'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_093'])
    return out

# unit r094
def encode_r094(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_094'] = scale_encode(record['amount_0'], 10)
    if 'labels_1' not in record:
        out['qty_094'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_094'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_094'] = None
    else:
        out['flag_094'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_094'] = decimal_encode(record['count_3'])
    return out

def decode_r094(record: dict) -> dict:
    out = {}
    if 'v_094' not in record:
        pass
    elif record['v_094'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_094'], 10)
    if 'qty_094' not in record:
        out['labels_1'] = ['default']
    elif record['qty_094'] is None:
        raise ValueError('qty_094')
    else:
        out['labels_1'] = strings_decode(record['qty_094'])
    if 'flag_094' not in record:
        raise KeyError('flag_094')
    elif record['flag_094'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_094'])
    if 'mode_094' not in record:
        pass
    elif record['mode_094'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_094'])
    return out

# unit r095
def encode_r095(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_095'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_095'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_095'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_095'] = None
    else:
        out['flag_095'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_095'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r095(record: dict) -> dict:
    out = {}
    if 'v_095' not in record:
        pass
    elif record['v_095'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_095'])
    if 'qty_095' not in record:
        out['title_1'] = 'unset'
    elif record['qty_095'] is None:
        raise ValueError('qty_095')
    else:
        out['title_1'] = text_decode(record['qty_095'])
    if 'flag_095' not in record:
        raise KeyError('flag_095')
    elif record['flag_095'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_095'])
    if 'mode_095' not in record:
        pass
    elif record['mode_095'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_095'], ['yes', 'no'])
    return out

# unit r096
def encode_r096(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_096'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_096'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_096'] = None
    else:
        out['qty_096'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_096'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_096'] = 'H96'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_096'] = enum_encode(record['state_3'], {'ready': 'R96', 'held': 'H96', 'done': 'D96'})
    return out

def decode_r096(record: dict) -> dict:
    out = {}
    if 'v_096' not in record:
        out['title_0'] = 'unset'
    elif record['v_096'] is None:
        raise ValueError('v_096')
    else:
        out['title_0'] = text_decode(record['v_096'])
    if 'qty_096' not in record:
        raise KeyError('qty_096')
    elif record['qty_096'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_096'])
    if 'flag_096' not in record:
        pass
    elif record['flag_096'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_096'], ['ON', 'OFF'])
    if 'mode_096' not in record:
        out['state_3'] = 'held'
    elif record['mode_096'] is None:
        raise ValueError('mode_096')
    else:
        out['state_3'] = enum_decode(record['mode_096'], {'ready': 'R96', 'held': 'H96', 'done': 'D96'})
    return out

