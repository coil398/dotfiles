def filter_rows(rows: list[dict], key: str, value: int):
    return [row.copy() for row in rows if key in row and row[key] == value]


def sum_column(rows: list[dict], key: str):
    return sum(row.get(key, 0) for row in rows)
