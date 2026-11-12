def truncate(text: str, limit: int, marker: str):
    if len(text) <= limit: return text
    if len(marker) >= limit: return marker[:limit]
    return text[:limit-len(marker)] + marker


def ascii_digits(text: str):
    return ''.join(c for c in text if '0' <= c <= '9')
