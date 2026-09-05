---
name: "review-pr"
description: "PR・リモートブランチ単位でコードレビューする。PR番号・PRのURL・リモートブランチ名を渡されたとき、「PR確認して」「PRレビュー」「review this PR」「gh pr の差分を見て」といった要望に使う。ローカルの未コミット差分・ファイル指定のレビューは /reviewer を使うこと。ユーザーが /review-pr と入力したら必ずこのスキルを使う。"
argument-hint: "[PR番号, ブランチ名, またはファイルパス]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Cursor で提供されない専用 lifecycle / hook API は使わず、必要な分担は通常の `Task` で行う
> - Task の `model` は省略するか `inherit` のみ（親 Auto に従う）。ベンダー名はハードコードしない
> - Cursor agent の `model` は `inherit` か公式モデル ID。仕事の分類は `role: coding|reasoning`

# Review PR — コードレビュー

変更差分をレビューします。このスキル本体（= メインエージェント）がオーケストレーターとなり、`reviewer` を `Task` ツールで **ハイブリッド並列起動**（correctness / consistency / quality / security / architecture の 5 観点から必要なものを選択して 1〜5 体）します。子 subagent からの Task 起動は Cursor では制限されるため、起動責任はスキル本体に集約されます。

**対象**: $ARGUMENTS（PR番号、ブランチ名、またはファイルパス。省略時は現在のステージング差分）

---

## ステップ 0: 実行コンテキストの確認

対象リポジトリの実体を確認する。差分 artifact や reviewer report を保存する場合だけ、親または Cursor が渡す実在の `RUN_DIR` / `PROJECT_MEMORY_DIR` を使用する。PIR² の run path が必要なときは `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を Read してその手順を一度だけ実行し、`sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` の規則を使います。既に渡された値を再計算・再予約しない。保存が不要なら run directory を作成しない。

`/review-pr` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

---

## ステップ 1: 差分の取得

まず `$ARGUMENTS` から `--reviewers=<roles>` と `--all-reviewers` フラグを**抽出して除去**し、残りを対象指定として扱う。次に残り部分に応じて差分を取得する:

- **PR番号が指定された場合**: `gh pr diff <番号>` で差分を取得する
- **ブランチ名が指定された場合**: `git diff <ブランチ名>...HEAD` で差分を取得する
- **ファイルパスが指定された場合**: 該当ファイルを Read する
- **引数なし**: `git diff HEAD` でステージング済み＋未ステージの差分を取得する

いずれもユーザーが対象（PR/ブランチ/ファイル）を明示した上での差分・ピンポイント取得であり、`AGENTS.md (shared SSOT)`「コードベース探索の委譲」の例外（VCS 軽量確認 / ユーザー提示ファイルのピンポイント Read）に該当します。メインエージェント が自発的に広域探索（Grep/Glob 等）を開始する場合はこの例外に該当しないため、explorer に委譲してください。

取得した差分は、複数 reviewer が同じ内容を参照する必要があり、かつ親が安全性を確認した実在の保存先を渡した場合だけ `{RUN_DIR}/diff.patch` に Write する。保存しない場合は親が差分を直接渡す。変更ファイル一覧は実際の差分から取得する。

---

## ステップ 2: レビュー（実差分のリスクに応じた Task 起動）

### 2-1: REVIEWER_SET 決定（非 planner 系：自動選定がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグ**: ステップ 1 で抽出した `--reviewers=<roles>` があればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` があれば全 5 観点。両方指定時は `--reviewers=` を優先
2. **フラグ未指定時の自動選定**（以下を上から評価）:
   1. `correctness` は常に含める
   2. 変更ファイル一覧にコード拡張子が含まれる（ドキュメント・設定のみでない） → `consistency` を追加
   3. `{RUN_DIR}/diff.patch` の内容または PR タイトル/本文に**セキュリティ関連語句**（認証 / 認可 / auth / token / secret / password / credential / SQL / XSS / CSRF / シリアライズ / 外部API / ユーザー入力 / validate / sanitize / 権限 / 暗号 / crypto / 脆弱性）が含まれる → `security` を追加
   4. 差分に**新規ファイル追加**（`diff --git a/dev/null` or `new file mode`）、または変更ファイルが 2 つ以上の異なるトップレベルディレクトリにまたがる → `architecture` を追加
   5. 差分に**新規関数・メソッド・クラスの追加**、または**差分行数 > 20 行** → `quality` を追加
   6. **判断に迷う**（diff が取得できない・対象が曖昧・上記ルールで 1 体しか選ばれないが自信なし） → **全 5 観点にフォールバック**
3. 決定した `REVIEWER_SET` をユーザー提示に含める

### 2-2: reviewer の起動

独立した観点は同一 wave の `Task` に分けられるが、1体で足りる場合は増やさない。起動宣言、固定の同時体数、特定の起動順を完了条件にしない。

各 reviewer の起動パラメータ:

- model: `role=coding`
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - 親が実在する値を渡した場合だけ `PROJECT_MEMORY_DIR=[パス]` / `RUN_DIR=[パス]`
  - `REVIEW_INDEX` は親が report を管理する場合だけ付ける
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - 変更ファイル一覧
  - 保存した場合だけ差分ファイルのパス: `{RUN_DIR}/diff.patch`
  - 「これはコードレビューです。実装は行わず、レビューのみ行ってください。plan / implementation / runner report は実在する場合だけ補助資料として Read し、変更されたファイルの現状も必要に応じて確認してください。親が安全性を確認した保存先を渡した場合だけ report を保存し、渡されなければ VERDICT と根拠をチャットで返してください」

---

## ステップ 3: 結果の統合・提示

起動した reviewer の実際の VERDICT と、保存した場合だけ実在するレポートをユーザーに提示する。未起動の担当や未生成の成果物を補完しない:

### VERDICT 集約

- **全体 VERDICT = PASS**: 起動した全員が `VERDICT: PASS`
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL`

### ユーザーへの提示フォーマット

```
## PR レビュー完了

### 対象
[PR番号 / ブランチ名 / ファイルパス]

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
