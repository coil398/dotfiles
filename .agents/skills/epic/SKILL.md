---
name: epic
description: 大規模タスク（エピック）を複数サブタスクに分割し、依存グラフに沿って各サブタスクを /pir2 としてネスト起動する上位オーケストレーションワークフロー。人管理を抜いた PM／テックリード相当。1 つの機能追加では収まらない・複数サブシステムを横断する・独立フィーチャーが並行する大型タスクに使う。「まとめて全部作って」「複数機能を一気に」「大きめの改修を段階的に」といった要望に対応する。ユーザーが /epic と入力したら必ずこのスキルを使う。先頭に --codex を付けると下位起動を /pir2codex に一律差し替える。
---

# Epic — 大規模タスクの多段オーケストレーション

epic 本体（= main/primary agent）がオーケストレーターとなり、探索結果を統合してエピックの計画とDAGを作成・更新し、DAGに沿って各サブタスクを `/pir2`（`--codex` 時は `/pir2codex`）としてネスト起動します。

以下の前提を必ず踏まえて進めてください（技術的整合性の詳細は本文末尾「Agent ネスト起動方式の技術整合性」を参照）:

- epic 本体（= main/primary agent）がオーケストレーター。explorerのread-only調査を統合して計画とDAGを作成し、ネストpir2を起動する。
- **3 階層ネスト構造**: epic 本体(L0) → ネスト pir2 ランナー(L1) → 各 pir2 が起動する explorer/implementer/reviewer/tester(L2)。nested subagent support〜 のネスト起動に依存する。
- **深さバジェット制約**: L2 のエージェントがさらに explorer をネスト起動すると L3 になる。epic は設計上 L0→L1→L2 の 3 階層に収める。`experimental.md` の実験も含めてL3以深の実挙動は未検証のため、ネストpir2は **L2で頭打ちにする運用**（後述ステップ3-3）とし、L3が必要になったら、そのpir2配下ではexplorerを再ネストせずL1ランナー自身が直接Glob/Grep/Readで調べる縮退運用にフォールバックする。
- **ユーザー対話はmain/primary agentに集約**: サブエージェント（ネスト pir2 ランナー含む）はユーザーと対話できない。計画レビュー（Phase 1.5）およびサブ pir2 内部で発生するユーザー確認はすべてmain/primary agentが担う（後述ステップ2.5 / 3-4）。ただし、元の依頼ですでに許可された範囲を内部プロセス上の一律承認待ちで止めない。

**タスク**: $ARGUMENTS

---

## ステップ 1: EPIC_RUN_DIR の確定と --codex パース

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `EPIC_RUN_DIR` を確定し、以降のすべてのステップで使用してください。RUN_DIR パターンは pir2 ステップ 1 を踏襲し、SSOT を流用します（`~/.agents/skills/pir2/references/sanitized-cwd.md`＝PROJECT_MEMORY_DIR 用、`run-dir-base.md`＝基底パス）。epic 専用に `EPIC_RUN_DIR` を作ります（feature slug に `epic-` を織り込む）:

```bash
PROJECT_ROOT="$(pwd)"
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.codex/projects/${sanitized_cwd}/memory"
# --codex パース（先頭のみ）: 下位起動スキルを決定し、タスク説明からフラグを除去
SUBTASK_SKILL="pir2"
TASK="$ARGUMENTS"
case "$TASK" in
  "--codex "*) SUBTASK_SKILL="pir2codex"; TASK="${TASK#--codex }" ;;
  "--codex")   SUBTASK_SKILL="pir2codex"; TASK="" ;;
esac
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

`--codex` は「下位スキル名を pir2→pir2codex に差し替えるだけ」であり epic 本体のロジック・分割判定は一切変えません（サブタスクごとの混在はしない＝全サブタスク一律 `SUBTASK_SKILL`）。

---

## ステップ 2: Phase 1 — 探索とエピック計画

main/primary agentが `explorer` subagentをread-only調査担当として起動し、全体探索レポートを `{EPIC_RUN_DIR}/epic-exploration-*.md` に作成させてください。main/primary agentはレポートとタスク内容（`--codex` 除去後の `TASK`）をReadし、サブタスクごとの実装詳細、所有範囲、禁止範囲、成果物、依存辺、共有リソース、完了条件を含む `{EPIC_RUN_DIR}/epic-plan.md` を直接作成してください。

計画とDAGの作成・更新責任はmain/primary agentにあります。explorerは調査とレポート作成だけを行い、具体的な実装は各サブタスクのimplementer/worker、独立した品質判定はreviewer/testerが担当します。

`epic-plan.md` の `### EXPLORATION_NEEDED` にtopicが残る場合、main/primary agentが不足topicを判断して追加のexplorer調査を委譲し、結果をReadして既存の `epic-plan.md` に必要箇所だけ増分反映してください。plan全体を破棄せず、計画担当subagentを起動・再起動しません。最大5回で収束しなければ未解決topicを記録してPhase 1.5へ進みます。

