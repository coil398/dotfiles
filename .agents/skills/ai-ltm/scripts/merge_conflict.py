#!/usr/bin/env python3
"""
ai-ltm merge_conflict: Merge episodes from a local dump into the remote DB.

Used when git pull causes a binary conflict on memory.db.
The workflow is:
  1. Before resolving: dump local episodes to JSON
  2. After checking out remote version: import local episodes, skipping duplicates

Usage:
  # Step 1: Dump local episodes before checkout --theirs
  python3 merge_conflict.py dump --db ~/ai-ltm-data/memory.db --out /tmp/ltm_local.json

  # Step 2: After git checkout --theirs memory.db, import the dump
  python3 merge_conflict.py import --db ~/ai-ltm-data/memory.db --input /tmp/ltm_local.json
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path


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
