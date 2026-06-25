#!/usr/bin/env python3
"""
ai-ltm vector search: TF-IDF + cosine similarity (Python stdlib only).

Usage:
  # Search episodes by vector similarity
  python3 vector_search.py search --db ~/ai-ltm-data/memory.db --query "some query" --limit 5

  # Search with tag/date filters
  python3 vector_search.py search --db ~/ai-ltm-data/memory.db --query "query" --tags "learning typescript" --since 2025-01-01

  # Rebuild embeddings for all episodes (run after bulk import or schema migration)
  python3 vector_search.py rebuild --db ~/ai-ltm-data/memory.db

  # Combined search: FTS + vector, weighted by config table values
  python3 vector_search.py combined --db ~/ai-ltm-data/memory.db --query "some query" --limit 10

  # Embed a single episode
  python3 vector_search.py embed --db ~/ai-ltm-data/memory.db --id 42

  # Mark episodes as used (increment used_count, update last_used_at)
  python3 vector_search.py mark-used --db ~/ai-ltm-data/memory.db --ids 1,2,3

  # Archive old unused episodes
  python3 vector_search.py archive --db ~/ai-ltm-data/memory.db

  # Unarchive episodes by ID
  python3 vector_search.py unarchive --db ~/ai-ltm-data/memory.db --ids 1,2,3
"""

import argparse
import json
import math
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path


_RE_CJK = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff\u3400-\u9fff\uf900-\ufaff\U00020000-\U0002fa1f]")
_RE_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Split text into tokens. ASCII words stay as-is; CJK uses character bigrams."""
    if not text:
        return []
    text = text.lower()
    tokens: list[str] = []
    # Extract ASCII words
    tokens.extend(_RE_WORD.findall(text))
    # Extract CJK character bigrams for better partial matching
    cjk_chars = _RE_CJK.findall(text)
    for i in range(len(cjk_chars)):
        tokens.append(cjk_chars[i])  # unigram
        if i + 1 < len(cjk_chars):
            tokens.append(cjk_chars[i] + cjk_chars[i + 1])  # bigram
    return tokens


def build_idf(corpus: list[list[str]]) -> dict[str, float]:
    """Compute inverse document frequency for each token in the corpus."""
    n = len(corpus)
    if n == 0:
        return {}
    df: Counter = Counter()
    for tokens in corpus:
        df.update(set(tokens))
    return {token: math.log((n + 1) / (freq + 1)) + 1 for token, freq in df.items()}


def tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    """Compute TF-IDF vector as a sparse dict."""
    tf = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {t: (c / total) * idf.get(t, 1.0) for t, c in tf.items()}


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vectors."""
    if not a or not b:
        return 0.0
    keys = set(a) & set(b)
    dot = sum(a[k] * b[k] for k in keys)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def vector_to_json(vec: dict[str, float]) -> str:
    """Serialize sparse vector to compact JSON."""
    return json.dumps(vec, ensure_ascii=False, separators=(",", ":"))


def json_to_vector(s: str) -> dict[str, float]:
    """Deserialize sparse vector from JSON."""
    if not s:
        return {}
    return json.loads(s)