---

## ステップ 2.5: Phase 1.5 — 分割結果のレビューと自動継続（main/primary agent）

検出トリガー・確認フォーマットは pir2 の plan-choice-gate に倣います（`~/.agents/skills/pir2/references/plan-choice-gate.md` を参照）。

main/primary agentが `{EPIC_RUN_DIR}/epic-plan.md` をReadし、**サブタスク一覧＋依存グラフ＋各pir2タスク記述**をユーザーへ進捗共有します。この提示は既定では承認ゲートではありません。次の順で扱ってください。

1. 元の依頼が実行まで明示的に許可しており、計画がその範囲内なら、`{EPIC_RUN_DIR}/user-decisions.md` に `EXECUTION_AUTHORIZED_BY_ORIGINAL_REQUEST` と根拠を記録し、回答ターンを終了せず待機なしで Phase 2 へ進みます。`/goal`、「最後まで」「全部実行」「Issue を作成」などの終端条件はこの扱いです。終端条件は権限を拡張しませんが、内部計画の再承認理由にもなりません。
2. 実行権限はあるものの任意の異論受付が有益な **soft review** では、推奨案と「異論がなければ30秒後に自動継続する」旨を提示し、そのターンを終了しません。安全な read-only / no-regret 作業を続け、必要なら待機機構を一度だけ最大30秒使います。新しい反対・変更入力がなければ `AUTO_CONTINUE_AFTER_30S` を `user-decisions.md` に記録して Phase 2 へ進みます。カウントダウンの反復や無期限ポーリングは禁止です。
3. 次の **hard gate** だけは `HARD_WAITING_USER` として停止し、タイムアウトで越えてはいけません: ユーザーが計画のみ・実行前承認を明示した場合、未許可の破壊的／不可逆操作、新たな外部書き込み・送信・課金・本番変更、資格情報や権限の欠如、成果物を実質的に変える複数案から選択が不可欠な場合。無応答を新しい権限の同意とみなしてはいけません。

`epic-plan.md` に USER_DECISION_REQUIRED / EXPLORATION_NEEDED があっても、ラベルだけでhard gateと判定しません。既存の依頼・仕様・リポジトリから安全に解決できるものはmain/primary agentが推奨案を採用して記録し、自動継続します。hard gateに該当する未解決事項だけをユーザーへ提示します。ユーザーが分割方針を変えた場合は決定を記録し、既存の `epic-plan.md` に影響範囲と変更点を増分反映してください。計画を最初から作り直さないでください。

**この判定と進捗共有は必ずmain/primary agentが行う**（サブエージェントはユーザー対話不可のため）。

---

## ステップ 3: Phase 2 — サブタスクのネスト pir2 実行

### 3-0: ネスト pir2 の起動方式

下記「Agent ネスト起動方式の技術整合性」の結論をここに反映します。各サブタスクを `Agent` ツールで `subagent_type=general-purpose` として起動し、プロンプトで「あなたはこのサブタスクの PIR² オーケストレーターです。`~/.agents/skills/${SUBTASK_SKILL}/SKILL.md` をReadし、その手順に従ってサブタスク `<Ti タスク記述>` を最後まで実行してください」と指示します。計画の作成・更新は各サブタスクのmain/primary agentが担います。

general-purposeランナーはSKILL.md全文を自分で解釈し、explorer/implementer/reviewer/testerの起動・ループ管理・VERDICT集約・ユーザー確認ゲートの委譲判断まで自律的にこなします。起動する役割と実行形態は、利用可能な実行環境の定義に従ってください。

### 3-1: 独立サブタスクの並列 fan-out

DAG で辺のない独立集合は同一メッセージ内で複数 `Agent` 起動して並列実行します。pir2 の Fan-Out Gate 慣習に倣い、並列発火直前に自己コミットメント宣言（起動体数＝独立集合サイズ、同一 function_calls ブロックに並べる）を書いてください。宣言テンプレは pir2 ステップ 7-2A の型を流用します（`~/.agents/skills/pir2/references/fan-out-gate.md` を参照）。

### 3-2: 依存サブタスクの直列実行と先行成果の注入

