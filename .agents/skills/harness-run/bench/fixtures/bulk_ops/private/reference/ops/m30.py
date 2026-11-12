def distinct_rows(rows: list[dict], key: str):
    seen = set()
    out = []
    for row in rows:
        if row[key] not in seen:
            seen.add(row[key])
            out.append(row.copy())
    return out


def transpose_records(rows: list[dict], keys: list[str], default: int):
    return {k: [row.get(k, default) for row in rows] for k in keys}
