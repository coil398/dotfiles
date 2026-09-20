# 記憶の記録

学び・失敗・意思決定・中断点が確定したときだけ、この資料を読む。親が記録・embed・同期の統合責任を持ち、単なる進捗ログは記録しない。

## 記録条件

- **学び**: 新しく知った技術的知見、ライブラリの癖、ハマりポイント
- **失敗**: 試みて失敗したアプローチとその理由
- **意思決定**: 複数の選択肢から選んだ理由
- **中断点**: 作業を中断する場合の状態と次のステップ

記録する際は、シングルクォートのエスケープに注意する。サマリやコンテキストに `'` が含まれる場合は `''` に置換する:

```bash
EPISODE_ID=$(sqlite3 ~/ai-ltm-data/memory.db <<'EOSQL'
INSERT INTO episodes (summary, context, tags)
VALUES (
  '簡潔なサマリ（シングルクォートは''で二重化）',
  '詳細な文脈',
  'スペース区切りのタグ'
);
SELECT last_insert_rowid();
EOSQL
)
```

記録後、ベクトル埋め込みを生成する:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" embed \
  --db ~/ai-ltm-data/memory.db \
  --id "$EPISODE_ID"
```

## タグの付け方

タグはスペース区切りの自然言語。以下のカテゴリを組み合わせる:

- **種別**: `learning`, `failure`, `decision`, `checkpoint`, `schema-change`
- **技術**: 使用した言語・フレームワーク・ツール名（例: `typescript`, `react`, `sqlite`）
- **プロジェクト**: 作業中のプロジェクト名
- **トピック**: 作業内容のキーワード（例: `auth`, `migration`, `performance`）

## スキーマを拡張する場合

既存のスキーマに収まらない情報が出てきた場合:

1. `ALTER TABLE` または `CREATE TABLE` で拡張する
2. 変更の経緯をepisodesに記録する（タグに `schema-change` を含める）
3. 埋め込みをリビルドする（スキーマ変更でテキストカラムが増えた場合）

```bash
sqlite3 ~/ai-ltm-data/memory.db "ALTER TABLE episodes ADD COLUMN <新カラム> <型>;"

sqlite3 ~/ai-ltm-data/memory.db <<'EOSQL'
INSERT INTO episodes (summary, context, tags)
VALUES (
  'スキーマ変更: episodesに<新カラム>を追加',
  'なぜこのカラムが必要になったかの説明',
  'schema-change sqlite'
);
EOSQL
```
