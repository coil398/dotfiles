# AI Long-Term Memory (ai-ltm)

AIアシスタント（Claude）にセッションを跨いだ長期記憶を提供するシステム。
プロジェクト横断で過去の学び・失敗・意思決定・中断点を SQLite に蓄積し、ハイブリッド検索（FTS + ベクトル類似度）で関連記憶を呼び出す。
使用頻度フィードバックと自動アーカイブにより、時間とともに検索品質が改善される自己改善型の設計。

## 特徴

- セッション横断の記憶: 過去の経験を蓄積し、次回セッションで自動的に参照
- ハイブリッド検索: SQLite FTS5 の全文検索と TF-IDF ベクトル類似度検索の組み合わせ
- 自己改善: 使われた記憶をスコアブーストし、使われない記憶は自動アーカイブ
- 外部依存なし: Python 標準ライブラリと SQLite のみで動作
- Git 同期: プライベート GitHub リポジトリでデータをバックアップ・同期
- CJK 対応: 日本語・中国語・韓国語テキストのバイグラムトークナイズに対応
- 自動マイグレーション: スクリプト起動時にスキーマを自動更新し、既存 DB の互換性を維持

## 構成

```
ai-ltm/
├── SKILL.md                    # Codex スキル定義
├── init.sql                    # SQLite スキーマ初期化
├── scripts/
│   ├── vector_search.py        # 検索エンジン（TF-IDF + コサイン類似度）
│   └── merge_conflict.py       # git コンフリクト時のエピソードマージ
└── references/
    └── setup.md                # 初回セットアップガイド
```

## 必要環境

- Python 3
- SQLite3
- Git

外部パッケージのインストールは不要です。

## セットアップ

スキルは `.cursor/skills/cursor-ai-ltm/` にインストールされる想定。以下では `SKILL_DIR` 変数にスキルの実パスをセットして参照する:

```bash
SKILL_DIR="$(dirname "$(readlink -f .cursor/skills/cursor-ai-ltm/SKILL.md)")"
```

### 1. データディレクトリの作成

```bash
mkdir -p ~/ai-ltm-data && cd ~/ai-ltm-data
git init
sqlite3 ~/ai-ltm-data/memory.db < "$SKILL_DIR/init.sql"
cp "$SKILL_DIR/.gitignore" ~/ai-ltm-data/.gitignore
git remote add origin <your-private-repo-url>
git add memory.db .gitignore
git commit -m "init: AI長期記憶システム初期化"
git push -u origin main
```

既存のリモートリポジトリがある場合:

```bash
git clone <remote-url> ~/ai-ltm-data
```

## 使い方

### 記憶の記録

INSERT と `last_insert_rowid()` は同一の sqlite3 セッション内で取得する必要がある:

```bash
EPISODE_ID=$(sqlite3 ~/ai-ltm-data/memory.db <<'EOSQL'
INSERT INTO episodes (summary, context, tags)
VALUES (
  '学んだことの要約',
  '詳細なコンテキスト',
  'learning typescript react'
);
SELECT last_insert_rowid();
EOSQL
)

python3 "$SKILL_DIR/scripts/vector_search.py" embed \
  --db ~/ai-ltm-data/memory.db \
  --id "$EPISODE_ID"
```

### 記憶の検索

```bash
# 複合検索（FTS + ベクトル類似度 + 時間減衰 + 使用頻度ブースト）
python3 "$SKILL_DIR/scripts/vector_search.py" combined \
  --db ~/ai-ltm-data/memory.db \
  --query "検索クエリ" \
  --limit 10

# ベクトル類似度検索のみ
python3 "$SKILL_DIR/scripts/vector_search.py" search \
  --db ~/ai-ltm-data/memory.db \
  --query "検索クエリ" \
  --limit 10

# 全エンベディング再構築（50件程度の追加ごと推奨）
python3 "$SKILL_DIR/scripts/vector_search.py" rebuild \
  --db ~/ai-ltm-data/memory.db
```

### フィルタオプション

`search` / `combined` はタグ・日付でフィルタできる:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" combined \
  --db ~/ai-ltm-data/memory.db \
  --query "auth" \
  --tags "learning typescript" \
  --since 2026-01-01 \
  --until 2026-04-14

# アーカイブ済みの記憶も含めて検索
python3 "$SKILL_DIR/scripts/vector_search.py" combined \
  --db ~/ai-ltm-data/memory.db \
  --query "検索クエリ" \
  --include-archived
