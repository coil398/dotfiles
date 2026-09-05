---
name: "reviewer"
description: "reviewerエージェントにローカルの差分・ファイルをレビューさせる。バグ・セキュリティ・パフォーマンス・保守性・命名一貫性・リグレッション・データアクセス重複などの観点でレビューし VERDICT: PASS/FAIL を返す。「reviewerに見せて」「reviewer」「ローカルの差分を見て」といった要望に使う。PR番号・リモートブランチ・gh pr 経由のレビューは /review-pr を使うこと。ユーザーが /reviewer と入力したら必ずこのスキルを使う。"
argument-hint: "[レビュー範囲の指定（例: ファイルパス、ブランチ名、コミット範囲。省略時は未コミットの差分）]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Cursor で提供されない専用 lifecycle / hook API は使わず、必要な分担は通常の `Task` で行う
> - Task の `model` は省略するか `inherit` のみ（親 Auto に従う）。ベンダー名はハードコードしない
> - Cursor agent の `model` は `inherit` か公式モデル ID。仕事の分類は `role: coding|reasoning`

# Reviewer — コードレビュー

reviewer エージェントにコードレビューを実行させます。このスキル本体（= メインエージェント）がオーケストレーターとなり、`reviewer` を `Task` ツールで **ハイブリッド並列起動**（correctness / consistency / quality / security / architecture の 5 観点から必要なものを選択して 1〜5 体）します。子 subagent からの Task 起動は Cursor では制限されるため、起動責任はスキル本体に集約されます。

**レビュー範囲**: $ARGUMENTS

---

## ステップ 0: 実行コンテキストの確認

対象リポジトリと差分を確認する。report や差分 artifact を保存する場合だけ、親または Cursor が渡す実在の `RUN_DIR` / `PROJECT_MEMORY_DIR` を使用する。PIR² の run path が必要なときは `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を Read してその手順を一度だけ実行し、`sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` の規則を使います。既に渡された値を再計算・再予約しない。保存が不要なら run directory を作成しない。

`/reviewer` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

---

## ステップ 1: レビュー対象の特定

まず `$ARGUMENTS` から `--reviewers=<roles>` と `--all-reviewers` フラグを**抽出して除去**し、残りをレビュー範囲指定として扱う。次に残り部分に応じてレビュー対象を決定する:

- 指定なし: `git diff --name-only HEAD` で未コミットの差分を取得
- ファイルパス: 指定されたファイルをそのまま対象とする
- ブランチ名: `git diff --name-only <branch>...HEAD` でブランチとの差分を取得
- コミット範囲（例: `HEAD~3..HEAD`）: `git diff --name-only <range>` で差分を取得

対象ファイルが0件の場合はユーザーに報告して終了する。

---

## ステップ 2: レビュー実行（実差分のリスクに応じた Task 起動）

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

### 2-2: reviewer の起動

独立した観点は同一 wave の `Task` に分けられるが、1体で足りる場合は増やさない。起動宣言、固定の同時体数、特定の起動順を完了条件にしない。

各 reviewer の起動パラメータ:

- model: `role=coding`
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - 親が実在する値を渡した場合だけ `PROJECT_MEMORY_DIR=[パス]` / `RUN_DIR=[パス]`
  - `REVIEW_INDEX` は親が report を管理する場合だけ付ける
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - レビュー対象のファイル一覧
  - 差分の取得コマンド（ステップ1で使用したものと同じ git diff コマンド。`--name-only` を外したもの）
  - 「plan / implementation / runner report は実在する場合だけ補助資料として Read してください。親が安全性を確認した保存先を渡した場合だけ report を保存し、渡されなければ VERDICT と根拠をチャットで返してください」

---

## ステップ 3: 結果の統合・提示

起動した reviewer の実際の VERDICT と、保存した場合だけ実在するレポートをユーザーに提示する。未起動の担当や未生成の成果物を補完しない:

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
（REVIEWER_SET に含まれる、実際に起動した観点のみ。保存した場合だけ実在する成果物への参照を含める）
- [role]: [PASS|FAIL] — [保存した場合だけ実在する report path]

### 主な指摘事項（Critical / High のみ）
- [深刻度] `ファイル:行` — [問題の要約]（出典: [ROLE]）
```

各 reviewer の実際の返り値を読み、Critical / High の問題、未確認事項、必要な追加確認を統合してユーザーに提示する。保存した report がある場合だけその実在パスを Read し、未生成のファイルを前提にしない。Medium / Low は後続判断に役立つ場合だけ要約する。
