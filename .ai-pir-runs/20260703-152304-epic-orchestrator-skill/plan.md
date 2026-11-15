## プランレポート: 上位オーケストレータースキル `/epic` と専任エージェント `epic-planner` の新規作成

### 概要

大規模タスク（エピック）を `epic-planner` に分割させ、依存グラフ（DAG）に沿って各サブタスクを `/pir2`（`--codex` 時は `/pir2codex`）としてネスト起動する上位オーケストレーションワークフローを新設する。成果物は 4 ファイル（新規スキル本体 1・新規エージェント定義 1・CLAUDE.md 追記・experimental.md 起票）。位置づけは試験実装で、既存 pir2 系の命名・構造・書式慣習に厳密に従う。

> ⚠️ このタスクはコード実装ではなく**指示ドキュメント（SKILL.md / agent.md / CLAUDE.md / experimental.md）の著述**である。テストスイートは存在しない。検証は静的（frontmatter/構造の妥当性・sync 再生成の成否・ファイル存在）に限る。

---

### 実装ステップ

実装対象は密結合の 4 ファイル。**単一 implementer で実装する**（分割しない。詳細は「実装規模の見積もり」参照）。ステップ順は 1→2→3→4（1 と 2 が相互参照の契約を張るので、この順で書き、書き終えたら相互参照の整合を最後に見直す）。

#### ステップ 1: `.claude/skills/epic/SKILL.md`（新規作成）

**配置**: `/Users/kawasetakumi/dotfiles/.claude/skills/epic/SKILL.md`（Claude Code 専用。`.agents/skills/` portable には**置かない**）。link.sh は `.claude/skills/` ディレクトリ全体をリンクするため配置のみで自動リンクされる（改修不要）。

**frontmatter**（pir2/pir2codex/research の型に厳密準拠。「ユーザーが /epic と入力したら必ずこのスキルを使う」を必ず含める）:

```yaml
---
name: epic
description: 大規模タスク（エピック）を複数サブタスクに分割し、依存グラフに沿って各サブタスクを /pir2 としてネスト起動する上位オーケストレーションワークフロー。人管理を抜いた PM／テックリード相当。1 つの機能追加では収まらない・複数サブシステムを横断する・独立フィーチャーが並行する大型タスクに使う。「まとめて全部作って」「複数機能を一気に」「大きめの改修を段階的に」といった要望に対応する。ユーザーが /epic と入力したら必ずこのスキルを使う。先頭に --codex を付けると下位起動を /pir2codex に一律差し替える。
argument-hint: [大規模タスクの説明]（先頭に任意で --codex）
---
```

**本文冒頭（`# Epic — 大規模タスクの多段オーケストレーション` の直後）に必ず明記する前提**（これは会話で確定した「技術的整合性の明示」要求への対応。下記「Agent ネスト起動方式」セクションの結論を要約して書く）:

- epic 本体（= メイン Claude）がオーケストレーター。`Agent` ツールで epic-planner とネスト pir2 を起動する。
- **3 階層ネスト構造**: epic 本体(L0) → ネスト pir2 ランナー(L1) → 各 pir2 が起動する explorer/planner/implementer/reviewer/tester(L2)。Claude Code v2.1.172〜 のネスト起動に依存する。
- **深さバジェット制約**: L2 のエージェント（planner/reviewer 等）がさらに explorer をネスト起動すると L3 になる。既存 pir2 系は L0→L1→L2 の 3 階層で運用実績がある（`experimental.md` の nested-explorer 実験）が L3 以深は未確認。よってネスト pir2 は **L2 で頭打ちにする運用**（後述ステップ 3-3）とし、L3 が必要になったら inline フォールバックする。
- **ユーザー対話は epic 本体に集約**: サブエージェント（ネスト pir2 ランナー含む）はユーザーと対話できない。分割確認ゲート（Phase 1.5）およびサブ pir2 内部で発生するユーザー確認ゲートはすべて epic 本体が担う（後述ステップ 2.5 / 3-4）。Auto mode でも例外なし。

**ステップ構成**（見出しは pir2 の採番慣習＝`## ステップ N:` に従う。フェーズ名は括弧で併記）:

