---
name: "ir"
description: "軽量な Implement → Review の2フェーズワークフロー。タスクが明確で小さい場合に使う。バグ修正・小機能追加・設定変更・ファイル修正など、計画不要で「サクッとやって」「これ直して」「簡単な変更」といった要望に対応する。ユーザーが /ir と入力したら必ずこのスキルを使う。"
argument-hint: "[タスクの説明]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意（第2波）**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Cursor で提供されない専用 lifecycle / hook API は使わず、必要な分担は通常の `Task` で行う
> - Task の `model` は省略するか `inherit` のみ（親 Auto に従う）。ベンダー名はハードコードしない
> - Cursor agent の `model` は `inherit` か公式モデル ID。仕事の分類は `role: coding|reasoning`


# IR — Implement → Review

軽量ワークフローを実行します。プランニング・振り返りなしで、小さいタスクに使います。このスキル本体（= メインエージェント）がオーケストレーターとなり、`implementer` / `reviewer` を `Task` ツールで順に起動します。子 subagent からの Task 起動は Cursor では制限されるため、起動責任はスキル本体に集約されます。

**タスク**: $ARGUMENTS

---

## ステップ 0: 実行コンテキストの確定

成果物を保存する必要がある場合だけ、親または Cursor が渡す実在の `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `RUN_DIR` を使用してください。PIR² の run path が必要なときは `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を Read してその手順を一度だけ実行し、`sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` の規則を使います。既に渡された値を再計算・再予約しません。不要な run directory、plan、handoff、report は作成しません。

`/ir` は handoff 連携を行わないため、`HANDOFF_PATH` / `RESUME_MODE` は不要です。

---

## ステップ 1: 実装 (role=coding)

スキル本体（メインエージェント）が `implementer` subagentを `Task` ツールで起動してください。

- role: coding（モデル名はピンしない）
- プロンプト:
  - 親が実在する値を渡した場合だけ `PROJECT_MEMORY_DIR=[パス]` / `RUN_DIR=[パス]`
  - `IMPL_INDEX` は親が複数回の実装を管理する場合だけ付ける
  - タスク内容（$ARGUMENTS）、変更してよいファイル、禁止範囲、既存差分の保全
  - 「この経路では plan を作成しない。保存先を親が渡した場合だけ実装レポートを保存し、渡されなければ完了要約をチャットで返してください」

実装要約を受け取ったら次のステップへ進んでください。

---

## ステップ 2: レビュー（実差分のリスクに応じた Task 起動）

### 2-1: REVIEWER_SET 決定（非 planner 系：自動選定がデフォルト）

`REVIEWER_SET` を決定する:

1. **ユーザーフラグのパース**: `$ARGUMENTS` に `--reviewers=<roles>` が含まれていればカンマ区切りを観点集合として採用（未知 role は無視）。`--all-reviewers` が含まれていれば全 5 観点を採用。両方指定時は `--reviewers=` を優先。フラグ抽出後の残りをタスク説明として扱う
2. **フラグ未指定時の自動選定**（以下を上から評価し該当観点を集合に追加）:
   1. `correctness` は常に含める（動作正否の最低限ゲート）
   2. 実装がコード変更を含む（ドキュメント・設定のみでない。implementer 返り値の変更ファイル一覧で判定） → `consistency` を追加
   3. タスク文言または `{RUN_DIR}/implementation-{IMPL_INDEX}.md` の差分テキストに**セキュリティ関連語句**（認証 / 認可 / auth / token / secret / password / credential / SQL / XSS / CSRF / シリアライズ / 外部API / ユーザー入力 / validate / sanitize / 権限 / 暗号 / crypto / 脆弱性）が含まれる → `security` を追加
   4. 実装で**新規ファイル追加**・**新規ディレクトリ作成**・**複数モジュール/レイヤー跨ぎ** → `architecture` を追加
   5. 実装で**新規関数・メソッド・クラスの追加**、または**ロジック変更行数 > 20 行** → `quality` を追加
   6. **判断に迷う**（implementation-*.md が読めない・タスク文言が曖昧・上記ルールで 1 体しか選ばれないが自信なし） → **全 5 観点にフォールバック**
3. 決定した `REVIEWER_SET` を最終サマリー（ステップ 4）に記録

### 2-2: reviewer の起動

独立した観点は同一 wave の `Task` に分けられるが、1体で足りる場合は増やさない。起動宣言、固定の同時体数、特定の起動順を完了条件にしない。

各 reviewer の起動パラメータ:

- role: coding（モデル名はピンしない）
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - 親が実在する値を渡した場合だけ `PROJECT_MEMORY_DIR=[パス]` / `RUN_DIR=[パス]`
  - `REVIEW_INDEX` は親が report を管理する場合だけ付ける
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - 実在する implementation report がある場合だけ、そのパス
  - 「plan / implementation / runner report は実在する場合だけ補助資料として Read してください。親が安全性を確認した保存先を渡した場合だけ report を保存し、渡されなければ VERDICT と根拠をチャットで返してください」

### VERDICT 集約

**今回起動した reviewer** の VERDICT を以下のルールで集約する:

- **全体 VERDICT = PASS**: 起動した全員が `VERDICT: PASS`
- **全体 VERDICT = FAIL**: 1体でも `VERDICT: FAIL`

---

## ステップ 3: レビューループ (最大2回)

**LOOP_COUNT = 0 から始めてください。**

全体 `VERDICT: FAIL` の場合:

1. `LOOP_COUNT += 1`
2. `LOOP_COUNT >= 2` に達した場合はループを終了してステップ4へ進む
3. `implementer` を再起動する（`IMPL_INDEX` をインクリメント、**FAIL を返した全 reviewer の `{RUN_DIR}/review-{最新}-{ROLE}.md` パスを全て**レビュー指摘事項として渡す、元のタスク内容も渡す）
4. `reviewer` を必要な範囲で再起動して VERDICT を確認する（親が管理する場合だけ `REVIEW_INDEX` を更新し、実在する最新 implementation report を渡す。PASS を返した観点も、修正の影響があれば再レビューする。未起動担当や未生成 report を補わない）
5. 全体 FAIL なら繰り返す

全体 `VERDICT: PASS` になったらステップ4へ進んでください。

---

## ステップ 4: 最終サマリーの提示

```
## IR 完了サマリー

### タスク
[タスクの説明]

### 変更ファイル
[実差分で確認した一覧。implementation report を保存していない場合も自己申告で補わない]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- ループ回数: [LOOP_COUNT]
- REVIEWER_SET: [起動した観点をカンマ区切り、例: correctness,consistency]
- 観点別の VERDICT: [REVIEWER_SET に含まれる観点のみ。例: correctness=[...], consistency=[...]]
- [主な指摘事項があれば記載]
```
