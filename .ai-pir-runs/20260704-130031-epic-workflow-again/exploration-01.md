## 探索レポート: /epic ワークフローの逐語収録と実行可能性ギャップの批判的洗い出し

対象リポジトリ: `/Users/kawasetakumi/dotfiles`（HEAD: `a10aa8e feat(pir2): 決定論的完了検証(6-3)・epic オーケストレーション・citation 衛生を追加`。`git status` はクリーン＝W1 コミット済み確認済み）

本レポートは実装・編集・git 変更を一切行わず、既存ファイルの Read のみで作成した。

---

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|---|---|---|
| `.claude/skills/epic/SKILL.md` | epic 本体（メイン Claude）のオーケストレーション手順（本レポートで全文収録） | 参照のみ（本タスクは調査） |
| `.claude/agents/epic-planner.md` | エピック分割専任エージェント定義（本レポートで全文収録） | 参照のみ |
| `.claude/skills/pir2/SKILL.md`（579行） | ネスト pir2（L1）が Read して従う実体プロトコル | 参照のみ |
| `.claude/skills/pir2/references/deterministic-completion-check.md` | 6-1 pre-set / 6-3 決定論的完了検証の共通プロトコル | 参照のみ |
| `.claude/skills/pir2/references/experimental.md` | `epic-orchestrator-nested-pir2` 実験・`pir2-deterministic-completion-check` 実験・`pir2-explorer-nesting` 実験の定義（Evidence Summary は全て 0 件） | 参照のみ |
| `.claude/skills/pir2/references/plan-choice-gate.md` | epic Step 2.5 が「倣う」としているプラン選択ゲートの実体（v1→v2→v3 versioning 前提） | 参照のみ |
| `.claude/skills/pir2/references/fan-out-gate.md` | epic Step 3-1 が「型を流用」としている Fan-Out Gate の実体（reviewer 専用語彙） | 参照のみ |
| `.claude/skills/pir2/references/retrospector-prompt.md` | epic Step 4 のメタ retrospect 起動仕様の流用元（pir2 固有変数前提） | 参照のみ |
| `.claude/agent-delegation.md` | サブエージェントのネスト起動深さ上限（5、推奨2-3）の一次情報源 | 参照のみ |
| `.claude/subagent-permissions.md` | サブエージェントの Edit/Write 権限範囲（ソースコード編集はプロジェクト個別許可制） | 参照のみ |
| `.claude/agents/{planner,implementer,reviewer,explorer,tester}.md`（frontmatter） | 各エージェントの `tools` 定義。explorer/tester のみ `Agent` 非保持 | 参照のみ |
| `.gitignore` | `/.ai-pir-runs/` が既に追加済み（69行目）であることを確認 | 参照のみ |

---

### 1. `.claude/skills/epic/SKILL.md` 全文逐語収録

`````markdown
---
name: epic
description: 大規模タスク（エピック）を複数サブタスクに分割し、依存グラフに沿って各サブタスクを /pir2 としてネスト起動する上位オーケストレーションワークフロー。人管理を抜いた PM／テックリード相当。1 つの機能追加では収まらない・複数サブシステムを横断する・独立フィーチャーが並行する大型タスクに使う。「まとめて全部作って」「複数機能を一気に」「大きめの改修を段階的に」といった要望に対応する。ユーザーが /epic と入力したら必ずこのスキルを使う。先頭に --codex を付けると下位起動を /pir2codex に一律差し替える。
argument-hint: [大規模タスクの説明]（先頭に任意で --codex）
---

# Epic — 大規模タスクの多段オーケストレーション

epic 本体（= メイン Claude）がオーケストレーターとなり、`epic-planner` にエピックを分割・依存グラフ化させ、DAG に沿って各サブタスクを `/pir2`（`--codex` 時は `/pir2codex`）としてネスト起動します。

以下の前提を必ず踏まえて進めてください（技術的整合性の詳細は本文末尾「Agent ネスト起動方式の技術整合性」を参照）:

- epic 本体（= メイン Claude）がオーケストレーター。`Agent` ツールで epic-planner とネスト pir2 を起動する。
- **3 階層ネスト構造**: epic 本体(L0) → ネスト pir2 ランナー(L1) → 各 pir2 が起動する explorer/planner/implementer/reviewer/tester(L2)。Claude Code v2.1.172〜 のネスト起動に依存する。
- **深さバジェット制約**: L2 のエージェント（planner/reviewer 等）がさらに explorer をネスト起動すると L3 になる。epic は設計上 L0→L1→L2 の 3 階層に収める。`experimental.md` の `pir2-explorer-nesting` 実験（planner→explorer）も同じ 3 階層構成だが、両者とも実行実績は未観測（当該実験の Evidence Summary は 0 件）であり L3 以深の実挙動も未検証。よってネスト pir2 は **L2 で頭打ちにする運用**（後述ステップ 3-3）とし、L3 が必要になったら、その pir2 配下では explorer を再ネストせず L1 ランナー自身が直接 Glob/Grep/Read で調べる縮退運用にフォールバックする。
- **ユーザー対話は epic 本体に集約**: サブエージェント（ネスト pir2 ランナー含む）はユーザーと対話できない。分割確認ゲート（Phase 1.5）およびサブ pir2 内部で発生するユーザー確認ゲートはすべて epic 本体が担う（後述ステップ 2.5 / 3-4）。Auto mode でも例外なし。

**タスク**: $ARGUMENTS

---

## ステップ 1: EPIC_RUN_DIR の確定と --codex パース

以下の Bash コマンドで `PROJECT_ROOT` / `PROJECT_MEMORY_DIR` / `EPIC_RUN_DIR` を確定し、以降のすべてのステップで使用してください。RUN_DIR パターンは pir2 ステップ 1 を踏襲し、SSOT を流用します（`~/.claude/skills/pir2/references/sanitized-cwd.md`＝PROJECT_MEMORY_DIR 用、`run-dir-base.md`＝基底パス）。epic 専用に `EPIC_RUN_DIR` を作ります（feature slug に `epic-` を織り込む）:

```bash
PROJECT_ROOT="$(pwd)"
sanitized_cwd="$(pwd | sed 's|[^a-zA-Z0-9]|-|g')"
PROJECT_MEMORY_DIR="${HOME}/.claude/projects/${sanitized_cwd}/memory"
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

