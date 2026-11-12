def common_prefix(left: str, right: str):
    i = 0
    while i < min(len(left), len(right)) and left[i] == right[i]:
        i += 1
    return left[:i]


def common_suffix(left: str, right: str):
    i = 0
    while i < min(len(left), len(right)) and left[-1-i] == right[-1-i]:
        i += 1
    return left[len(left)-i:]
