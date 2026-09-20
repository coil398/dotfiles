# 記憶の検索

過去の経緯を参照するとき、または検索結果の挙動を調整するときだけ、この資料を読む。`search` / `combined` は既存 DB を read-only で開き、検索中にスキーマや IDF を変更しない。

## スキーマと検索前提

`init.sql` が現行スキーマのSSOTである。必要なテーブル、カラム、FTS、cached IDF、設定値が不足または不正な場合は、具体的な schema/config エラーを非ゼロで報告して停止する。新規DBは初回セットアップ時に `init.sql` を適用し、既存DBの更新は書き込みを伴う明示的なメンテナンス手順として実施する。検索経路が不足スキーマを自動補完することや、手動更新が不要であることを前提にしない。

## スコアリング

combined searchスクリプトは以下のロジックで統合スコアを算出する:

1. **FTS スコア**: SQLite FTS5 の BM25 ランキング（正規化済み）
2. **ベクトルスコア**: TF-IDF cosine similarity（正規化済み）
3. **統合**: `fts_weight * fts_score + vector_weight * vector_score`
4. **時間減衰**: `combined * 1/(1 + 経過日数/time_decay_days)`
5. **使用頻度ブースト**: `combined * (1 + usage_boost_weight * log(1 + used_count) * recency_factor)` — `recency_factor` は `last_used_at` が新しいほど大きく、古いほど減衰する（`usage_recency_days` で調整）

各重みは `config` テーブルで調整できる:

```bash
# ベクトル検索を重視する場合
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '0.3' WHERE key = 'fts_weight';"
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '0.7' WHERE key = 'vector_weight';"

# 古い記憶もよく引くようにする場合（減衰を緩やかに）
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '90' WHERE key = 'time_decay_days';"

# 使用頻度ブーストの強さを調整（0で無効化、大きいほど使用済み記憶を優遇）
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '0.5' WHERE key = 'usage_boost_weight';"

# 使用頻度ブーストのリーセンシー減衰期間を調整（小さいほど「最近使った」を強く優遇）
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '60' WHERE key = 'usage_recency_days';"

# 自動アーカイブまでの日数を変更
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '365' WHERE key = 'archive_after_days';"
```

埋め込みのリビルド目安: 50件程度の episode 追加ごと、または検索精度に違和感を感じたとき。IDF は新しい episode が追加されるたびに語彙の重み付けがずれていくため、定期的なリビルドで精度を維持する:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" rebuild --db ~/ai-ltm-data/memory.db
```