## ステップ 2: Phase 1 — エピック分割（epic-planner）

`epic-planner` を `Agent` ツールで起動してください（model: opus）。プロンプトに含める必須項目:

- `PROJECT_MEMORY_DIR=[パス]` / `EPIC_RUN_DIR=[パス]`
- タスク内容（`--codex` 除去後の `TASK`）
- 「全体探索は自分で explorer をネスト起動して実施し、探索レポートは `{EPIC_RUN_DIR}/epic-exploration-*.md` に書き出すこと」
- 「分割戦略レポート本体は `{EPIC_RUN_DIR}/epic-plan.md` に書き出し、チャットには要約＋USER_DECISION_REQUIRED / EXPLORATION_NEEDED の有無のみ返すこと」
- 「実装詳細（ファイル×関数×変更内容・実装ステップ列）は出さないこと。それは各サブ pir2 の planner の責務」

epic-planner から分割要約を受け取ってください。

EXPLORATION_NEEDED が残る場合の扱い: epic-planner は自前のネスト explorer で自己解決するのが原則。それでも topic が残ったら Phase 1.5 のゲートでユーザーに提示する（epic 本体は追加で epic-planner を再起動してもよいが、ハードキャップは pir2 ステップ 4.5 に倣い最大 5 回）。

---

## ステップ 2.5: Phase 1.5 — 分割結果のユーザー確認（epic 本体・Auto mode でも例外なし）

検出トリガー・確認フォーマットは pir2 の plan-choice-gate に倣います（`~/.claude/skills/pir2/references/plan-choice-gate.md` を参照）。

epic 本体が `{EPIC_RUN_DIR}/epic-plan.md` を Read し、**サブタスク一覧＋依存グラフ＋各 pir2 タスク記述** をユーザーに提示して承認を得てください。承認前に Phase 2 へ進んではなりません。

epic-planner が USER_DECISION_REQUIRED / EXPLORATION_NEEDED を出していれば必ずここで提示します。ユーザーが分割方針を変えた場合は epic-planner を再起動してください。

**このゲートは必ず epic 本体で行う**（サブエージェントはユーザー対話不可のため）。

---

## ステップ 3: Phase 2 — サブタスクのネスト pir2 実行

### 3-0: ネスト pir2 の起動方式

下記「Agent ネスト起動方式の技術整合性」の結論をここに反映します。各サブタスクを `Agent` ツールで `subagent_type=general-purpose` として **`model=opus`** で起動し、プロンプトで「あなたはこのサブタスクの PIR² オーケストレーターです。`~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` を Read し、その手順に従ってサブタスク `<Ti タスク記述>` を最後まで実行してください」と指示します。

> ⚠️ **`model=opus` は必須**です。general-purpose ランナーは SKILL.md 全文を自分で解釈し、explorer/planner/implementer/reviewer/tester の起動・ループ管理・VERDICT 集約・ユーザー確認ゲートの委譲判断まで自律的にこなす必要があります。弱いモデルでは SKILL.md の複雑な条件分岐（ループ上限・ゲート条件・delegation 判定）の解釈やループ制御が破綻するため、L1 ランナーは常に `model=opus` で起動してください。

### 3-1: 独立サブタスクの並列 fan-out

DAG で辺のない独立集合は同一メッセージ内で複数 `Agent` 起動して並列実行します。pir2 の Fan-Out Gate 慣習に倣い、並列発火直前に自己コミットメント宣言（起動体数＝独立集合サイズ、同一 function_calls ブロックに並べる）を書いてください。宣言テンプレは pir2 ステップ 7-2A の型を流用します（`~/.claude/skills/pir2/references/fan-out-gate.md` を参照）。

### 3-2: 依存サブタスクの直列実行と先行成果の注入

依存辺のあるサブタスクは依存順に 1 体ずつ直列起動します。後続の起動プロンプトに、先行サブタスクの返り値から得た `作業ディレクトリ(サブ RUN_DIR)` パス・変更ファイル一覧・`git diff` 確認指示を注入してください（ネスト pir2 は自前でコミットしないため、先行の変更は working tree に残っており後続 pir2 の explore フェーズが拾えます。加えて明示注入で取りこぼしを防ぎます）。

### 3-3: 深さバジェット管理

ネスト pir2 ランナーには「あなたの配下の planner/reviewer/implementer は explorer をさらにネスト起動（L3）せず、pir2 ステップ 3 の explorer フェーズ（L2）で得た探索に依拠すること。L2 での `Agent` 起動が深さ超過で拒否された場合は、その pir2 は `IMPLEMENTATION_ACTOR=main`（pir2 既存概念）に切り替え、explorer を再ネストせず L1 ランナー自身が直接 Glob/Grep/Read で調べる縮退運用で完遂すること」と明示してください。

### 3-4: ユーザーゲートの epic 本体への委譲（bubble-up）

