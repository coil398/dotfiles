---
name: reviewer
description: reviewerエージェントにローカルの差分・ファイルをレビューさせる。バグ・セキュリティ・パフォーマンス・保守性・命名一貫性・リグレッション・データアクセス重複などの観点でレビューし VERDICT: PASS/FAIL を返す。「reviewerに見せて」「reviewer」「ローカルの差分を見て」といった要望に使う。PR番号・リモートブランチ・gh pr 経由のレビューは /review-pr を使うこと。ユーザーが /reviewer と入力したら必ずこのスキルを使う。
argument-hint: [レビュー範囲の指定（例: ファイルパス、ブランチ名、コミット範囲。省略時は未コミットの差分）]
---

# Reviewer — コードレビュー

reviewer エージェントにコードレビューを実行させます。このスキル本体（= メイン Claude）がオーケストレーターとなり、`reviewer` を `Agent` ツールで **ハイブリッド並列起動**（correctness / consistency / quality / security / architecture の 5 観点から必要なものを選択して 1〜5 体）します。サブエージェント内からの Agent 呼び出しは Claude Code の設計上不可能なため、起動責任はスキル本体に集約されます。

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

まず `$ARGUMENTS` から `--reviewers=<roles>` と `--all-reviewers` フラグを**抽出して除去**し、残りをレビュー範囲指定として扱う。次に残り部分に応じてレビュー対象を決定する:

- 指定なし: `git diff --name-only HEAD` で未コミットの差分を取得
- ファイルパス: 指定されたファイルをそのまま対象とする
- ブランチ名: `git diff --name-only <branch>...HEAD` でブランチとの差分を取得
- コミット範囲（例: `HEAD~3..HEAD`）: `git diff --name-only <range>` で差分を取得

対象ファイルが0件の場合はユーザーに報告して終了する。

---

## ステップ 2: レビュー実行 (Sonnet ハイブリッド並列)

### 2-1: REVIEWER_SET 決定（非 planner 系：自動選定がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグ**: ステップ 1 で抽出した `--reviewers=<roles>` があればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` があれば全 5 観点。両方指定時は `--reviewers=` を優先
2. **フラグ未指定時の自動選定**: 詳細プロトコル: `~/.claude/skills/pir2/references/reviewer-set-algorithm.md` を参照（デフォルト挙動 / ユーザーフラグ / 自動選定アルゴリズムの 5 ルール + フォールバック）。入力ソース: `git diff --name-only <range>` / `git diff <range>` の出力を判定対象とする
3. 決定した `REVIEWER_SET` をユーザー提示に含める

### 2-2A: 起動宣言（Fan-Out Gate — 並列発火の直前に必ず書く）

reviewer 並列起動メッセージを送信する **直前のターン本文中** に、Fan-Out Gate 宣言テンプレートを必ず生成すること。テンプレート本体・運用ルール・違反パターンは `~/.claude/skills/pir2/references/fan-out-gate.md` を参照（再レビュー時も省略しない）。

### 2-2B: 並列発火（同一メッセージ内）

直前ターンで宣言した REVIEWER_SET の各観点について、同一の `<function_calls>` ブロック内に Agent ツール呼び出しを **N 個** 並べて 1 メッセージで同時送信する。各体は `REVIEWER_ROLE` を変えて担当観点を分割する。

観点マッピング（REVIEWER_ROLE ごとの担当分野）: `~/.claude/skills/pir2/references/fan-out-gate.md` の「## 観点マッピング」セクションを参照。

各体の起動パラメータ:

- model: `sonnet`
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - `PROJECT_MEMORY_DIR=[ステップ0で取得したパス]`
  - `RUN_DIR=[ステップ0で取得したパス]`
  - `REVIEW_INDEX=01`（起動する全体で同じ番号を共有する）
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - レビュー対象のファイル一覧
  - 差分の取得コマンド（ステップ1で使用したものと同じ git diff コマンド。`--name-only` を外したもの）
  - 「plan.md / implementation-*.md は存在しません。上記の差分コマンドで変更内容を確認し、変更されたファイルを Read してレビューしてください。レビューレポート本体は `{RUN_DIR}/review-{REVIEW_INDEX}-{REVIEWER_ROLE}.md` に書き出し、チャットには VERDICT + 要約のみ返してください」

---

## ステップ 3: 結果の統合・提示

起動した reviewer の VERDICT と書き出したレポートをユーザーに提示する:

### VERDICT 集約

- **全体 VERDICT = PASS**: 起動した全員が `VERDICT: PASS`
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL`

### ユーザーへの提示フォーマット

```
## レビュー完了

### 全体 VERDICT
[PASS|FAIL]

### REVIEWER_SET
[起動した観点のカンマ区切り、例: correctness,consistency,security]

### 観点別 VERDICT
（REVIEWER_SET に含まれる観点のみ。例）
- correctness: [PASS|FAIL] — {RUN_DIR}/review-01-correctness.md
- consistency: [PASS|FAIL] — {RUN_DIR}/review-01-consistency.md
- security: [PASS|FAIL] — {RUN_DIR}/review-01-security.md

### 主な指摘事項（Critical / High のみ）
- [深刻度] `ファイル:行` — [問題の要約]（出典: [ROLE]）
```

各 reviewer が書き出した `{RUN_DIR}/review-01-{ROLE}.md` を Read して、Critical / High の問題一覧を統合してユーザーに提示する。Medium / Low は件数サマリーのみに留める（詳細はファイル参照）。
