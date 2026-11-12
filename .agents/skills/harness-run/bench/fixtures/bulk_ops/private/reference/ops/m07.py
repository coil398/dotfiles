def chunks(items: list[int], size: int):
    return [items[i:i+size] for i in range(0, len(items), size)]


def windows(items: list[int], size: int):
    return [items[i:i+size] for i in range(len(items)-size+1)]
