# Cursor 向け AI ワークフロー移植 設計ドキュメント

_作成: 2026-07-13_

## 目標

Claude / Codex 向けに整備済みのコンセプト・手順・プロンプトを、Cursor ランタイム向けに**再実装**する。バイト一致の完全互換は目指さない。既存の **shared core + native overlay**（`AI-WORKFLOW-SPEC.md`）に Cursor を第4 runtime として載せる。

完了の定義を分ける:

- **第1波完了** = Cursor 日常運用が可能（Rules / MCP / 主要 agents / 限定スキル）
- **第2波** = PIR² / deepthink / epic / research 相当のオーケストレーション再実装（「移植しきり」の残り）

## 採用アプローチ: B — shared core + `sync-cursor` adapter

Codex 現状と同型。Rules / MCP など機械変換しやすいものだけ生成。agents / skills は Cursor-native overlay（初回 seed 後は手編集。日常 sync で上書きしない）。

却下:

- A（手書きのみ）— SSOT が割れ、dotfiles 一元管理と弱い
- C（毎回フルミラー）— Codex がやめた旧パス。再実装が潰れる

## 前提・運用合意

- guidance SSOT for Cursor = **`AGENTS.md`**（`CLAUDE.md` は読まない・sync 入力にしない）
- 日常モデル: reasoning（旧 Opus 枠）→ **Grok**、coding（旧 Sonnet 枠）→ **Composer**。難所のみ API 枠。定義にモデル名をハードコードしない（運用で調整）
- 逆同期（Cursor → Claude）なし
- agents seed 元: `.claude/agents` / skills seed 元: `.agents/skills`
- Codex 第二意見（gpt-5.6-sol / xhigh, 2026-07-13）を反映済み

## アーキテクチャ

### 所有権マップ（Cursor 追加分）

| 領域 | 役割 | 種別 |
|---|---|---|
| `AGENTS.md` / `.agents/skills/**` / `mcp-servers.json` | 横断意図・共有スキル核・MCP | Shared core |
| `.cursor/agents/**` | Cursor 用エージェントプロンプト | Native overlay |
| `.cursor/skills/**` | Cursor 用スキル（手順の再実装） | Native overlay |
| `.cursor/rules/**` | 生成 Rules | Generated adapter |
| `.cursor/mcp.json` | 生成 MCP | Generated adapter |
| `~/.cursor/skills-cursor/**` | Cursor 公式 | **触らない** |

### リンク方針

`~/.cursor` **全体 symlink 禁止**（Codex の `~/.codex` 方針と同型）。`etc/link.sh` は `rules` / `agents` / `skills`（必要なら MCP）を個別リンク。

### 同期方向

```
AGENTS.md / mcp-servers.json / (初回のみ seed 元)
        │
        ▼
  etc/sync-cursor.sh     # rules + MCP のみ
  SYNC_CURSOR_SEED=1 …   # 欠落分のみ overlay 種まき（通常 sync と分離）
        │
        ▼
  etc/link.sh → ~/.cursor/{rules,agents,skills,…}
```

## コンポーネント設計

### `etc/sync-cursor.sh`（通常）

**やってよい:**

- `.cursor/rules/` の生成（下記「二重ロード = A」）
- `.cursor/mcp.json` の生成（`claudeCodeOnly` / `openCodeOnly` / `codexOnly` を除外。必要なら `cursorOnly` 追加）
- temp → 構文検証 → atomic rename。内容不変なら書き換えない
- 推奨: `--check`（生成差分・MCP schema・native overlay 非変更）

**やってはいけない:**

- `.cursor/agents/**` / `.cursor/skills/**` の日常上書き
- seed を通常 sync の副作用に混ぜる
- `~/.cursor/skills-cursor/**` への介入

### Seed（`SYNC_CURSOR_SEED=1` または専用 `seed-cursor-overlay.sh`）

- 欠落した agent ファイル / skill ディレクトリのみ作成
- **既存は上書きしない**（force 経路は持たない／廃止）
- 既存ディレクトリ内部の「足りないファイル補完」もしない（丸ごと既存なら触らない）

### 二重ロード回避（決定: **A**）

dotfiles を開くと root `AGENTS.md` と user Rules が二重になり得る。

**採用 A（要約＋参照）:**

- Rule 本文は portable な最小ルール + 「詳細 SSOT はリポの `AGENTS.md`」
- `AGENTS.md` 全文コピー禁止
- `@AGENTS.md` での再展開禁止
- 「project 優先」と書くだけでは Codex の `AGENTS.override.md` 相当の precedence にはならない点を認識する

### MCP

- 出力先は実装時に Cursor 現行仕様で確定（user `~/.cursor/mcp.json` と project `.cursor/mcp.json`）
- remote は Cursor が受理する形へ変換（`type: "remote"` のまま落とすと CLI が設定全体を無効化する報告あり → `{url}` または `type: "http"` 等へ）
- global symlink と project 実体の二重起動に注意（dotfiles 作業時）

### エージェント（第1波・絞り込み）

最小セット（Codex 推奨を採用）:

| Agent | 役割ラベル | 運用既定 |
|---|---|---|
| explorer | coding | Composer |
| implementer | coding | Composer |
| reviewer | coding | Composer |

追加は検証後に段階投入可: planner（reasoning/Grok）, tester, tech-validator, refactor-advisor, sentinel-iac, ui-ux-reviewer

