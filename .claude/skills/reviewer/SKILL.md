---
name: reviewer
description: reviewerエージェントにローカルの差分・ファイルをレビューさせる。バグ・セキュリティ・パフォーマンス・保守性・命名一貫性・リグレッション・データアクセス重複などの観点でレビューし VERDICT: PASS/FAIL を返す。「reviewerに見せて」「reviewer」「ローカルの差分を見て」といった要望に使う。PR番号・リモートブランチ・gh pr 経由のレビューは /review-pr を使うこと。ユーザーが /reviewer と入力したら必ずこのスキルを使う。
argument-hint: [レビュー範囲の指定（例: ファイルパス、ブランチ名、コミット範囲。省略時は未コミットの差分）]
---

# Reviewer — コードレビュー

reviewer エージェントにコードレビューを実行させます。このスキル本体（= メイン Claude）がオーケストレーターとなり、`reviewer` を `Agent` ツールで **3体並列起動**（correctness / consistency / quality の3観点）します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。

**レビュー範囲**: $ARGUMENTS

---

## ステップ 0: メモリパスと RUN_DIR の解決

以下の Bash コマンドで PROJECT_MEMORY_DIR と RUN_DIR を取得し、以降のすべてのステップで使用してください:

```bash
sh ~/.claude/lib/pir-preflight.sh "$ARGUMENTS"
```

出力フォーマット（5 行の `KEY=VALUE`）:
- `PROJECT_MEMORY_DIR=...`
- `PROJECT_ROOT=...`
- `RUN_DIR=...`
- `HANDOFF_PATH=...`（/reviewer では使用しない）
- `RESUME_MODE=...`（/reviewer では使用しない）

`/reviewer` は handoff 連携を行わないため、`HANDOFF_PATH` と `RESUME_MODE` は無視してください。

---

## ステップ 1: レビュー対象の特定

`$ARGUMENTS` の内容に応じてレビュー対象を決定する:

- 指定なし: `git diff --name-only HEAD` で未コミットの差分を取得
- ファイルパス: 指定されたファイルをそのまま対象とする
- ブランチ名: `git diff --name-only <branch>...HEAD` でブランチとの差分を取得
- コミット範囲（例: `HEAD~3..HEAD`）: `git diff --name-only <range>` で差分を取得

対象ファイルが0件の場合はユーザーに報告して終了する。

---

## ステップ 2: レビュー実行 (Sonnet 3体並列)

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
  - レビュー対象のファイル一覧
  - 差分の取得コマンド（ステップ1で使用したものと同じ git diff コマンド。`--name-only` を外したもの）
  - 「plan.md / implementation-*.md は存在しません。上記の差分コマンドで変更内容を確認し、変更されたファイルを Read してレビューしてください。レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

---

## ステップ 3: 結果の統合・提示

3体の VERDICT と書き出したレポートをユーザーに提示する:

### VERDICT 集約

- **全体 VERDICT = PASS**: 3体すべて `VERDICT: PASS`
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL`

### ユーザーへの提示フォーマット

```
## レビュー完了

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
