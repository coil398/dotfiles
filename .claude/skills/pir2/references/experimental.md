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

- 2026-06-22: Claude 版実験を作成。`.claude/skills/pir2/` に shard 実行プロトコル（`implementation-delegation.md`、SKILL.md ステップ6/7-4/8-2 分岐）と planner/implementer の shard 対応を移植。まだ実運用での効果観測はない。
- 2026-06-23: project=<project-A>, run=<run-id>, actor=（automata 独自プロトコル＝experimental.md Scope `.claude/skills/pir2/**` 外）, initial_shards=N/A, review_fix_shards=N/A, verdict=PASS, inner=1, outer=0, outcome=対象外, note=automata の本文直接返却方式 run（`~/.ai-pir-runs/` 不使用・グローバル pir2 SKILL.md 非経由）のため shard 実験の eligibility 計装対象外。単一 implementer×3（初回実装→reviewer FAIL 修正→refactor 適用）を順次起動して完結。INNER_LOOP=1 の原因はカウント整合 FAIL で shard 分割可否とは無関係。

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

- 2026-06-23: 実験を作成。Claude Code v2.1.172 ネスト起動解禁を受け、planner/implementer/reviewer の `tools` に `Agent` 追加・能動探索手順・EXPLORATION_NEEDED ハイブリッド化を実装（コミット d37c3ac）。まだ実運用での効果観測はない。
