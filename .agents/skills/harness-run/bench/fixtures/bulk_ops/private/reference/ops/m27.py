def group_rows(rows: list[dict], key: str):
    out = {}
    for row in rows: out.setdefault(row[key], []).append(row.copy())
    return out


def sort_rows(rows: list[dict], key: str):
    return [row.copy() for row in sorted(rows, key=lambda row: row[key])]
