VERDICT: FAIL

### 担当 role
consistency

### レビュー対象
- `.claude/skills/epic/SKILL.md`（新規）
- `.claude/agents/epic-planner.md`（新規）
- `CLAUDE.md` 追記（スキル表・エージェント表・pir2系サブセクション）
- `.claude/skills/pir2/references/experimental.md` 追記（`epic-orchestrator-nested-pir2` 実験起票）

前回の review-01-consistency.md は実装未反映時点（implementer 未実行）のものだったが、本レビュー時点では `.claude/skills/epic/SKILL.md` / `.claude/agents/epic-planner.md` / `CLAUDE.md` 追記 / `experimental.md` 追記のいずれも実体が存在することを確認済み（`git diff HEAD -- CLAUDE.md .claude/skills/pir2/references/experimental.md` で差分確認、`.claude/agents/epic-planner.md` と `.claude/skills/epic/SKILL.md` を Read 済み）。以降は実体に基づくレビュー結果。

比較基準として `.claude/skills/pir2/SKILL.md` / `.claude/skills/pir2codex/SKILL.md` / `.claude/skills/pir2async/SKILL.md` / `.claude/skills/research/SKILL.md` / `.claude/skills/deepthink/SKILL.md` / `.claude/skills/ir/SKILL.md` / `.claude/agents/planner.md` / `.claude/agents/reviewer.md` / `.claude/agents/tester.md` / `.claude/agents/implementer.md` / `.claude/agents/ui-ux-reviewer.md` / `.claude/agents/retrospector.md` / `.claude/skills/pir2/references/{plan-choice-gate,fan-out-gate,retrospector-prompt,sanitized-cwd,run-dir-base,experimental}.md` を実際に Read して照合した。

---

### 判断根拠

- **frontmatter の型一致**: epic/SKILL.md の frontmatter（`name`/`description`/`argument-hint`）は pir2/pir2codex と同型。`description` は「用途→ユースケース例（『』引用の要望文）→ユーザーが /epic と入力したら必ずこのスキルを使う」という確立された記述順序に沿っている。ただし末尾に「先頭に --codex を付けると下位起動を /pir2codex に一律差し替える。」という追加文が「ユーザーが〜必ずこのスキルを使う。」の**後**に続く。既存 5 件（pir2, pir2codex, retro, instruction-refactor, walkthrough）全てで「ユーザーが /name と入力したら必ずこのスキルを使う。」が description の**最終文**になっており、trailing 文の位置は逸脱（Low、後述）。epic-planner.md の frontmatter（`name`/`description`/`model`/`tools`）は planner.md と同型。`model: opus` も既存の「オーケストレーション判断層は opus」規約と整合。
- **CORE セクションの書式**: epic-planner.md の CORE は `<!-- CORE: このセクションは変更禁止 -->` 〜 `<!-- /CORE -->` の記法・改行位置まで planner.md と完全一致。中身も「役割宣言 → 日本語出力強制 → フォーマット強制 → ツール/責務境界」の 4 行構成が planner.md と一致しており、良好。
- **ステップ採番・見出し**: epic/SKILL.md は `## ステップ N:` / `## ステップ N.M:` / `### N-M:` の pir2 系採番慣習に厳密に従っている（`## ステップ 2.5`, `### 3-0`〜`3-5` など）。pir2async に `## 残ステップ` / `## 完了済み`、deepthink に `## 思考モデルのモード` のような「ステップ番号なし ##」が混在する先例があるため、epic 末尾の `## Agent ネスト起動方式の技術整合性` / `## 変更不要` / `## 試験実装の位置づけ` も許容範囲内（違反ではない）。
- **references 参照の一貫性**: `sanitized-cwd.md` / `run-dir-base.md` / `plan-choice-gate.md` / `fan-out-gate.md` / `retrospector-prompt.md` はいずれも実在するファイルパスであることを確認した（`ls .claude/skills/pir2/references/` で列挙済み）。ただし**パスの存在**と**内容の適用可能性**は別問題であり、`fan-out-gate.md` と `retrospector-prompt.md` の参照は内容ミスマッチがあり High として下記「問題一覧」に記載する。
- **フォーマット契約の一致**: epic/SKILL.md ステップ2「分割戦略レポート本体は `{EPIC_RUN_DIR}/epic-plan.md` に書き出し」と epic-planner.md の「エピック分割レポートフォーマット」は語彙・セクション名（`### サブタスク一覧` `### 依存グラフ（DAG）` `### 適用される既存ルール` `### USER_DECISION_REQUIRED` `### EXPLORATION_NEEDED` 等）まで完全一致。返り値フォーマット（要点＋USER_DECISION_REQUIRED/EXPLORATION_NEEDED の有無）も SKILL.md 側の指示と epic-planner.md 側の出力フォーマットが一致している。ここは良好。
- **CLAUDE.md 追記の書式一致**: エージェント表・スキル表への行追加は既存行と同じ `| \`file\` | 説明 |` 形式で 1 行ずつ追加されている（アンカー行の直後に正しく挿入されていることを diff で確認）。pir2 系サブセクション（`### エピックオーケストレーション`）は直前の `### PIR² ワークフロー (`/pir2`)` の直後に挿入されており、トーン・具体性のレベルも整合している。experimental.md への追記は既存 3 エントリ（`pir2-implementer-shards-and-review-fix-shards` / `pir2-implementer-sequential-units` / `pir2-explorer-nesting`）と `## Experiment:` 〜 `### Observation Log` のセクション構成・見出し文言が完全一致（grep で全エントリの `^## \|^### ` を突合済み）。