- **`## ステップ 1: EPIC_RUN_DIR の確定と --codex パース`**
  - RUN_DIR パターンは pir2 ステップ 1 を踏襲。SSOT は流用する（`~/.claude/skills/pir2/references/sanitized-cwd.md`＝PROJECT_MEMORY_DIR 用、`run-dir-base.md`＝基底パス）。epic 専用に `EPIC_RUN_DIR` を作る（feature slug に `epic-` を織り込む）。以下の bash ブロックを本文に載せる:
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
    run_feature="$(printf '%s' "$TASK" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-32)"
    [ -z "$run_feature" ] && run_feature="epic"
    EPIC_RUN_DIR="${PROJECT_ROOT}/.ai-pir-runs/${run_ts}-epic-${run_feature}"
    mkdir -p "$EPIC_RUN_DIR"
    if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      grep -qxF '/.ai-pir-runs/' "${PROJECT_ROOT}/.gitignore" 2>/dev/null || echo '/.ai-pir-runs/' >> "${PROJECT_ROOT}/.gitignore"
    fi
    echo "SUBTASK_SKILL=$SUBTASK_SKILL"
    echo "EPIC_RUN_DIR=$EPIC_RUN_DIR"
    ```
  - `--codex` は「下位スキル名を pir2→pir2codex に差し替えるだけ」であり epic 本体のロジック・分割判定は一切変えない旨を明記（サブタスクごとの混在はしない＝全サブタスク一律 `SUBTASK_SKILL`）。

- **`## ステップ 2: Phase 1 — エピック分割（epic-planner）`**
  - `epic-planner` を `Agent` ツールで起動（model: opus）。プロンプトに含める必須項目:
    - `PROJECT_MEMORY_DIR=[パス]` / `EPIC_RUN_DIR=[パス]`
    - タスク内容（`--codex` 除去後の `TASK`）
    - 「全体探索は自分で explorer をネスト起動して実施し、探索レポートは `{EPIC_RUN_DIR}/epic-exploration-*.md` に書き出すこと」
    - 「分割戦略レポート本体は `{EPIC_RUN_DIR}/epic-plan.md` に書き出し、チャットには要約＋USER_DECISION_REQUIRED / EXPLORATION_NEEDED の有無のみ返すこと」
    - 「実装詳細（ファイル×関数×変更内容・実装ステップ）は出さないこと。それは各サブ pir2 の planner の責務」
  - epic-planner から分割要約を受け取る。
  - EXPLORATION_NEEDED が残る場合の扱い: epic-planner は自前のネスト explorer で自己解決するのが原則。それでも topic が残ったら Phase 1.5 のゲートでユーザーに提示する（epic 本体は追加で epic-planner を再起動してもよいが、ハードキャップは pir2 ステップ 4.5 に倣い最大 5 回）。

- **`## ステップ 2.5: Phase 1.5 — 分割結果のユーザー確認（epic 本体・Auto mode でも例外なし）`**
  - 検出トリガー・確認フォーマットは pir2 の plan-choice-gate に倣う（`~/.claude/skills/pir2/references/plan-choice-gate.md` を参照と明記）。
  - epic 本体が `{EPIC_RUN_DIR}/epic-plan.md` を Read し、**サブタスク一覧＋依存グラフ＋各 pir2 タスク記述** をユーザーに提示して承認を得る。承認前に Phase 2 へ進んではならない。
  - epic-planner が USER_DECISION_REQUIRED / EXPLORATION_NEEDED を出していれば必ずここで提示する。ユーザーが分割方針を変えた場合は epic-planner を再起動する。
  - **このゲートは必ず epic 本体で行う**（サブエージェントはユーザー対話不可）。理由を 1 文添える。

