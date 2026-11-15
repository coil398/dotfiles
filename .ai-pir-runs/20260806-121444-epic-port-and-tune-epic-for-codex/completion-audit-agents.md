## Completion Audit: .codex/agents and config sanity

### Scope
- `.codex/agents/*.toml`
- `.codex/config.base.toml`
- `.codex/config.toml`

### Findings

1. `Agent` ツール前提が複数の agent 指示に残っており、現行の collaboration API と不整合です。
- `implementer.toml:17` - `Agent` ツールで explorer をネスト起動してよい、という記述があるが、現在の実装環境で使えるのは `spawn_agent` / `followup_task` / `send_message` / `list_agents` であり、`Agent` という呼称は存在しない。
- `planner.toml:6` - 同様に `Agent` ツールで explorer を起動できる前提になっている。
- `reviewer.toml:12` - 同様に `Agent` ツールで explorer をネスト起動できる前提になっている。
- `reviewer.toml:20` - 「`tools` に `Agent` を持つ」という説明も同じ旧前提を繰り返している。
- `explorer.toml:6` - 自身は `Agent` を持たない設計と書いてあり、上記の旧前提と用語体系が揺れている。
- 影響: このままだと、実際のオーケストレーション実装とロール記述がずれて、呼び出し側が誤った API 名で実装するリスクがあります。

2. `implementer` の shard / actor 記述は現行の役割分担としては一応整合していますが、厳密な単一責務化は弱いです。
- `implementer.toml:10-12` - `IMPLEMENTATION_ACTOR` に `implementer-subagent` / `implementer-shards` / `main` を持たせ、`SHARD_ID` と許可/禁止ファイル集合まで定義している。
- これは shard 実験としては合理的だが、本文全体は `Agent` 前提のネスト探索まで含むため、worker 側に制御フローが寄りやすい。
- 判定: 直ちに修正必須ではないが、今後は `worker` の責務と探索責務の境界をさらに明文化した方が安全です。

3. モデル設定と TOML 構文は問題ありません。
- `config.base.toml:6-13` と `config.toml:9-16` - `sandbox_mode = "workspace-write"`、`model = "gpt-5.6-terra"`、`model_reasoning_effort = "medium"`、`approvals_reviewer = "auto_review"` は両ファイルで一致している。
- `config.base.toml:31-35` と `config.toml:34-38` - `gpt-5-codex -> gpt-5.2-codex` の migration と `gpt-5.5` の NUX 設定も整合している。
- `python3 tomllib` で `config.base.toml` と `config.toml` の両方をパースし、構文エラーなしを確認済み。

4. Claude 残滓は主に provenance コメントで、致命的な混入ではありません。
- `implementer.toml:1`, `planner.toml:1`, `reviewer.toml:1`, `explorer.toml:1`, `tester.toml:1`, `tech-validator.toml:1`, `synthesizer.toml:1` などに `.claude/agents/...` から同期された旨のコメントがある。
- これは生成元の説明としては許容範囲ですが、運用文脈では「Codex native overlay」との二重表現があるため、対外向け説明には残さない方がよいです。

### TOML / Configuration validity
- `config.base.toml`: parse OK
- `config.toml`: parse OK
- 主要 model pin: `gpt-5.6-terra`, `gpt-5.5`, `gpt-5.4-mini` の組み合わせは現ファイル内で一貫

### Recommendation
- 最優先で `Agent` という旧呼称を、現行の collaboration API 名に置換するか、少なくとも「Codex collaboration API（spawn_agent 等）」という表現へ統一するべきです。
- その上で `implementer` / `planner` / `reviewer` の探索起動責務と、実装責務の境界をもう一段だけ明確にすると、Sol/Luna 役割分担の誤解が減ります。
