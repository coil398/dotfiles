# 記憶の管理

記憶の削除、修正、一覧、アーカイブを明示的に行うときだけ、この資料を読む。自動 cleanup はしない。

## 不要な記憶の削除

FTS インデックスはトリガーで自動的に同期されるため、episodes テーブルから DELETE するだけでよい:

```bash
# IDを指定して削除
sqlite3 ~/ai-ltm-data/memory.db "DELETE FROM episodes WHERE id = <ID>;"
```

削除した episode に embedding が設定されていた場合、IDF の再計算が望ましい。件数が少なければ即座の rebuild は不要だが、大量削除した場合は rebuild する:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" rebuild --db ~/ai-ltm-data/memory.db
```

## 記録の修正

summary や context を修正する場合、FTS インデックスは UPDATE トリガーで自動同期される:

```bash
sqlite3 ~/ai-ltm-data/memory.db <<'EOSQL'
UPDATE episodes
SET summary = '修正後のサマリ',
    context = '修正後の文脈'
WHERE id = <ID>;
EOSQL
```

修正後は embedding を再生成する:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" embed \
  --db ~/ai-ltm-data/memory.db \
  --id <ID>
```

## 記憶の一覧確認

```bash
sqlite3 ~/ai-ltm-data/memory.db "SELECT id, created_at, used_count, substr(summary, 1, 80), tags FROM episodes WHERE archived = 0 ORDER BY created_at DESC LIMIT 20;"
```

## アーカイブの管理

自動アーカイブはセッション終了時に実行される（`archive_after_days` 経過かつ `used_count = 0` かつ `last_used_at` も古い episode が対象）。手動で実行することもできる:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" archive --db ~/ai-ltm-data/memory.db
```

アーカイブ対象をドライランで確認する（更新せず件数とサンプルIDのみ表示）:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" archive \
  --db ~/ai-ltm-data/memory.db \
  --dry-run
```

アーカイブ済み記憶も含めて検索する:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" combined \
  --db ~/ai-ltm-data/memory.db \
  --query 'キーワード' \
  --include-archived
```

アーカイブ済みの記憶を復活させる場合:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" unarchive \
  --db ~/ai-ltm-data/memory.db \
  --ids '1,2,3'
```

アーカイブ済み記憶の一覧確認:

```bash
sqlite3 ~/ai-ltm-data/memory.db "SELECT id, created_at, substr(summary, 1, 60), tags FROM episodes WHERE archived = 1 ORDER BY created_at DESC;"
```
