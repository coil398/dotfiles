def split_first(text: str, separator: str):
    a, _, b = text.partition(separator)
    return [a,b]


def split_last(text: str, separator: str):
    a, sep, b = text.rpartition(separator)
    return [a,b] if sep else [text, ""]
