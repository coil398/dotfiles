---
name: "epic"
description: 大規模タスク（エピック）を複数サブタスクに分割し、依存グラフに沿って concrete worker を起動する上位オーケストレーションワークフロー。人管理を抜いた PM／テックリード相当。1 つの機能追加では収まらない・複数サブシステムを横断する・独立フィーチャーが並行する大型タスクに使う。「まとめて全部作って」「複数機能を一気に」「大きめの改修を段階的に」といった要望に対応する。ユーザーが /epic と入力したら必ずこのスキルを使う。先頭に --codex を付けると実装 worker を `codex-runner` に差し替える。
argument-hint: "[大規模タスクの説明]（先頭に任意で --codex）"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

> **Cursor 実行時の注意**
> - 子エージェントは `Task` ツール（`subagent_type`）で起動する。Claude の `Agent` ツール語彙は使わない
> - メインエージェントがオーケストレーター。VERDICT ループ・ユーザー確認ゲート・ループカウンタはメインが保持する
> - Claude 専用機能（`TeamCreate` / Agent Teams / `~/.claude/hooks`）は Cursor では非対応のためスキップする
> - Task の `model` は省略するか `inherit` のみ（親 Auto に従う）。ベンダー名はハードコードしない
> - Cursor agent の `model` は `inherit` か公式モデル ID。仕事の分類は `role: coding|reasoning`
> - Codex CLI 橋渡し（`/codex` / `/pir2codex`）では Codex 側 model ID の明示指定は許可する

# Epic — 大規模タスクの多段オーケストレーション

epic 本体（= メイン Cursor agent、Auto / `inherit`）が、探索結果を統合してエピックの要件・スコープ・サブタスク分割・依存グラフ（DAG）を直接決め、`epic-plan.md` を管理します。Task は read-only の `explorer`、具体的なサブタスクを実装する worker、`reviewer` / `tester` に限って起動します。

以下の前提を必ず踏まえて進めてください（技術的整合性の詳細は本文末尾「Task 起動方式の技術整合性」を参照）:

- epic 本体（= メイン Cursor agent）がオーケストレーター。探索結果を集約し、計画・DAG・要件・スコープを保持したまま各サブタスクを起動する。
- **2 階層を基本とする**: epic 本体(L0) → read-only explorer / concrete implementer / reviewer / tester(L1)。計画を委譲する専用 Task や、サブタスクから制御エージェントを再起動する経路は作らない。
- **深さバジェット制約**: L1 の worker がさらに Task を起動する場合は read-only の explorer に限る。実装・レビュー・テストの起動とループ管理はメインに戻す。
- **ユーザー対話は epic 本体に集約**: worker はユーザーと対話できない。分割確認ゲート（Phase 1.5）および実装・レビュー・テスト中に発生するユーザー確認はすべて epic 本体が担う（後述ステップ 2.5 / 3-4）。Auto mode でも例外なし。

**タスク**: $ARGUMENTS

---

## ステップ 1: EPIC_RUN_DIR の確定と --codex パース

最初に `--codex` を先頭フラグとしてだけ解析し、実装 worker とタスク本文を確定します:

```bash
IMPLEMENTATION_WORKER="implementer"
TASK="${ARGUMENTS-}"
case "$TASK" in
  "--codex "*) IMPLEMENTATION_WORKER="codex-runner"; TASK="${TASK#--codex }" ;;
  "--codex")   IMPLEMENTATION_WORKER="codex-runner"; TASK="" ;;
esac
echo "IMPLEMENTATION_WORKER=$IMPLEMENTATION_WORKER"
```

