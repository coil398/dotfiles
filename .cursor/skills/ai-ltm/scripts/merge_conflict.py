#!/usr/bin/env python3
"""
ai-ltm merge_conflict: Explicit episode dump/import utilities.

通常の同期と競合復旧には sync_memory.py を使用する。このスクリプトの
dump/import は明示的なデータ移送が必要な場合だけ使用し、Git の片側を
checkout して SQLite を上書きする手順には使わない。

Usage:
  python3 merge_conflict.py dump --db ~/ai-ltm-data/memory.db --out /tmp/ltm_local.json
  python3 merge_conflict.py import --db ~/ai-ltm-data/memory.db --input /tmp/ltm_local.json
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any


MERGED_TABLES = ("episodes", "meta", "config")


def dump_episodes(db_path: str, out_path: str) -> int:
    """Dump all episodes to a JSON file."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT summary, context, tags, embedding, created_at FROM episodes"
    ).fetchall()
    conn.close()

    episodes = [dict(r) for r in rows]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)
    return len(episodes)


def import_episodes(db_path: str, input_path: str) -> tuple[int, int]:
    """Import episodes from JSON, skipping duplicates (same summary + created_at)."""
    with open(input_path, "r", encoding="utf-8") as f:
        episodes = json.load(f)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    imported = 0
    skipped = 0
    for ep in episodes:
        # Check for duplicate by summary + created_at
        existing = conn.execute(
            "SELECT id FROM episodes WHERE summary = ? AND created_at = ?",
            (ep["summary"], ep["created_at"]),
        ).fetchone()

        if existing:
            skipped += 1
            continue

        conn.execute(
            """INSERT INTO episodes (summary, context, tags, embedding, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (ep["summary"], ep["context"], ep["tags"],
             ep.get("embedding"), ep["created_at"]),
        )
        imported += 1

    conn.commit()
    conn.close()
    return imported, skipped


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def _table_info(conn: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    return conn.execute(f'PRAGMA table_info("{table}")').fetchall()


def _primary_key(columns: list[sqlite3.Row]) -> list[str]:
    return [row["name"] for row in sorted(columns, key=lambda row: row["pk"]) if row["pk"]]


def _read_rows(
    conn: sqlite3.Connection, table: str, key_columns: list[str]
) -> dict[tuple[Any, ...], dict[str, Any]]:
    rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
    return {
        tuple(row[column] for column in key_columns): dict(row)
        for row in rows
    }


def _merge_episode_row(
    base: dict[str, Any], local: dict[str, Any], remote: dict[str, Any]
) -> tuple[dict[str, Any], bool]:
    merged = dict(remote)
    ambiguous = False
    for column in merged:
        if column == "id":
            continue
        base_value = base.get(column)
        local_value = local.get(column)
        remote_value = remote.get(column)
        if local_value == remote_value or local_value == base_value:
            continue
        if remote_value == base_value:
            merged[column] = local_value
        elif column == "used_count":
            base_count = base_value or 0
            merged[column] = max(0, base_count + (local_value or 0) - base_count + (remote_value or 0) - base_count)
        elif column == "last_used_at":
            merged[column] = max(value for value in (local_value, remote_value) if value is not None)
        elif column == "archived":
            # Concurrent disagreement keeps the episode visible. Normal one-sided
            # archive/unarchive changes are handled by the base comparisons above.
            merged[column] = min(local_value or 0, remote_value or 0)
        else:
            ambiguous = True
    return merged, ambiguous


def _insert_row(conn: sqlite3.Connection, table: str, row: dict[str, Any]) -> None:
    columns = list(row)
    quoted = ", ".join(f'"{column}"' for column in columns)
    placeholders = ", ".join("?" for _ in columns)
    conn.execute(
        f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})',
        [row[column] for column in columns],
    )


def _replace_row(
    conn: sqlite3.Connection,
    table: str,
    key_columns: list[str],
    key: tuple[Any, ...],
    row: dict[str, Any],
) -> None:
    assignments = ", ".join(f'"{column}" = ?' for column in row if column not in key_columns)
    predicate = " AND ".join(f'"{column}" IS ?' for column in key_columns)
    values = [row[column] for column in row if column not in key_columns]
    conn.execute(
        f'UPDATE "{table}" SET {assignments} WHERE {predicate}',
        values + list(key),
    )


def _merge_table(
    target: sqlite3.Connection,
    base: sqlite3.Connection,
    local: sqlite3.Connection,
    remote: sqlite3.Connection,
    table: str,
) -> None:
    present = [_table_exists(conn, table) for conn in (base, local, remote)]
    if not any(present):
        return
    if not all(present):
        raise ValueError(f"schema mismatch: table {table!r} is not present in all databases")

    column_sets = [[row["name"] for row in _table_info(conn, table)] for conn in (base, local, remote)]
    if column_sets[0] != column_sets[1] or column_sets[0] != column_sets[2]:
        raise ValueError(f"schema mismatch: columns differ for table {table!r}")
    columns = _table_info(target, table)
    key_columns = _primary_key(columns)
    if not key_columns:
        raise ValueError(f"cannot merge table without primary key: {table!r}")

    base_rows = _read_rows(base, table, key_columns)
    local_rows = _read_rows(local, table, key_columns)
    remote_rows = _read_rows(remote, table, key_columns)
    next_episode_id = None
    if table == "episodes" and key_columns == ["id"]:
        integer_ids = [key[0] for key in set(base_rows) | set(local_rows) | set(remote_rows) if isinstance(key[0], int)]
        next_episode_id = max(integer_ids, default=0) + 1

    for key in sorted(set(base_rows) | set(local_rows) | set(remote_rows), key=repr):
        if table == "config" and key == ("_idf",):
            continue
        base_row = base_rows.get(key)
        local_row = local_rows.get(key)
        remote_row = remote_rows.get(key)

        if local_row == remote_row or local_row == base_row:
            continue
        if remote_row == base_row:
            if local_row is None:
                predicate = " AND ".join(f'"{column}" IS ?' for column in key_columns)
                target.execute(f'DELETE FROM "{table}" WHERE {predicate}', list(key))
            elif remote_row is None:
                _insert_row(target, table, local_row)
            else:
                _replace_row(target, table, key_columns, key, local_row)
            continue

        if local_row is None:
            continue
        if remote_row is None:
            _insert_row(target, table, local_row)
            continue

        if table == "episodes":
            if base_row is None:
                local_copy = dict(local_row)
                local_copy["id"] = next_episode_id
                next_episode_id += 1
                _insert_row(target, table, local_copy)
                continue
            merged, ambiguous = _merge_episode_row(base_row, local_row, remote_row)
            _replace_row(target, table, key_columns, key, merged)
            if ambiguous:
                local_copy = dict(local_row)
                local_copy["id"] = next_episode_id
                next_episode_id += 1
                _insert_row(target, table, local_copy)
            continue

        raise ValueError(f"simultaneous conflicting changes in {table!r} for key {key!r}")


def _refresh_search_state_if_needed(
    target: sqlite3.Connection, base: sqlite3.Connection
) -> None:
    if not _table_exists(target, "episodes"):
        return
    text_columns = ("id", "summary", "context", "tags")
    projection = ", ".join(f'"{column}"' for column in text_columns)
    target_rows = target.execute(
        f'SELECT {projection} FROM episodes ORDER BY id'
    ).fetchall()
    base_rows = base.execute(
        f'SELECT {projection} FROM episodes ORDER BY id'
    ).fetchall()
    corpus_changed = [tuple(row) for row in target_rows] != [tuple(row) for row in base_rows]
    if corpus_changed:
        target.execute("UPDATE episodes SET embedding = NULL")
        if _table_exists(target, "config"):
            target.execute("DELETE FROM config WHERE key = '_idf'")

    if not _table_exists(target, "episodes_fts"):
        return
    if corpus_changed:
        target.execute("INSERT INTO episodes_fts(episodes_fts) VALUES ('rebuild')")
    target.execute(
        "INSERT INTO episodes_fts(episodes_fts, rank) VALUES ('integrity-check', 1)"
    )


def validate_database(db_path: str | Path) -> None:
    """Raise ValueError unless SQLite reports a healthy database."""
    try:
        with sqlite3.connect(db_path) as conn:
            result = conn.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.Error as exc:
        raise ValueError(f"invalid SQLite database: {db_path}: {exc}") from exc
    if result is None or result[0] != "ok":
        raise ValueError(f"SQLite integrity check failed for {db_path}: {result}")


def merge_databases(
    base_path: str | Path,
    local_path: str | Path,
    remote_path: str | Path,
    output_path: str | Path,
) -> None:
    """Three-way merge episodes, meta and config into an atomic database copy."""
    for path in (base_path, local_path, remote_path):
        validate_database(path)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(remote_path, temporary)
        connections = [sqlite3.connect(path) for path in (temporary, base_path, local_path, remote_path)]
        try:
            for conn in connections:
                conn.row_factory = sqlite3.Row
            target, base, local, remote = connections
            target.execute("BEGIN IMMEDIATE")
            for table in MERGED_TABLES:
                _merge_table(target, base, local, remote, table)
            _refresh_search_state_if_needed(target, base)
            target.commit()
        except Exception:
            connections[0].rollback()
            raise
        finally:
            for conn in connections:
                conn.close()
        validate_database(temporary)
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="ai-ltm merge conflict resolver")
    parser.add_argument("command", choices=["dump", "import"])
    parser.add_argument("--db", required=True, help="Path to memory.db")
    parser.add_argument("--out", help="Output JSON path (for dump)")
    parser.add_argument("--input", help="Input JSON path (for import)")
    args = parser.parse_args()

    db_path = str(Path(args.db).expanduser())

    if args.command == "dump":
        if not args.out:
            print("Error: --out required for dump command", file=sys.stderr)
            sys.exit(1)
        if not Path(db_path).exists():
            print(f"Error: database not found: {db_path}", file=sys.stderr)
            sys.exit(1)
        count = dump_episodes(db_path, args.out)
        print(f"Dumped {count} episodes to {args.out}")

    elif args.command == "import":
        if not args.input:
            print("Error: --input required for import command", file=sys.stderr)
            sys.exit(1)
        if not Path(db_path).exists():
            print(f"Error: database not found: {db_path}", file=sys.stderr)
            sys.exit(1)
        if not Path(args.input).exists():
            print(f"Error: input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        imported, skipped = import_episodes(db_path, args.input)
        print(f"Imported {imported} episodes, skipped {skipped} duplicates.")


if __name__ == "__main__":
    main()
