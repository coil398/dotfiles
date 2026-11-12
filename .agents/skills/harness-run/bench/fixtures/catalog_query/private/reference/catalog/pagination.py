def pagination(offset, limit, page=False):
    if type(offset) is not int or offset < 0:
        raise ValueError('offset must be a nonnegative integer')
    if limit is None and not page:
        return
    if type(limit) is not int or limit < 0:
        raise ValueError('limit must be a nonnegative integer')

