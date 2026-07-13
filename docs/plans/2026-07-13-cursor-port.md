# Cursor port phase-1→2 実装記録

_作成: 2026-07-13 | ステータス: 第2波完了（runtime smoke は未）_

## 目標

`docs/brainstorm/2026-07-13-cursor-port.md` に沿い Cursor overlay を移植。第1波是正のあと第2波（agents/skills 拡張 + オーケストレーション再実装）まで実施。

## 実装計画

- [x] ステップ 1: `sync-cursor.sh` — Rules A・atomic・MCP type・`--check`
- [x] ステップ 2: `seed-cursor-overlay.sh` — force 廃止・モデル非ハードコード・最小スライス
- [x] ステップ 3: `.cursor` overlay 縮退 + 再 sync（第1波）
- [x] ステップ 4: `link.sh` Cursor リンク安全化 + SPEC/AGENTS 更新
- [x] ステップ 5: 第1波スモーク
- [x] ステップ 6: 第2波 agents/skills 拡張 seed
- [x] ステップ 7: オーケストレーション系 Cursor 注記 + vendor model ピン除去
- [x] ステップ 8: `/pir2` 相当の手動 runtime smoke（本エージェントで実施）

## 成果物サマリ

| 種別 | 内容 |
|---|---|
| agents (17) | explorer … thinker（codex-runner 除外） |
| skills (19) | chat … check-updates（pir2/deepthink/epic/research 含む） |
| generated | `.cursor/rules/shared-agents.mdc`（要約 A）, `.cursor/mcp.json` |
| home | `~/.cursor/{agents,skills/*,rules,mcp.json}` 個別 symlink |

## 設計詳細

設計 SSOT: `docs/brainstorm/2026-07-13-cursor-port.md`  
RUN_DIR (移植作業): `.ai-pir-runs/20260713-162537-cursor-port`  
RUN_DIR (pir2 smoke): `~/.ai-pir-runs/-home-coil398-dotfiles/20260713-170047-pir2-smoke`

## 実装ログ

### 第1波
- Rules=A、atomic、MCP url-only、seed force 廃止、スライス最小、link 安全化

### 第2波
- seed 拡張 + `.claude/skills` フォールバック
- オーケストレーション SKILL に Task / VERDICT / TeamCreate 非対応注記
- vendor model ピン除去
- スキル内 `~/.codex/projects` → `~/.cursor/projects` 等へ置換

### Runtime smoke（エージェント実施 2026-07-13）
- Task `explorer`: agents 17 / skills 19、Rules=A、MCP OK。初期指摘: pir2 等に `.codex` パス残存 → 修正済み
- Task `reviewer` (contracts): **PASS**
- Task `planner` (pir2 smoke stub): 5 step no-op プラン
- Task `reviewer` (pir2 loop): **PASS**（explore→plan→noop implement、PROJECT_MEMORY_DIR は `~/.cursor/projects`）
- TeamCreate / Agent Teams: 未使用（設計どおりスキップ）

## 残課題

- deepthink / research / epic の shared core（`.agents/skills`）昇格可否
- `.agents/skills` vs `.cursor/skills` の discovery precedence のより厳密な実測
- 実タスクでのフル `/pir2`（implement あり）は任意の別タスクで
