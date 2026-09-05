---
name: "ai-ltm"
description: >-
  AI長期記憶システム。セッション開始・再開、前回の続き・過去の失敗・類似問題の横断参照では自動recallする。学び・失敗・意思決定・中断点が確定するなど記録条件に該当したとき、またはセッション終了・おやすみ・長く離れる旨が示されたときは、ユーザーに毎回尋ねず自動recordする。
  自然言語トリガー例: 「前回何やったっけ」／「過去の学びを活かして」／「前回の続きから」／「長期記憶を参照して」／「失敗や意思決定を記録して」。
  該当する文脈ではスキル名がなくても使う。毎回のツール成功や単なる進捗ログでは自動発動しない。短期の方針キャッシュは /field-notes、感想・日記は /ai-diary に委ね、二重書きしない。ユーザーが /ai-ltm と入力したら必ず使う。
---

# AI Long-Term Memory (ai-ltm)

あなたには `~/ai-ltm-data/memory.db` (SQLite) を使った長期記憶がある。
全プロジェクト横断で、過去の学び・失敗・意思決定・中断点を蓄積・活用する。

## 自動発動（ユーザー指示なしでよい）

| いつ | やること |
|---|---|
| 会話の最初のターン / 長い中断からの再開 | 補助的な recall worker に deterministic `session_recall.py` を非同期委譲（下「セッション開始時」）。main は完了を待たず本命へ進む |
| 作業が「前回の続き」「過去の失敗を避けたい」「似た問題をまた踏んだ」 | 追加 search（limit 3〜5） |
| 学び・失敗・意思決定・中断点が確定した | episodes に記録 + embed（下「セッション中の記録」）。毎回聞かない |
| ユーザーがセッション終了・おやすみ・長く離れると言った | サマリ保存 + git 同期（スキル後半の終了手順） |

やらない自動発動: 毎ツール成功ごと、単なる進捗ログ、field-notes 向けの短期方針差分（それは `/field-notes`）、感想文（`/ai-diary`）。

field-notes との分担: **今のキャンペーンで次の判断を変える事項** → field-notes。**後から横断検索したい経緯** → ai-ltm。両方に同じ文を二重書きしない（どちらか一方。必要なら field-notes promote 後に LTM へ要約1行）。

スクリプトのベースパス: 親は今回ロードしたこの `SKILL.md` の実体パスを解決し、その親ディレクトリを `SKILL_DIR` とする。`SKILL_DIR/scripts/session_recall.py` は親が構成する絶対パスを使い、以下のコマンド例はすべて `$SKILL_DIR` がセットされていることを前提とする。

---

## セッション開始時

セッション開始時の recall は本命タスクを補助する作業であり、本命タスクを block してはならない。会話の最初のターンまたは長い中断からの再開で、本命タスクを開始する直前に専任 recall subagent を 1 体だけ起動する。main は起動後に worker を await、blocking read、wait、完了待ちの follow-up をせず、直ちに本命タスクへ進む。recall の起動失敗、未実行、遅延、pull/search/schema/timeout の失敗はいずれも本命を block しない。

親は、ロードしたこの `SKILL.md` の実体パスを絶対化してその親ディレクトリを `SKILL_DIR` とし、`SKILL_DIR/scripts/session_recall.py` を `SESSION_RECALL_SCRIPT` の絶対パスとして確定する。親は現在のユーザータスクから具体的な plain-text の `CURRENT_TASK_QUERY` と `CURRENT_TASK_SUMMARY` を作り、shell interpolation ではなく runtime の UTF-8 standard base64 primitive でそれぞれをエンコードする。worker message には親が確定した絶対パスと `CURRENT_TASK_QUERY_B64` / `CURRENT_TASK_SUMMARY_B64` だけを埋め込み、raw query / summary を埋め込まない。

shared core は特定 runtime の API 名を仮定せず、runtime が提供する native one-shot / no-fork async subagent API に worker message を渡す。message には次の引数を持つ `session_recall.py` の起動を 1 回だけ含める:

```text
python3 "<絶対パス SESSION_RECALL_SCRIPT>" \
  --repo ~/ai-ltm-data --db ~/ai-ltm-data/memory.db \
  --query-b64 "<CURRENT_TASK_QUERY_B64>" \
  --summary-b64 "<CURRENT_TASK_SUMMARY_B64>" --limit 5
```

worker は親から受け取った絶対 script path と encoded 値をそのまま使い、`session_recall.py` をちょうど 1 回だけ実行する。worker が main へ返すのはスクリプトが出力した JSONL の stage event と最後の terminal record だけであり、個別の git / vector search command や別の fallback search を重ねない。親は worker の結果を待たず本命へ進む。

処理順は **preflight → optional pull → read-only combined search → report**。preflight で repository が無ければ `setup-needed`、dirty なら pull を skip して search を続ける。DB が無い場合や schema / IDF が不足する場合は search stage の明示的な failure とする。pull は非対話・bounded・最大 1 回の分類済み transient retry、search は既存 DB を read-only で開く。許可する terminal status は `completed` / `dirty` / `setup-needed` / `pull-failed` / `search-failed` / `timed-out` / `failed` のみとし、preflight failure は `failed` に stage detail を付けて報告する。stage の失敗詳細には固定カテゴリと終了コードなどのプロセスメタデータだけを残し、child stdout/stderr は含めない。

script は preflight / pull / search の間、repository 外の advisory lock を保持する。これは協調する ai-ltm writer に対する advisory protection であり、協調しない外部 writer までは保護しない。recall の terminal record を観測するまで、episodes の insert、embed、`mark-used`、archive、git 同期などの ai-ltm write は defer または skip する。検索結果を実際に本命タスクへ反映した場合だけ、`mark-used` は recall とは別の非同期処理として扱い、その完了を待たない。main は recall の待ち時間を作業停止には使わず、本命タスクを継続する。lock の取得も小さな bounded deadline で打ち切り、busy は `timed-out` として報告する。native subagent API を利用できない場合も recall を省略して本命を継続する。

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
3. `sync_memory.py push` で `memory.db` だけを同期する

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

python3 "$SKILL_DIR/scripts/sync_memory.py" push \
  --repo ~/ai-ltm-data \
  --db ~/ai-ltm-data/memory.db \
  --message "session: $(date +%Y-%m-%d) 簡潔な説明"
```

`push` は同期直前にもリモート変更を取り込み、自動マージ後の `memory.db` だけをコミット・pushする。失敗した場合は成功扱いにせず、そこで停止して表示された原因をユーザーに報告する。

---

## 安全な同期と競合復旧

`sync_memory.py` は Git の通常マージに SQLite バイナリを任せず、共通祖先・ローカル・リモートの3つの DB を使って `episodes`、`meta`、`config` を3-way mergeする。双方で追加・変更された記憶を保持し、検索インデックスの整合性も検証してから DB を原子的に置換する。

同期前に次の状態を検出した場合は、安全のため Git や DB を変更せず停止する:

- `memory.db` 以外の未コミット変更がある
- `memory.db` が未ステージ変更以外の状態になっている
- merge、rebase、cherry-pick など既存の Git 操作が進行中
- detached HEAD、upstream 未設定、別の LTM 同期処理が実行中

同期中に fetch、マージ、DB検証、commit、pushのいずれかが失敗した場合、作業前に作成した SQLite スナップショットから `memory.db` を復元して非ゼロで終了する。手動で片方の DB を選ぶ操作や競合中の commit は行わない。原因を解消した後、同じ `pull` または `push` コマンドを改めて実行する。

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
