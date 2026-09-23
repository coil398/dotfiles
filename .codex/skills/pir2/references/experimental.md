# PIR² Experimental Workflow Registry

PIR² の恒久採用前の運用を追跡する実験レジストリです。実験の仮説、採用/廃止条件、
集計だけを持ちます。実際の作業経路は Codex Native Runtime Supplement と、共有
PIR² skill の `references/implementation-delegation.md` を正とします。

観測は実在する diff、担当の短い報告、focused checks、既存の run 記録から行います。
存在しない artifact、reviewer/tester verdict、未使用の担当を実験のために作りません。

## Retro 運用

- `Status: Active` のうち、当該 run で使われた実験だけを観測します。
- 実在する plan、diff、worker report、checks、review/test report を材料にします。
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
  collaboration の子（`[agents]` の既定 model/effort）、難所は親が起動時に
  `gpt-6-sol` の high/max を明示して初手から選べます。
- 初回 shard は plan の `IMPLEMENTATION_SHARDS` に排他的所有範囲、依存、統合確認が
  定義されている場合だけ、アクティブ設定の `max_concurrent_threads_per_session` と実行時空き枠の低い方で並列化します。完了済みを空き枠と推測しません。
- review-fix shard は指摘、修正方針、所有範囲が独立している場合だけ使います。
- 自動 fallback は使いません。十分な入力に対する既定 model の能力不足を実測した場合だけ、
  親が Sol へ切り替えます。

### Quality Guardrails

- 書き込みファイルが shard 間で重ならない。
- 共通型、API/schema、migration、lockfile、生成物、golden、共有 config/helper を
  複数 shard が同時に変更しない。
- shard 間に順序依存がなく、未確定の命名・抽象・データ形状へ依存しない。
- Astra が統合後の実 diff と必要な focused checks を確認する。
- reviewer/tester は変更リスクに必要な観点だけを使います。OS 権限、安全、security、
  data loss、本番操作、runtime・データ整合性、必要な回帰テストは省略しませんが、
  固定人数、固定した review 範囲、tester、全 artifact を一律に要求しません。
- 条件が曖昧なら、Astra 直接実装または単一担当へ直列化します。

### Metrics

- 初回 shard 数、review-fix shard 数、待ち時間
- shard 境界の衝突、重複抽象、未接続実装、手戻り
- 実行した model/effort と、実測に基づく担当変更
- 実行した focused checks と、必要な場合の reviewer/tester 結果
- reviewer/tester を使った場合の再発・loop 数

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

## Experiment: astra-medium-orchestration-hands

- Status: Active
- Started: 2026-09-06
- Scope: Astra Medium を司令塔とする通常のCodex運用、および Luna Max / Sol hands への実作業委譲
- Owner: user
- Recommendation: Continue observing

### Observation definition

- Astra のモデル条件は Medium を所与とし、High との性能比較やMedium起因の改善をこの実験から主張しない。
- 実際にAstra Mediumを使ったrunを対象とし、委譲した場合はLuna Max / Solの割当・返却を確認する。委譲しなかったrunも、直接作業の範囲と理由を観測する。設計文書や未実施のprivate運用は実績に数えない。
- 実測資料は assignment、diff、worker返却、focused checks、review/test report、既存のrun/retro出力とする。未取得のusage、費用、時間、介入は未測定のまま残し、数値を補完しない。
- モデル条件とworkflow構造・review/test構成・割当を同時に変えたrunは交絡として記録し、モデル効果へ帰属しない。
- 既存の証跡、Unity状態の排他、最終HEAD、権限境界を観測条件として維持する。新しいgate、台帳基盤、恒久採用条件はこの実験では追加しない。

### Metrics

- 品質: 欠陥・回帰・誤判定、証跡の有効性、データ保全、Unity排他、最終HEAD、権限上の問題
- 手戻り: review/test loop、引継ぎ、Astra直作業の肥大、誤指摘、再実装、再QA
- 運用負担: 完了までの実時間とcritical path、待ち時間、総トークン、費用、人間介入

### Observation handling

Retro はcallerが明示した既存のrun/retro出力へ、実在する観測だけを追記する。未指定の保存先は推測せず、今回未実施のprivate Astra運用について成功・改善・数値を作成しない。開始時のRecommendationはContinue observingとし、実測に応じて判断材料を更新する。Mediumの既定はユーザー裁定として維持する。
