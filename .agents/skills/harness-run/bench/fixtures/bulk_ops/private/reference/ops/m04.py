def mask_tail(text: str, keep: int):
    n = max(0, len(text) - keep)
    return '*' * n + text[n:]


def initials(text: str):
    return ''.join(word[0].upper() for word in text.split())