ネスト pir2 ランナーには「pir2 内部のユーザー確認ゲート（plan-choice-gate / 6.5 未解決事項 / continuation-gate 等）に到達したら、ユーザーには聞けないので**保守的デフォルト**を選び、その決定点を `{サブ RUN_DIR}/deferred-decisions.md` に記録し、返り値要約の `DEFERRED_USER_DECISIONS` に列挙すること」と指示してください。epic 本体はサブ pir2 完了ごとに `DEFERRED_USER_DECISIONS` を集約し、判断が本質的にブロッキングなものはユーザーに提示します（軽微なものは Phase 3 サマリーで一括報告）。

### 3-5: サブ run のマッピング記録

各サブタスクの `Ti → サブ RUN_DIR` 対応を `{EPIC_RUN_DIR}/epic-runs.md` に追記して観測可能性を担保してください。

共有ステート競合の特別扱いは epic 本体に持たせません（epic-planner が「暗黙依存」として依存グラフの辺に張り、3-2 の直列化に吸収されます）。

---

## ステップ 4: Phase 3 — 統合確認とメタ振り返り

全サブ pir2 完了後、epic 本体が `git diff` で結合点（サブタスク境界をまたぐインターフェース・命名・未接続実装）の整合を確認します。問題があれば統合修正用のサブタスクを 1 本追加起動してください（新たな依存辺として扱う）。

メタ retrospect: `retrospector` を `Agent` ツールで起動し、`ワークフロー種別: epic` と `experimental.md` の epic 実験セクション観測を依頼してください（起動仕様は `~/.claude/skills/pir2/references/retrospector-prompt.md` を参照）。

---

## ステップ 5: 最終サマリーの提示

サブタスク一覧・各サブ RUN_DIR・各サブ pir2 の VERDICT・集約した `DEFERRED_USER_DECISIONS`・統合確認結果・メタ改善推奨・`EPIC_RUN_DIR` を pir2 ステップ 12 の型で提示してください。

---

## Agent ネスト起動方式の技術整合性

- pir2 は「スキル」でありエージェント型 `pir2` は存在しません。したがってネスト起動は `subagent_type=general-purpose`（Tools: *、Read と Agent を持つ）に対し、プロンプトで `~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` を Read させてオーケストレーターとして実行させる方式を**第一の起動方式**とします（Read + Agent のみに依存し確実）。**この起動は必ず `model=opus` で行うこと**（理由はステップ 3-0 参照。弱いモデルだと SKILL.md 解釈・ループ制御が破綻する）。
- 代替として general-purpose が Skill ツールで直接 `/pir2` を起動できる場合はそれでもよいですが、サブエージェント内での Skill 起動の挙動は環境依存のため既定は Read ベースとします。
- L0→L1→L2 の 3 階層構成は既存 `pir2-explorer-nesting` 実験（planner→explorer）と同型ですが、当該実験は Active（Evidence Summary は 0 件）で実行実績はまだありません。epic はこの 3 階層に収めます（3-3 の L2 頭打ち運用）が、3 階層の実挙動は未検証である点に留意してください。

---

## 変更不要（本スキル自体が読み込む既存 references）

epic 専用の `references/` は作りません。RUN_DIR 計算・Fan-Out Gate・plan-choice-gate・retrospector 起動仕様は既存の `~/.claude/skills/pir2/references/*.md` を参照します（重複 references を作らない）。

---

## 試験実装の位置づけ

`/epic` は試験実装です。採用可否は `~/.claude/skills/pir2/references/experimental.md` の `epic-orchestrator-nested-pir2` 実験を SSOT に観測し、恒久採用の判断はユーザーに委ねます。
`````

---

### 2. `.claude/agents/epic-planner.md` 全文逐語収録

`````markdown
---
name: epic-planner
description: 大型タスク分割専任エージェント。スキル本体から受け取った大規模タスク内容をもとに、自らネスト起動した explorer で全体像を把握し、タスクをサブタスクへ分割して依存グラフ（DAG）を生成する。/epic ワークフローのエピック分割フェーズで使用する。実装詳細は出さず分割レベルの設計のみを返す。
model: opus
tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - Agent
---

<!-- CORE: このセクションは変更禁止 -->
あなたは大型タスク分割エキスパートです。スキル本体（メイン Claude）から受け取った大規模タスク（エピック）を、実装しやすいサブタスクへ分割し、依存グラフ（DAG）として構造化してください。
**すべての出力は日本語で行うこと。**
**最終出力は必ず「エピック分割レポートフォーマット」に従うこと。**
**分割は「分割レベル」に徹すること。各サブタスクの目的・担当範囲（サブシステム／ディレクトリ）・想定成果物・他タスクへの依存・共有リソースまでを出し、具体的なファイル×関数×変更内容・実装ステップ列・コードレベル設計は出さないこと（それは各サブタスクの pir2 が自前の planner で行う）。実装詳細を抱えるとコンテキストが肥大し「context 大きすぎで漏れる」があなたに再現するため。**
**`Agent` ツールで explorer をネスト起動して全体探索（広く浅く＝全体像・feature の切れ目・サブシステム境界・依存関係の把握）を行ってよい。ただし planner / implementer / reviewer / tester の起動・ループ管理・ユーザー確認ゲートはスキル本体（メイン Claude）に集約する設計のため、あなたは起動しない。分割戦略の策定に集中せよ。**
<!-- /CORE -->

## 役割

大規模タスク（エピック）を受け取り、実装しやすいサブタスクへ分割し、依存グラフ（DAG）を生成する。オーケストレーション（ネスト pir2 の起動・ループ管理・ユーザー確認ゲート）はスキル本体が担当するため、あなたは分割戦略の策定に専念する。

## 入力

スキル本体から以下が渡される:

- `PROJECT_MEMORY_DIR`（メモリ追記用パス）
- `EPIC_RUN_DIR`（`${PROJECT_ROOT}/.ai-pir-runs/<run>/` の絶対パス。分割戦略レポート本体と探索レポートの書き出し先）
- タスク内容（`--codex` 除去後のユーザー依頼内容）

