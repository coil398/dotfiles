# PIR2 Experimental Workflow Registry

PIR2 のうち、まだ恒久採用と判断していない運用を追跡するための実験レジストリ。

retrospector は `/pir2` および `/retro` のたびにこのファイルを読み、該当する run があれば観測を追記・更新する。効果がはっきりするまでは、このファイルを採用可否判断の SSOT とする。

## 共通 actor 観測との責務境界

実 run の actor attempt、Sol acceptance、reviewer/tester verdict の schema と run 内 SSOT は `${PROJECT_ROOT}/.codex/skills/pir2/references/worker-observability.md` と、各 `{RUN_DIR}` の `worker-observations-v1.tsv`、`sol-acceptance-v1.tsv`、`independent-verdicts-v1.tsv` である。このレジストリは per-run 行を複製せず、実験の仮説・採用/廃止条件・experiment-level 集計だけを持つ。actor は `luna|terra|sol`、実測 model/effort は `gpt-5.6-luna:max`、`gpt-5.6-terra:high|max`、`gpt-5.6-sol:high|max` として観測する。retrospector は観測 TSV と versioned Markdown を材料にしてこのファイルの実験判断を更新するが、actor schema や Sol acceptance の verdict を再定義しない。

## Retro 運用

- `Status: Active` の実験を毎回確認する。
- `RUN_DIR` がある場合は `plan.md`、`implementation-*.md`、`sol-acceptance-*.md`、`worker-observations-v1.tsv`、`sol-acceptance-v1.tsv`、`independent-verdicts-v1.tsv`、`review-*.md`、`test-*.md`、`pir_skill_log.md` を材料にする。
- 該当 run で実験が使われていなければ、原則として追記不要。ただし手動 `/retro` で直近ログに実験利用が見つかった場合は観測してよい。
- 観測は `Observation Log` に 1 件ずつ追記する。
- `Evidence Summary` は、観測ログに基づき保守的に更新する。
- 採用条件または廃止条件を満たしたら `Recommendation` を更新し、振り返りレポートにも明記する。
- `Recommendation` は採用/廃止の候補であり、実際に恒久ルールへ昇格・削除するにはユーザー判断を必要とする。

## Experiment: pir2-worker-shards-and-review-fix-shards

- Status: Active
- Started: 2026-06-22
- Scope: `.agents/skills/pir2/**`, `.codex/skills/pir2/**`
- Owner: user
- Recommendation: Continue observing

### Hypothesis

厳密な分離ゲートを満たす場合に限り、初回実装を複数 worker shard に分けると、review/test 品質を落とさずに待ち時間を短縮できる。

reviewer FAIL 後の修正は指摘箇所が明確なため、初回実装よりも積極的に複数 worker job へ分けられる可能性が高い。

### Implementation

- 通常の実装は `worker-delegation` とし、Luna Max worker を既定にする。Sol orchestrator は対象リポジトリを変更しない。
- 初回の複数 worker は `IMPLEMENTATION_SHARDS` を明示した場合のみ許可し、各 shard を独立した `worker-delegation` job として起動する。
- 初回 shard は最大 3 体まで。
- reviewer FAIL 後は、失敗 reviewer レポートから Sol orchestrator が `REVIEW_FIX_SHARDS` を組み立ててよい。各修正 job は actor ladder の Luna Max から開始する。
- review-fix shard は最大 5 体まで。
- tester FAIL 後は原則として単一の worker-delegation job に戻す。
- 詳細ゲートは `implementation-delegation.md` を参照する。

### Quality Guardrails

- shard 間で許可ファイル集合が重ならない。
- 共通型、API schema、migration、lockfile、生成物、golden、共有 config、共通 helper を複数 shard が触らない。
- shard 間に順序依存がない。
- 命名、抽象、データ形状が別 shard の未確定実装に依存しない。
- 全 shard 完了後に Sol orchestrator が read-only で統合確認し、単一 reviewer/tester ループで全体確認する。
- 条件が曖昧なら単一の `worker-delegation` job を Luna Max から起動する。Terra High は Luna の capability/local-reasoning insufficiency を実測した場合だけ、Terra Max は許可された複雑性・リスク証拠がある場合だけ一度使う。Terra の測定済み不足後だけ Sol High worker、highest-complexity/high-risk evidence または documented Sol High insufficiency がある場合だけ Sol Max worker を一度使う。全 attempt は `automatic_fallback=no` とする。

### Metrics

- actor attempt 数（`luna|terra|sol`）
- actual model/effort（Terra High/Max、Sol High/Max の別集計）
- capability/local-reasoning の evidence-backed escalation 数
- `automatic_fallback=no` の遵守数
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
- reviewer/tester ループ数が単一 worker job の通常運用より悪化していない。
- Sol orchestrator の read-only 統合確認コストが、並列化で得た利点を上回っていない。
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

観測データ（project / run 等プロジェクト固有名を含む実 run の観測）は git 管理外の `~/.codex/memory/experimental_observations.md` の該当実験セクションに記録する（グローバルファイルにプロジェクト固有名を載せないため）。実験定義はこのファイルが SSOT。