---

### 問題一覧

- **High** `.claude/agents/epic-planner.md:65` — メモリログの命名規約違反。全既存エージェント（`planner.md:321` → `pir_planner_log.md`、`implementer.md:85` → `pir_implementer_log.md`、`reviewer.md:225` → `pir_reviewer_log.md`、`tester.md:171` → `pir_tester_log.md`、`ui-ux-reviewer.md:104` → `pir_uiux_reviewer_log.md`）は例外なく「1 エージェント 1 ログ（`pir_<agent名>_log.md`）」規約に従っている（`grep -n "PROJECT_MEMORY_DIR}/pir_" .claude/agents/*.md` で6件とも確認済み）。epic-planner.md だけがこの規約から逸脱し、独自の `pir_epic_planner_log.md` を作らず既存の `pir_planner_log.md`（planner 専用ログ）に相乗りしている。`retrospector.md:232` はこのログを「今回 run の `PLAN_STRATEGY_CHANGED=true` フラグ付きエントリ（再起動された planner の最終出力）」を抽出する専用の解析対象として直接 Read しており、epic-planner のエントリ（`## [エピック名] — ...` 形式、`PLAN_STRATEGY_CHANGED` の概念を持たない）が混入すると、この既存解析ロジックの前提（このログは planner 専用）が崩れる。plan.md にもこの相乗りの理由（容量節約以外の必然性）が記載されておらず、単なる工数節約のための規約逸脱に見える。
  → 修正方法: `{PROJECT_MEMORY_DIR}/pir_epic_planner_log.md` を新設し、他 6 エージェントと同じ 1 エージェント 1 ログ規約に揃える。

- **High** `.claude/skills/epic/SKILL.md:117` — `retrospector-prompt.md` への丸投げ参照が、epic 自身の実行モデルと整合しない必須パラメータを含む。`retrospector-prompt.md` は「以下の情報をすべて渡す」として `RUN_DIR` / `INNER_LOOP_COUNT` / `OUTER_LOOP_COUNT` / `REPLAN_COUNT` / `PLAN_STRATEGY_CHANGED` / `{RUN_DIR}/review-*.md` / `{RUN_DIR}/test-*.md` を必須項目に挙げているが、epic は独自の inner/outer loop・review・test フェーズを一切持たず（それらは各ネスト pir2 内部にのみ存在し、それぞれ別の `RUN_DIR` を持つ）、`EPIC_RUN_DIR` という別名の変数しか持たない。`retrospector.md` の model 選択ロジック（`INNER_LOOP_COUNT` と `OUTER_LOOP_COUNT` が両方 0 なら sonnet、いずれか 1 以上なら opus）はこれらの値の存在を前提にしており、epic のメタ retrospect 起動時にこれらをどう扱うか（省略可か、`EPIC_RUN_DIR` を `RUN_DIR` として渡すのか、固定値 0 で埋めるのか）が SKILL.md 本文に一切書かれていない。pir2codex がステップごとに「/pir2 のステップ N と同一」と書きつつ差分箇所（`PLAN_STRATEGY_CHANGED` の扱い等）を都度明示しているのと対照的に、epic はこの不整合を放置している。
  → 修正方法: ステップ4に「`RUN_DIR=EPIC_RUN_DIR` として渡す／`INNER_LOOP_COUNT`・`OUTER_LOOP_COUNT`・`REPLAN_COUNT`・`PLAN_STRATEGY_CHANGED` は epic に該当機構がないため固定値（例: 全て 0 / false）で渡す／review・test パスは該当なしとして渡さない」等、retrospector-prompt.md の必須項目と epic の実行モデルとのマッピングを明記する。