- **`## ステップ 3: Phase 2 — サブタスクのネスト pir2 実行`**
  - **3-0: ネスト pir2 の起動方式**（下記「Agent ネスト起動方式の技術整合性」の結論を本文に記載）。各サブタスクを `Agent` ツールで `subagent_type=general-purpose` として起動し、プロンプトで「あなたはこのサブタスクの PIR² オーケストレーターです。`~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` を Read し、その手順に従ってサブタスク `<Ti タスク記述>` を最後まで実行してください」と指示する。
  - **3-1: 独立サブタスクの並列 fan-out**。DAG で辺のない独立集合は同一メッセージ内で複数 `Agent` 起動して並列実行する。pir2 の Fan-Out Gate 慣習に倣い、並列発火直前に自己コミットメント宣言（起動体数＝独立集合サイズ、同一 function_calls ブロックに並べる）を書く。宣言テンプレは pir2 ステップ 7-2A の型を流用（`~/.claude/skills/pir2/references/fan-out-gate.md` を参照と明記）。
  - **3-2: 依存サブタスクの直列実行と先行成果の注入**。依存辺のあるサブタスクは依存順に 1 体ずつ直列起動する。後続の起動プロンプトに、先行サブタスクの返り値から得た `作業ディレクトリ(サブ RUN_DIR)` パス・変更ファイル一覧・`git diff` 確認指示を注入する（ネスト pir2 は自前でコミットしないため、先行の変更は working tree に残っており後続 pir2 の explore フェーズが拾える。加えて明示注入で取りこぼしを防ぐ）。
  - **3-3: 深さバジェット管理**。ネスト pir2 ランナーには「あなたの配下の planner/reviewer/implementer は explorer をさらにネスト起動（L3）せず、pir2 ステップ 3 の explorer フェーズ（L2）で得た探索に依拠すること。L2 での `Agent` 起動が深さ超過で拒否された場合は、その pir2 は `IMPLEMENTATION_ACTOR=main`／直接探索の inline モードにフォールバックして完遂すること」と明示する。
  - **3-4: ユーザーゲートの epic 本体への委譲（bubble-up）**。ネスト pir2 ランナーには「pir2 内部のユーザー確認ゲート（plan-choice-gate / 6.5 未解決事項 / continuation-gate 等）に到達したら、ユーザーには聞けないので**保守的デフォルト**を選び、その決定点を `{サブ RUN_DIR}/deferred-decisions.md` に記録し、返り値要約の `DEFERRED_USER_DECISIONS` に列挙すること」と指示する。epic 本体はサブ pir2 完了ごとに `DEFERRED_USER_DECISIONS` を集約し、判断が本質的にブロッキングなものはユーザーに提示する（軽微なものは Phase 3 サマリーで一括報告）。
  - **3-5: サブ run のマッピング記録**。各サブタスクの `Ti → サブ RUN_DIR` 対応を `{EPIC_RUN_DIR}/epic-runs.md` に追記して観測可能性を担保する。
  - 共有ステート競合の特別扱いは epic 本体に持たせない（epic-planner が「暗黙依存」として DAG の辺に張り、3-2 の直列化に吸収される）旨を 1 文で明記。

- **`## ステップ 4: Phase 3 — 統合確認とメタ振り返り`**
  - 全サブ pir2 完了後、epic 本体が `git diff` で結合点（サブタスク境界をまたぐインターフェース・命名・未接続実装）の整合を確認する。問題があれば統合修正用のサブタスクを 1 本追加起動する（新たな依存辺として扱う）。
  - メタ retrospect: `retrospector` を `Agent` ツールで起動し、`ワークフロー種別: epic` と `experimental.md` の epic 実験セクション観測を依頼する（起動仕様は `~/.claude/skills/pir2/references/retrospector-prompt.md` を参照と明記）。

- **`## ステップ 5: 最終サマリーの提示`**
  - サブタスク一覧・各サブ RUN_DIR・各サブ pir2 の VERDICT・集約した `DEFERRED_USER_DECISIONS`・統合確認結果・メタ改善推奨・`EPIC_RUN_DIR` を pir2 ステップ 12 の型で提示する。

**「Agent ネスト起動方式の技術整合性」小節を本文に含める**（会話の必須要求）。結論を明記:
- pir2 は「スキル」でありエージェント型 `pir2` は存在しない。したがってネスト起動は `subagent_type=general-purpose`（Tools: *、Read と Agent を持つ）に対し、プロンプトで `~/.claude/skills/${SUBTASK_SKILL}/SKILL.md` を Read させてオーケストレーターとして実行させる方式を**第一の起動方式**とする（Read + Agent のみに依存し確実）。
- 代替として general-purpose が Skill ツールで直接 `/pir2` を起動できる場合はそれでもよいが、サブエージェント内での Skill 起動の挙動は環境依存のため既定は Read ベースとする。
- L0→L1→L2 の 3 階層は既存 nested-explorer 実験（planner→explorer）で運用実績があり支持される。epic はこの 3 階層に収める（3-3 の L2 頭打ち運用）。

#### ステップ 2: `.claude/agents/epic-planner.md`（新規作成）

**配置**: `/Users/kawasetakumi/dotfiles/.claude/agents/epic-planner.md`。link.sh が `.claude/agents/` 全体をリンク（改修不要）。PostToolUse hook で sync-opencode/sync-codex が自動発火する。

**frontmatter**（planner.md の型に準拠。exploration-02 の最終案を採用）:

```yaml
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
```

**CORE セクション**（`<!-- CORE: このセクションは変更禁止 -->` 〜 `<!-- /CORE -->`。planner.md の CORE の型に準拠。exploration-02 の案をベースに、出力フォーマット名を「エピック分割レポートフォーマット」に、責務境界を「分割レベルのみ・実装詳細は各 pir2 の planner に委譲」に確定）:

