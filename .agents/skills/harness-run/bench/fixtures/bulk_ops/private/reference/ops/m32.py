def join_nonempty(items: list[str], separator: str):
    return separator.join(x for x in items if x != "")


def replace_words(text: str, replacements: dict[str, str]):
    return ' '.join(replacements.get(word, word) for word in text.split())