- **High** `.claude/skills/epic/SKILL.md:91` — `fan-out-gate.md` 参照の内容ミスマッチ。ステップ 3-1 は「pir2 の Fan-Out Gate 慣習に倣い…宣言テンプレは pir2 ステップ 7-2A の型を流用します（`~/.claude/skills/pir2/references/fan-out-gate.md` を参照）」としているが、`fan-out-gate.md` の冒頭は「PIR² 系スキル（/pir2 等）の**reviewer 並列起動仕様**」と明記され、本文も「観点マッピング（reviewer.md の SSOT に従う）」「reviewer 起動パラメータ（`REVIEWER_ROLE` 等）」「refactor-advisor との関係」など reviewer 専用の内容のみで構成されている（`Ti` サブタスクの並列起動に一般化できる記述は存在しない）。実際にこのファイルを開いた実行者は `REVIEWER_ROLE` の話しか得られず、epic のサブタスク fan-out には転用できない。宣言テンプレートの実体（`> **Fan-Out Gate（reviewer）** ...`）は `fan-out-gate.md` ではなく pir2/SKILL.md 本文の 7-2A に直接埋め込まれているため、epic が本当に参照すべきは pir2/SKILL.md 側であり `fan-out-gate.md` ではない。
  → 修正方法: 参照先を「pir2/SKILL.md ステップ 7-2A の宣言テンプレート（の考え方）」に限定するか、epic 独自の宣言テンプレート（`REVIEWER_SET` → `独立集合 {T1,T2,...}` に読み替えた具体的な blockquote）を SKILL.md 本文に直接埋め込む。`fan-out-gate.md` への参照は削除するか「reviewer 専用ファイルだが起動体数宣言の考え方だけ流用する」と明記する。

- **Medium** `.claude/skills/epic/SKILL.md:121-125` — 最終サマリー（ステップ5）に具体的なテンプレートが埋め込まれていない。pir2（ステップ12）・pir2codex（ステップ12）・pir2async（ステップ8）・ir（ステップ4）・research（ステップ6）・deepthink（ステップ6）は全てコードフェンス付きの最終サマリーテンプレート（フィールド名を持つ具体的な雛形）を SKILL.md 本文に直接埋め込んでいる。epic のステップ5は「pir2 ステップ 12 の型で提示してください」という指示のみで、雛形コードブロックを持たない。他の全ての pir2 系スキルが最終サマリーステップを自己完結させている慣習から逸脱している。
  → 修正方法: epic 独自の最終サマリーテンプレート（サブタスク一覧 / 各サブ RUN_DIR / 各サブ pir2 の VERDICT / DEFERRED_USER_DECISIONS / 統合確認結果 / メタ改善推奨 / EPIC_RUN_DIR の各フィールドを持つコードフェンス）を明示的に追加する。

- **Medium** `.claude/skills/epic/SKILL.md`（ステップ1〜5全体） — オーケストレーター自身のレベルでの中断復帰観測機構（`next-steps.md` 相当）が欠落している。pir2・pir2codex・pir2async は全て「オーケストレーター自身のどのステップまで完了したか」を `{RUN_DIR}/next-steps.md` に checkbox で保存し、「ユーザー会話による中断後は必ずこのファイルを Read してから動く」ことを必須運用としている。epic の `epic-runs.md`（3-5）は `Ti → サブ RUN_DIR` の対応記録に過ぎず、epic 自身が Phase 1/1.5/2/3 のどこまで完了したかを追跡する仕組みではない。DAG 実行中（特に並列 fan-out 中）にセッションが中断した場合、再開手順が SKILL.md に規定されていない。
  → 修正方法: `{EPIC_RUN_DIR}/epic-next-steps.md`（または `epic-runs.md` の拡張）として Phase 単位の完了 checkbox を導入し、next-steps-queue.md 相当の「中断後は必ず Read」運用を明記する。

