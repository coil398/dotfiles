def project_rows(rows: list[dict], keys: list[str]):
    return [{k: row[k] for k in keys if k in row} for row in rows]


def number_rows(rows: list[dict], start: int):
    out = []
    for i, row in enumerate(rows):
        copy = row.copy()
        copy['_index'] = start+i
        out.append(copy)
    return out