第2波以降: deliberator, gate, synthesizer, hypothesizer, epic-planner, retrospector, meta-retrospector, thinker, codex-runner

形式: `.cursor/agents/*.md`（Cursor subagent）。Claude の `Agent` ツール語彙 → Task / subagent。モデル名は書かない。

### スキル（第1波・絞り込み）

最初は **subagent を起動しない純粋 skill 1〜2**（例: `chat`、または薄い `reviewer` ラッパ）で precedence を実測してから増やす。

第1波後半の候補: brainstorm, walkthrough, review-pr, refactor-advisor, tester, sentinel-review（いずれも Cursor 語彙へ手直し前提）

第2波: pir2, pir2async, pir2codex, epic, deepthink, research, debug, ir, writing-plan, retro 等（マルチエージェント／重いオーケストレーション）

### `link.sh`

- sync-cursor を呼んでから個別リンク
- 通常ファイル／ディレクトリを拒否し、dotfiles 所有 symlink だけ更新
- Windows 向け破壊的 `rm -rf` は不可

### ドキュメント

- `AI-WORKFLOW-SPEC.md` に Cursor ownership / sync 契約 / review 分類を追加
- `AGENTS.md` に Cursor を対応 runtime として追記可
- `CLAUDE.md` への追記は必須でない（Claude 利用者向け地図が必要なら一行）

## データフロー

### 初回

1. `SYNC_CURSOR_SEED=1` で欠落 overlay のみ種まき
2. overlay を Cursor 語彙に手直し
3. `sync-cursor.sh`（Rules=A 方式 + MCP）
4. `link.sh`

### 日常（shared 変更）

`AGENTS.md` / `mcp-servers.json` 編集 → `sync-cursor.sh` → rules/MCP のみ更新

### 日常（Cursor 手順変更）

`.cursor/agents` / `.cursor/skills` を直接編集（sync 不要）。横断意図だけ `AGENTS.md` / `.agents/skills` へ promote

### 実行（第1波）

メイン Agent が Rules（要約）+ Skill を読み、必要なら Task で subagent 起動。制御所有はメインに集約。

## テスト戦略

### 機械

- sync 冪等（連続2回で意図しない差分なし）
- overlay 非破壊（手編集が通常 sync で残る）
- seed 安全（既存上書きなし）
- MCP フィルタ（claudeCodeOnly 等が出ない）
- `skills-cursor` 非改変
- link 冪等・`~/.cursor` が丸ごと symlink でないこと

### 手動スモーク

1. Rules（A）が効き、dotfiles で AGENTS 全文二重になっていないこと
2. 限定 skill が拾える
3. explorer / implementer / reviewer が Task で動く（Claude 方言が残っていない）
4. モデル名ハードコードがない
5. MCP が IDE/CLI 両方で壊れていない

### 第1波受け入れ

- [x] sync / link / seed 契約テスト通過（`etc/test-cursor-contracts.sh`、2026-07-15）
- [x] Rules が A 方式
- [x] 最小 agents + 1〜2 skills が実測済み
- [x] `AI-WORKFLOW-SPEC.md` に Cursor 追記
- [x] Codex 指摘のリリースブロッカー（全文 Rules、force seed、MCP type、過剰 seed）を解消または明示チケット化

### 第3波（2026-07-15）

- [x] 欠けスキル seed（`ai-*` / `unity-mcp-skill` / `codex` / `pir2codex`）+ `codex-runner`
- [x] `deepthink` / `research` / `epic` の `.agents/skills` 昇格
- [x] `/codex` shared SSOT を CLI + `codex-runner` に統一
- [x] 契約テスト追加

## Codex 第二意見の反映メモ

出典: `codex exec` gpt-5.6-sol / xhigh（session 019f5a38-…, 2026-07-13）

- 方針骨格は Codex ガバナンスと整合
- 二重ロード **A 推奨** → 本設計で採用
- 第1スライス対象数を削減 → 本設計で採用
- sync/seed 分離・atomic・`--check`・MCP type 変換・link 安全化 → 実装要件に採用
- リスク: 二重発見（`.agents/skills` vs `.cursor/skills`）、機械変換の意味欠落、静かな失敗

## 現行 WIP との差分（実装前に要是正）

調査時点で既に存在:

- `etc/sync-cursor.sh` / `etc/seed-cursor-overlay.sh`
- `.cursor/rules/shared-agents.mdc`（**AGENTS.md 全文 + alwaysApply** → 決定 A に違反）
- `.cursor/mcp.json`
- 多数の `.cursor/agents/**` / `.cursor/skills/**`（第1波としては過大）

実装フェーズでは「新規ゼロから」ではなく、**WIP を本設計に合わせて縮退・修正**する。

## 保留事項・リスク

- `.agents/skills` と `.cursor/skills` の発見 precedence がランタイム未保証 → 実測してから同名を増やさない
- model tier（reasoning/coding）の解決責任者を overlay 注釈か短い運用メモに置く
- MCP global/project 二重
- Cursor IDE と CLI で MCP/Rules 挙動差
- エージェント実行時のワークスペース外書き込みは Cursor「Run Everything」等に依存（本設計の範囲外だが運用前提）

## 次のステップ

`/writing-plan` で実装プラン作成（WIP 是正: Rules を A 化 → seed/sync 契約修正 → スライス縮退 → SPEC 更新 → スモーク）。
