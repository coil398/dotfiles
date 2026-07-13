---
name: epic
description: 大規模タスク（エピック）を複数サブタスクに分割し、依存グラフに沿って各サブタスクを /pir2 としてネスト起動する上位オーケストレーションワークフロー。人管理を抜いた PM／テックリード相当。1 つの機能追加では収まらない・複数サブシステムを横断する・独立フィーチャーが並行する大型タスクに使う。「まとめて全部作って」「複数機能を一気に」「大きめの改修を段階的に」といった要望に対応する。ユーザーが /epic と入力したら必ずこのスキルを使う。先頭に argument-hint: [大規模タスクの説明]（先頭に任意で --codex）
---

<!-- Cursor native overlay: seeded from .claude/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意（第2波）**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Claude 専用機能（`TeamCreate` / Agent Teams / `~/.claude/hooks`）は Cursor では非対応のためスキップする（必要なら通常の直列 Task 起動へ縮退）
> - ベンダーモデル名（reasoning / coding / reasoning 等）はハードコードしない。agent overlay の `role=reasoning|coding` と Cursor UI の運用既定に従う


# Epic — 大規模タスクの多段オーケストレーション

epic 本体（= メインエージェント）がオーケストレーターとなり、`epic-planner` にエピックを分割・依存グラフ化させ、DAG に沿って各サブタスクを `/pir2` としてネスト起動します。

> **Cursor**: 
以下の前提を必ず踏まえて進めてください（技術的整合性の詳細は本文末尾「Agent ネスト起動方式の技術整合性」を参照）:

- epic 本体（= メインエージェント）がオーケストレーター。`Task` ツールで epic-planner とネスト pir2 を起動する。
- **3 階層ネスト構造**: epic 本体(L0) → ネスト pir2 ランナー(L1) → 各 pir2 が起動する explorer/planner/implementer/reviewer/tester(L2)。Cursor (Task/subagent)〜 のネスト起動に依存する。
- **深さバジェット制約**: L2 のエージェント（planner/reviewer 等）がさらに explorer をネスト起動すると L3 になる。epic は設計上 L0→L1→L2 の 3 階層に収める。`experimental.md` の `pir2-explorer-nesting` 実験（planner→explorer）も同じ 3 階層構成だが、両者とも実行実績は未観測（当該実験の Evidence Summary は 0 件）であり L3 以深の実挙動も未検証。よってネスト pir2 は **L2 で頭打ちにする運用**（後述ステップ 3-3）とし、L3 が必要になったら、その pir2 配下では explorer を再ネストせず L1 ランナー自身が直接 Glob/Grep/Read で調べる縮退運用にフォールバックする。
- **ユーザー対話は epic 本体に集約**: サブエージェント（ネスト pir2 ランナー含む）はユーザーと対話できない。分割確認ゲート（Phase 1.5）およびサブ pir2 内部で発生するユーザー確認ゲートはすべて epic 本体が担う（後述ステップ 2.5 / 3-4）。Auto mode でも例外なし。

**タスク**: $ARGUMENTS

---

## ステップ 1: EPIC_RUN_DIR の確定と --codex パース

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `EPIC_RUN_DIR` を確定し、以降のすべてのステップで使用してください。RUN_DIR パターンは pir2 ステップ 1 を踏襲し、SSOT を流用します（`.cursor/skills/pir2/references/sanitized-cwd.md`＝PROJECT_MEMORY_DIR 用、`run-dir-base.md`＝基底パス）。epic 専用に `EPIC_RUN_DIR` を作ります（feature slug に `epic-` を織り込む）:

```bash
PROJECT_ROOT="$(pwd)"
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.cursor/projects/${sanitized_cwd}/memory"
# --codex パース（先頭のみ）: 下位起動スキルを決定し、タスク説明からフラグを除去
SUBTASK_SKILL="pir2"
TASK="$ARGUMENTS"
case "$TASK" in
  "  "esac
run_ts="$(date +%Y%m%d-%H%M%S)"
run_feature="$(printf '%s' "$TASK" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
[ -z "$run_feature" ] && run_feature="epic"
EPIC_RUN_DIR="${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-epic-${run_feature}"
mkdir -p "$EPIC_RUN_DIR"
if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  grep -qxF '/.ai-pir-runs/' "${PROJECT_ROOT}/.gitignore" 2>/dev/null || echo '/.ai-pir-runs/' >> "${PROJECT_ROOT}/.gitignore"
fi
echo "SUBTASK_SKILL=$SUBTASK_SKILL"
echo "EPIC_RUN_DIR=$EPIC_RUN_DIR"
```


