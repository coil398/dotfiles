def line_numbers(text: str):
    return [f'{i}: {line}' for i, line in enumerate(text.splitlines(), 1)]


def word_lengths(text: str):
    return [len(word) for word in text.split()]