次に、読み込み済みの本 `SKILL.md` の実体パスから、その親ディレクトリの親を `CURSOR_SKILLS_DIR` として確定します。対象アプリケーションの `PROJECT_ROOT` から Skill の場所を組み立ててはいけません。`${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を Read し、「Cursor の run directory」の安全な排他的予約手順を一度だけ実行してください。その手順の `ARGUMENTS` 入力には `--codex` 除去後の `TASK` を使います。

予約手順が返した `RUN_DIR` を直後に `EPIC_RUN_DIR="$RUN_DIR"` と一度だけ束縛し、以降は再計算・再予約しません。下位 Task と記録へ渡す `EPIC_RUN_DIR` がすべてこの値と一致することを確認してください。`PROJECT_ROOT` / `PROJECT_MEMORY_DIR` も同じ予約手順が返した値を使います。

`--codex` は実装 worker を `implementer` から `codex-runner` に差し替えるだけであり、epic 本体の探索・計画・分割判定は一切変えません（サブタスクごとの混在はしない＝全サブタスク一律 `IMPLEMENTATION_WORKER`）。

---

## ステップ 2: Phase 1 — メインによる分割・DAG策定

メイン Cursor agent が `explorer` を `Task` ツールで起動し、全体像・サブシステム境界・依存関係を read-only で調査させてください。探索結果をすべて Read した後、メイン自身が要件・スコープ・サブタスク・DAG を決定して `{EPIC_RUN_DIR}/epic-plan.md` を作成します。計画のための専用 Task は起動しません。

- `PROJECT_MEMORY_DIR=[パス]` / `EPIC_RUN_DIR=[パス]`
- タスク内容（`--codex` 除去後の `TASK`）
- 「探索レポート本体は `{EPIC_RUN_DIR}/epic-exploration-*.md` に書き出し、チャットには要約のみ返すこと」
- 「探索フェーズでは実装・レビュー・テスト・計画の確定を行わず、`git add` / `git commit` などリポジトリ状態を変更する操作も行わないこと」
- 「サブシステム境界・feature の切れ目・主要依存関係・既存ルールを調査すること」

メインは探索レポートを根拠に、`epic-plan.md` の次の内容を直接作成します:

- 全体要件と変更しない範囲
- サブタスクの目的・担当範囲・想定成果物・許可/禁止境界
- サブタスク間の依存グラフ（DAG）、並列集合、共有リソースによる直列化
- 各サブタスクへ渡す実装要件、完了基準、検証方法
- `USER_DECISION_REQUIRED` / `EXPLORATION_NEEDED` と、その根拠

作成後、メインが分割要約を提示します。

---

## ステップ 2.5: Phase 1.5 — 分割結果のユーザー確認（epic 本体・Auto mode でも例外なし）

検出トリガー・確認フォーマットは pir2 の plan-choice-gate に倣います（`.cursor/skills/pir2/references/plan-choice-gate.md` を参照）。

epic 本体が `{EPIC_RUN_DIR}/epic-plan.md` を Read し、**サブタスク一覧＋依存グラフ＋各サブタスクの要件・境界** をユーザーに提示して承認を得てください。承認前に Phase 2 へ進んではなりません。

`epic-plan.md` に `USER_DECISION_REQUIRED` / `EXPLORATION_NEEDED` があれば必ずここで提示します。ユーザーが分割方針を変えた場合は、メインが影響する要件・スコープ・DAG・サブタスク記述だけを増分更新し、確定済みの計画を破棄しません。

**このゲートは必ず epic 本体で行う**（サブエージェントはユーザー対話不可のため）。

---

## ステップ 3: Phase 2 — サブタスク実行

### 3-0: concrete worker の起動方式

`epic-plan.md` の各サブタスクを、具体的な実装責務を持つ `implementer`（`--codex` 時は `codex-runner`）として `Task` ツールで起動します。`model` は省略または `inherit` とし、親 Auto の設定に従わせます。プロンプトにはサブタスクの目的・要件・許可/禁止境界・完了基準・検証方法・`EPIC_RUN_DIR` を含め、計画を再委譲する指示は含めません。

> Task `model` は省略/`inherit` のみ。強さは親 Auto と agent overlay の role に任せる。ユーザーがモデルを指名したときだけ Task に渡す。

### 3-1: 独立サブタスクの並列 fan-out

DAG で辺のない独立集合は同一メッセージ内で複数 `Task` 起動して並列実行します。pir2 の Fan-Out Gate 慣習に倣い、並列発火直前に自己コミットメント宣言（起動体数＝独立集合サイズ、同一ターン内に並べる）を書いてください。宣言テンプレは pir2 ステップ 7-2A の型を流用します（`.cursor/skills/pir2/references/fan-out-gate.md` を参照）。

### 3-2: 依存サブタスクの直列実行と先行成果の注入

依存辺のあるサブタスクは依存順に 1 体ずつ直列起動します。後続の起動プロンプトに、先行サブタスクの変更ファイル一覧・完了レポート・`git diff` 確認指示を注入してください。先行成果を読み、`epic-plan.md` の境界と命名・契約に従って実装させます。

### 3-3: 深さバジェット管理

worker には「追加調査が必要な場合も read-only の explorer だけを起動し、実装・レビュー・テスト・計画更新の制御 Task は起動しないこと」と明示してください。追加探索の結果はメインへ返し、メインが `epic-plan.md` を必要箇所だけ増分更新してから実装判断を行います。

### 3-4: ユーザーゲートの epic 本体への集約（bubble-up）

worker がユーザー判断を必要とする事項に到達したら、ユーザーには聞けないので**保守的デフォルト**を選び、その決定点を `{EPIC_RUN_DIR}/deferred-decisions.md` に記録し、返り値要約の `DEFERRED_USER_DECISIONS` に列挙するよう指示してください。epic 本体は各 worker 完了後に `DEFERRED_USER_DECISIONS` を集約し、判断が本質的にブロッキングなものはユーザーに提示します（軽微なものは Phase 3 サマリーで一括報告）。

### 3-5: サブ run のマッピング記録

各サブタスクの `Ti → サブ RUN_DIR` 対応を `{EPIC_RUN_DIR}/epic-runs.md` に追記して観測可能性を担保してください。

共有ステート競合はメインが「暗黙依存」として DAG の辺に張り、3-2 の直列化に吸収します。

---

## ステップ 4: Phase 3 — 統合確認とメタ振り返り

全サブタスクの worker 完了後、epic 本体が `git diff` で結合点（サブタスク境界をまたぐインターフェース・命名・未接続実装）の整合を確認します。問題があれば統合修正用の concrete worker を 1 本追加起動してください（新たな依存辺として扱う）。

メタ retrospect: `retrospector` を `Task` ツールで起動し、`ワークフロー種別: epic` と `experimental.md` の epic 実験セクション観測を依頼してください（起動仕様は `.cursor/skills/pir2/references/retrospector-prompt.md` を参照）。

---

## ステップ 5: 最終サマリーの提示

サブタスク一覧・各 worker の作業ディレクトリ・各 worker の結果・集約した `DEFERRED_USER_DECISIONS`・統合確認結果・メタ改善推奨・`EPIC_RUN_DIR` を提示してください。

---

## Task 起動方式の技術整合性

- 計画と DAG はメイン Cursor agent が直接保持し、Task は read-only explorer、concrete implementer、reviewer、tester に限定します。
- `--codex` 時もメインが `epic-plan.md` を作成・更新し、実装だけを `codex-runner` に渡します。Codex bridge に計画・スコープ・DAG の判断を委譲しません。
- Task `model` は省略または `inherit` とし、Cursor の Auto 運用を維持します。

---

## 変更不要（本スキル自体が読み込む既存 references）

epic 専用の `references/` は作りません。RUN_DIR 計算・Fan-Out Gate・ユーザー確認・retrospector 起動仕様は既存の `.cursor/skills/pir2/references/*.md` を参照します（重複 references を作らない）。

---

## 試験実装の位置づけ

`/epic` は試験実装です。運用結果の採用可否はユーザーに委ねます。