---

## ステップ 2: Phase 1 — エピック分割（epic-planner）

`epic-planner` を `Task` ツールで起動してください（role=reasoning。モデル名はピンしない）。プロンプトに含める必須項目:

- `PROJECT_MEMORY_DIR=[パス]` / `EPIC_RUN_DIR=[パス]`
- タスク内容（`--codex` 除去後の `TASK`）
- 「全体探索は自分で explorer をネスト起動して実施し、探索レポートは `{EPIC_RUN_DIR}/epic-exploration-*.md` に書き出すこと」
- 「分割戦略レポート本体は `{EPIC_RUN_DIR}/epic-plan.md` に書き出し、チャットには要約＋USER_DECISION_REQUIRED / EXPLORATION_NEEDED の有無のみ返すこと」
- 「実装詳細（ファイル×関数×変更内容・実装ステップ）は出さないこと。それは各サブ pir2 の planner の責務」

epic-planner から分割要約を受け取ってください。

EXPLORATION_NEEDED が残る場合の扱い: epic-planner は自前のネスト explorer で自己解決するのが原則。それでも topic が残ったら Phase 1.5 のゲートでユーザーに提示する（epic 本体は追加で epic-planner を再起動してもよいが、ハードキャップは pir2 ステップ 4.5 に倣い最大 5 回）。

---

## ステップ 2.5: Phase 1.5 — 分割結果のユーザー確認（epic 本体・Auto mode でも例外なし）

検出トリガー・確認フォーマットは pir2 の plan-choice-gate に倣います（`.cursor/skills/pir2/references/plan-choice-gate.md` を参照）。

epic 本体が `{EPIC_RUN_DIR}/epic-plan.md` を Read し、**サブタスク一覧＋依存グラフ＋各 pir2 タスク記述** をユーザーに提示して承認を得てください。承認前に Phase 2 へ進んではなりません。

epic-planner が USER_DECISION_REQUIRED / EXPLORATION_NEEDED を出していれば必ずここで提示します。ユーザーが分割方針を変えた場合は epic-planner を再起動してください。

**このゲートは必ず epic 本体で行う**（サブエージェントはユーザー対話不可のため）。

---

## ステップ 3: Phase 2 — サブタスクのネスト pir2 実行

### 3-0: ネスト pir2 の起動方式

下記「Agent ネスト起動方式の技術整合性」の結論をここに反映します。各サブタスクを `Task` ツールで `subagent_type=general-purpose` として role=reasoning（モデル名はピンしない）で起動し、プロンプトで「あなたはこのサブタスクの PIR² オーケストレーターです。`.cursor/skills/${SUBTASK_SKILL}/SKILL.md` を Read し、その手順に従ってサブタスク `<Ti タスク記述>` を最後まで実行してください」と指示します。

> ⚠️ **L1 ランナーは role=reasoning 相当**で起動すること（モデル名はピンしない）。general-purpose ランナーは SKILL.md 全文を自分で解釈し、explorer/planner/implementer/reviewer/tester の起動・ループ管理・VERDICT 集約・ユーザー確認ゲートの委譲判断まで自律的にこなす必要があります。

### 3-1: 独立サブタスクの並列 fan-out

DAG で辺のない独立集合は同一メッセージ内で複数 `Task` 起動して並列実行します。pir2 の Fan-Out Gate 慣習に倣い、並列発火直前に自己コミットメント宣言（起動体数＝独立集合サイズ、同一 function_calls ブロックに並べる）を書いてください。宣言テンプレは pir2 ステップ 7-2A の型を流用します（`.cursor/skills/pir2/references/fan-out-gate.md` を参照）。

### 3-2: 依存サブタスクの直列実行と先行成果の注入

依存辺のあるサブタスクは依存順に 1 体ずつ直列起動します。後続の起動プロンプトに、先行サブタスクの返り値から得た `作業ディレクトリ(サブ RUN_DIR)` パス・変更ファイル一覧・`git diff` 確認指示を注入してください（ネスト pir2 は自前でコミットしないため、先行の変更は working tree に残っており後続 pir2 の explore フェーズが拾えます。加えて明示注入で取りこぼしを防ぎます）。

