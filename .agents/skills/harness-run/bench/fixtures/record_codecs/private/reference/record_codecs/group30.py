from .primitives import (text_encode, text_decode, decimal_encode, decimal_decode, boolean_encode, boolean_decode, enum_encode, enum_decode, scale_encode, scale_decode, strings_encode, strings_decode)

# unit r181
def encode_r181(record: dict) -> dict:
    out = {}
    if 'count_0' not in record:
        pass
    elif record['count_0'] is None:
        out['v_181'] = None
    else:
        out['v_181'] = decimal_encode(record['count_0'])
    if 'active_1' not in record:
        out['qty_181'] = 'no'
    elif record['active_1'] is None:
        pass
    else:
        out['qty_181'] = boolean_encode(record['active_1'], ['yes', 'no'])
    if 'state_2' not in record:
        raise KeyError('state_2')
    elif record['state_2'] is None:
        raise ValueError('state_2')
    else:
        out['flag_181'] = enum_encode(record['state_2'], {'ready': 'R181', 'held': 'H181', 'done': 'D181'})
    if 'amount_3' not in record:
        pass
    elif record['amount_3'] is None:
        out['mode_181'] = None
    else:
        out['mode_181'] = scale_encode(record['amount_3'], 2)
    return out

def decode_r181(record: dict) -> dict:
    out = {}
    if 'v_181' not in record:
        pass
    elif record['v_181'] is None:
        out['count_0'] = None
    else:
        out['count_0'] = decimal_decode(record['v_181'])
    if 'qty_181' not in record:
        out['active_1'] = False
    elif record['qty_181'] is None:
        pass
    else:
        out['active_1'] = boolean_decode(record['qty_181'], ['yes', 'no'])
    if 'flag_181' not in record:
        raise KeyError('flag_181')
    elif record['flag_181'] is None:
        raise ValueError('flag_181')
    else:
        out['state_2'] = enum_decode(record['flag_181'], {'ready': 'R181', 'held': 'H181', 'done': 'D181'})
    if 'mode_181' not in record:
        pass
    elif record['mode_181'] is None:
        out['amount_3'] = None
    else:
        out['amount_3'] = scale_decode(record['mode_181'], 2)
    return out

# unit r182
def encode_r182(record: dict) -> dict:
    out = {}
    if 'active_0' not in record:
        pass
    elif record['active_0'] is None:
        out['v_182'] = None
    else:
        out['v_182'] = boolean_encode(record['active_0'], ['ON', 'OFF'])
    if 'state_1' not in record:
        out['qty_182'] = 'H182'
    elif record['state_1'] is None:
        pass
    else:
        out['qty_182'] = enum_encode(record['state_1'], {'ready': 'R182', 'held': 'H182', 'done': 'D182'})
    if 'amount_2' not in record:
        raise KeyError('amount_2')
    elif record['amount_2'] is None:
        raise ValueError('amount_2')
    else:
        out['flag_182'] = scale_encode(record['amount_2'], 2)
    if 'labels_3' not in record:
        pass
    elif record['labels_3'] is None:
        out['mode_182'] = None
    else:
        out['mode_182'] = strings_encode(record['labels_3'])
    return out

def decode_r182(record: dict) -> dict:
    out = {}
    if 'v_182' not in record:
        pass
    elif record['v_182'] is None:
        out['active_0'] = None
    else:
        out['active_0'] = boolean_decode(record['v_182'], ['ON', 'OFF'])
    if 'qty_182' not in record:
        out['state_1'] = 'held'
    elif record['qty_182'] is None:
        pass
    else:
        out['state_1'] = enum_decode(record['qty_182'], {'ready': 'R182', 'held': 'H182', 'done': 'D182'})
    if 'flag_182' not in record:
        raise KeyError('flag_182')
    elif record['flag_182'] is None:
        raise ValueError('flag_182')
    else:
        out['amount_2'] = scale_decode(record['flag_182'], 2)
    if 'mode_182' not in record:
        pass
    elif record['mode_182'] is None:
        out['labels_3'] = None
    else:
        out['labels_3'] = strings_decode(record['mode_182'])
    return out

# unit r183
def encode_r183(record: dict) -> dict:
    out = {}
    if 'state_0' not in record:
        pass
    elif record['state_0'] is None:
        pass
    else:
        out['v_183'] = enum_encode(record['state_0'], {'ready': 'R183', 'held': 'H183', 'done': 'D183'})
    if 'amount_1' not in record:
        out['qty_183'] = 6
    elif record['amount_1'] is None:
        raise ValueError('amount_1')
    else:
        out['qty_183'] = scale_encode(record['amount_1'], 2)
    if 'labels_2' not in record:
        raise KeyError('labels_2')
    elif record['labels_2'] is None:
        out['flag_183'] = None
    else:
        out['flag_183'] = strings_encode(record['labels_2'])
    if 'title_3' not in record:
        pass
    elif record['title_3'] is None:
        pass
    else:
        out['mode_183'] = text_encode(record['title_3'])
    return out

def decode_r183(record: dict) -> dict:
    out = {}
    if 'v_183' not in record:
        pass
    elif record['v_183'] is None:
        pass
    else:
        out['state_0'] = enum_decode(record['v_183'], {'ready': 'R183', 'held': 'H183', 'done': 'D183'})
    if 'qty_183' not in record:
        out['amount_1'] = 3
    elif record['qty_183'] is None:
        raise ValueError('qty_183')
    else:
        out['amount_1'] = scale_decode(record['qty_183'], 2)
    if 'flag_183' not in record:
        raise KeyError('flag_183')
    elif record['flag_183'] is None:
        out['labels_2'] = None
    else:
        out['labels_2'] = strings_decode(record['flag_183'])
    if 'mode_183' not in record:
        pass
    elif record['mode_183'] is None:
        pass
    else:
        out['title_3'] = text_decode(record['mode_183'])
    return out

