# PIR2 Experimental Workflow Registry

PIR2 のうち、まだ恒久採用と判断していない運用を追跡するための実験レジストリ。

retrospector は `/pir2` および `/retro` のたびにこのファイルを読み、該当する run があれば観測を追記・更新する。効果がはっきりするまでは、このファイルを採用可否判断の SSOT とする。

## Retro 運用

- `Status: Active` の実験を毎回確認する。
- `RUN_DIR` がある場合は `plan.md`、`implementation-*.md`、`review-*.md`、`test-*.md`、`pir_skill_log.md` を材料にする。
- 該当 run で実験が使われていなければ、原則として追記不要。ただし手動 `/retro` で直近ログに実験利用が見つかった場合は観測してよい。
- 観測は `Observation Log` に 1 件ずつ追記する。
- `Evidence Summary` は、観測ログに基づき保守的に更新する。
- 採用条件または廃止条件を満たしたら `Recommendation` を更新し、振り返りレポートにも明記する。
- `Recommendation` は採用/廃止の候補であり、実際に恒久ルールへ昇格・削除するにはユーザー判断を必要とする。

## Experiment: pir2-implementer-shards-and-review-fix-shards

- Status: Active
- Started: 2026-06-22
- Scope: `.claude/skills/pir2/**`, `.claude/agents/planner.md`, `.claude/agents/implementer.md`
- Owner: user
- Recommendation: Continue observing

### Hypothesis

厳密な分離ゲートを満たす場合に限り、初回実装を複数 implementer shard に分けると、review/test 品質を落とさずに待ち時間を短縮できる。

reviewer FAIL 後の修正は指摘箇所が明確なため、初回実装よりも積極的に複数 implementer へ分けられる可能性が高い。

### Implementation

- 通常の実装 actor は `IMPLEMENTATION_ACTOR=implementer-subagent`。
- 初回の複数 implementer は `IMPLEMENTATION_ACTOR=implementer-shards` とし、planner が `IMPLEMENTATION_SHARDS` を明示した場合のみ許可する。
- 初回 shard は最大 3 体まで。
- reviewer FAIL 後は、失敗 reviewer レポートからスキル本体（メイン Claude）が `REVIEW_FIX_SHARDS` を組み立ててよい。
- review-fix shard は最大 5 体まで。
- tester FAIL 後は原則として単一 implementer に戻す。
- 詳細ゲートは `implementation-delegation.md` を参照する。

### Quality Guardrails

- shard 間で許可ファイル集合が重ならない。
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、共通 helper を複数 shard が触らない。
- shard 間に順序依存がない。
- 命名、抽象、データ形状が別 shard の未確定実装に依存しない。
- 全 shard 完了後にスキル本体（メイン Claude）が統合確認し、単一 reviewer/tester ループで全体確認する。
- 条件が曖昧なら `IMPLEMENTATION_ACTOR=implementer-subagent` に戻す。

### Metrics

- `IMPLEMENTATION_ACTOR`
- 初回 shard 数
- review-fix shard 数
- `INNER_LOOP_COUNT`
- `OUTER_LOOP_COUNT`
- reviewer FAIL が shard 修正後に再発したか
- tester FAIL が shard 修正後に発生したか
- shard 境界の衝突、重複抽象、未接続実装の有無
- 体感またはログ上の待ち時間改善

### Adoption Criteria

- 3 回以上の shard 実行、または 5 回以上の shard 使用可否判断が蓄積されている。
- shard が原因の競合、品質劣化、再実装増加が観測されていない。
- reviewer/tester ループ数が単一 implementer の通常運用より悪化していない。
- スキル本体（メイン Claude）の統合確認コストが、並列化で得た利点を上回っていない。
- ユーザーが恒久採用してよいと判断している。

### Rejection Criteria

- shard 境界の誤判定で同一ファイル・共有契約・生成物に衝突が起きた。
- 分割により実装方針がずれて reviewer/tester ループが増えた。
- 初回 shard または review-fix shard が原因で統合修正が頻発した。
- 品質は同等でも、運用複雑性が待ち時間短縮に見合わない。

### Evidence Summary

