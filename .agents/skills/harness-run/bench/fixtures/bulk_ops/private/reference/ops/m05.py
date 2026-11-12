def escape_pairs(text: str):
    return ''.join(chr(92) + c if c in (chr(92), '|') else c for c in text)


def rotate_text(text: str, offset: int):
    if not text:
        return text
    k = offset % len(text)
    return text[k:] + text[:k]
