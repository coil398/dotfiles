# Remaining follow-up 実装記録（2026-07-15）

_ステータス: 完了（blockers なし）_

## タスク

前回列挙した残件を実施する:

1. Codex 欠落 agents/skills を埋める
2. shared rule 片寄せ drift checker
3. OpenCode / Codex skills 方針決定
4. 実 implement 付きスモーク（残件そのものを実装タスクとして）

## Explore → Plan → Implement（短縮 PIR²）

### Explore
- Codex agents/skills は native overlay。通常 sync は上書きしない
- 不足 agents: deliberator / epic-planner / gate / hypothesizer / synthesizer / thinker（codex-runner は Codex 上不要）
- 不足 skills: deepthink / research / epic / unity-mcp-skill
- OpenCode agents は `.claude` から毎回生成

### Plan
1. `etc/seed-codex-overlay.sh`（missing-only）
2. `etc/check-shared-drift.sh` + `etc/test-codex-contracts.sh`
3. SPEC で方針固定（OpenCode=generated 維持、Codex skills=full snapshot + seed）
4. 契約テストで PASS 確認、`link.sh` で `~/.codex` 反映

### Implement（実施済み）
- `etc/seed-codex-overlay.sh` / `etc/check-shared-drift.sh` / `etc/test-codex-contracts.sh`
- `.codex/agents/{deliberator,epic-planner,gate,hypothesizer,synthesizer,thinker}.toml`
- `.codex/skills/{deepthink,research,epic,unity-mcp-skill}/`
- `AI-WORKFLOW-SPEC.md` Open items 解消
- review High（macOS `find -printf` 偽クリーン）→ portable `find|basename` に修正

### Test
```text
bash etc/test-codex-contracts.sh   # 19 PASS
bash etc/test-cursor-contracts.sh  # 11 PASS
bash etc/check-shared-drift.sh     # 60 PASS
```

### Review
- correctness: 初回 FAIL（find -printf）→ 修正後、契約テスト緑

## 方針決定（残 Open の決着）

| 論点 | 決定 |
|---|---|
| OpenCode native overlay | **しない**（現状の `.claude`→生成を維持） |
| Codex skills | **フルスナップショット overlay 維持**。欠落は seed-missing |
| Drift checker | **実装済み** `etc/check-shared-drift.sh` |
| フル /pir2 | 本件実装を real implement スモークとする。別プロダクト repo での soak は任意 |

## VERDICT

**PASS** — 列挙残件は方針決定・実装・契約テストまで完了。