## プロセス

### 1. 入力の確認

`PROJECT_MEMORY_DIR` / `EPIC_RUN_DIR` / タスク内容が揃っているか確認する。不足があればスキル本体に確認する。

### 2. 全体探索

`Agent` ツールで explorer をネスト起動し「サブシステム境界・feature の切れ目・主要依存関係」を把握する。探索レポートは `{EPIC_RUN_DIR}/epic-exploration-*.md` に書く。広く浅くが原則であり、深掘りは各サブ pir2 に委ねる。

### 3. 分割の粒度指針

1 サブタスク＝1 つの pir2 で「fresh に回せる意味のある境界」（1 サブシステム／1 フィーチャー相当）とする。過度な細粒度化は並列運用コストが逆転するので避ける。

### 4. 依存グラフ生成

順序依存（先行の成果物が必要）を辺に張る。**共有リソース競合（同一ファイル・同一外部状態を触る複数サブタスク）は「暗黙の依存」として辺を張り直列化する**（並列集合は互いにファイル所有が非重複であることを保証する）。

### 5. 各 pir2 タスク記述

WHAT と境界（触ってよい／いけない範囲）のみを書く。実装手段は書かない。

### 6. 既存ルール照合

`CLAUDE.md` / feedback と今回の分割方針が整合しているか照合し、USER_DECISION_REQUIRED の発行条件（分割方針が複数成立する・スコープ縮小・外部依存ギャップ）は planner.md と同じ姿勢で判断する。

### 7. メモリへの記録

完了後、プロンプトで受け取った `PROJECT_MEMORY_DIR` 配下のメモリファイルに追記する:

- まず `mkdir -p {PROJECT_MEMORY_DIR}` でディレクトリを作成する
- パス: `{PROJECT_MEMORY_DIR}/pir_planner_log.md`（planner と同じログに `## [エピック名] — ...` で追記）

### 8. ファイル書き出し

完成した分割戦略レポート本体を以下のパスに `Write` で書き出す:

- パス: `{EPIC_RUN_DIR}/epic-plan.md`（再策定時も同名で上書き）
- 内容: 下記「エピック分割レポートフォーマット」のフル版
- 書き出し前に `mkdir -p {EPIC_RUN_DIR}` を実行する

## エピック分割レポートフォーマット

```markdown
## エピック分割レポート: [エピック名]

### 概要
[エピックの規模・全体像と分割方針を 1〜2 文で]

### 全体探索サマリー
[ネスト explorer が把握したサブシステム境界 / feature の切れ目 / 主要依存関係。探索レポートパス一覧]

### サブタスク一覧
- T1: [目的（WHAT）]
  - 担当範囲: [サブシステム / ディレクトリ]
  - 想定成果物: [WHAT レベル。ファイル×関数は書かない]
  - 依存: [none / T_x]
  - 共有リソース: [触る共有ファイル・外部状態。競合検知用。なければ「なし」]
- T2: ...

### 依存グラフ（DAG）
[テキスト図で並列集合と直列辺を明示]
- 並列実行可能グループ: {T1, T2, ...}
- 直列辺: [T_a → T_b ...]
- 暗黙依存（共有リソース競合による直列化）: [あれば列挙、なければ「なし」]

### 各 pir2 へ渡すタスク記述（WHAT と境界のみ）
- T1: "[サブ pir2 に丸ごと渡す WHAT ＋ 触ってよい/いけない境界。実装詳細・ファイル×関数は書かない]"
- T2: ...

### 適用される既存ルール
- 照合した参照元: [...]
- 適用ルール一覧: [...]（または「該当なし」）

### USER_DECISION_REQUIRED（分割方針に複数案 / スコープ縮小 / 外部依存ギャップがある場合のみ）
- 判断要請の理由 / 選択肢(A)(B)... / 推奨案

### 注意点・リスク
- [並列化の運用コスト / サブタスク境界の不整合リスク / 深さバジェット]

### EXPLORATION_NEEDED（ネスト探索でも解消しなかった場合のみ）
- [topic]: [調査観点]
```

## 呼び出し元への返り値フォーマット

ファイル書き出し後、呼び出し元には以下の **要約のみ** を返す:

```
## エピック分割要約: [エピック名]

### 書き出し先
{EPIC_RUN_DIR}/epic-plan.md

### 要点（5〜10行）
- サブタスク数: [N 件]
- 並列実行可能グループ数: [N 件]
- 直列辺の有無: [あり / なし]
- USER_DECISION_REQUIRED: [あり / なし]

### EXPLORATION_NEEDED
[あり / なし]
[ありの場合は topic だけ箇条書きで列挙（詳細は epic-plan.md 側に書く）]
```

## ガイドライン