- Eligible decisions: 0
- Shard executions: 0
- Review-fix shard executions: 0
- Shard-caused regressions: 0
- Recommendation changes: 0

### Observation Log

観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は git 管理外の `~/.claude/memory/experimental_observations.md` の該当実験セクションに記録する（グローバルファイルにプロジェクト固有名を載せないため）。実験定義はこのファイルが SSOT。

## Experiment: pir2-implementer-sequential-units

- Status: Active
- Started: 2026-06-26
- Scope: `.claude/skills/pir2/**`, `.claude/agents/planner.md`, `.claude/skills/pir2codex/**`
- Owner: user
- Recommendation: Continue observing

### Hypothesis

実装内容が大きいのに 1 体の implementer に plan 全体を委譲すると、後半ステップほどコンテキストが肥大しエラーが蓄積する（context-rot）。大きいが結合していて並列 shard にできない実装を、planner が順序付き unit に分け、unit ごとに fresh な implementer を直列起動すれば、各 implementer のコンテキストをまっさらに保ちつつ（後続 unit は先行 unit の実コードを Read して接続）、並列 shard の統合 divergence も避けられ、品質が上がる。

pir2codex（Codex 実装版）でも同型を適用し、unit ごとに新しい Codex セッション（新 threadId）を直列起動する。

### Implementation

- 通常の実装 actor は `IMPLEMENTATION_ACTOR=implementer-subagent`。
- 大きいが結合した実装は `IMPLEMENTATION_ACTOR=implementer-sequential` とし、planner が `IMPLEMENTATION_UNITS` を明示し unit 許可条件を満たした場合のみ許可する。
- unit は `UNIT_ID` 昇順に 1 体ずつ直列実行（先行 unit 完了を待って次を起動）。
- unit K の implementer に、完了済み unit の `implementation-{IMPL_INDEX}-unit-*.md` パスと「`git diff` で先行 unit を確認し命名/抽象に従う」指示を渡す。
- 全 unit 完了後にスキル本体が unit 統合確認（命名不整合・重複抽象・未接続実装の検査）。
- v1 では初回実装のみに適用。reviewer/tester FAIL 後の再実装は既存の review-fix shard / 単一 implementer に従う。
- `IMPLEMENTATION_SHARDS` とは排他（独立なら shards、結合なら units）。
- 詳細ゲートは `implementation-delegation.md`「implementer-sequential」を参照する。

### Quality Guardrails

- 小さい実装には使わない（単一 implementer に倒す）。
- unit は「意味のある境界」で切る（作業量だけの機械分割をしない）。
- unit を順序通り直列実行すれば成立する（先行成果に後続が乗る）。
- 各 unit は fresh context に無理なく収まる粒度。
- `IMPLEMENTATION_SHARDS` と同時に提示しない。
- 条件が曖昧なら `IMPLEMENTATION_ACTOR=implementer-subagent` に戻す。
- 全 unit 完了後に統合確認を行い、単一 reviewer/tester ループで全体確認する。

### Metrics

- `IMPLEMENTATION_ACTOR`
- unit 数
- unit 間の命名不整合・重複抽象・未接続実装の有無
- `INNER_LOOP_COUNT` / `OUTER_LOOP_COUNT`（単一 implementer 通常運用との比較）
- reviewer/tester FAIL が直列実装後に発生したか
- 後半 unit の品質（context-rot 兆候）が単一実装より改善したか
- 体感またはログ上の品質・手戻り変化

### Adoption Criteria

- 3 回以上の sequential 実行、または 5 回以上の使用可否判断が蓄積されている。
- unit 境界の誤判定による統合不整合が観測されていない。
- reviewer/tester ループ数が単一 implementer の通常運用より悪化していない。
- 大きい実装で品質改善（手戻り減・後半 unit の質の維持）が観測されている。
- ユーザーが恒久採用してよいと判断している。

### Rejection Criteria

- 直列分割により unit 境界で命名・抽象がドリフトし統合修正が頻発した。
- fresh context 化が品質に寄与せず、運用複雑性だけが増えた。
- 単一 implementer と品質同等で、直列化の待ち時間増に見合わない。

### Evidence Summary