```

### 自己改善（使用頻度フィードバック）

検索結果から実際に参照した記憶があれば `mark-used` でフィードバックする。`used_count` が増え、次回以降のスコアが上がる:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" mark-used \
  --db ~/ai-ltm-data/memory.db \
  --ids 42,17,3
```

### アーカイブ管理

180日以上経過し、一度も参照されていない記憶を自動アーカイブできる:

```bash
# 事前確認（dry-run）
python3 "$SKILL_DIR/scripts/vector_search.py" archive \
  --db ~/ai-ltm-data/memory.db \
  --dry-run

# 本番実行
python3 "$SKILL_DIR/scripts/vector_search.py" archive \
  --db ~/ai-ltm-data/memory.db

# アーカイブ解除
python3 "$SKILL_DIR/scripts/vector_search.py" unarchive \
  --db ~/ai-ltm-data/memory.db \
  --ids 42
```

### 検索パラメータの調整

```bash
# FTS/ベクトル検索の重み（デフォルト: 各0.5）
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '0.3' WHERE key = 'fts_weight';"
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '0.7' WHERE key = 'vector_weight';"

# 時間減衰（デフォルト: 30日）
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '90' WHERE key = 'time_decay_days';"

# 使用頻度ブーストの重み（デフォルト: 0.3）
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '0.5' WHERE key = 'usage_boost_weight';"

# リーセンシー減衰（デフォルト: 30日）
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '60' WHERE key = 'usage_recency_days';"

# アーカイブ閾値（デフォルト: 180日）
sqlite3 ~/ai-ltm-data/memory.db "UPDATE config SET value = '365' WHERE key = 'archive_after_days';"
```

### スコアリング式

`combined` のスコアは以下で算出される:

```
combined = (fts_weight * fts_score + vec_weight * vec_score)
         * time_decay(created_at)
         * usage_boost(used_count, last_used_at)

time_decay   = 1 / (1 + days_since_created / time_decay_days)
usage_boost  = 1 + log(1 + used_count) * usage_boost_weight * recency_factor
recency_factor = 1 / (1 + days_since_last_used / usage_recency_days)
```

`last_used_at` が NULL のときは `recency_factor = 1.0`（新しい記憶にペナルティを掛けない）。

## DB スキーマ

| カラム | 説明 |
|---|---|
| `id` | 主キー |
| `summary` | 1-2文の簡潔なサマリ |
| `context` | 詳細な文脈（再現に必要な情報） |
| `tags` | スペース区切りの自然言語タグ |
| `embedding` | TF-IDF スパースベクトル（JSON） |
| `used_count` | 参照された回数（mark-used でインクリメント） |
| `last_used_at` | 最終参照日時 |
| `archived` | アーカイブフラグ（0/1） |
| `created_at` | 作成日時 |

| テーブル | 説明 |
|---|---|
| `episodes` | 記憶本体 |
| `episodes_fts` | FTS5 仮想テーブル（全文検索用、トリガーで自動同期） |
| `config` | 検索チューニングパラメータ |

## タグ規約

- 種別: `learning`, `failure`, `decision`, `checkpoint`, `schema-change`, `session-summary`
- 技術: 言語・フレームワーク名（例: `typescript`, `react`, `sqlite`）
- プロジェクト: プロジェクト識別子
- トピック: 具体的なキーワード（例: `auth`, `performance`, `migration`）

## コンフリクト対処

`git pull` でバイナリコンフリクトが発生した場合は `scripts/merge_conflict.py` を使う:

```bash
cd ~/ai-ltm-data
python3 "$SKILL_DIR/scripts/merge_conflict.py" dump --db ~/ai-ltm-data/memory.db --out /tmp/ltm_local.json
git checkout --theirs memory.db
git add memory.db
python3 "$SKILL_DIR/scripts/merge_conflict.py" import --db ~/ai-ltm-data/memory.db --input /tmp/ltm_local.json
python3 "$SKILL_DIR/scripts/vector_search.py" rebuild --db ~/ai-ltm-data/memory.db
git add memory.db
git commit -m "merge: resolve binary conflict, merged episodes"
git push
rm -f /tmp/ltm_local.json
```

重複は `summary + created_at` の組み合わせで判定してスキップする。予防としてセッション開始時の `git pull --rebase` を省略しないこと。