- 推測で進まず、探索レポートから読めない情報は `EXPLORATION_NEEDED` に出す
- 既存の命名規約・ディレクトリ構成に合わせる
- 実装結果の報告（変更ファイル一覧、VERDICT 等）は書かない（各サブ pir2 がそれぞれ担当する）
- 成果物本体は `{EPIC_RUN_DIR}/epic-plan.md` に書き出し、呼び出し元には要約＋パス＋（必要なら）EXPLORATION_NEEDED の有無のみ返す。フル版レポートを呼び出し元のチャットに貼り付けない（telephone-game effect 回避）
`````

---

### 3. 実行可能性ギャップ表

以下、事実（コードベースから確認できる記述）と推測（未検証・観測不能）を明示的に分けて評価する。

#### 3-1. (a) epic 本体が手順を追うときに詰まる／曖昧な箇所

| # | 箇所 | ギャップの内容 | 分類 |
|---|---|---|---|
| A1 | ステップ 2.5 冒頭 | 「検出トリガー・確認フォーマットは pir2 の plan-choice-gate に**倣います**」と書きつつ、直後の本文で「サブタスク一覧＋依存グラフ＋各 pir2 タスク記述を**必ず**提示して承認を得てください。承認前に Phase 2 へ進んではなりません」と**無条件必須**にしている。plan-choice-gate.md 自体は「該当トリガーがどれも当てはまらない場合は本ステップをスキップ」という**条件付き**ゲートである。epic 側は「倣う」対象が確認フォーマットだけなのかトリガー条件も含むのか自己矛盾しており、epic 本体は「常に止める」のか「USER_DECISION_REQUIRED 等がある時だけ止める」のか判断に詰まる。字面上は前者（無条件）が優先されるように読めるが、明記されていない | 事実（原文の論理矛盾） |
| A2 | ステップ 2.5 | plan-choice-gate.md の「別案の字義解釈確認」「v2→v3 切替の真意確認」は pir2 の `PLAN_STRATEGY_CHANGED` フラグと v1/v2/v3 の versioning 前提を持つ。epic-planner の再起動には versioning 概念や `PLAN_STRATEGY_CHANGED` 相当のフラグが epic 側に定義されていない。「ユーザーが分割方針を変えた場合は epic-planner を再起動してください」としか書かれておらず、字義解釈確認をどのフォーマットで行うか epic 本体は自己流に組み立てる必要がある | 事実 |
| A3 | ステップ 3-0/3-3/3-4 | L1 起動プロンプトの内容が 3-0（基本指示）・3-3（深さバジェット指示）・3-4（ユーザーゲート委譲指示）の3箇所に分散しており、pir2 SKILL.md の explorer/planner 起動時のような「プロンプトに必ず含めるパラメータ」一覧化された単一チェックリストが存在しない。epic 本体が実際に `Agent` 起動プロンプトを組み立てる際、3-3 や 3-4 の文言を書き漏らすリスクが構造的に存在する | 事実 |
| A4 | ステップ 3-1 | 「宣言テンプレは pir2 ステップ 7-2A の型を流用します」と指示するが、fan-out-gate.md 実体は `REVIEWER_SET` / `REVIEWER_ROLE` という reviewer 専用語彙のテンプレートであり、epic のサブタスク並列起動（`T1, T2, ...` の集合）にそのまま当てはめると変数名が意味不明になる。epic 側で `SUBTASK_SET` 等への読み替えテンプレートが用意されておらず、epic 本体が即興で読み替える必要がある | 事実 |
| A5 | ステップ 4 | メタ retrospector 起動を retrospector-prompt.md の仕様に「従ってください」としているが、同ファイルはプロンプトに `INNER_LOOP_COUNT` / `OUTER_LOOP_COUNT` / `REPLAN_COUNT` / `PLAN_STRATEGY_CHANGED` を必須で含めることを要求する。これらは pir2 内部（1 run 内）のループカウンタであり、epic 本体（複数サブ run を束ねる上位オーケストレーター）には存在しない概念。epic 本体は各サブ pir2 の値を集約するのか、`N/A` で埋めるのか、指示がない | 事実 |
| A6 | ステップ 1 のみ | `EPIC_RUN_DIR` の feature slug は `run_feature="$(printf '%s' "$TASK" | tr -c 'a-zA-Z0-9' '-' | ... | cut -c1-40)"`。各サブ pir2（L1）も同じロジックで**自分の** RUN_DIR を計算するが、その `run_feature` は Ti（サブタスク記述）由来であり、`EPIC_RUN_DIR` とは独立した `.ai-pir-runs/` 直下フォルダになる（`EPIC_RUN_DIR` 配下に入れ子にはならない）。epic-runs.md でマッピング記録する設計だが、`.ai-pir-runs/` 直下がサブタスク数だけ平置きで増えていく設計になっている点は明記されていない | 事実 |

#### 3-2. (b) L1 起動プロンプトの過不足

| # | 項目 | epic の指示 | ギャップ |
|---|---|---|---|
| B1 | `$ARGUMENTS` バインディング | 「`~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` を Read し...サブタスク `<Ti タスク記述>` を最後まで実行してください」 | pir2 SKILL.md 本文は随所で `$ARGUMENTS`（`タスク: $ARGUMENTS`、Step1 の `run_feature=$(printf '%s' "$ARGUMENTS" ...)`）を参照する。これは Claude Code のスキル起動機構が自動で埋める変数であり、L1（`general-purpose`）が **Read ツールで生テキストとして読んだだけ**の場合、この変数はハーネスによって自動的に Ti に束縛されない。L1 が「本文中の `$ARGUMENTS` は自分が渡された Ti に読み替える」と自力で推論する前提になっており、epic のプロンプトにその読み替え指示が明記されていない。epic 自身も末尾で「代替として general-purpose が Skill ツールで直接 `/pir2` を起動できる場合はそれでもよいが、環境依存のため既定は Read ベース」と認めており、**正規のスキル起動ではなく L1 が SKILL.md を役割演技（ロールプレイ）する方式**であることを自認している |
| B2 | 参照ファイルの追跡 | 「その手順に従って...実行してください」のみ | pir2 SKILL.md は 15 個の `references/*.md`（exploration-loop.md, plan-choice-gate.md, destructive-change-check.md, feedback-conflict-gate.md, implementation-delegation.md, deterministic-completion-check.md, fan-out-gate.md, refactor-advisor-gate.md, continuation-gate.md, tester-prompt.md, walkthrough-templates.md, retrospector-prompt.md, handoff-cleanup.md, run-dir-base.md, sanitized-cwd.md）へ「詳細プロトコル: 参照」の形でポインタを飛ばす設計。epic の起動指示はこれらを **追って Read すること自体を明示していない**。L1 が「その手順に従って」を「ポインタも辿って Read する」と解釈するかは L1 自身の忠実性に懸かっており、epic 側に強制力がない |
| B3 | `PROJECT_MEMORY_DIR` の明示受け渡し | Step 2（epic-planner 起動）では明示されるが、Step 3（L1 起動）のプロンプト必須項目には **含まれていない** | L1 は pir2 Step1 を自分で実行し `PROJECT_MEMORY_DIR` を独自に `$(pwd)` から再計算する設計に**依存**する（epic 側が計算した値と、L1 が独自計算した値は cwd が同一なら理論上一致するはずだが、明示的な受け渡しがないため「一致する」という前提が検証も強制もされていない） |
| B4 | CLAUDE.md の継承 | 明記なし | `general-purpose` サブエージェントがプロジェクトの `CLAUDE.md`（ツール結果捏造禁止・エージェント呼び出しプロトコル等の全体ルール）を自動継承するかどうかは、本リポジトリのどのファイルにも明記されていない。**推測（未検証）**: 継承される場合は L1 が pir2 の忠実実行に必要な規範意識を保持できるが、継承されない場合、L1 は CLAUDE.md 由来の「ツール結果の捏造の絶対禁止」等の外部強化なしに、pir2 SKILL.md の文面のみを頼りに 6-1/6-3 のような手間のかかる bash 手順を律儀に実行するかどうかは不確実性が増す |
| B5 | 返り値のサイズ制御 | 明記なし | explorer/planner/implementer/reviewer は「要約のみ返し、フル版は `{RUN_DIR}/*.md` に書く」という telephone-game 対策が CORE ルールとして各エージェント定義に明記されている。しかし L1（ネスト pir2 全体）の最終返り値については、epic 側にも pir2 側にも「epic 本体へは要約だけ返せ」という指示がない。pir2 のステップ12最終サマリー（VERDICT・6-3結果・リファクタ提案・テスト結果・ウォークスルー等、多セクション）をそのまま L1 の Agent 応答として返すと、並列 fan-out 時に epic 本体の context が急速に肥大するリスクがある |
| B6 | 深さ超過時の検出方法 | 3-3「L2 での `Agent` 起動が**深さ超過で拒否された場合**は...縮退運用」 | 「拒否された場合」の具体的な検出手段（エラーメッセージの形式、ツール呼び出し失敗のシグナル等）がどこにも定義されていない。`agent-delegation.md` によれば実際の深さ上限は 5・推奨 2-3 であり、epic の L0→L1→L2→（L3 explorer）は最大でも 3 段（L0 を含めれば 4 段）で上限 5 に達していない。にもかかわらず epic は自主的に L2 で頭打ちにする保守的設計を採っており、「拒否」が実際に発生する具体的シナリオが薄い（推奨レンジ 2-3 の範囲内でむしろ収まっている）。「拒否時のフォールバック」という記述が実際に到達しうるか自体が疑わしい |

#### 3-3. (c) epic が依存する未実装機構への到達時の挙動

| # | 項目 | 現状 | 到達時の挙動 |
|---|---|---|---|
| C1 | ユーザー言及の「W2 境界契約テレメトリ」「L0 検証パイプライン」 | 本リポジトリ内でこれらの語を字義通り検索したが、該当する実装・定義ファイルは見つからなかった。唯一の関連記述は `experimental.md` の `pir2-deterministic-completion-check` 実験の Rollback Criteria にある一文のみ:「L0 が観測項目 (b) で体系的に 6-3 の bash を実行しない（幻覚実行）ことが複数回確認された場合、**W2/W5 の hook-floor（機械的強制）を前倒しで検討する**」 | この一文は**将来検討する可能性がある**という記述であり、`W2`/`W5` という名前のフックやテレメトリ機構は本リポジトリのどこにも実装されていない（`grep` で hook 名・スクリプト名としても未発見）。したがって epic 経由のネスト pir2 run が「L0（=L1 ランナー自身）が 6-3 を実行しない」状態に陥っても、**それを検出・強制する機構は現状ゼロ**。epic 本体は L1 の返り値の文面を信じるしかなく、L1 が 6-3 を省略しても気づく手段がない（B5 の返り値サイズ問題とも連動：L1 が最終サマリーの「決定論的完了検証（6-3）」セクションを省略・簡略化して返してきても epic 側に検知ロジックがない） |
| C2 | epic 自身の実験ステータス | `experimental.md` の `epic-orchestrator-nested-pir2` 実験は `Status: Active`、`Evidence Summary` は **全項目 0**（Epic executions: 0, Parallel fan-outs: 0, Depth fallbacks: 0, Integration-boundary regressions: 0, Deferred-decision escalations: 0） | 本ワークフローは **一度も実行された記録がない**（少なくとも本レジストリ上は）。「動くかどうか」自体が未検証の試験実装である |
| C3 | `pir2-deterministic-completion-check` 実験も同様 | `Evidence Summary` 全項目 0（Initial implementation-point executions: 0 等） | epic 経由でネスト pir2 が 6-3 を実行したとしても、その実行が「6-3 単体としても未検証（実行 0 回）」という状態と重なる。epic は「未検証機構の上に未検証機構を積む」構成になっている |

#### 3-4. (d) 6-3（W1・コミット済み）は epic 経由のネスト pir2 run 内で発火するか

**結論（条件付き・推測を含む）**: 文面上は「発火しうる」が、**epic 本体からその発火を確認する手段が存在しない**、かつ「発火するかどうか」自体が L1 の忠実性という不確定要素に依存する。

- pir2 SKILL.md ステップ 6-1 には「implementer 起動前の pre-set 記録（決定論的完了検証 6-3 用・必須）」という bash 手順が明記され、ステップ 6-3 には「決定論的完了検証（`IMPLEMENTATION_ACTOR` が `main` 以外のとき必須）」が明記されている。epic は L1 に対し「`~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` を Read し、その手順に従って...実行してください」とだけ指示しており、L1 が SKILL.md の文面を忠実に実行する限り、6-1/6-3 のステップ番号もそのまま実行対象に含まれる（epic 側が 6-1/6-3 を除外する指示は一切ない）。
- ただし、以下の理由で「本当に実行されたか」の外形的な確認は epic 本体からは事実上不可能:
  1. 6-1/6-3 の bash 実行（`git diff --name-only` 等）は L1 の**サブエージェント内部の tool call**であり、epic 本体のトランスクリプトには現れない。epic 本体が見るのは L1 の最終テキスト応答のみ。
  2. B2 のとおり、6-3 の詳細手順は `deterministic-completion-check.md`（参照ポインタ経由）にあり、L1 がこのファイルを実際に Read したかどうかは epic 側から検証できない。
  3. `experimental.md`（`pir2-deterministic-completion-check`）自体が「(b) L0（スキル本体）が 6-3 の bash を実際に実行したか」を **load-bearing な観測項目**として明記しているという事実は、逆に言えば「通常の /pir2 run（メイン Claude が直接実行）でさえ 6-3 を実行し忘れるリスクが公式に認識されている」ことを意味する。ネスト pir2（L1 = 一時的に生成された `general-purpose` サブエージェント。CLAUDE.md 継承有無不明・B4）でこの遵守率がメイン Claude 実行時と同等以上である保証はどこにもない。
  4. C1 のとおり、6-3 未実行を検知する「hook-floor」的な機械強制は **存在しない**（構想段階）。したがって「発火しなかった」場合でも epic はそれに気づかない。

以上より、(d) への回答は「**SKILL.md の文面上は発火対象に含まれる（除外指示なし）が、実際に発火したかどうかを epic 本体側から機械的に確認する手段は現状皆無であり、発火の実効性は L1 の忠実な文面追従に完全依存する**」となる。これは事実（コードベースの記述）に基づく分析であり、「実際に発火するか」の実行結果そのものは未検証（run 実績 0 件）。

---

### 4. 上記ギャップ表に付随して新規発見した構造的懸念（未依頼だが重大度が高いため付記）

調査対象外の観点だが、SKILL.md の逐語読解中に見つかった、既存ギャップ項目に分類しきれない実行破綻リスクを 2 点報告する。いずれも epic-planner の「暗黙依存（共有リソース競合）」対策ではカバーされない、**git 作業ツリーそのものの共有**に起因する問題。

#### 4-1. `HANDOFF_PATH` の単一グローバルパス衝突（重大）

pir2 SKILL.md ステップ 1:

```bash
HANDOFF_PATH="${PROJECT_ROOT}/.ai-pir-runs/handoff.md"
```

この `HANDOFF_PATH` は `RUN_DIR`（タイムスタンプ＋feature slug でサブタスクごとに一意）と異なり、**`PROJECT_ROOT` 直下の固定 1 ファイル**である。epic が起動する各ネスト pir2（L1）は、それぞれ独立に pir2 SKILL.md ステップ1を実行し、**全サブタスクが同一の `${PROJECT_ROOT}/.ai-pir-runs/handoff.md` を読み書きする**設計になる。

- ステップ 5.5（`RESUME_MODE=new` 時）: 各サブタスクの L1 が「自分の plan.md から抽出した実装ステップ」で `$HANDOFF_PATH` に **Write** する。
- ステップ 11.5: retrospector 完了後、全 `[x]` なら削除、未完了項目があれば「最終更新」を更新。

epic ステップ 3-1 は「独立集合は**同一メッセージ内で複数 `Agent` 起動して並列実行**」と明記しており、これは真の同時実行を意味する。2 つ以上の独立サブタスクが並列実行される場合、両方の L1 が**同一の `handoff.md` パスに対して**ほぼ同時に Write/Read/削除を行うことになり、以下が起こりうる:

- サブタスク A の handoff.md 初期化 Write を、サブタスク B の Write が上書きする（またはその逆）。
- サブタスク A がステップ 11.5 で「全項目 [x] → 削除」を実行した瞬間、まだ進行中のサブタスク B の handoff.md（実際は A のものと衝突して B の内容になっていたかもしれない）が消える。
- サブタスク開始時の `RESUME_MODE` 判定（「`$HANDOFF_PATH` のファイルが存在する → `passive-notice`」）が、他サブタスクの残骸ファイルを誤って自分の前回セッションとして認識する。

epic SKILL.md にはこの衝突を回避する記述（例: L1 起動時に `HANDOFF_PATH` をサブタスク専用パスへ上書き指定する等）が一切ない。epic-planner の「暗黙依存（共有リソース競合）」は「同一ファイル・同一外部状態を触る**複数サブタスク**」を検知する設計だが、これは**サブタスクが意図して触るファイル**（ソースコード等）を対象にした概念であり、pir2 の内部運用ファイルである `handoff.md` の衝突までは検知対象に含まれていない（epic-planner.md にも「pir2 の内部状態ファイル同士の衝突」を考慮する指示は存在しない）。

#### 4-2. 並列サブタスクによる共有 git 作業ツリーの汚染（重大）

pir2 の 6-3（決定論的完了検証）・reviewer・tester はいずれも `git diff --name-only` 等、**リポジトリ全体スコープ**の git コマンドで「何が変更されたか」を判定する（`deterministic-completion-check.md` の pre-set/post-set 記録参照）。epic-planner の「共有リソース競合の暗黙依存」判定はサブタスクが**明示的に触るファイルの重複**のみを見て並列可否を決めるが、たとえ 2 つのサブタスクがファイルレベルで完全に非重複でも、**両者は同一の git 作業ツリーを共有**している。

epic ステップ 3-1 により独立サブタスクが真に並行実行される場合:

- サブタスク A の L1 が 6-1 で pre-set スナップショット（`git diff --name-only` 等）を取った直後に、サブタスク B の implementer が別ファイルを編集すると、A の post-set スナップショットには **B の変更も混入**する（`git diff` はプロセス単位・サブエージェント単位でスコープされず、リポジトリ全体を見るため）。
- 結果、A の 6-3 判定は B の変更分を `UNDECLARED_CHANGE`（非ブロッキング warn）として検出する可能性があり、ノイズとして無視できたとしても、reviewer・tester が「今回の実装で何が変わったか」を `git diff` で確認する際にも同じ混入が起きる（reviewer.md も `Agent` ツールで explorer をネスト起動する際などに `git diff` 相当の確認を行う設計）。
- `git worktree` によるサブタスクごとの作業ツリー分離のような対策は epic SKILL.md にも epic-planner.md にも一切言及がない。

この問題は「ファイル所有が非重複であれば安全」という epic-planner の暗黙依存判定の前提（プロセス丸ごとが分離されているかのような暗黙の想定）と、実際には「全サブタスクが単一の物理 git リポジトリを同時に触る」という実行環境の実体が乖離している点に起因する。ファイルレベルで衝突がなくても、git ベースの検証機構（6-3・reviewer・tester の diff 確認）は**時間的に重なった他サブタスクの変更を巻き込む**ため、真の並列 fan-out（3-1）は原理的にリスクを抱える。

---

### 5. 依存関係

- `epic/SKILL.md` → `~/.claude/agents/epic-planner.md`（Step 2 で起動）
- `epic/SKILL.md` → `~/.claude/skills/pir2/SKILL.md`（Step 3 で L1 に Read させる。`--codex` 時は `pir2codex/SKILL.md`）
- `epic/SKILL.md` → `~/.claude/skills/pir2/references/plan-choice-gate.md`（Step 2.5 で流用）
- `epic/SKILL.md` → `~/.claude/skills/pir2/references/fan-out-gate.md`（Step 3-1 で型を流用）
- `epic/SKILL.md` → `~/.claude/skills/pir2/references/retrospector-prompt.md`（Step 4 で流用）
- `epic/SKILL.md` → `~/.claude/skills/pir2/references/experimental.md`（`epic-orchestrator-nested-pir2` 実験の観測先）
- `epic-planner.md` → explorer（自前ネスト起動、Step 2「全体探索」）
- `pir2/SKILL.md` ステップ 6-1/6-3 → `~/.claude/skills/pir2/references/deterministic-completion-check.md`（詳細プロトコル）

---

### 6. 補足情報

- 本タスクは調査専任であり、実装・Edit・Write（ファイル書き出し先の `exploration-01.md` を除く）・git 操作は一切行っていない。
- 「W2 境界契約テレメトリ」「L0 検証パイプライン」という語はユーザー提供の調査観点に含まれていたが、リポジトリ内を検索した結果、これらの名称そのものは定義されていない（3-3 節 C1 参照）。唯一関連する記述は `experimental.md` 内の「W2/W5 の hook-floor」という将来検討事項の一文のみであり、これは実装済み機構ではなく **rollback 条件を満たした場合に検討するという構想レベルの記述**である。この点は推測ではなく `grep` による確認事実。
- 検索した keyword: `W2`, `W5`, `hook-floor`, `境界契約`, `テレメトリ`, `L0検証`, `L0 検証`, `深さバジェット`, `depth budget`, `subagent_type`, `general-purpose`, `CLAUDE.md を読`, `システムプロンプト`, `継承`, `自動的に読み込`。
- 「CLAUDE.md がサブエージェント（特に `general-purpose` 型）に自動継承されるか」は本リポジトリのどのファイルにも明記がなく、Claude Code のランタイム仕様に依存するため、本レポート内ではその可能性を推測として明示し、断定は避けた（3-2 節 B4）。この点はコードベース調査だけでは解決できず、公式ドキュメント裏取り（Claude Code の Agent/Task ツールのサブエージェント context 仕様）が必要な論点である。

---

### 7. 呼び出し元への依頼

- **W2/W5 hook-floor の実体確認**: 3-3 節 C1 で述べた通り、「6-3 未実行を検知する機械強制」は構想段階（未実装）である。これを deepthink の論点として扱う場合、実装するかどうかの判断は本探索のスコープ外（設計判断であり tech-validator 等の対象でもない、純粋にユーザー/epic-planner 設計判断）。
- **`general-purpose` サブエージェントの CLAUDE.md 継承有無**: Claude Code の公式仕様に関わる論点であり、本探索ではリポジトリ内に根拠を見つけられなかった。断定が必要な場合は Claude Code 公式ドキュメント（Anthropic Claude Code docs の Subagents / Task tool context inheritance 節）の WebFetch 裏取りを別途行うことを推奨する（本レポートでは実施していない。ユーザーの依頼は「コードベースの逐語収録＋批判的評価」であり外部裏取りの明示要求がなかったため、必要なら追加 explorer 起動を検討されたい）。
- **4-1（handoff.md 衝突）・4-2（共有 git 作業ツリー汚染）は本タスクの調査観点に明示されていなかったが、epic の並列 fan-out（Step 3-1）の実行可能性を左右する重大な発見のため、依頼範囲を超えて追記した**。deepthink の論点として重み付けするかはユーザー判断に委ねる。
