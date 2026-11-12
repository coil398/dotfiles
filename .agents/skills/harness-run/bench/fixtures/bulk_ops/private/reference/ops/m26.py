def pluck(rows: list[dict], key: str, default: int):
    return [row.get(key, default) for row in rows]


def index_last(rows: list[dict], key: str):
    return {row[key]: row.copy() for row in rows}