依存辺のあるサブタスクは依存順に 1 体ずつ直列起動します。後続の起動プロンプトに、先行サブタスクの返り値から得た `作業ディレクトリ(サブ RUN_DIR)` パス・変更ファイル一覧・`git diff` 確認指示を注入してください（ネスト pir2 は自前でコミットしないため、先行の変更は working tree に残っており後続 pir2 の explore フェーズが拾えます。加えて明示注入で取りこぼしを防ぎます）。

### 3-3: 深さバジェット管理

ネスト pir2 ランナーには「あなたの配下のimplementerは、explorerをさらにネスト起動（L3）せず、pir2ステップ3のexplorerフェーズ（L2）で得た探索に依拠すること。L2での `Agent` 起動が深さ超過で拒否された場合は、そのpir2を `IMPLEMENTATION_ACTOR=main`（pir2既存概念）に切り替え、explorerを再ネストせずL1ランナー自身が直接Glob/Grep/Readで調べる縮退運用で完遂すること」と明示してください。

### 3-4: ユーザーゲートの epic 本体への委譲（bubble-up）

ネスト pir2 ランナーには「pir2 内部のユーザー確認ゲート（plan-choice-gate / 6.5 未解決事項 / continuation-gate 等）に到達したら、ユーザーには聞けないので**元の依頼の権限内で保守的デフォルト**を選び、その決定点を `{サブ RUN_DIR}/deferred-decisions.md` に記録し、返り値要約の `DEFERRED_USER_DECISIONS` に列挙すること。hard gate に該当する場合だけ、そのサブタスクを `HARD_WAITING_USER` として返すこと」と指示してください。epic 本体はサブ pir2 完了ごとに `DEFERRED_USER_DECISIONS` を集約します。軽微なものは続行して Phase 3 サマリーで一括報告し、hard gate があっても影響を受けない ready-set のサブタスクは止めずに進めます。依存上どうしても必要な hard gate だけをユーザーへ提示します。

### 3-5: サブ run のマッピング記録

各サブタスクの `Ti → サブ RUN_DIR` 対応を `{EPIC_RUN_DIR}/epic-runs.md` に追記して観測可能性を担保してください。

共有ステート競合はmain/primary agentが「暗黙依存」としてDAGの辺に張り、3-2の直列化に吸収します。

---

## ステップ 4: Phase 3 — 統合確認とメタ振り返り

全サブ pir2 完了後、main/primary agentが `git diff` で結合点（サブタスク境界をまたぐインターフェース・命名・未接続実装）の整合を確認します。問題があれば統合修正用のサブタスクを1本追加起動してください（新たな依存辺として扱う）。

メタ retrospect: `retrospector` を `Agent` ツールで起動し、`ワークフロー種別: epic` と `experimental.md` の epic 実験セクション観測を依頼してください（起動仕様は `~/.agents/skills/pir2/references/retrospector-prompt.md` を参照）。

---

## ステップ 5: 最終サマリーの提示

サブタスク一覧・各サブ RUN_DIR・各サブ pir2 の VERDICT・集約した `DEFERRED_USER_DECISIONS`・統合確認結果・メタ改善推奨・`EPIC_RUN_DIR` を pir2 ステップ 12 の型で提示してください。

---

## Agent ネスト起動方式の技術整合性

- pir2 は「スキル」でありエージェント型 `pir2` は存在しません。したがってネスト起動は `subagent_type=general-purpose`（Tools: *、Read と Agent を持つ）に対し、プロンプトで `~/.agents/skills/${SUBTASK_SKILL}/SKILL.md` をReadさせてオーケストレーターとして実行させる方式を**第一の起動方式**とします（Read + Agent のみに依存し確実）。起動する役割と実行形態は利用可能な実行環境の定義に従います。
- 代替として general-purpose が Skill ツールで直接 `/pir2` を起動できる場合はそれでもよいですが、サブエージェント内での Skill 起動の挙動は環境依存のため既定は Read ベースとします。
- L0→L1→L2 の 3 階層構成は既存のexplorerネスト実験と同型ですが、当該実験は Active（Evidence Summary は 0 件）で実行実績はまだありません。epic はこの 3 階層に収めます（3-3 の L2 頭打ち運用）が、3 階層の実挙動は未検証である点に留意してください。

---

## 変更不要（本スキル自体が読み込む既存 references）

epic 専用の `references/` は作りません。RUN_DIR 計算・Fan-Out Gate・plan-choice-gate・retrospector 起動仕様は既存の `~/.agents/skills/pir2/references/*.md` を参照します（重複 references を作らない）。

---

## 試験実装の位置づけ

`/epic` は試験実装です。採用可否は `~/.agents/skills/pir2/references/experimental.md` の `epic-orchestrator-nested-pir2` 実験を SSOT に観測し、恒久採用の判断はユーザーに委ねます。
