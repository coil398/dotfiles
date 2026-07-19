---
name: "cursor-ai-ltm"
description: "AI長期記憶システム。セッション開始時に関連記憶をロードし、セッション中に学び・失敗・意思決定を記録し、セッション終了時にサマリを保存してGitHub同期する。「前回何やったっけ」「過去の学びを活かして」「前回の続きから」「失敗を記録して」「セッション終了」といった要望や、プロジェクト横断で過去の経験を参照したい場面で使う。"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Claude 専用機能（`TeamCreate` / Agent Teams / `~/.claude/hooks`）は Cursor では非対応のためスキップする
> - ベンダーモデル名（Cursor 側）はハードコードしない。agent overlay の `role=reasoning|coding` と Cursor UI の運用既定に従う
> - Codex CLI 橋渡し（`/cursor-codex` / `codex-runner` / `/cursor-pir2codex`）では Codex 側 model ID の明示指定は許可する

# AI Long-Term Memory (ai-ltm)

あなたには `~/ai-ltm-data/memory.db` (SQLite) を使った長期記憶がある。
全プロジェクト横断で、過去の学び・失敗・意思決定・中断点を蓄積・活用する。

スクリプトのベースパス: このSKILL.mdと同じディレクトリに `scripts/` がある。
セッション開始時にまず SKILL_DIR を特定し、以降のコマンドで使用する:

```bash
SKILL_DIR="$(dirname "$(readlink -f .cursor/skills/cursor-ai-ltm/SKILL.md 2>/dev/null || echo .cursor/skills/cursor-ai-ltm/SKILL.md)")"
```

以下のコマンド例はすべて `$SKILL_DIR` がセットされていることを前提とする。

---

## セッション開始時

会話の最初のターンで以下を実行する:

```bash
if [ -d ~/ai-ltm-data/.git ]; then
  cd ~/ai-ltm-data && git pull --rebase --quiet 2>/dev/null; echo "ltm-sync: ok"
else
  echo "ltm-setup-needed"
fi
```

`ltm-setup-needed` が返った場合は `references/setup.md` を読んで初回セットアップを案内する。

その後、現在のタスクに関連する記憶を**combined search**（FTS + ベクトル類似度の複合検索）で検索する:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" combined \
  --db ~/ai-ltm-data/memory.db \
  --query '<現在のタスクに関連するキーワード>' \
  --limit 5
```

検索キーワードは現在の作業内容から判断する。関連する記憶があれば活用し、なければそのまま作業を進める。

検索結果の記憶を実際に活用した場合（参照して作業に反映した場合）、使用した記憶の used_count をインクリメントする:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" mark-used \
  --db ~/ai-ltm-data/memory.db \
  --ids '<活用したepisodeのIDをカンマ区切りで>'
```

FTS検索でエラーになる場合（クエリ構文の問題など）は、ベクトル検索にフォールバックする:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" search \
  --db ~/ai-ltm-data/memory.db \
  --query '<キーワード>' \
  --limit 5
```

---

## セッション中の記録

以下のいずれかに該当する場合、episodesに記録する:

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

### タグの付け方

タグはスペース区切りの自然言語。以下のカテゴリを組み合わせる:

- **種別**: `learning`, `failure`, `decision`, `checkpoint`, `schema-change`
- **技術**: 使用した言語・フレームワーク・ツール名（例: `typescript`, `react`, `sqlite`）
- **プロジェクト**: 作業中のプロジェクト名
- **トピック**: 作業内容のキーワード（例: `auth`, `migration`, `performance`）

---

## スキーマの自己拡張

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

---

## 検索のスコアリング

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

---

## セッション終了時

ユーザーが作業を終了するとき（明示的に終了を伝えた場合、または会話が自然に終わる場合）:

1. 会話全体のサマリをepisodesに記録する
2. 埋め込みを生成する
3. git pushで同期する

```bash
EPISODE_ID=$(sqlite3 ~/ai-ltm-data/memory.db <<'EOSQL'
INSERT INTO episodes (summary, context, tags)
VALUES (
  'セッション全体の簡潔なサマリ',
  '何をやって、何が決まって、何が残っているか',
  'session-summary プロジェクト名 主要トピック'
);
SELECT last_insert_rowid();
EOSQL
)

python3 "$SKILL_DIR/scripts/vector_search.py" embed \
  --db ~/ai-ltm-data/memory.db \
  --id "$EPISODE_ID"

# 古くて使われていない記憶を自動アーカイブ
python3 "$SKILL_DIR/scripts/vector_search.py" archive \
  --db ~/ai-ltm-data/memory.db

cd ~/ai-ltm-data && git add memory.db && git commit -m "session: $(date +%Y-%m-%d) 簡潔な説明" && git push
```

`git add` は `memory.db` のみを対象にする。`-A` は使わない（一時ファイルの混入を防ぐため）。

---

## コンフリクト対処

`git pull` でコンフリクトが発生した場合（SQLiteはバイナリなので通常のマージはできない）。

予防: 必ず pull → 作業 → push の順で操作する。セッション開始時の `git pull --rebase` を省略しない。

ポリシー: 両方のデータを保持する。ローカルの episodes を JSON にダンプし、リモート版をチェックアウトしてからローカル分をインポートする。

```bash
cd ~/ai-ltm-data

