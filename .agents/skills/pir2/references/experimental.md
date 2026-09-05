# PIR2 Experimental Workflow Registry

PIR2 のうち、まだ恒久採用と判断していない運用を追跡するための実験レジストリ。

このファイルは、親またはユーザーが実験の観測を明示的に求めた場合だけ読み、該当する実在 run があるときに観測を追記・更新する。実験の採否は実測と親またはユーザーの判断で決める。

以下の実験固有の担当名、上限、指標は観測対象であり、通常 workflow の既定、必須人数、完了条件ではない。

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
- Scope: 親またはユーザーが明示した実在の skill package 範囲
- Owner: user
- Recommendation: Continue observing

### Hypothesis

厳密な分離ゲートを満たす場合に限り、初回実装を複数 implementer shard に分けると、review/test 品質を落とさずに待ち時間を短縮できる。

reviewer FAIL 後の修正は指摘箇所が明確なため、初回実装よりも積極的に複数 implementer へ分けられる可能性が高い。

### Implementation

- 通常の実装は、親が所有範囲とリスクに応じて直接行うか、runtime の実装担当へ委譲する。
- 複数 shard は、親が計画に所有範囲と独立性を明示し、共有状態に競合がない場合だけ許可する。
- reviewer FAIL 後の修正 shard も、指摘の独立性、容量、統合コストを親が確認して選ぶ。
- tester FAIL 後は、親が原因と所有範囲を再確認して実装経路を選び直す。
- 詳細ゲートは `implementation-delegation.md` を参照する。

### Quality Guardrails

- shard 間で許可ファイル集合が重ならない。
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、共通 helper を複数 shard が触らない。
- shard 間に順序依存がない。
- 命名、抽象、データ形状が別 shard の未確定実装に依存しない。
- 全 shard 完了後に親が統合確認し、変更リスクに応じた reviewer/tester で全体を確認する。
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

- 複数回の shard 実行または使用可否判断が蓄積されている。
- shard が原因の競合、品質劣化、再実装増加が観測されていない。
- reviewer/tester ループ数が単一 implementer の通常運用より悪化していない。
- main/primary agentの統合確認コストが、並列化で得た利点を上回っていない。
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

観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は、親またはユーザーが選んだ実在の保存先に記録する。保存先を推測せず、実験定義はこのファイルを参照する。
