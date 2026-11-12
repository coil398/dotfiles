from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r073
def encode_r073(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_073'] = None
    else:
        out['v_073'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_073'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_073'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_073'] = enum_encode(record['state_2'], {'ready': 'R73', 'held': 'H73', 'done': 'D73'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_073'] = None
    else:
        out['mode_073'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r073(record: dict) -> dict:
    out = {}
    if 'v_073' not in record:
        pass
    elif record['v_073'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_073'])
    if 'qty_073' not in record:
        out['active_1'] = False
    elif record['qty_073'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_073'], ['yes', 'no'])
    if 'flag_073' not in record:
        raise KeyError('flag_073')
    elif record['flag_073'] is None:
        raise ValueError('flag_073')
    else:
        out['state_2'] = enum_decode(record['flag_073'], {'ready': 'R73', 'held': 'H73', 'done': 'D73'})
    if 'mode_073' not in record:
        pass
    elif record['mode_073'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_073'], 2)
    return out

# unit r074
def encode_r074(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_074'] = None
    else:
        out['v_074'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_074'] = 'H74'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_074'] = enum_encode(record['state_1'], {'ready': 'R74', 'held': 'H74', 'done': 'D74'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_074'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_074'] = None
    else:
        out['mode_074'] = strings_encode(record['labels_3'])
    return out

def decode_r074(record: dict) -> dict:
    out = {}
    if 'v_074' not in record:
        pass
    elif record['v_074'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_074'], ['ON', 'OFF'])
    if 'qty_074' not in record:
        out['state_1'] = 'held'
    elif record['qty_074'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_074'], {'ready': 'R74', 'held': 'H74', 'done': 'D74'})
    if 'flag_074' not in record:
        raise KeyError('flag_074')
    elif record['flag_074'] is None:
        raise ValueError('flag_074')
    else:
        out['amount_2'] = scale_decode(record['flag_074'], 2)
    if 'mode_074' not in record:
        pass
    elif record['mode_074'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_074'])
    return out

# unit r075
def encode_r075(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_075'] = enum_encode(record['state_0'], {'ready': 'R75', 'held': 'H75', 'done': 'D75'})
    if 'amount_1' not in record:
        out['qty_075'] = 6
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_075'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_075'] = None
    else:
        out['flag_075'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_075'] = text_encode(record['title_3'])
    return out

def decode_r075(record: dict) -> dict:
    out = {}
    if 'v_075' not in record:
        pass
    elif record['v_075'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_075'], {'ready': 'R75', 'held': 'H75', 'done': 'D75'})
    if 'qty_075' not in record:
        out['amount_1'] = 3
    elif record['qty_075'] is None:
        raise ValueError('qty_075')
    else:
        out['amount_1'] = scale_decode(record['qty_075'], 2)
    if 'flag_075' not in record:
        raise KeyError('flag_075')
    elif record['flag_075'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_075'])
    if 'mode_075' not in record:
        pass
    elif record['mode_075'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_075'])
    return out

# unit r076
def encode_r076(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_076'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        out['qty_076'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_076'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_076'] = None
    else:
        out['flag_076'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_076'] = decimal_encode(record['count_3'])
    return out

def decode_r076(record: dict) -> dict:
    out = {}
    if 'v_076' not in record:
        pass
    elif record['v_076'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_076'], 2)
    if 'qty_076' not in record:
        out['labels_1'] = ['default']
    elif record['qty_076'] is None:
        raise ValueError('qty_076')
    else:
        out['labels_1'] = strings_decode(record['qty_076'])
    if 'flag_076' not in record:
        raise KeyError('flag_076')
    elif record['flag_076'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_076'])
    if 'mode_076' not in record:
        pass
    elif record['mode_076'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_076'])
    return out

# unit r077
def encode_r077(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_077'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_077'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_077'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_077'] = None
    else:
        out['flag_077'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_077'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r077(record: dict) -> dict:
    out = {}
    if 'v_077' not in record:
        pass
    elif record['v_077'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_077'])
    if 'qty_077' not in record:
        out['title_1'] = 'unset'
    elif record['qty_077'] is None:
        raise ValueError('qty_077')
    else:
        out['title_1'] = text_decode(record['qty_077'])
    if 'flag_077' not in record:
        raise KeyError('flag_077')
    elif record['flag_077'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_077'])
    if 'mode_077' not in record:
        pass
    elif record['mode_077'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_077'], ['yes', 'no'])
    return out

# unit r078
def encode_r078(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_078'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_078'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_078'] = None
    else:
        out['qty_078'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_078'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_078'] = 'H78'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_078'] = enum_encode(record['state_3'], {'ready': 'R78', 'held': 'H78', 'done': 'D78'})
    return out

def decode_r078(record: dict) -> dict:
    out = {}
    if 'v_078' not in record:
        out['title_0'] = 'unset'
    elif record['v_078'] is None:
        raise ValueError('v_078')
    else:
        out['title_0'] = text_decode(record['v_078'])
    if 'qty_078' not in record:
        raise KeyError('qty_078')
    elif record['qty_078'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_078'])
    if 'flag_078' not in record:
        pass
    elif record['flag_078'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_078'], ['ON', 'OFF'])
    if 'mode_078' not in record:
        out['state_3'] = 'held'
    elif record['mode_078'] is None:
        raise ValueError('mode_078')
    else:
        out['state_3'] = enum_decode(record['mode_078'], {'ready': 'R78', 'held': 'H78', 'done': 'D78'})
    return out

