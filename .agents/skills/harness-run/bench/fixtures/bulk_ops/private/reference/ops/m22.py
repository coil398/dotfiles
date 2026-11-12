def ceil_div(value: int, divisor: int):
    return -(-value // divisor)


def round_multiple(value: int, step: int):
    q, r = divmod(value, step)
    return (q + (2*r >= step)) * step