```markdown
<!-- CORE: このセクションは変更禁止 -->
あなたは大型タスク分割エキスパートです。スキル本体（メイン Claude）から受け取った大規模タスク（エピック）を、実装しやすいサブタスクへ分割し、依存グラフ（DAG）として構造化してください。
**すべての出力は日本語で行うこと。**
**最終出力は必ず「エピック分割レポートフォーマット」に従うこと。**
**分割は「分割レベル」に徹すること。各サブタスクの目的・担当範囲（サブシステム／ディレクトリ）・想定成果物・他タスクへの依存・共有リソースまでを出し、具体的なファイル×関数×変更内容・実装ステップ列・コードレベル設計は出さないこと（それは各サブタスクの pir2 が自前の planner で行う）。実装詳細を抱えるとコンテキストが肥大し「context 大きすぎで漏れる」があなたに再現するため。**
**`Agent` ツールで explorer をネスト起動して全体探索（広く浅く＝全体像・feature の切れ目・サブシステム境界・依存関係の把握）を行ってよい。ただし planner / implementer / reviewer / tester の起動・ループ管理・ユーザー確認ゲートはスキル本体（メイン Claude）に集約する設計のため、あなたは起動しない。分割戦略の策定に集中せよ。**
<!-- /CORE -->
```

**本文に含めるプロセス**（planner.md の構成に倣い、以下を節立てで書く）:
- 入力の確認（`PROJECT_MEMORY_DIR` / `EPIC_RUN_DIR` / タスク内容）
- 全体探索: explorer をネスト起動して「サブシステム境界・feature の切れ目・主要依存関係」を把握。探索レポートは `{EPIC_RUN_DIR}/epic-exploration-*.md` に書く。広く浅くが原則（深掘りは各サブ pir2 に委ねる）。
- 分割の粒度指針: 1 サブタスク＝1 つの pir2 で「fresh に回せる意味のある境界」（1 サブシステム／1 フィーチャー相当）。過度な細粒度化は並列運用コストが逆転するので避ける。
- 依存グラフ生成: 順序依存（先行の成果物が必要）を辺に張る。**共有リソース競合（同一ファイル・同一外部状態を触る複数サブタスク）は「暗黙の依存」として辺を張り直列化する**（並列集合は互いにファイル所有が非重複であることを保証）。
- 各 pir2 タスク記述: WHAT と境界（触ってよい／いけない範囲）のみ。実装手段は書かない。
- 既存ルール照合（`CLAUDE.md` / feedback）と USER_DECISION_REQUIRED の発行条件（分割方針が複数成立する・スコープ縮小・外部依存ギャップ）は planner.md と同じ姿勢。
- メモリ記録: `{PROJECT_MEMORY_DIR}/pir_planner_log.md`（planner と同じログに `## [epic 名] — ...` で追記）。
- ファイル書き出し: `{EPIC_RUN_DIR}/epic-plan.md`。

**「エピック分割レポートフォーマット」**（planner の「プランレポートフォーマット」とは別物。実装ステップ／SHARDS／UNITS は**出さない**。以下の構造で本文に定義する）:

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

#### ステップ 3: `CLAUDE.md` 追記（3 箇所）

すべて Edit で**テキストアンカー**を使って挿入する（行番号は drift するため行番号指定しない）。

1. **エージェント定義一覧表への行追加**。アンカー行:
   ```
   | `gate.md` | position を成功基準（rubric）に客観照合し VERDICT: PASS/FAIL を返す十分性ゲート（/deepthink、Opus） |
   ```
   の**直後**に次を追加:
   ```
   | `epic-planner.md` | 大規模タスク（エピック）の分割と依存グラフ生成（/epic のエピック分割フェーズ、Opus） |
   ```

2. **スキル一覧表への行追加**。アンカー行:
   ```
   | `/deepthink` | 探索 → 熟考（複数並列）→ 統合 → ゲートを rubric 充足まで反復する多エージェント熟考ワークフロー |
   ```
   の**直後**に次を追加:
   ```
   | `/epic` | 大規模タスクを分割し依存グラフ順に /pir2 をネスト起動する上位オーケストレーション（試験実装。--codex で下位を /pir2codex に差し替え） |
   ```

