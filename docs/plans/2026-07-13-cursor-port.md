# Cursor port phase-1→3 実装記録

_作成: 2026-07-13 | 更新: 2026-07-15 | ステータス: 第3波完了（フル /pir2 実タスク smoke は任意フォロー）_

## 目標

`docs/brainstorm/2026-07-13-cursor-port.md` に沿い Cursor overlay を移植。第1波是正 → 第2波（オーケストレーション）→ 第3波（欠けスキル・shared 昇格・Codex 橋・契約テスト）まで実施。

## 実装計画

- [x] ステップ 1: `sync-cursor.sh` — Rules A・atomic・MCP type・`--check`
- [x] ステップ 2: `seed-cursor-overlay.sh` — force 廃止・モデル非ハードコード・最小スライス
- [x] ステップ 3: `.cursor` overlay 縮退 + 再 sync（第1波）
- [x] ステップ 4: `link.sh` Cursor リンク安全化 + SPEC/AGENTS 更新
- [x] ステップ 5: 第1波スモーク
- [x] ステップ 6: 第2波 agents/skills 拡張 seed
- [x] ステップ 7: オーケストレーション系 Cursor 注記 + vendor model ピン除去
- [x] ステップ 8: `/pir2` 相当の手動 runtime smoke（**部分 PASS**: explore→plan→noop implement。フル implement は未）
- [x] ステップ 9: 全体レビュー FAIL の Critical/High remediation
- [x] ステップ 10: 第3波 — 欠けスキル seed（`ai-*` / `unity` / `codex` / `pir2codex`）+ `codex-runner`
- [x] ステップ 11: `deepthink` / `research` / `epic` を `.agents/skills` へ昇格
- [x] ステップ 12: `etc/test-cursor-contracts.sh` 追加・全パス
- [x] ステップ 13: epic Cursor overlay 再 seed（`--codex` case 破損修正）+ GNU sed brace 修正

## 成果物サマリ

| 種別 | 内容 |
|---|---|
| agents (18) | explorer … thinker + **codex-runner** |
| skills (26) | chat … check-updates + **pir2codex / ai-* / unity / codex** |
| shared | `.agents/skills/{deepthink,research,epic,codex}`（codex は CLI+codex-runner SSOT） |
| generated | `.cursor/rules/shared-agents.mdc`（要約 A）, `.cursor/mcp.json` |
| tests | `etc/test-cursor-contracts.sh`（11 assertions） |
| home | `~/.cursor/{agents,skills/*,rules,mcp.json}` 個別 symlink |

## 設計詳細

設計 SSOT: `docs/brainstorm/2026-07-13-cursor-port.md`  
RUN_DIR (移植作業): `.ai-pir-runs/20260713-162537-cursor-port`  
RUN_DIR (pir2 smoke): `~/.ai-pir-runs/-home-coil398-dotfiles/20260713-170047-pir2-smoke`  
レビュー: `docs/reviews/20260713-cursor-port-review.md`

## 実装ログ

### 第1波
- Rules=A、atomic、MCP url-only、seed force 廃止、スライス最小、link 安全化

### 第2波
- seed 拡張 + `.claude/skills` フォールバック
- オーケストレーション SKILL に Task / VERDICT / TeamCreate 非対応注記
- vendor model ピン除去
- スキル内 `~/.codex/projects` → `~/.cursor/projects` 等へ置換

### 第3波（2026-07-15）
- seed リストに Codex 橋・submodule 系を追加。フルツリー copy（`SKILL.md` 以外も）
- `deepthink` / `research` / `epic` を Claude → `.agents/skills`（パスを `~/.agents/skills` / `~/.codex/projects` へ）
- shared `/codex` を MCP 版から CLI + `codex-runner` に更新（`.codex/skills/codex` も追随）
- GNU sed の `\$\{HOME\}` を `\$[{]HOME[}]` に修正（adapt が常時失敗しうるバグ）
- epic overlay 削除→再 seed（`case` / `argument-hint` 破損を解消）
- hygiene: Codex 橋のみ gpt-5 言及を許可
- `etc/test-cursor-contracts.sh` — 11 PASS

### Runtime smoke（エージェント実施 2026-07-13）
- Task `explorer`: agents 17 / skills 19、Rules=A、MCP OK。初期指摘: pir2 等に `.codex` パス残存 → 修正済み
- Task `reviewer` (contracts): **PASS**
- Task `planner` (pir2 smoke stub): 5 step no-op プラン
- Task `reviewer` (pir2 loop): **PASS**（explore→plan→noop implement、PROJECT_MEMORY_DIR は `~/.cursor/projects`）
- TeamCreate / Agent Teams: 未使用（設計どおりスキップ）
- **範囲**: フル `/pir2`（実 implement）は未保証。部分 smoke のみ完了

### レビュー FAIL remediation（2026-07-13）
- リポ内 `.codex-runtime/` 削除（正本 `~/.codex`）
- seed の破壊的 path rewrite 廃止 + hygiene guard
- Agent / Opus·Sonnet / gpt ピン / epic パス / references を `.cursor` 基準へ一掃
- `AGENTS.md` / SPEC に Cursor skill precedence を契約化
- brainstorm バナー短縮

## 残課題

- 実タスクでのフル `/pir2`（implement あり）は任意の別タスクで
- OpenCode native overlay 化・Codex skills スナップショット方針・ドリフト検知（runtime 横断）