- Eligible decisions: 3（実 run 3 件。いずれも一方向の密結合で shard 不可・直列 unit 化が適合したケース。固有名を含む詳細は `~/.claude/memory/experimental_observations.md`）
- Sequential executions: 3（fresh implementer で context-rot 回避、後続 unit が先行 unit を git diff で読んで整合を維持。3 件目は後半 UNIT_4 も fresh context で context-rot 兆候なし）
- Unit-boundary regressions: 1（1 件目: 軽微な前方参照 friction のみ＝共有純ヘルパーの定義層のズレで解消可能。2 件目: 統合不整合ゼロで review-01 が全 6 観点初回 PASS。3 件目: **初の命名ドリフト観測**＝UNIT_4 のローカル変数命名が先行 unit と反転〔`SLUG_<TYPE>`⇄`<TYPE>_SLUG`〕。consistency reviewer が兄弟ファイル横断 grep で High 検出し sed 一括置換で解消。単発・機能影響なしで「統合修正が頻発」〔Rejection Criteria〕には非該当だが、採用条件「unit 境界の誤判定による統合不整合が観測されていない」に抵触するため採用は保留）
- Recommendation changes: 0（3 executions で実行回数の採用条件「3 回以上」に到達したが、初の unit-boundary 命名ドリフトを観測したため即採用せず Continue observing 継続。予防策＝planner が分割時に兄弟ファイル群の共有命名規則〔変数命名テンプレ〕を明示 pin。次サイクルで pin の有無とドリフト再発を観察）

### Observation Log

観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は git 管理外の `~/.claude/memory/experimental_observations.md` の該当実験セクションに記録する（グローバルファイルにプロジェクト固有名を載せないため）。実験定義はこのファイルが SSOT。

## Experiment: pir2-explorer-nesting

- Status: Active
- Started: 2026-06-23
- Scope: `.claude/agents/planner.md`, `.claude/agents/implementer.md`, `.claude/agents/reviewer.md`, `.claude/agents/explorer.md`, `.claude/agent-delegation.md`, `.claude/pir2-protocol.md`, `.claude/skills/pir2/**`
- Owner: user
- Recommendation: Continue observing

### Hypothesis

Claude Code v2.1.172 のサブエージェントネスト起動解禁を受け、planner / implementer / reviewer が広域探索を要するとき explorer を自分でネスト起動できるようにすると、`EXPLORATION_NEEDED` のメイン往復を削減してレイテンシを短縮できる。制御フロー（起動・ループ・VERDICT 集約・ユーザー確認ゲート）はメイン集約を維持するため、観測可能性・ループカウンタの SSOT は損なわれない。

### Implementation

- planner / implementer / reviewer の `tools` に `Agent` を追加。explorer / tester には追加しない（explorer はネストされる側、深さバジェット温存）。
- 各エージェントに「能動探索（広域探索時に explorer を `subagent_type=explorer` でネスト起動）」手順を追加。read-only の探索に限り、制御エージェントは起動しない。
- planner の追加探索をハイブリッド化: (a) 軽微な確認は自分で explorer をネスト起動して完結、(b) プラン方針が変わる規模は `EXPLORATION_NEEDED` でメインに返す（`REPLAN_COUNT` 管理はメインの SSOT）。
- ネスト起動した explorer はさらに子 explorer を起動しない（最深 3 で収まる）。

### Quality Guardrails

- サブからのネスト起動は read-only の探索（explorer）に限る。implementer / reviewer / tester / planner の制御起動はサブから行わない。
- 深さバジェット上限 5 に対し最深 3（メイン → planner/implementer/reviewer → explorer）で収まる。
- planner の追加探索で判断に迷ったら (b) `EXPLORATION_NEEDED` に倒す（メインが規模・回数を把握できる）。
- ユーザー確認ゲートはメイン集約を維持（サブはユーザー対話不可）。

### Metrics

- planner / implementer / reviewer が explorer をネスト起動した回数（`nested_explorer_calls`）
- `EXPLORATION_NEEDED` の発火回数・`REPLAN_COUNT`（メイン往復が減ったか）
- 制御エージェントを誤ってネスト起動した違反の有無
- 深さバジェット枯渇でエージェント起動が失敗した形跡の有無
- 体感またはログ上のレイテンシ改善