### 3-3: 深さバジェット管理

ネスト pir2 ランナーには「あなたの配下の planner/reviewer/implementer は explorer をさらにネスト起動（L3）せず、pir2 ステップ 3 の explorer フェーズ（L2）で得た探索に依拠すること。L2 での `Task` 起動が深さ超過で拒否された場合は、その pir2 は `IMPLEMENTATION_ACTOR=main`（pir2 既存概念）に切り替え、explorer を再ネストせず L1 ランナー自身が直接 Glob/Grep/Read で調べる縮退運用で完遂すること」と明示してください。

### 3-4: ユーザーゲートの epic 本体への委譲（bubble-up）

ネスト pir2 ランナーには「pir2 内部のユーザー確認ゲート（plan-choice-gate / 6.5 未解決事項 / continuation-gate 等）に到達したら、ユーザーには聞けないので**保守的デフォルト**を選び、その決定点を `{サブ RUN_DIR}/deferred-decisions.md` に記録し、返り値要約の `DEFERRED_USER_DECISIONS` に列挙すること」と指示してください。epic 本体はサブ pir2 完了ごとに `DEFERRED_USER_DECISIONS` を集約し、判断が本質的にブロッキングなものはユーザーに提示します（軽微なものは Phase 3 サマリーで一括報告）。

### 3-5: サブ run のマッピング記録

各サブタスクの `Ti → サブ RUN_DIR` 対応を `{EPIC_RUN_DIR}/epic-runs.md` に追記して観測可能性を担保してください。

共有ステート競合の特別扱いは epic 本体に持たせません（epic-planner が「暗黙依存」として DAG の辺に張り、3-2 の直列化に吸収されます）。

---

## ステップ 4: Phase 3 — 統合確認とメタ振り返り

全サブ pir2 完了後、epic 本体が `git diff` で結合点（サブタスク境界をまたぐインターフェース・命名・未接続実装）の整合を確認します。問題があれば統合修正用のサブタスクを 1 本追加起動してください（新たな依存辺として扱う）。

メタ retrospect: `retrospector` を `Task` ツールで起動し、`ワークフロー種別: epic` と `experimental.md` の epic 実験セクション観測を依頼してください（起動仕様は `.cursor/skills/pir2/references/retrospector-prompt.md` を参照）。

---

## ステップ 5: 最終サマリーの提示

サブタスク一覧・各サブ RUN_DIR・各サブ pir2 の VERDICT・集約した `DEFERRED_USER_DECISIONS`・統合確認結果・メタ改善推奨・`EPIC_RUN_DIR` を pir2 ステップ 12 の型で提示してください。

---

## Agent ネスト起動方式の技術整合性

- pir2 は「スキル」でありエージェント型 `pir2` は存在しません。したがってネスト起動は `subagent_type=general-purpose`（Tools: *、Read と Task を持つ）に対し、プロンプトで `.cursor/skills/${SUBTASK_SKILL}/SKILL.md` を Read させてオーケストレーターとして実行させる方式を**第一の起動方式**とします（Read + Task のみに依存し確実）。**この起動は role=reasoning 相当で行うこと**（理由はステップ 3-0 参照）。
- 代替として general-purpose が Skill ツールで直接 `/pir2` を起動できる場合はそれでもよいですが、サブエージェント内での Skill 起動の挙動は環境依存のため既定は Read ベースとします。
- L0→L1→L2 の 3 階層構成は既存 `pir2-explorer-nesting` 実験（planner→explorer）と同型ですが、当該実験は Active（Evidence Summary は 0 件）で実行実績はまだありません。epic はこの 3 階層に収めます（3-3 の L2 頭打ち運用）が、3 階層の実挙動は未検証である点に留意してください。

---

## 変更不要（本スキル自体が読み込む既存 references）

epic 専用の `references/` は作りません。RUN_DIR 計算・Fan-Out Gate・plan-choice-gate・retrospector 起動仕様は既存の `.cursor/skills/pir2/references/*.md` を参照します（重複 references を作らない）。

---

## 試験実装の位置づけ

`/epic` は試験実装です。採用可否は `.cursor/skills/pir2/references/experimental.md` の `epic-orchestrator-nested-pir2` 実験を SSOT に観測し、恒久採用の判断はユーザーに委ねます。
