---
name: "refactor-advisor"
description: "refactor-advisor エージェントにローカルの差分・ファイルを対象としたリファクタリング提案を出させる。reviewer の Critical/High 判定とは別に、Medium/Low 相当の「直したら良くなる改善余地」を提案させる。「リファクタ提案して」「改善余地ある？」「refactor」といった要望に使う。/pir2 ワークフローでは必要な reviewer の確認後に自動起動されるが、このスキルは PIR² 外で単体起動するためのルート。ユーザーが /refactor-advisor と入力したら必ずこのスキルを使う。"
argument-hint: "[対象範囲の指定（例: ファイルパス、ブランチ名、コミット範囲。省略時は未コミットの差分）]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Cursor で提供されない専用 lifecycle / hook API は使わず、必要な分担は通常の `Task` で行う
> - Task の `model` は省略するか `inherit` のみ（親 Auto に従う）。ベンダー名はハードコードしない
> - Cursor agent の `model` は `inherit` か公式モデル ID。仕事の分類は `role: coding|reasoning`

# Refactor Advisor — リファクタリング提案

refactor-advisor エージェントにリファクタリング提案を出させます。このスキル本体（= メインエージェント）がオーケストレーターとなり、`refactor-advisor` を `Task` ツールで **1 体起動**します。reviewer のような複数観点並列ではなく、refactor-advisor は単一の役割（Medium/Low 相当の改善提案）を担当する 1 体構成です。

**対象範囲**: $ARGUMENTS

> ℹ️ このスキルは `refactor-advisor` の **単体起動ルート**です。`/pir2` ワークフロー内では必要な reviewer の確認後に自動起動されるため、このスキルを別途呼ぶ必要はありません。本スキルは PIR² 外でリファクタ提案だけ欲しい場合（既に書き終わったコードに「直したら良くなる改善余地」を出してほしいだけのとき）に使ってください。

---

## ステップ 0: 実行コンテキストの確認

対象リポジトリと現在の status/diff を確認する。report を保存する場合だけ、親または Cursor が渡す実在の `RUN_DIR` / `PROJECT_MEMORY_DIR` を使用する。PIR² の run path が必要なときは `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を Read してその手順を一度だけ実行し、`sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` の規則を使います。既に渡された値を再計算・再予約しない。保存が不要なら run directory を作成しない。

`/refactor-advisor` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

---

## ステップ 1: 対象範囲の特定

`$ARGUMENTS` に応じて対象を決定する:

- 指定なし: `git diff --name-only HEAD` で未コミットの差分を取得
- ファイルパス: 指定されたファイルをそのまま対象とする
- ブランチ名: `git diff --name-only <branch>...HEAD` でブランチとの差分を取得
- コミット範囲（例: `HEAD~3..HEAD`）: `git diff --name-only <range>` で差分を取得

対象ファイルが 0 件の場合はユーザーに「対象がないため refactor-advisor は起動しません」と報告して終了する（提案ゼロ件の起動は無駄なので）。

---

## ステップ 2: refactor-advisor 起動

スキル本体（メインエージェント）が `refactor-advisor` subagentを `Task` ツールで **1 体起動**してください。

起動パラメータ:

- model: `role=coding`
- プロンプトに以下をすべて含める:
  - 親が実在する値を渡した場合だけ `PROJECT_MEMORY_DIR=[パス]` / `RUN_DIR=[パス]`
  - `REVIEW_INDEX` は親が report を管理する場合だけ付ける
  - 対象ファイル一覧（ステップ1で確定したもの）
  - 差分の取得コマンド（ステップ1で使用したものと同じ git diff コマンド。`--name-only` を外したもの）
  - 「plan / implementation / runner report は実在する場合だけ補助資料として Read してください。親が安全性を確認した保存先を渡した場合だけ提案 report を保存し、渡されなければ PROPOSALS 数と根拠をチャットで返してください」

refactor-advisor エージェントは、呼び出し元が渡した実在する plan / implementation / runner report だけを補助資料として Read し、渡されない資料を作業条件にしません。単体起動では上記の実差分と返り値を主資料にし、保存先が渡された場合だけ提案 report を保存してください。

---

## ステップ 3: 結果の提示

refactor-advisor の実際の返り値を受け取り、保存した場合だけ実在する `{RUN_DIR}/refactor-01.md` を Read して提案リストをユーザーに提示する。未生成の report を前提にしない。

### ユーザーへの提示フォーマット

```
## リファクタリング提案

### PROPOSALS
[N]件（Medium: [M]件 / Low: [L]件）

### 書き出し先（保存した場合のみ）
[保存した場合だけ実在する report path、または「なし」]

### 提案一覧（要約）
- [M|L] `ファイル:行` — [タイトル]（根拠: 既存先例 or ガードレール充足の要点 1 行）
...

### 除外した候補
[N]件（refactor-advisor がガードレールで除外したもの。詳細はファイル参照）
```

提案が 0 件の場合は `PROPOSALS: 0件` を明記し、refactor-advisor が出した「除外メモ」「言語イディオム上のコメント」があれば併せて転記する。

> ℹ️ このスキルは **ユーザーゲート（all / 指定番号 / none 選択 → 適用）を持ちません**。提案を実装に反映したい場合は `/ir` や `/pir2` で、実在する report path またはチャット返却の候補を指定してください。`/pir2` 経由なら適用後に必要な reviewer/test を選びます。
