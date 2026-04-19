---
name: review-pr
description: PR・リモートブランチ単位でコードレビューする。PR番号・PRのURL・リモートブランチ名を渡されたとき、「PR確認して」「PRレビュー」「review this PR」「gh pr の差分を見て」といった要望に使う。ローカルの未コミット差分・ファイル指定のレビューは /reviewer を使うこと。ユーザーが /review-pr と入力したら必ずこのスキルを使う。
argument-hint: [PR番号, ブランチ名, またはファイルパス]
---

# Review PR — コードレビュー

変更差分をレビューします。このスキル本体（= メイン Claude）がオーケストレーターとなり、`reviewer` を `Agent` ツールで **3体並列起動**（correctness / consistency / quality の3観点）します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。

**対象**: $ARGUMENTS（PR番号、ブランチ名、またはファイルパス。省略時は現在のステージング差分）

---

## ステップ 0: プロジェクトメモリパスと RUN_DIR の確認

以下の Bash コマンドで PROJECT_MEMORY_DIR と RUN_DIR を取得し、以降のすべてのステップで使用してください:

```bash
sh ~/.claude/lib/pir-preflight.sh "$ARGUMENTS"
```

出力フォーマット（5 行の `KEY=VALUE`）:
- `PROJECT_MEMORY_DIR=...`
- `PROJECT_ROOT=...`
- `RUN_DIR=...`
- `HANDOFF_PATH=...`（/review-pr では使用しない）
- `RESUME_MODE=...`（/review-pr では使用しない）

`/review-pr` は handoff 連携を行わないため、`HANDOFF_PATH` と `RESUME_MODE` は無視してください。

---

## ステップ 1: 差分の取得

以下のルールで差分を取得してください:

- **PR番号が指定された場合**: `gh pr diff <番号>` で差分を取得する
- **ブランチ名が指定された場合**: `git diff <ブランチ名>...HEAD` で差分を取得する
- **ファイルパスが指定された場合**: 該当ファイルを Read する
- **引数なし**: `git diff HEAD` でステージング済み＋未ステージの差分を取得する

いずれもユーザーが対象（PR/ブランチ/ファイル）を明示した上での差分・ピンポイント取得であり、`~/.claude/CLAUDE.md`「コードベース探索の委譲」の例外（VCS 軽量確認 / ユーザー提示ファイルのピンポイント Read）に該当します。メイン Claude が自発的に広域探索（Grep/Glob 等）を開始する場合はこの例外に該当しないため、explorer に委譲してください。

取得した差分を `{RUN_DIR}/diff.patch` に Write で保存してください（reviewer 3体に同じ差分を参照させるため、インライン展開ではなくファイル経由で渡す）。変更ファイル一覧は差分からパースして取得する。

---

## ステップ 2: レビュー (Sonnet 3体並列)

スキル本体（メイン Claude）が `reviewer` サブエージェントを `Agent` ツールで **3体並列起動** してください。1メッセージ内に Agent ツール呼び出しを3つ並べて同時発火させること（逐次起動は禁止）。3体はそれぞれ `REVIEWER_ROLE` を変えて担当観点を分割する:

- `REVIEWER_ROLE=correctness`: バグ・正確性 / セキュリティ / パフォーマンス / リグレッション
- `REVIEWER_ROLE=consistency`: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- `REVIEWER_ROLE=quality`: 保守性 / テストの質 / データアクセス重複 / スコープ逸脱

各体の起動パラメータ:

- model: `sonnet`
- プロンプト（3体共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[ステップ0で取得したパス]`
  - `RUN_DIR=[ステップ0で取得したパス]`
  - `REVIEW_INDEX=01`（3体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality]`（体ごとに変える）
  - 変更ファイル一覧
  - 差分ファイルのパス: `{RUN_DIR}/diff.patch`
  - 「これはコードレビューです。実装は行わず、レビューのみ行ってください。plan.md / implementation-*.md は存在しません。`{RUN_DIR}/diff.patch` を Read して変更内容を確認し、変更されたファイルの現状も必要に応じて Read してレビューしてください。レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

---

## ステップ 3: 結果の統合・提示

3体の VERDICT と書き出したレポートをユーザーに提示する:

### VERDICT 集約

- **全体 VERDICT = PASS**: 3体すべて `VERDICT: PASS`
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL`

### ユーザーへの提示フォーマット

```
## PR レビュー完了

### 対象
[PR番号 / ブランチ名 / ファイルパス]

### 全体 VERDICT
[PASS|FAIL]

### 観点別 VERDICT
- correctness: [PASS|FAIL] — {RUN_DIR}/review-01-correctness.md
- consistency: [PASS|FAIL] — {RUN_DIR}/review-01-consistency.md
- quality: [PASS|FAIL] — {RUN_DIR}/review-01-quality.md

### 主な指摘事項（Critical / High のみ）
- [深刻度] `ファイル:行` — [問題の要約]（出典: [ROLE]）
```

各 reviewer が書き出した `{RUN_DIR}/review-01-{ROLE}.md` を Read して、Critical / High の問題一覧を統合してユーザーに提示する。Medium / Low は件数サマリーのみに留める（詳細はファイル参照）。