# 1. ローカルの episodes を JSON にダンプ
python3 "$SKILL_DIR/scripts/merge_conflict.py" dump \
  --db ~/ai-ltm-data/memory.db \
  --out /tmp/ltm_local.json

# 2. リモート版を採用
git checkout --theirs memory.db
git add memory.db

# 3. ローカルの episodes をインポート（重複は summary + created_at で判定しスキップ）
python3 "$SKILL_DIR/scripts/merge_conflict.py" import \
  --db ~/ai-ltm-data/memory.db \
  --input /tmp/ltm_local.json

# 4. 埋め込みをリビルドしてコミット
python3 "$SKILL_DIR/scripts/vector_search.py" rebuild --db ~/ai-ltm-data/memory.db
git add memory.db
git commit -m "merge: resolve binary conflict, merged episodes"
git push

# 5. 一時ファイルを削除
rm -f /tmp/ltm_local.json
```

---

## 記憶の管理

### 不要な記憶の削除

FTS インデックスはトリガーで自動的に同期されるため、episodes テーブルから DELETE するだけでよい:

```bash
# IDを指定して削除
sqlite3 ~/ai-ltm-data/memory.db "DELETE FROM episodes WHERE id = <ID>;"
```

削除した episode に embedding が設定されていた場合、IDF の再計算が望ましい。件数が少なければ即座の rebuild は不要だが、大量削除した場合は rebuild する:

```bash
python3 "$SKILL_DIR/scripts/vector_search.py" rebuild --db ~/ai-ltm-data/memory.db
```

### 記録の修正

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

### 記憶の一覧確認

```bash
sqlite3 ~/ai-ltm-data/memory.db "SELECT id, created_at, used_count, substr(summary, 1, 80), tags FROM episodes WHERE archived = 0 ORDER BY created_at DESC LIMIT 20;"
```

### アーカイブの管理

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

### スキーマの自動マイグレーション

`vector_search.py` は起動時に自動的に `used_count` / `last_used_at` / `archived` カラムと関連 config の有無をチェックし、欠けているものを追加する。そのため既存 DB でも手動マイグレーションは原則不要。内部では `ALTER TABLE episodes ADD COLUMN` を実行しているだけなので、既存データは保持される。

手動で行う場合の SQL:

```bash
sqlite3 ~/ai-ltm-data/memory.db <<'EOSQL'
ALTER TABLE episodes ADD COLUMN used_count INTEGER DEFAULT 0;
ALTER TABLE episodes ADD COLUMN last_used_at DATETIME;
ALTER TABLE episodes ADD COLUMN archived INTEGER DEFAULT 0;
INSERT OR IGNORE INTO config VALUES ('usage_boost_weight', '0.3');
INSERT OR IGNORE INTO config VALUES ('usage_recency_days', '30');
INSERT OR IGNORE INTO config VALUES ('archive_after_days', '180');
EOSQL
```

---

## 記憶の棚卸し（cleanup）

粒度がまだ固まっていない段階では **オンデマンド実行** を基本とする。ユーザーが「記憶を掃除して」「/clean-ltm」等の意図を示したときのみ実行する。自動発動はしない。

### cleanup で対象にする候補

1. **重複候補** — ベクトル類似度が高い（例: cosine > 0.92）ペアを提示し、統合 or 片方削除を対話で決める
2. **stale 参照** — summary/context に含まれるファイルパス・シンボル名が実在しない記憶（特定プロジェクト固有の型名が消えた等）
3. **低スコア長期未使用** — `created_at > 90日` かつ `used_count = 0` かつ最近のクエリで上位に来ない記憶（archive_after_days 未満でも候補に挙げる）
4. **プロジェクト固有すぎる decision** — タグに特定プロジェクト名のみ含まれ、他プロジェクトでは引き出されないもの。LTM ではなくプロジェクトメモリに集約できる可能性を検討
5. **session-summary の粒度過多** — 1日に複数セッションサマリが入っている場合、1件にマージ

### cleanup 実行フロー

1. 候補を最大 10 件抽出して提示
2. 各候補について `keep / archive / delete / merge` を対話で決定（自動判定はしない）
3. 実行結果を1件 episode に記録（タグ: `cleanup-session`）
4. IDF のズレが大きい場合は `rebuild` を推奨

### 将来の自動化への余地

運用が安定して cleanup の基準がルール化できたら、以下の方向で自動発動にも切り替えられる:

- **間隔ベース（A 案）**: `config` に `last_cleanup_at` と `cleanup_interval_days` を持たせ、セッション開始時に経過日数を確認して「cleanup を実行する？」と提案する
- **サイズベース**: episodes 件数が閾値を超えたら同様に提案
- **セッションカウンタ**: `session_count` を increment し N セッションごとに提案

いずれも「自動 DELETE はしない／ユーザーに提案して対話確定」の原則を守る。自動化に移行する前に、オンデマンド cleanup を何度か回して「消したい／残したい」判断のパターンを蓄積すること。

---

## 注意事項

- 記録は簡潔に。1つのepisodeのsummaryは1-2文に収める
- contextには再現に必要な情報を入れるが、コード全体のコピーは避ける
- 機密情報（パスワード、トークン、秘密鍵）は絶対に記録しない
- 検索は控えめに。毎回全検索するのではなく、関連しそうなときだけ引く
- SQLにユーザー入力を埋め込む際は、シングルクォートを `''` にエスケープする
