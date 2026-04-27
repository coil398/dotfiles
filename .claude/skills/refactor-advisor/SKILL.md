---
name: refactor-advisor
description: refactor-advisor エージェントにローカルの差分・ファイルを対象としたリファクタリング提案を出させる。reviewer の Critical/High 判定とは別に、Medium/Low 相当の「直したら良くなる改善余地」を提案させる。「リファクタ提案して」「改善余地ある？」「refactor」といった要望に使う。/pir2 ワークフローでは reviewer 全員 PASS 後に自動起動されるが、このスキルは PIR² 外で単体起動するためのルート。ユーザーが /refactor-advisor と入力したら必ずこのスキルを使う。
argument-hint: [対象範囲の指定（例: ファイルパス、ブランチ名、コミット範囲。省略時は未コミットの差分）]
---

# Refactor Advisor — リファクタリング提案

refactor-advisor エージェントにリファクタリング提案を出させます。このスキル本体（= メイン Claude）がオーケストレーターとなり、`refactor-advisor` を `Agent` ツールで **1 体起動**します。reviewer のような複数観点並列ではなく、refactor-advisor は単一の役割（Medium/Low 相当の改善提案）を担当する 1 体構成です。

**対象範囲**: $ARGUMENTS

> ℹ️ このスキルは `refactor-advisor` の **単体起動ルート**です。`/pir2` ワークフロー内では reviewer 全員 PASS 後に自動起動されるため、このスキルを別途呼ぶ必要はありません。本スキルは PIR² 外でリファクタ提案だけ欲しい場合（既に書き終わったコードに「直したら良くなる改善余地」を出してほしいだけのとき）に使ってください。

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
- `HANDOFF_PATH=...`（/refactor-advisor では使用しない）
- `RESUME_MODE=...`（/refactor-advisor では使用しない）

`/refactor-advisor` は handoff 連携を行わないため、`HANDOFF_PATH` と `RESUME_MODE` は無視してください。

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

スキル本体（メイン Claude）が `refactor-advisor` サブエージェントを `Agent` ツールで **1 体起動**してください。

起動パラメータ:

- model: `sonnet`
- プロンプトに以下をすべて含める:
  - `PROJECT_MEMORY_DIR=[ステップ0で取得したパス]`
  - `RUN_DIR=[ステップ0で取得したパス]`
  - `REVIEW_INDEX=01`（単体起動なので 01 固定。差し戻しループはなし）
  - 対象ファイル一覧（ステップ1で確定したもの）
  - 差分の取得コマンド（ステップ1で使用したものと同じ git diff コマンド。`--name-only` を外したもの）
  - 「plan.md / implementation-*.md は存在しません。上記の差分コマンドで対象を確認し、変更されたファイルを Read してリファクタ提案を出してください。提案レポート本体は `{RUN_DIR}/refactor-{REVIEW_INDEX}.md` に書き出し、チャットには PROPOSALS 数 + 要約のみ返してください」

> ⚠️ refactor-advisor エージェント定義（`~/.claude/agents/refactor-advisor.md`）のプロセス節は `{RUN_DIR}/plan.md` と `{RUN_DIR}/implementation-{最新}.md` を Read することを前提に書かれている。単体スキルからの起動ではこれらが存在しないため、上記プロンプトの「plan.md / implementation-*.md は存在しません」指示で**明示的に上書き**すること（reviewer スキルが reviewer に対して同様のフォールバック指示を出している先例と一致させる）。

---

## ステップ 3: 結果の提示

refactor-advisor が書き出した `{RUN_DIR}/refactor-01.md` を Read し、提案リストをユーザーに提示する。

### ユーザーへの提示フォーマット

```
## リファクタリング提案

### PROPOSALS
[N]件（Medium: [M]件 / Low: [L]件）

### 書き出し先
{RUN_DIR}/refactor-01.md

### 提案一覧（要約）
- [M|L] `ファイル:行` — [タイトル]（根拠: 既存先例 or ガードレール充足の要点 1 行）
...

### 除外した候補
[N]件（refactor-advisor がガードレールで除外したもの。詳細はファイル参照）
```

提案が 0 件の場合は `PROPOSALS: 0件` を明記し、refactor-advisor が出した「除外メモ」「言語イディオム上のコメント」があれば併せて転記する。

> ℹ️ このスキルは **ユーザーゲート（all / 指定番号 / none 選択 → 適用）を持ちません**。提案を実装に反映したい場合は `/ir` や `/pir2` で「`{RUN_DIR}/refactor-01.md` の N 番を適用してほしい」と依頼してください。`/pir2` 経由なら適用後に再 reviewer で退行検知まで自動で回ります。
