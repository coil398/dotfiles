## 追加探索レポート: Codex 5.6 family model routing / Luna escalation

### 目的
承認後の追加要件に基づき、Codex 版 epic を Claude 由来の general-purpose runner 思想から、Sol 司令塔 + Luna/Terra/Sol 段階昇格の責任分離へ再設計するための分割材料を確認した。

### 確認した資産
- `.codex/skills/luna-max-worker/SKILL.md`
- `.codex/skills/luna-max-worker/scripts/run-luna-max.sh`
- `.codex/skills/luna-max-worker/agents/openai.yaml`
- `.codex/skills/codex/SKILL.md`
- `.codex/skills/epic/SKILL.md`
- `.codex/config.base.toml`
- `.codex/config.toml`

### 確認事実
- `luna-max-worker` は、Sol が判断・計画・完了要件・最終判定を持ち、Luna Max が具体作業を実行する責任境界を既に定義している。
- 同 skill は Luna の自己申告を合否根拠にせず、Sol が `git status`、差分、requirements 対応の実測で PASS/FAIL を決める設計になっている。
- `run-luna-max.sh` は `codex exec -m gpt-5.6-luna -c model_reasoning_effort="max"` 固定で、別 model / effort へ fallback しない。
- `luna-max-worker` は品質レビューをしないと明記しており、品質保証は別系統の `reviewer` に委ねる前提である。
- `.codex/skills/codex/SKILL.md` には GPT-5.6 系の model/effort 表があり、`gpt-5.6-sol` と `gpt-5.6-terra` は `ultra` まで、`gpt-5.6-luna` は `max` まで対応するとされている。
- `.codex/config.base.toml` と `.codex/config.toml` の既定 model は `gpt-5.6-terra`、`agents.max_depth = 1`。したがって epic が深い subagent ネストを前提にしない方向は既に進行中 T1 の差分と整合する。
- 進行中の `.codex/skills/epic/SKILL.md` 変更は、`--codex` / `pir2codex` / 固定 `gpt-5.5` / Claude 由来の 3 階層説明を削り、Codex native orchestration・main fallback・`agent_type="default"` 方向に寄せている。ただし追加要件の Sol/Luna/Terra/Sol 段階昇格は未反映に見える。

### 分割に効く境界
- epic 本体のオーケストレーション契約: `.codex/skills/epic/**`
- Luna 実行ランナー / 昇格 policy: `.codex/skills/luna-max-worker/**`、必要なら新規 Codex worker skill/runner
- epic-planner の分割出力契約: `.codex/agents/epic-planner.toml`
- 品質レビュー独立性・観測仕様: `.codex/skills/pir2/references/**`、`docs/epic-observation-checklist.md`
- sync/config/contract: `etc/*codex*`, `.codex/config.base.toml`, `AI-WORKFLOW-SPEC.md`

### 主要リスク
- Luna runner 側で自動 fallback を実装すると、既存 `luna-max-worker` の「別 model や effort へフォールバックしない」という安全規則と衝突する。追加要件は「Luna 自身の自動 fallback」ではなく「Sol 管理の明示的 escalation policy」と読むべき。
- Sol が要件適合を実測する契約と reviewer 品質評価を混ぜると、Luna worker の責任境界が曖昧になる。DAG では model routing と review/observability を分ける必要がある。
- T1 が既に `.codex/skills/epic/**` を編集中なので、同じファイルを触る後続タスクは T1 完了後に直列化する。

### EXPLORATION_NEEDED
なし。
