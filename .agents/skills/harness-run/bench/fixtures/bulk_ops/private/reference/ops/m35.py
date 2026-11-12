def title_tokens(text: str):
    return ' '.join(w[0].upper()+w[1:].lower() for w in text.split())


def char_counts(text: str):
    out = {}
    for c in text: out[c] = out.get(c, 0) + 1
    return out