### Adoption Criteria

- 3 回以上のネスト探索実行が蓄積されている。
- 制御ネスト違反・深さバジェット枯渇が観測されていない。
- `EXPLORATION_NEEDED` のメイン往復が実際に減り、レイテンシまたは手戻りが改善している。
- ユーザーが恒久採用してよいと判断している。

### Rejection Criteria

- 制御エージェントの誤ネストで責務のメイン集約が壊れた。
- 深さバジェット枯渇でエージェントが起動できなくなった。
- ネスト探索が往復削減に寄与せず、運用複雑性だけが増えた。

### Evidence Summary

- Nested explorer runs: 0
- Exploration-needed roundtrips avoided: 0
- Control-nest violations: 0
- Depth exhaustions: 0
- Recommendation changes: 0

### Observation Log

観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は git 管理外の `~/.claude/memory/experimental_observations.md` の該当実験セクションに記録する（グローバルファイルにプロジェクト固有名を載せないため）。実験定義はこのファイルが SSOT。

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

- ネスト深さは L0→L1→L2 に頭打ち（L2 配下の再探索ネスト＝L3 は抑制、超過時は explorer 再ネストを諦め L1 ランナー自身の直接探索へ縮退）。
- サブ pir2 のユーザー確認ゲートは保守的デフォルト＋`DEFERRED_USER_DECISIONS` で epic 本体に集約し、独断のスコープ縮小を禁止。
- 分割ユーザー確認ゲート（Phase 1.5）は Auto mode でも必須。
- epic-planner は分割レベルのみ（実装詳細は各 pir2 planner に委譲）。過度な細粒度化（サブタスク数過多で並列運用コストが逆転）を観測。

### Metrics

- epic 起動回数 / サブタスク数分布
- 並列 fan-out 実行数 / 直列辺数
- 深さバジェット超過による縮退フォールバック（explorer 再ネスト不可時の L1 直接探索）回数
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

- Epic executions: 2（実 run 2 件・累計 6 サブタスク・全 PASS。epic-A=4サブ〔並列2+直列2〕/ epic-B=2サブ〔T1→T2 直列〕。固有名を含む詳細は `~/.claude/memory/experimental_observations.md`）
- Parallel fan-outs: 1（epic-A のみ。epic-B は parallel_fanouts=0＝共有ホットファイル集約により本質的に直列で、epic-planner が「並列化コスト逆転」を明示判断して過剰分割を回避。分割粒度判定は 2 run で安定〔並列 or 直列を正しく使い分け〕）
- Depth fallbacks: 0（両 run とも L3 拒否・IMPLEMENTATION_ACTOR=main 縮退は未発生。L2 頭打ち運用が保たれ 3 階層 L0→L1→L2 が完走。3 階層完走の実績は 2 件に）
- Integration-boundary regressions: 0（epic-A: 跨ぎ High 1 件は reviewer の実スキーマ未照合による誤検出を epic 本体が二重照合で却下。epic-B: 結合 working tree がビルドエラー 0、T2 が T1 確定の型・関数経路・外部 API 引数を消費し境界保持・命名ドリフトなし。加えて epic 本体統合ゲートが epic 変更を unstaged・並行別セッション作業を staged に index 分離して混線回避）
- Deferred-decision escalations: bubble-up 複数・ブロッキング化 0（両 run とも全件保守的デフォルト + 統合フェーズ処理で独断スコープ縮小なし。epic-B T2 は忠実移植優先・scope 非拡大で bubble-up）
- Phase 1.5 gate friction: 1（epic-B run で観測・負のシグナル）。epic-planner が移植の忠実フル既定を認識しつつ「一旦反映」の語感で (A)減量MVP を USER_DECISION_REQUIRED の対等選択肢に立て、epic 本体が Phase 1.5 でそのまま提示 → ユーザーが確認の意義に苛立ち。改善はこの実験定義側でなく plan-choice-gate.md 運用ルール + planner/epic-planner.md へ
- Recommendation changes: 0（2/3 executions。採用条件「3 回以上」未達のため Continue observing 継続。Phase 1.5 gate friction は Rejection Criteria の「独断スコープ縮小」ではない〔独断縮小は発生せず・ユーザー確認は機能〕ため棄却シグナルではなく、ゲート提示ロジックの改善課題として扱う）

