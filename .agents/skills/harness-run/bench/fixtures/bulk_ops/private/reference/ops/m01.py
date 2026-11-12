def slug(text: str):
    import re
    return re.sub('[^a-z0-9]+', '-', ''.join(chr(ord(c)+32) if 'A' <= c <= 'Z' else c for c in text)).strip('-')


def collapse_spaces(text: str):
    return ' '.join(text.split())