3. **pir2 系説明セクションの追加**（新規 `###` サブセクション）。既存の `### PIR² ワークフロー (`/pir2`)` セクションは**変更せず**、その末尾（アンカー行 `3. **retrospector** — パターンをグローバルレジストリ ...` の段落の直後、`### エージェント定義 (`.claude/agents/`)` の**直前**）に新規サブセクションを挿入:
   ```markdown
   ### エピックオーケストレーション (`/epic`・試験実装)

   1 タスクに収まらない大規模タスク（エピック）を扱う上位オーケストレーター。epic 本体（メイン Claude）が `epic-planner` にエピックを分割・依存グラフ化させ、DAG に沿って各サブタスクを `/pir2`（`--codex` 時は `/pir2codex`）として `Agent` ツールでネスト起動する。

   - **3 階層ネスト**: epic 本体 → ネスト pir2 ランナー → 各 pir2 配下の explorer/implementer/reviewer（Claude Code v2.1.172〜 のネスト起動に依存。深さバジェット制約のため pir2 配下の再探索ネストは抑制し、超過時は inline フォールバック）
   - **ユーザー対話は epic 本体に集約**: 分割確認ゲートおよびサブ pir2 内部のユーザー確認ゲートはすべて epic 本体が担う（サブエージェントはユーザー対話不可）。サブ pir2 は保守的デフォルト＋`DEFERRED_USER_DECISIONS` で epic 本体に上げる
   - **共有ステート競合**: epic-planner が「暗黙依存」として依存グラフの辺に張り直列化する（epic 本体に特別な競合ロジックは持たせない）
   - 位置づけは試験実装。採用可否は `.claude/skills/pir2/references/experimental.md` の該当実験を SSOT に観測する
   ```
   （プロジェクト固有名は含めない。汎用表現のみ。）

#### ステップ 4: `.claude/skills/pir2/references/experimental.md` 追記（起票）

ファイル末尾（現在の最終セクション nested-explorer 実験の Observation Log の後）に、新規 `## Experiment:` セクションを追加する。exploration-02 の起票テンプレート構造（Status/Started/Scope/Owner/Recommendation ＋ Hypothesis/Implementation/Quality Guardrails/Metrics/Adoption Criteria/Rejection Criteria/Evidence Summary/Observation Log）に準拠。以下の内容で書く:

```markdown
## Experiment: epic-orchestrator-nested-pir2

- Status: Active
- Started: 2026-07-03
- Scope: `.claude/skills/epic/**`, `.claude/agents/epic-planner.md`, `CLAUDE.md`
- Owner: user
- Recommendation: Continue observing

### Hypothesis
1 タスクに収まらない大規模タスクを、epic 本体が epic-planner に分割・依存グラフ化させ、各サブタスクを /pir2 としてネスト起動する上位オーケストレーターを導入すると、(1) planner 1 体が巨大タスクを抱えて context 肥大で漏れる問題を回避でき、(2) 独立サブタスクの並列化でスループットが上がり、(3) サブタスク境界と依存が明示文書化されることで結合点の不整合が減る、と仮説する。

### Implementation
- 新規スキル `.claude/skills/epic/SKILL.md`（Claude Code 専用）と新規エージェント `.claude/agents/epic-planner.md`（model: opus）を追加。
- epic 本体（メイン Claude）が Phase 1（epic-planner 分割）→ Phase 1.5（分割ユーザー確認）→ Phase 2（DAG 順ネスト pir2 起動）→ Phase 3（統合確認＋メタ retro）を制御。
- ネスト pir2 は `subagent_type=general-purpose` に `~/.claude/skills/pir2/SKILL.md`（--codex 時 pir2codex）を Read させオーケストレーターとして実行させる。
- 独立サブタスクは並列 fan-out、依存サブタスクは先行成果（サブ RUN_DIR・変更ファイル・git diff）を注入して直列化。共有リソース競合は epic-planner が暗黙依存の辺に張る。

### Quality Guardrails
- ネスト深さは L0→L1→L2 に頭打ち（L2 配下の再探索ネスト＝L3 は抑制、超過時 inline フォールバック）。
- サブ pir2 のユーザー確認ゲートは保守的デフォルト＋`DEFERRED_USER_DECISIONS` で epic 本体に集約し、独断のスコープ縮小を禁止。
- 分割ユーザー確認ゲート（Phase 1.5）は Auto mode でも必須。
- epic-planner は分割レベルのみ（実装詳細は各 pir2 planner に委譲）。過度な細粒度化（サブタスク数過多で並列運用コストが逆転）を観測。

### Metrics
- epic 起動回数 / サブタスク数分布
- 並列 fan-out 実行数 / 直列辺数
- 深さバジェット超過による inline フォールバック回数
- サブタスク境界の結合不整合の発生回数
- `DEFERRED_USER_DECISIONS` の発生・ブロッキング化回数
- Phase 3 統合修正サブタスクの追加回数

### Adoption Criteria
- 3 回以上の epic 実行が蓄積されている。
- 分割判定が安定している（同種エピックで分割方針が回により逆転しない）。
- サブタスク境界の結合不整合・命名ドリフトが単一 pir2 運用より悪化していない。
- 深さバジェット超過が運用を破綻させていない。
- ユーザーが恒久採用してよいと判断している。

### Rejection Criteria
- ネスト深さ超過でサブ pir2 が起動・完遂できない事象が頻発する。
- サブタスク分割が細粒度化しすぎて並列運用コストが逆転する。
- サブ pir2 のユーザーゲート委譲が機能せず、独断のスコープ縮小・仕様変更が発生する。
- 結合点の不整合が単一 pir2 運用より増え、統合修正コストが並列化の利得を上回る。

### Evidence Summary
- Epic executions: 0
- Parallel fan-outs: 0
- Depth fallbacks: 0
- Integration-boundary regressions: 0
- Deferred-decision escalations: 0
- Recommendation changes: 0

### Observation Log
観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は git 管理外の `~/.claude/memory/experimental_observations.md` の該当実験セクションに記録する（グローバルファイルにプロジェクト固有名を載せないため）。実験定義はこのファイルが SSOT。
```

---

### 変更不要（implementer は触らないこと）

- **`etc/link.sh`**: 改修不要。`for claude_dir in agents skills lib hooks` ループが `.claude/agents/` と `.claude/skills/` を丸ごとリンクするため、新規ファイル配置のみで自動リンクされる（exploration-03 で確定）。
- **`.claude/settings.json`**: 登録不要。Claude Code はスキル・エージェントをディレクトリ構造＋ファイル配置で自動認識する。settings.json に登録機構はない（exploration-03 で確定）。
- **`etc/sync-opencode.sh` / `etc/sync-codex.sh`**: SSOT リスト編集不要。`.claude/agents/*.md` パターンで epic-planner.md は OpenCode に自動抽出される（Write 時に PostToolUse hook が自動発火）。epic SKILL.md は `.claude/skills/` 配置＝Claude Code 専用のため sync 対象外で正しい（会話で「.agents/skills には置かない」と確定済み）。
- **`.claude/skills/epic/references/` サブディレクトリ**: 作らない。epic SKILL.md は自己完結させ、RUN_DIR 計算・Fan-Out Gate・plan-choice-gate・retrospector 起動仕様は既存の `~/.claude/skills/pir2/references/*.md` を参照する（重複 references を作らない＝feedback_no_redundant_skills 準拠）。

---

### IMPLEMENTATION_SHARDS

なし。

### IMPLEMENTATION_UNITS

なし。

**実装規模の見積もり**: 4 ファイル（新規 2・追記 2）だが密結合（epic SKILL.md ↔ epic-planner.md の出力フォーマット契約 ↔ experimental.md 起票 ↔ CLAUDE.md 追記が相互参照）。ファイル数は少なく、単一の fresh context に無理なく収まる規模であり、命名・フォーマット契約の一貫性を 1 体が通しで担保すべき。**分割せず単一 implementer で実装する**（決定木: 小さい実装 → 分割しない。かつ結合が強いため仮に大きくても shards は不適）。

---

### 適用される既存ルール（ステップ 1.5 照合結果）

- **照合した参照元（Read 済み）**:
  - `/Users/kawasetakumi/dotfiles/CLAUDE.md`（プロジェクト CLAUDE.md）
  - `/Users/kawasetakumi/.claude/CLAUDE.md`（グローバル CLAUDE.md）
  - `/Users/kawasetakumi/.claude/projects/-Users-kawasetakumi-dotfiles/memory/MEMORY.md`（目次）
  - `/Users/kawasetakumi/.claude/projects/-Users-kawasetakumi-dotfiles/memory/feedback_no_redundant_skills.md`（本文）
- **適用されるルール一覧**:
  - **既存スキルでカバーできる用途を別スキルに切り出さない（feedback_no_redundant_skills）** — 本タスクは新スキル `/epic` の新設。**ユーザーが明示的に `/epic` 新設を指示済み**（設計会話で確定）であり、かつ `/epic` は既存 `/pir2` が扱わない capability（複数サブタスクの上位オーケストレーション。pir2 の SHARDS/UNITS は単一 plan 内の実装分割で粒度が異なる）を提供するため、feedback の「ユーザー明示があれば分離可・重複は削る」条件を満たす。**重複回避策として** references を新設せず pir2 の既存 references を再利用、experimental の観測機構も既存 registry に相乗り、フェーズ/Fan-Out Gate も既存プロトコルを参照する形にした。
  - **グローバルファイルの汎用性ルール（グローバル CLAUDE.md）** — `.claude/` 配下は全プロジェクト共通。SKILL.md / epic-planner.md / CLAUDE.md 追記に Unity/Figma 等の具体名・プロジェクト固有名を混入させない（会話の例示は成果物に書かない）。汎用表現のみ使用。
  - **既存構造パターンからの逸脱には事前確認（グローバル CLAUDE.md）** — スキル配置（`.claude/skills/epic/SKILL.md` 単一ファイル・references なし）は既存 pir2codex/ir/research と同型で逸脱なし。エージェント配置（`.claude/agents/epic-planner.md` 単一ファイル）も既存と同型。逸脱なし。
  - **サブエージェントはユーザー対話不可（PIR² 設計原則・pir2-protocol）** — Phase 1.5 ゲートとサブ pir2 内ゲートをすべて epic 本体に集約する設計に反映（本体オーケストレーション責務の集約を維持）。
  - **後方互換・dead code 温存禁止 / スコープ厳守（グローバル CLAUDE.md）** — 4 ファイルのみ変更。既存 pir2 SKILL.md・planner.md 等は一切改変しない（ネスト pir2 は既存 SKILL.md を read-only で流用）。
  - **Co-Authored-By 行を付けない / git add -A 禁止（グローバル CLAUDE.md）** — 本実装ではコミットは行わない（ユーザー指示があるまで）。implementer への念のための注記に留める。
- **違反検出の有無**: 違反なし。特に「新スキル切り出し」は feedback_no_redundant_skills に抵触しないことを上記で確認済み（ユーザー明示＋非重複 capability＋重複回避策あり）。

---

### 既存パターン照合結果

- **対象**: 新スキルの frontmatter・本文採番、新エージェントの frontmatter・CORE・出力フォーマット、experimental.md 起票、CLAUDE.md 表追記。
- **既存の慣例**（exploration-01/02/03 で確認）:
  - スキル frontmatter は `name` / `description`（用途＋ユースケース例＋「ユーザーが /name と入力したら必ず…」）/ `argument-hint` の 3 要素。本文は `# フロー名` → `## ステップ N:` 採番。バリアントは親スキルのステップを「〜と同一」で参照。
  - エージェント frontmatter は `name` / `description` / `model` / `tools`。オーケストレーション判断層は `model: opus`。CORE は「役割宣言＋日本語出力＋フォーマット強制＋ツール/責務境界」の 4 点。
  - experimental.md は統一セクション構成（Status〜Observation Log）で末尾追記。
  - CLAUDE.md は Markdown 表への行追加。
- **今回のプランの整合性**: 全て**合致**。epic は pir2codex 同様「pir2 のステップ/references を参照するバリアント寄りの上位スキル」として書く。epic-planner は planner.md の型に準拠しつつ出力フォーマットのみ「エピック分割レポート」に置換（planner の実装ステップ/SHARDS/UNITS は出さない＝責務差の反映）。

---

### 既存パターン逸脱の事前申告

- **逸脱内容**: epic-planner の出力フォーマットは planner.md の「プランレポートフォーマット」を流用せず、新規「エピック分割レポートフォーマット」を定義する（実装ステップ・IMPLEMENTATION_SHARDS/UNITS を**出さない**）。
- **逸脱理由**: epic-planner の責務は「エピック→サブタスク分割＋DAG」であり「単一タスク→ファイル×関数の実装ステップ」ではない。planner の実装ステップ節を持たせると会話で確定した「実装詳細を抱えるとコンテキスト肥大で漏れる」問題が epic-planner に再現する。これは planner との**責務の本質差**であり、フォーマットを分けるのが正しい。
- **既存パターンに合わせた代替案**: planner フォーマットに「実装ステップは省略」と注記して流用する案もあるが、混乱を招く（SHARDS/UNITS は実装分割の概念でサブタスク分割とは別レイヤー）。
- **スキル本体への依頼**: この逸脱は会話の確定仕様（epic-planner は分割レベルのみ）に沿ったものであり、**ユーザー確認は既に取得済みと解釈できる**。ただし念のため最終サマリーで「epic-planner は独自フォーマットを採用した」と 1 行報告することを推奨。

---

### テスト・検証方法

このタスクはドキュメント著述でテストスイートなし。役割境界に従い分離して記載する。

- **追加/更新が必要なテストファイル**: なし（テストコード対象外）。
- **implementer が自己検証すべき項目**（静的検証・生成物確認のみ）:
  - 4 ファイルがそれぞれ Write/Edit 成功していること（`git status` で新規 2・変更 1〜2 を確認）。
  - `.claude/skills/epic/SKILL.md` / `.claude/agents/epic-planner.md` の frontmatter が YAML として妥当（`---` 対で囲まれ `name` を持つ）。
  - epic-planner.md 内に `<!-- CORE: このセクションは変更禁止 -->` 〜 `<!-- /CORE -->` の対が存在すること。
  - epic SKILL.md 本文冒頭に「3 階層ネスト / 深さバジェット / ユーザー対話 epic 本体集約」の 3 前提が明記されていること。
  - epic SKILL.md と epic-planner.md の**フォーマット契約が一致**（SKILL.md ステップ 2 が要求する `epic-plan.md` の中身＝epic-planner の「エピック分割レポートフォーマット」）。
  - epic-planner.md の Write により PostToolUse hook（sync-opencode / sync-codex）が自動発火する。hook 発火後、OpenCode 側生成物 `~/.config/opencode/agents/epic-planner.md` が生成されていること（`Read` またはファイル存在確認）。※これは codegen 相当の確認であり implementer の自己検証範囲。
  - CLAUDE.md の 2 表に行が 1 行ずつ増え、pir2 系説明の新規サブセクションが追加されていること。既存 pir2 セクション本文が改変されていないこと（`git diff CLAUDE.md` が追加のみ）。
- **tester が実行する最小スコープのテストコマンド**: なし（テストフレームワーク非対象）。強いて挙げれば sync スクリプトの冪等再実行確認だが、hook で自動発火済みのため tester フェーズでの追加実行は不要。tester には「本タスクはドキュメント著述であり実行テスト対象なし。生成物の存在と markdown 構造の妥当性のみ確認」と伝える。

---

### 注意点・リスク

- **深さバジェット（最重要リスク）**: L0→L1→L2 の 3 階層は既存 nested-explorer 実験で実績があるが、L2 配下（サブ pir2 の planner/reviewer）がさらに explorer をネストすると L3 となり未確認領域。SKILL.md ステップ 3-3 で L2 頭打ち運用＋inline フォールバックを必ず明記すること。初回 `/epic` 実行時に実際のネスト挙動を検証すべき旨を experimental の Observation 対象とする。
- **ユーザーゲート委譲の抜け**: サブ pir2 は独断でスコープ縮小してはならない。保守的デフォルト＋`DEFERRED_USER_DECISIONS` 集約を SKILL.md ステップ 3-4 で明記しないと、サブ pir2 が仕様変更を握りつぶす退行が起きる（グローバル CLAUDE.md「スコープ厳守」「6.5 未解決事項はユーザーに委ねる」の精神）。
- **並列 fan-out の working tree 競合**: 独立サブタスクの並列実行は、ファイル所有が非重複であることが前提。epic-planner が並列集合の非重複性を保証し、共有リソースは暗黙依存の辺で直列化すること（SKILL.md ステップ 3-1／epic-planner の分割規則で担保）。非重複性が曖昧なら直列に倒す。
- **グローバル汎用性**: SKILL.md / epic-planner.md / CLAUDE.md 追記にプロジェクト固有名を混入させない（会話の Unity/Figma は例示。成果物に書かない）。
- **ネスト起動方式の環境依存**: general-purpose に Skill ツールで直接 `/pir2` を起動させる方式は環境依存のため、既定は Read（`~/.claude/skills/${SUBTASK_SKILL}/SKILL.md`）ベースにする。初回実行で Read ベース方式が機能することを確認する。
- **試験実装の位置づけ**: 恒久機能として断定しない。experimental.md の該当実験を SSOT に観測し、採用可否はユーザー判断とする。

---

### スキル本体への追加調査依頼

なし。

### EXPLORATION_NEEDED

なし。

> ℹ️ Agent ネスト起動方式・深さバジェットの技術整合性は、既存 nested-explorer 実験（L0→L1→L2 の実績）と Agent ツール仕様（general-purpose は Read+Agent を持つ）から本プラン内で解決済み。ランタイムの L3 以深挙動は「初回 `/epic` 実行時の検証事項」として experimental Observation に委ね、authoring をブロックしない（本タスクは指示ドキュメント著述であり、ランタイム挙動の実測は成果物の前提ではない）。
