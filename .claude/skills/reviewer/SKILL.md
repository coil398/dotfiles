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
2. **フラグ未指定時の自動選定**（以下を上から評価）:
   1. `correctness` は常に含める
   2. 対象ファイル一覧にコード拡張子が含まれる（ドキュメント・設定のみでない） → `consistency` を追加
   3. レビュー範囲指定テキストまたは差分テキスト（`git diff <range>` の出力）に**セキュリティ関連語句**（認証 / 認可 / auth / token / secret / password / credential / SQL / XSS / CSRF / シリアライズ / 外部API / ユーザー入力 / validate / sanitize / 権限 / 暗号 / crypto / 脆弱性）が含まれる → `security` を追加
   4. 差分に**新規ファイル追加** (`git diff --diff-filter=A`) または**複数モジュール/レイヤー跨ぎ**（対象ファイルが 2 つ以上の異なるトップレベルディレクトリにまたがる） → `architecture` を追加
   5. 差分に**新規関数・メソッド・クラスの追加**、または**差分行数 > 20 行** → `quality` を追加
   6. **判断に迷う**（差分が取得できない・範囲が曖昧・上記ルールで 1 体しか選ばれないが自信なし） → **全 5 観点にフォールバック**
3. 決定した `REVIEWER_SET` をユーザー提示に含める

### 2-2: reviewer を並列起動

スキル本体（メイン Claude）が `reviewer` サブエージェントを `Agent` ツールで **REVIEWER_SET の観点数ぶん並列起動** してください。1メッセージ内に Agent ツール呼び出しを **観点数ぶん** 並べて同時発火させること（逐次起動は禁止）。各体は `REVIEWER_ROLE` を変えて担当観点を分割する:

- `REVIEWER_ROLE=correctness`: バグ・正確性 / パフォーマンス / リグレッション
- `REVIEWER_ROLE=consistency`: 命名規則・構造一貫性 / 同一ロジック全適用網羅性 / 類似ファイル群波及網羅性
- `REVIEWER_ROLE=quality`: 保守性（局所スコープ）/ テストの質 / データアクセス重複 / スコープ逸脱
- `REVIEWER_ROLE=security`: セキュリティ（OWASP）/ 認可・認証 / シークレット漏洩 / 依存脆弱性
- `REVIEWER_ROLE=architecture`: レイヤリング / 循環依存 / 責務逸脱 / 抽象粒度

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
