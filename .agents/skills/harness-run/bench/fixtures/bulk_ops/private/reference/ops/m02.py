def strip_prefix(text: str, prefix: str):
    return text[len(prefix):] if prefix and text.startswith(prefix) else text


def strip_suffix(text: str, suffix: str):
    return text[:-len(suffix)] if suffix and text.endswith(suffix) else text