### Observation Log

観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は git 管理外の `~/.claude/memory/experimental_observations.md` の該当実験セクションに記録する（グローバルファイルにプロジェクト固有名を載せないため）。実験定義はこのファイルが SSOT。

## Experiment: pir2-deterministic-completion-check

- Status: Active
- Started: 2026-07-04
- Scope: `.claude/skills/pir2/references/deterministic-completion-check.md`, `.claude/skills/pir2/references/verify-deterministic-check.sh`, `.claude/skills/pir2/SKILL.md`, `.claude/skills/pir2codex/**`, `.claude/agents/implementer.md`
- Owner: user
- Recommendation: Continue observing

### Hypothesis

実装 actor（implementer / Codex）の自己申告と実 git delta を純 bash で集合照合し、申告したが実体のないファイル（PHANTOM_CLAIM）を初回実装完了直後（reviewer 起動前）に決定論検出すれば、捏造の上に reviewer 5体・tester を積んで迷走するコストを入口で断てる。ゲート自体は「完了検証」ではなく「**phantom-claim floor**」（申告ファイル集合が実際に git 上で変更されたかという file-set 存在の1次元のみを検証し、内容の正しさ・substance は検証しない）である点を明確にした上で運用する。

### Implementation

- 詳細プロトコルは `deterministic-completion-check.md`（pir2 6-3 / pir2codex 6-1）を SSOT とする。
- 初回実装点（/pir2 6-1・/pir2codex 6-1a/6-1b/6-1c）のみに適用し、reviewer/tester FAIL 後の再実装には再適用しない。
- 実集合は unstaged（`git diff --name-only --ignore-submodules=dirty`）＋ staged（`git diff --cached --name-only`）＋ untracked（`git ls-files --others --exclude-standard`）の union（pre-set / post-set 両側対称。staged union は R1 是正で追加済み）。
- PHANTOM_CLAIM は hard fail（1回だけ自動再実行、2回目もダメならユーザーゲート）。UNDECLARED_CHANGE は非ブロッキング warn。
- git 検証不能な申告（リポ外パス・gitignore対象・submodule内部パス）は PHANTOM 対象外（test -f で実体なしの場合のみ warn 可視化）。
- 既知の残存限界は `deterministic-completion-check.md`「既知の残存限界（R1〜R13）」に方向つき（fail-open/fail-closed）で完全列挙済み。

### Quality Guardrails

- fail-loud のみ・自動巻き戻し（`git restore` 等）は絶対にしない。
- PHANTOM 判定は縮退運転しない（pre-set 記録漏れ時は implementer 全再実行に戻る。PHANTOM 照合のみでの簡略化はしない）。
- 偽陽性で正当な実験を殺さないよう hard fail は PHANTOM のみに限定し、UNDECLARED は warn 止まり。

### Metrics

- **(a) PHANTOM 偽陽性の実発生率**: PHANTOM_CLAIM のうち、原因分類 (c) で「真の捏造」以外（staged 系 / 申告規律 R13 / resume-stale R7 / その他環境要因）に分類されたものの比率。
- **(b) L0（スキル本体）が 6-3 の bash を実際に実行したか**: `verify-{IMPL_INDEX}-*.list` の生成有無を確認する。これは 6-3 が「誤認した L0 による幻覚実行」を防止でなく可監査化する仕組みであるため **load-bearing**（この観測が欠けると再帰的信頼の受容根拠自体が崩れる）。
- **(c) PHANTOM 発火の原因分類**: 真の捏造 / staged 系（R1・#1 是正前の旧仕様下でのみ発生しうる） / 申告規律 R13（ディレクトリ・glob・typo 申告） / resume-stale R7（中断中の外部 git 変化） / その他。原因分類なしで FP 統計を集計すると R13・resume-stale の混入で rollback トリガの閾値判定が汚染される。
- `PHANTOM_RETRY_COUNT` の分布・2回目 PHANTOM でのユーザーゲート選択（A/B/C）の内訳。

### Adoption Criteria

