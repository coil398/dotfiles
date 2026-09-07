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

### reviewer の起動

同じメインが `${CURSOR_SKILLS_DIR}/reviewer/SKILL.md` を Read してその手順を実行します。別の進行担当を起動せず、対象版、要件、ユーザー指定、実在する差分、受入条件、必要な確認範囲を渡して reviewer の選定・配分・判定を委ねます。`--reviewers` の指定やその解釈をこの workflow で再定義しません。

shared reviewer が評価者を起動する場合、評価者には reviewer の進行手順を渡さず、`${CURSOR_SKILLS_DIR}/code-review-guidance/SKILL.md` の実体絶対 path と対象に対応する reference だけを渡します。通常の Task は `model` を省略または `inherit` とし、実在する対象と変更禁止範囲だけを入力にします。未生成の plan・report・verdict を作業条件にしません。

---

## ステップ 3: レビュー結果に応じた修正

reviewer の返却が要件未達または未確認を示す場合、メインが実差分・報告・要求を照合して根本原因を特定し、対象範囲の最小修正を `implementer` へ渡します。修正後は影響する確認だけを shared reviewer の手順で再確認します。原因不明の同じ呼び出しを繰り返さず、未確認事項を成功に変換しません。

---

## ステップ 4: 最終サマリーの提示

```
## IR 完了サマリー

### タスク
[タスクの説明]

### 変更ファイル
[実差分で確認した一覧。implementation report を保存していない場合も自己申告で補わない]

### レビュー結果
- reviewer: [実際に起動した shared reviewer と返却。未実行なら理由]
- [主な指摘事項があれば記載]
```
