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

`REVIEWER_SET` は、レビュー全体の配分と結果意味を定める `${CURSOR_SKILLS_DIR}/reviewer/SKILL.md` および `${CURSOR_SKILLS_DIR}/code-review-guidance/references/result-contract.md` に接続して決めます。明示指定された観点はそのまま親へ渡し、未知の観点は黙って捨てず未認識の指定として返します。未指定時は実差分、依頼、失敗時の具体的な実害から必要な観点だけを選び、低リスクで親のdiff照合が十分ならreviewerを起動しません。キーワード、ファイル数、行数、常時correctness、固定人数を選定条件にしません。

決定した `REVIEWER_SET` と未認識指定を最終サマリー（ステップ 4）に記録します。

### 2-2: reviewer の起動

独立した観点は同一 wave の `Task` に分けられるが、1体で足りる場合は増やさない。起動宣言、固定の同時体数、特定の起動順を完了条件にしない。

各 reviewer の起動パラメータ:

- role: coding（Taskのmodelは省略または `inherit` とし、Cursorの親Autoへ委ねる）
- プロンプト（共通。`REVIEWER_ROLE` のみ変える）:
  - 親が実在する値を渡した場合だけ `PROJECT_MEMORY_DIR=[パス]` / `RUN_DIR=[パス]`
  - `REVIEW_INDEX` は親が report を管理する場合だけ付ける
  - `REVIEWER_ROLE=[correctness|consistency|quality|security|architecture]`（体ごとに変える。REVIEWER_SET に含まれる観点のみ）
  - 実在する implementation report がある場合だけ、そのパス
  - `${CURSOR_SKILLS_DIR}/code-review-guidance/references/result-contract.md` と、親が指定した担当referenceをReadしてください
  - 「plan / implementation / runner report は実在する場合だけ補助資料として Read してください。親が安全性を確認した保存先を渡した場合だけ report を保存し、渡されなければ COVERAGE、VERDICT、根拠をチャットで返してください」

### VERDICT 集約

**今回起動した reviewer** の結果は共通契約に従って集約する:

- **全体 VERDICT = FAIL**: 確認済みの完了阻害問題がある
- **全体 VERDICT = INCOMPLETE**: 必須範囲に未確認が残る
- **全体 VERDICT = PASS**: 必須範囲を確認し、完了阻害問題がない
- `NOT_APPLICABLE` は評価不要の根拠がある場合だけ受け入れ、未起動担当や取得失敗をこの値へ変換しない

---

## ステップ 3: レビュー結果に応じた修正

全体 `VERDICT: FAIL` の場合、メインが実差分・報告・要求を照合して直接原因を特定し、対象範囲の最小修正を `implementer` へ渡します。修正を行う場合だけ実在する指摘、plan、implementation reportをpromptへ渡し、保存先のないreport pathを作りません。修正後は影響した観点だけを再確認します。

全体 `VERDICT: INCOMPLETE` の場合、未確認の必須範囲を特定して必要なreviewまたは確認を実行します。原因不明の同じ呼び出しを繰り返さず、合理的な修正や追加入力がない場合は未完了として報告します。固定回数やカウンタ到達で完了・停止を決めません。`PASS` になったらステップ4へ進みます。

---

## ステップ 4: 最終サマリーの提示

```
## IR 完了サマリー

### タスク
[タスクの説明]

### 変更ファイル
[実差分で確認した一覧。implementation report を保存していない場合も自己申告で補わない]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL/INCOMPLETE/NOT_APPLICABLE]
- COVERAGE: [complete/partial/none]
- REVIEWER_SET: [起動した観点をカンマ区切り、例: correctness,consistency]
- 観点別の COVERAGE/VERDICT: [REVIEWER_SET に含まれる観点のみ。未起動ならなし]
- [主な指摘事項があれば記載]
```