def episode_text(row: sqlite3.Row) -> str:
    """Concatenate episode fields into a single searchable string."""
    parts = []
    for field in ("summary", "context", "tags"):
        val = row[field]
        if val:
            parts.append(val)
    return " ".join(parts)


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Add missing columns and config defaults for self-improvement features.

    This function is idempotent and safe to run on every invocation. It ensures
    existing memory.db files (created before the self-improvement columns were
    added) get migrated automatically without requiring manual ALTER TABLE.
    """
    # Ensure config table exists (older DBs may lack it if created without init.sql)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)"
    )

    # Check existing columns on episodes
    cur = conn.execute("PRAGMA table_info(episodes)")
    existing_cols = {row[1] for row in cur.fetchall()}

    migrations = [
        ("used_count", "ALTER TABLE episodes ADD COLUMN used_count INTEGER DEFAULT 0"),
        ("last_used_at", "ALTER TABLE episodes ADD COLUMN last_used_at DATETIME"),
        ("archived", "ALTER TABLE episodes ADD COLUMN archived INTEGER DEFAULT 0"),
    ]
    for col, ddl in migrations:
        if col not in existing_cols:
            conn.execute(ddl)

    # Ensure new config defaults exist
    defaults = [
        ("usage_boost_weight", "0.3"),
        ("archive_after_days", "180"),
        ("usage_recency_days", "30"),
    ]
    for key, value in defaults:
        conn.execute(
            "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
            (key, value),
        )

    conn.commit()


def get_config(conn: sqlite3.Connection) -> dict[str, float]:
    """Read config values as floats (skip internal keys starting with '_')."""
    cur = conn.execute("SELECT key, value FROM config WHERE key NOT LIKE '\\_%' ESCAPE '\\'")
    return {row[0]: float(row[1]) for row in cur.fetchall()}


def rebuild_embeddings(conn: sqlite3.Connection) -> int:
    """Rebuild TF-IDF embeddings for all episodes."""
    rows = conn.execute(
        "SELECT id, summary, context, tags FROM episodes"
    ).fetchall()
    if not rows:
        return 0

    corpus = [tokenize(episode_text(r)) for r in rows]
    idf = build_idf(corpus)

    for row, tokens in zip(rows, corpus):
        vec = tfidf_vector(tokens, idf)
        conn.execute(
            "UPDATE episodes SET embedding = ? WHERE id = ?",
            (vector_to_json(vec), row["id"]),
        )

    # Store IDF as a special config entry for incremental updates
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('_idf', ?)",
        (json.dumps(idf, ensure_ascii=False, separators=(",", ":")),),
    )
    conn.commit()
    return len(rows)


def get_idf(conn: sqlite3.Connection) -> dict[str, float]:
    """Get stored IDF, rebuilding if missing."""
    row = conn.execute(
        "SELECT value FROM config WHERE key = '_idf'"
    ).fetchone()
    if row and row[0]:
        return json.loads(row[0])
    # IDF not cached yet; rebuild
    rebuild_embeddings(conn)
    row = conn.execute(
        "SELECT value FROM config WHERE key = '_idf'"
    ).fetchone()
    return json.loads(row[0]) if row and row[0] else {}


def embed_single(conn: sqlite3.Connection, episode_id: int) -> None:
    """Generate and store embedding for a single episode using cached IDF."""
    idf = get_idf(conn)
    row = conn.execute(
        "SELECT summary, context, tags FROM episodes WHERE id = ?",
        (episode_id,),
    ).fetchone()
    if not row:
        return
    tokens = tokenize(episode_text(row))
    vec = tfidf_vector(tokens, idf)
    conn.execute(
        "UPDATE episodes SET embedding = ? WHERE id = ?",
        (vector_to_json(vec), episode_id),
    )
    conn.commit()


def build_filter_clause(
    tags: str | None = None,
    since: str | None = None,
    until: str | None = None,
    include_archived: bool = False,
) -> tuple[str, list]:
    """Build WHERE clause fragments and params for tag/date filtering."""
    clauses = []
    params: list = []
    if not include_archived:
        clauses.append("archived = 0")
    if tags:
        for tag in tags.split():
            clauses.append("tags LIKE ?")
            params.append(f"%{tag}%")
    if since:
        clauses.append("created_at >= ?")
        params.append(since)
    if until:
        clauses.append("created_at <= ?")
        params.append(until)
    where = " AND ".join(clauses)
    return (f" WHERE {where}" if where else ""), params


def search_vector(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 10,
    tags: str | None = None,
    since: str | None = None,
    until: str | None = None,
    include_archived: bool = False,
) -> list[dict]:
    """Search episodes by vector similarity with optional tag/date filters."""
    idf = get_idf(conn)
    query_tokens = tokenize(query)
    query_vec = tfidf_vector(query_tokens, idf)

    where, params = build_filter_clause(tags, since, until, include_archived=include_archived)
    rows = conn.execute(
        f"SELECT id, summary, context, tags, embedding, created_at, used_count FROM episodes{where}",
        params,
    ).fetchall()

    results = []
    for row in rows:
        ep_vec = json_to_vector(row["embedding"])
        sim = cosine_similarity(query_vec, ep_vec)
        if sim > 0:
            results.append(
                {
                    "id": row["id"],
                    "summary": row["summary"],
                    "tags": row["tags"],
                    "created_at": row["created_at"],
                    "used_count": row["used_count"],
                    "vector_score": round(sim, 4),
                }
            )

    results.sort(key=lambda x: x["vector_score"], reverse=True)
    return results[:limit]


def search_combined(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 10,
    tags: str | None = None,
    since: str | None = None,
    until: str | None = None,
    include_archived: bool = False,
) -> list[dict]:
    """Combined FTS + vector search with configurable weights, time decay, and usage boost."""
    cfg = get_config(conn)
    fts_weight = cfg.get("fts_weight", 0.5)
    vec_weight = cfg.get("vector_weight", 0.5)
    decay_days = cfg.get("time_decay_days", 30)
    usage_boost_weight = cfg.get("usage_boost_weight", 0.3)
    usage_recency_days = cfg.get("usage_recency_days", 30)

    # FTS results — join tokens with OR for broader matching
    fts_query = " OR ".join(tokenize(query)) if tokenize(query) else query
    fts_scores: dict[int, float] = {}
    try:
        fts_rows = conn.execute(
            """
            SELECT rowid, rank * -1 AS fts_score
            FROM episodes_fts WHERE episodes_fts MATCH ?
            """,
            (fts_query,),
        ).fetchall()
        if fts_rows:
            max_fts = max(r["fts_score"] for r in fts_rows)
            for r in fts_rows:
                fts_scores[r["rowid"]] = r["fts_score"] / max_fts if max_fts > 0 else 0
    except sqlite3.OperationalError:
        pass  # FTS match syntax may fail; fall back to vector only

    # Vector results (with optional filters, excluding archived)
    idf = get_idf(conn)
    query_tokens = tokenize(query)
    query_vec = tfidf_vector(query_tokens, idf)

    where, params = build_filter_clause(tags, since, until, include_archived=include_archived)
    rows = conn.execute(
        f"SELECT id, summary, context, tags, embedding, created_at, used_count, last_used_at FROM episodes{where}",
        params,
    ).fetchall()

    vec_scores: dict[int, float] = {}
    episode_data: dict[int, dict] = {}
    for row in rows:
        ep_vec = json_to_vector(row["embedding"])
        sim = cosine_similarity(query_vec, ep_vec)
        vec_scores[row["id"]] = sim
        episode_data[row["id"]] = {
            "id": row["id"],
            "summary": row["summary"],
            "tags": row["tags"],
            "created_at": row["created_at"],
            "used_count": row["used_count"],
            "last_used_at": row["last_used_at"],
        }

    # Normalize vector scores
    max_vec = max(vec_scores.values()) if vec_scores else 0
    if max_vec > 0:
        vec_scores = {k: v / max_vec for k, v in vec_scores.items()}

    # Combine scores with time decay and usage boost
    all_ids = set(fts_scores) | set(vec_scores)
    results = []
    for eid in all_ids:
        data = episode_data.get(eid)
        if not data:
            continue

        fts_s = fts_scores.get(eid, 0)
        vec_s = vec_scores.get(eid, 0)
        combined = fts_weight * fts_s + vec_weight * vec_s

        # Time decay
        if data["created_at"]:
            try:
                created = conn.execute(
                    "SELECT julianday('now') - julianday(?)",
                    (data["created_at"],),
                ).fetchone()[0]
                decay = 1.0 / (1.0 + created / decay_days)
                combined *= decay
            except (sqlite3.OperationalError, TypeError):
                pass

        # Usage boost: log(1 + used_count) scaled by weight and recency factor
        used_count = data.get("used_count", 0) or 0
        usage_boost = math.log(1 + used_count)
        # recency_factor: 1.0 when never used (last_used_at is None), decays with age
        last_used = data.get("last_used_at")
        if last_used:
            try:
                days_since_use = conn.execute(
                    "SELECT julianday('now') - julianday(?)",
                    (last_used,),
                ).fetchone()[0]
                recency_factor = 1.0 / (1.0 + days_since_use / usage_recency_days)
            except (sqlite3.OperationalError, TypeError):
                recency_factor = 1.0
        else:
            recency_factor = 1.0
        combined *= 1.0 + usage_boost_weight * usage_boost * recency_factor

        if combined > 0:
            results.append(
                {
                    **data,
                    "fts_score": round(fts_s, 4),
                    "vector_score": round(vec_s, 4),
                    "combined_score": round(combined, 4),
                }
            )

    results.sort(key=lambda x: x["combined_score"], reverse=True)
    return results[:limit]


def mark_used(conn: sqlite3.Connection, episode_ids: list[int]) -> int:
    """Increment used_count and update last_used_at for given episode IDs."""
    updated = 0
    for eid in episode_ids:
        cur = conn.execute(
            """UPDATE episodes
               SET used_count = used_count + 1,
                   last_used_at = datetime('now')
               WHERE id = ?""",
            (eid,),
        )
        updated += cur.rowcount
    conn.commit()
    return updated


def archive_episodes(conn: sqlite3.Connection, dry_run: bool = False) -> tuple[int, list[int]]:
    """Archive episodes that are old, never used, and not used recently.

    Returns (count, sample_ids) where sample_ids is up to 10 IDs of affected episodes.
    When dry_run=True, no UPDATE is performed and the caller can preview the impact.
    """
    cfg = get_config(conn)
    archive_after_days = int(cfg.get("archive_after_days", 180))

    where_sql = """
        FROM episodes
        WHERE archived = 0
          AND used_count = 0
          AND julianday('now') - julianday(created_at) > ?
          AND (last_used_at IS NULL OR julianday('now') - julianday(last_used_at) > ?)
    """
    params = (archive_after_days, archive_after_days)

    # Find target IDs first (used for both dry-run preview and the actual UPDATE targets)
    target_ids = [
        row[0] for row in conn.execute(f"SELECT id {where_sql}", params).fetchall()
    ]
    count = len(target_ids)
    sample_ids = target_ids[:10]

    if not dry_run and count > 0:
        conn.execute(f"UPDATE episodes SET archived = 1 WHERE id IN ({','.join('?' * count)})", target_ids)
        conn.commit()

    return count, sample_ids


def unarchive_episodes(conn: sqlite3.Connection, episode_ids: list[int]) -> int:
    """Unarchive episodes by ID."""
    updated = 0
    for eid in episode_ids:
        cur = conn.execute(
            "UPDATE episodes SET archived = 0 WHERE id = ? AND archived = 1",
            (eid,),
        )
        updated += cur.rowcount
    conn.commit()
    return updated


def main():
    parser = argparse.ArgumentParser(description="ai-ltm vector search")
    parser.add_argument(
        "command",
        choices=["search", "rebuild", "combined", "embed", "mark-used", "archive", "unarchive"],
    )
    parser.add_argument("--db", required=True, help="Path to memory.db")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--id", type=int, help="Episode ID (for embed command)")
    parser.add_argument("--ids", help="Comma-separated episode IDs (for mark-used/unarchive)")
    parser.add_argument("--tags", help="Filter by tags (space-separated, AND logic)")
    parser.add_argument("--since", help="Filter: created_at >= date (YYYY-MM-DD)")
    parser.add_argument("--until", help="Filter: created_at <= date (YYYY-MM-DD)")
    parser.add_argument("--include-archived", action="store_true", help="Include archived episodes in search")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for archive command")
    args = parser.parse_args()

    db_path = Path(args.db).expanduser()
    if not db_path.exists():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)

    if args.command == "rebuild":
        count = rebuild_embeddings(conn)
        print(f"Rebuilt embeddings for {count} episodes.")

    elif args.command == "embed":
        if not args.id:
            print("Error: --id required for embed command", file=sys.stderr)
            sys.exit(1)
        embed_single(conn, args.id)
        print(f"Embedded episode {args.id}.")

    elif args.command == "search":
        if not args.query:
            print("Error: --query required", file=sys.stderr)
            sys.exit(1)
        results = search_vector(
            conn, args.query, args.limit,
            tags=args.tags, since=args.since, until=args.until,
            include_archived=args.include_archived,
        )
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif args.command == "combined":
        if not args.query:
            print("Error: --query required", file=sys.stderr)
            sys.exit(1)
        results = search_combined(
            conn, args.query, args.limit,
            tags=args.tags, since=args.since, until=args.until,
            include_archived=args.include_archived,
        )
        print(json.dumps(results, ensure_ascii=False, indent=2))

    elif args.command == "mark-used":
        if not args.ids:
            print("Error: --ids required for mark-used command", file=sys.stderr)
            sys.exit(1)
        episode_ids = [int(x.strip()) for x in args.ids.split(",")]
        count = mark_used(conn, episode_ids)
        print(f"Marked {count} episodes as used.")

    elif args.command == "archive":
        count, sample_ids = archive_episodes(conn, dry_run=args.dry_run)
        if args.dry_run:
            print(f"[dry-run] Would archive {count} episodes. Sample IDs: {sample_ids}")
        else:
            print(f"Archived {count} episodes.")

    elif args.command == "unarchive":
        if not args.ids:
            print("Error: --ids required for unarchive command", file=sys.stderr)
            sys.exit(1)
        episode_ids = [int(x.strip()) for x in args.ids.split(",")]
        count = unarchive_episodes(conn, episode_ids)
        print(f"Unarchived {count} episodes.")

    conn.close()


if __name__ == "__main__":
    main()