- **Low** `.claude/skills/epic/SKILL.md:4` — `argument-hint: [大規模タスクの説明]（先頭に任意で --codex）`。既存の複数フラグを持つスキル（`instruction-refactor`: `[--scope=user|project|all] [--no-implement] [path]`、`retro`: `[--meta] [--dream] [対象プロジェクトのパス]`）は全て `[flag]` 形式でブラケット区切りにフラグを列挙しているが、epic は全角括弧の説明文形式になっており記法が異なる。
  → 修正方法: `[大規模タスクの説明] [--codex]` のようにブラケット区切りに揃える。

- **Low** `.claude/skills/epic/SKILL.md:3` — frontmatter description の末尾。既存 5 件（pir2, pir2codex, retro, instruction-refactor, walkthrough）は「ユーザーが /name と入力したら必ずこのスキルを使う。」を description の最終文としているが、epic はその後に「先頭に --codex を付けると下位起動を /pir2codex に一律差し替える。」という追加文が続く。
  → 修正方法: `--codex` の説明を「ユーザーが〜必ずこのスキルを使う。」より前に移動する（pir2codex の「IMPLEMENTATION_UNITS による直列 fresh セッション化に対応。」が最終文の直前に置かれているのと同じ配置にする）。

---

### 担当外で気づいた点（参考）

- `.claude/skills/pir2/SKILL.md:35` の `HANDOFF_PATH="${PROJECT_ROOT}/.ai-pir-runs/handoff.md"` は `PROJECT_ROOT` 単位の単一ファイル（`RUN_DIR` に紐付かないグローバル1個）である。epic のステップ 3-1（独立サブタスクの並列 fan-out）は同一 `PROJECT_ROOT` から複数のネスト pir2 を同時起動するため、各ネスト pir2 が独立に同じ `HANDOFF_PATH` を計算・書き込みし合い競合する可能性がある（pir2 側の設計は「1 プロジェクトで同時に走る pir2 は 1 つ」を暗黙の前提にしていると見られる）。これは correctness/architecture 観点の懸念であり、consistency の VERDICT には含めない。

### 良好点

- epic-planner.md の CORE セクション（役割宣言・日本語出力強制・フォーマット強制・責務境界の4行構成）は planner.md の型と完全に一致しており、responsibility boundary（「planner/implementer/reviewer/tester の起動はスキル本体に集約、自分は分割戦略のみ」）の書き方まで忠実に踏襲されている。
- epic-planner.md の「エピック分割レポートフォーマット」と epic/SKILL.md が要求する `epic-plan.md` の構造は語彙・セクション名レベルで完全一致しており、フォーマット契約の整合性は良好。
- experimental.md への `epic-orchestrator-nested-pir2` 実験起票は既存 3 エントリと見出し構成が一字一句一致しており、Retro 運用の SSOT パターンを正しく踏襲している。

### 次のアクション

implementer への差し戻し指示:
1. `epic-planner.md` のメモリログ出力先を `{PROJECT_MEMORY_DIR}/pir_epic_planner_log.md` に変更し、他 6 エージェントと同じ「1 エージェント 1 ログ」規約に揃える。
2. `epic/SKILL.md` ステップ4のretrospector起動指示に、`retrospector-prompt.md` の必須パラメータ（`RUN_DIR`/`INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT`/`REPLAN_COUNT`/`PLAN_STRATEGY_CHANGED`/review・testパス）と epic 自身の実行モデル（`EPIC_RUN_DIR`のみ・ループカウンタなし）とのマッピングを明記する。
3. `epic/SKILL.md` ステップ3-1の `fan-out-gate.md` 参照を、実際に転用可能な内容（pir2/SKILL.md 7-2A の宣言テンプレート）に差し替えるか、epic 独自の宣言テンプレートを本文に直接埋め込む。
4. （任意・Medium）最終サマリーのコードフェンステンプレートを epic 独自に追加する。
5. （任意・Medium）epic 自身のレベルでの中断復帰チェックリスト（`next-steps.md` 相当）を追加する。
6. （任意・Low）argument-hint と description 末尾の trailing 文配置を既存パターンに揃える。