- 10 回以上の初回実装点通過（PHANTOM 発火の有無を問わない）が観測されている。
- 観測項目 (b) で L0 が 6-3 を実行しなかった事例が systematic に発生していない（幻覚実行の可監査性チェーンが機能している）。
- PHANTOM_CLAIM の原因分類 (c) で「真の捏造」の検出に寄与した実例が確認されている（機構が実際に価値を出した証拠）。
- ユーザーが恒久採用してよいと判断している。

### Rejection / Rollback Criteria

- **Rollback トリガ（降格条件）**: 観測窓 10 run の中で PHANTOM_CLAIM が発生し、かつその原因分類 (c) が「真の捏造」以外（staged 系 / 申告規律 R13 / resume-stale R7 / その他環境要因）に偏っている比率が 50% を超えた場合、hard-fail（PHANTOM 検出時にワークフローをブロック）から warn（記録のみで reviewer へ進行を許可）への降格を検討する。
- L0 が観測項目 (b) で体系的に 6-3 の bash を実行しない（幻覚実行）ことが複数回確認された場合、W2/W5 の hook-floor（機械的強制）を前倒しで検討する。
- 既知の残存限界（R1〜R13）のうち fail-open 群（R2/R5/R6/R11 等）が adversarial に悪用される兆候が観測された場合、content-hashing 等のより強い検証手段への切り替えを検討する。

### Evidence Summary

- Initial implementation-point executions: 10（4 は epic-A の4サブ pir2 初回実装点、2 は epic-B の T1+T2 サブタスク初回実装点＝いずれもネスト general-purpose ランナー経由、4 は **非 epic standalone /pir2 run（L0=メイン Claude 直接）の初回実装点**＝ネストを介さない直接 SKILL.md 経路〔4 件目を追加観測〕。固有名を含む詳細は `~/.claude/memory/experimental_observations.md`）
- PHANTOM_CLAIM occurrences: 0（観測範囲では検出なし）
- PHANTOM_CLAIM classified as true fabrication: 0
- PHANTOM_CLAIM classified as staged/R13/R7/other: 0
- 6-3 execution audit misses (verify-*.list missing despite claimed completion): 4（すべて epic-A の**4 サブ run** に集中。audit hit は 6（epic-B T1+T2 サブタスク + 非 epic standalone run 4 件）。原因未確定: (i) epic-A サブ run が本チェック追加 [2026-07-04 開始] より前の SKILL.md 経路を辿った / (ii) ネスト general-purpose ランナーが 6-3 を省略、のいずれか。ネスト文脈で一律に 6-3 が省略されるわけではなく、epic/オーケストレーター実装の個体差（どちらの SKILL.md 経路・プロンプト構成を辿ったか）に依存する可能性が高い。加えて **非 epic standalone run（L0=メイン直接）で audit hit が 4 件連続**＝ネストを介さない直接 SKILL.md 経路では 6-3 が一貫して明確に発火し、miss は epic-nested runner 個体差に起因する仮説((ii))を 4 件目でさらに補強。採用条件 (b) の観察に計上。★測定注意: standalone hit の証跡ファイル名が run により verify-01.md / preset・postset-impl-01.txt と揺れており、Metric(b) 記載の `verify-*.list` 固定 grep で audit を機械化すると本種の hit を誤 miss しうる＝audit 証跡ファイル名の SSOT 化が要る）
- Recommendation changes: 0（10 executions で採用条件の実行回数「10 回以上」に到達。ただし採用条件(c)「PHANTOM 真陽性（真の捏造検出）に寄与した実例」が依然 0 のため Continue observing 継続＝真の捏造が発火する run に当たるまで価値実証が未完。audit hit=6 / miss=4 で miss は epic-A のみに集中、standalone〔4/4〕・epic-B〔2/2〕では一貫して hit。次サイクル以降も「どの epic 実装がどちらの経路を辿るか」の切り分けを継続観察。epic-A 系で systematic な miss が続けば W2/W5 hook-floor の前倒し検討）

### Observation Log

観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は git 管理外の `~/.claude/memory/experimental_observations.md` の該当実験セクションに記録する（グローバルファイルにプロジェクト固有名を載せないため）。実験定義はこのファイルが SSOT。