# unit r184
def encode_r184(record: dict) -> dict:
    out = {}
    if 'amount_0' not in record:
        pass
    elif record['amount_0'] is None:
        pass
    else:
        out['v_184'] = scale_encode(record['amount_0'], 2)
    if 'labels_1' not in record:
        out['qty_184'] = ['default']
    elif record['labels_1'] is None:
        raise ValueError('labels_1')
    else:
        out['qty_184'] = strings_encode(record['labels_1'])
    if 'title_2' not in record:
        raise KeyError('title_2')
    elif record['title_2'] is None:
        out['flag_184'] = None
    else:
        out['flag_184'] = text_encode(record['title_2'])
    if 'count_3' not in record:
        pass
    elif record['count_3'] is None:
        pass
    else:
        out['mode_184'] = decimal_encode(record['count_3'])
    return out

def decode_r184(record: dict) -> dict:
    out = {}
    if 'v_184' not in record:
        pass
    elif record['v_184'] is None:
        pass
    else:
        out['amount_0'] = scale_decode(record['v_184'], 2)
    if 'qty_184' not in record:
        out['labels_1'] = ['default']
    elif record['qty_184'] is None:
        raise ValueError('qty_184')
    else:
        out['labels_1'] = strings_decode(record['qty_184'])
    if 'flag_184' not in record:
        raise KeyError('flag_184')
    elif record['flag_184'] is None:
        out['title_2'] = None
    else:
        out['title_2'] = text_decode(record['flag_184'])
    if 'mode_184' not in record:
        pass
    elif record['mode_184'] is None:
        pass
    else:
        out['count_3'] = decimal_decode(record['mode_184'])
    return out

# unit r185
def encode_r185(record: dict) -> dict:
    out = {}
    if 'labels_0' not in record:
        pass
    elif record['labels_0'] is None:
        pass
    else:
        out['v_185'] = strings_encode(record['labels_0'])
    if 'title_1' not in record:
        out['qty_185'] = 'unset'
    elif record['title_1'] is None:
        raise ValueError('title_1')
    else:
        out['qty_185'] = text_encode(record['title_1'])
    if 'count_2' not in record:
        raise KeyError('count_2')
    elif record['count_2'] is None:
        out['flag_185'] = None
    else:
        out['flag_185'] = decimal_encode(record['count_2'])
    if 'active_3' not in record:
        pass
    elif record['active_3'] is None:
        pass
    else:
        out['mode_185'] = boolean_encode(record['active_3'], ['yes', 'no'])
    return out

def decode_r185(record: dict) -> dict:
    out = {}
    if 'v_185' not in record:
        pass
    elif record['v_185'] is None:
        pass
    else:
        out['labels_0'] = strings_decode(record['v_185'])
    if 'qty_185' not in record:
        out['title_1'] = 'unset'
    elif record['qty_185'] is None:
        raise ValueError('qty_185')
    else:
        out['title_1'] = text_decode(record['qty_185'])
    if 'flag_185' not in record:
        raise KeyError('flag_185')
    elif record['flag_185'] is None:
        out['count_2'] = None
    else:
        out['count_2'] = decimal_decode(record['flag_185'])
    if 'mode_185' not in record:
        pass
    elif record['mode_185'] is None:
        pass
    else:
        out['active_3'] = boolean_decode(record['mode_185'], ['yes', 'no'])
    return out

# unit r186
def encode_r186(record: dict) -> dict:
    out = {}
    if 'title_0' not in record:
        out['v_186'] = 'unset'
    elif record['title_0'] is None:
        raise ValueError('title_0')
    else:
        out['v_186'] = text_encode(record['title_0'])
    if 'count_1' not in record:
        raise KeyError('count_1')
    elif record['count_1'] is None:
        out['qty_186'] = None
    else:
        out['qty_186'] = decimal_encode(record['count_1'])
    if 'active_2' not in record:
        pass
    elif record['active_2'] is None:
        pass
    else:
        out['flag_186'] = boolean_encode(record['active_2'], ['ON', 'OFF'])
    if 'state_3' not in record:
        out['mode_186'] = 'H186'
    elif record['state_3'] is None:
        raise ValueError('state_3')
    else:
        out['mode_186'] = enum_encode(record['state_3'], {'ready': 'R186', 'held': 'H186', 'done': 'D186'})
    return out

def decode_r186(record: dict) -> dict:
    out = {}
    if 'v_186' not in record:
        out['title_0'] = 'unset'
    elif record['v_186'] is None:
        raise ValueError('v_186')
    else:
        out['title_0'] = text_decode(record['v_186'])
    if 'qty_186' not in record:
        raise KeyError('qty_186')
    elif record['qty_186'] is None:
        out['count_1'] = None
    else:
        out['count_1'] = decimal_decode(record['qty_186'])
    if 'flag_186' not in record:
        pass
    elif record['flag_186'] is None:
        pass
    else:
        out['active_2'] = boolean_decode(record['flag_186'], ['ON', 'OFF'])
    if 'mode_186' not in record:
        out['state_3'] = 'held'
    elif record['mode_186'] is None:
        raise ValueError('mode_186')
    else:
        out['state_3'] = enum_decode(record['mode_186'], {'ready': 'R186', 'held': 'H186', 'done': 'D186'})
    return out

