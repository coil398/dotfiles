# PIR² Experimental Workflow Registry

PIR² の恒久採用前の運用を追跡する実験レジストリです。実験の仮説、採用/廃止条件、
集計だけを持ちます。実際の作業経路はロード済み `worker-delegation` skill と
`implementation-delegation.md` を正とします。

runner 台帳を使った run の schema は、この PIR² skill に同梱された
`worker-observability.md` と各 `{RUN_DIR}` の v1 TSV が SSOT です。native collaboration
や Astra 直接実装には台帳を要求せず、実在する diff、担当の短い報告、focused checks、
既存の run 記録から観測します。存在しない artifact、reviewer/tester verdict、未使用
actor を実験のために作りません。

## Retro 運用

- `Status: Active` のうち、当該 run で使われた実験だけを観測します。
- 実在する plan、diff、worker report、checks、review/test report、runner 台帳を材料にし、
  runner 固有 artifact は runner job の場合だけ読みます。
- 観測に基づき `Evidence Summary` と `Recommendation` を保守的に更新します。
- recommendation は候補であり、恒久ルールへの採用・削除はユーザー判断を必要とします。

## Experiment: pir2-worker-shards-and-review-fix-shards

- Status: Active
- Started: 2026-06-22
- Scope: `.agents/skills/pir2/**`, `.codex/skills/pir2/**`
- Owner: user
- Recommendation: Continue observing

### Hypothesis

所有範囲と依存を厳密に分離できる実装を shard 化すると、変更リスクに必要な確認を
維持したまま待ち時間を短縮できる。review FAIL 後も、指摘が独立していれば同じ効果を
得られる。

### Implementation

- 小さく密結合した変更は Astra が直接実装できます。通常の独立作業は native
  collaboration の worker（Luna Max）、難所は expert/expert_max（Sol high/max）を
  初手から選べます。Terra は実測根拠のある workload-specific exception だけです。
- 初回 shard は plan の `IMPLEMENTATION_SHARDS` に排他的所有範囲、依存、統合確認が
  定義されている場合だけ、他の稼働担当を含む最大6子の空き枠で並列化します。
- review-fix shard は指摘、修正方針、所有範囲が独立している場合だけ使います。
- runner は shard ごとに artifact/provenance が必要な場合だけ選びます。
- 自動 fallback は使いません。Luna の十分な入力に対する能力不足を実測した場合は
  `luna→sol` を許可し、Terra を強制経由しません。direct Sol は `none→none` です。

### Quality Guardrails

- 書き込みファイルが shard 間で重ならない。
- 共通型、API/schema、migration、lockfile、生成物、golden、共有 config/helper を
  複数 shard が同時に変更しない。
- shard 間に順序依存がなく、未確定の命名・抽象・データ形状へ依存しない。
- Astra が統合後の実 diff と必要な focused checks を確認する。
- reviewer/tester は変更リスクに必要な観点だけを使います。OS 権限、安全、security、
  data loss、本番操作、runtime・データ整合性、必要な回帰テストは省略しませんが、
  固定人数、全観点、tester、全 artifact を一律に要求しません。
- 条件が曖昧なら、Astra 直接実装または単一 worker/expert へ直列化します。

### Metrics

- 初回 shard 数、review-fix shard 数、待ち時間
- shard 境界の衝突、重複抽象、未接続実装、手戻り
- 実行した actor/model/effort と evidence-backed transition
- 実行した focused checks と、必要な場合の reviewer/tester 結果
- reviewer/tester を使った場合の再発・loop 数
- runner を使った場合の provenance/acceptance mismatch

### Adoption Criteria

- 3回以上の shard 実行、または5回以上の shard 使用可否判断がある。
- shard 起因の競合、品質劣化、再実装増加が観測されていない。
- 選択した review/test/check の結果が単一 job より悪化していない。
- Astra の統合確認コストが並列化の利点を上回っていない。
- ユーザーが恒久採用してよいと判断している。

### Rejection Criteria

- 同一ファイル、共有契約、生成物で衝突した。
- 分割で方針がずれ、必要な review/test/check の失敗や統合修正が増えた。
- 品質が同等でも、運用複雑性が待ち時間短縮に見合わない。

### Evidence Summary

- Eligible decisions: 0
- Shard executions: 0
- Review-fix shard executions: 0
- Shard-caused regressions: 0
- Recommendation changes: 0

### Observation Log

project/run 固有の観測は git 管理外の
`~/.codex/memory/experimental_observations.md` の該当実験セクションに記録します。
実験定義はこのファイルが SSOT です。
