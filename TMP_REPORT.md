# OpenCode 関連 md 監査レポート

- 日付: 2026-08-21
- 対象: dotfiles リポジトリの OpenCode 開発体験に関わる markdown 全般

## 1. 洗い出し結果

| ファイル群 | 件数 | 役割 |
|---|---|---|
| `~/.config/opencode/AGENTS.md` | 1 | 生成物（`AGENTS.md` 全文 + sync script FOOTER の補足ルール） |
| `~/.config/opencode/agents/*.md` | 18 | `.claude/agents/*.md` から変換生成 |
| `etc/sync-opencode.sh` 内 FOOTER | — | **OpenCode 固有知識の実質 SSOT**（生成物ゆえ SPEC/README から参照されない盲点だった） |
| `README.md` / `AI-WORKFLOW-SPEC.md` / `AGENTS.md` | 各1 | Codex/Cursor に比べ OpenCode 文書化だけ欠落 |

## 2. 不十分な点（深刻度順）

### 動作不能級

- FOOTER の `/skill-creator` 参照 — 該当スキルが存在しない確定バグ（実体は Claude Code マーケットプレイスプラグインで OpenCode から発見不可）
- tech-validator 等の `mcp__context7__*` 表記 — OpenCode では `context7_*` 形式（FOOTER 読み替え表で吸収される設計だが、表自体に抜けがあった）
- implementer「サブエージェントは MCP 呼べない」— OpenCode では偽。MCP 必須ステップが不必要にエスカレーションされる

### 誤情報

- モデル ID 例示 `claude-sonnet-4-6` vs 実マップ `claude-sonnet-5` の矛盾
- 「chat/walkthrough/brainstorm は単独 LLM 完結」— 実際は explorer 委譲前提で理由付けが虚偽
- スキル分類漏れ: `field-notes` 欠落、`epic`/`deepthink`/`research`/`tester`/`sentinel-review` 等 9 個未分類、`.claude/skills` 由来 `pir2codex` 未掲載

### 構造的欠落

- README に OpenCode 統合セクション不在（Codex 版はある）
- SPEC に `sync-opencode.sh Contract` 不在（codex/cursor 版はある）、`--check` も契約テストも無し
- skills 自動発見（`~/.agents` symlink → 外部 autoload）への依存がどこにも文書化ゼロの単一点障害

### 横断パターン（agents/*.md 本体）

- PascalCase ツール名約 242 箇所（Read 103 / Write 34 / Bash 24 / Edit 22 / Glob 21 / Grep 19 ほか）。`Glob("path", "pattern")` 型関数シグネチャ表記は誤用リスク高
- `Agent` ツール / `subagent_type=` / v2.1.172 バージョン参照 10+ 箇所（planner / implementer / reviewer / ui-ux-reviewer / epic-planner / explorer）
- CLAUDE.md・`~/.claude/` 直参照 82 箇所 / 17 ファイル（meta-retrospector の改善対象リストは OpenCode/Cursor 生成物を構造的に取りこぼす）
- retrospector の hooks N7/N8（Claude Code 専用）は OpenCode で丸ごと無意味
- frontmatter `tools:` 制限は同期されず「権限線引き」記述が実効性なし（thinker / deliberator / gate / hypothesizer / synthesizer / sentinel-iac）
- reviewer.md 57KB 中 19% が「呼び出し元運用ガイド」の同居（並列起動のたびに context 複製）。retrospector 91KB / planner 51KB は反復テンプレートで肥大化

## 3. 実施した修正

### 第 1 波: FOOTER 改訂と文書整備

| ファイル | 内容 |
|---|---|
| `etc/sync-opencode.sh` | FOOTER 全面改訂: skill-creator 削除、モデル ID 更新、読み替え表拡充（subagent_type・バージョン参照・MCP 制約の否定・run_in_background）、tools 制限非継承の明記、スキル発見経路セクション追加、スキル分類を「単独完結 / task tool 委譲あり / 対象外」に全面再分類（field-notes・ai-design-system 追加、epic/pir2codex/codex を対象外へ）、hooks 提案不採用ルール追加 |
| `~/.config/opencode/AGENTS.md` | 上記スクリプト再実行で再生成・検証済み（skill-creator 0 件、旧モデル ID 0 件確認） |
| `README.md` | 「OpenCode 統合」セクション追加（Codex 版と同粒度） |
| `AI-WORKFLOW-SPEC.md` | `sync-opencode.sh Contract` セクション追加 |

### 第 2 波: `--check` モードと契約テスト

| ファイル | 内容 |
|---|---|
| `etc/sync-opencode.sh` | `--check` モード追加（cursor 版と同型の `publish` ヘルパー方式）。書き込みなしで全生成物（opencode.json / agents 18 件 / AGENTS.md）の drift を検出し、孤児 agent の削除予定も検出して exit 非ゼロ。不正引数は exit 2 |
| `etc/test-opencode-contracts.sh` | 新規作成（21 テスト全 PASS）。ライブ `--check`、fake HOME fresh sync + 冪等性、opencode.json 形状（$schema / claudeCodeOnly 除外 / permission 既定 ask）、agent 変換契約（AUTO-GENERATED ヘッダ・mode: subagent・モデル alias マップ・SSOT 本文との byte 一致）、生成 AGENTS.md 契約（SSOT 全文埋込・補足セクション 5 種・skill-creator/旧モデル ID 回帰防止）、孤児削除 + 手書きファイル保護 |
| `etc/test-all-contracts.sh` | opencode ランナーを集計に追加（cursor / opencode / shared-drift の 3 契約化） |
| `README.md` | 契約テストセクションに opencode 追加、単独実行コマンド追記 |
| `AI-WORKFLOW-SPEC.md` | sync-opencode.sh Contract に `--check` と契約テストを追記（「契約テストなし」記述を削除） |

### 第 3 波: agent 本体の runtime 中立バグ修正 + MCP フィルタ対称化

| ファイル | 内容 |
|---|---|
| `.claude/agents/tester.md` | 構造修復: 「フェーズ1.5」重複解消（ローカルツール不在時の静的代替検証を `#### 1-C` としてフェーズ1 内へ移動、IaC 静的検証のみをフェーズ1.5 として残す）、アドホックテストの欠落番号（3. から始まる連番）を 1. から振り直し、フェーズ3/4 の番号剥がし。外部参照ゼロを確認済み |
| `.claude/agents/sentinel-iac.md` | frontmatter `model: sonnet` 追加（17/17 ファイルが指定済みの中で唯一の欠落。軽量静的検出の実務系という役割から既存多数派パターンの sonnet に準拠） |
| `etc/sync-opencode.sh` | MCP フィルタに `codexOnly` 除外を追加（cursor 版との対称化。openCodeOnly は引き続き含む）。現在 codexOnly エントリは無しのため生成物に差分なし |
| `etc/test-opencode-contracts.sh` | codexOnly 除外の検証に拡張（21 テスト継続 PASS） |
| `README.md` / `AI-WORKFLOW-SPEC.md` | codexOnly 除外を反映 |

## 4. 残課題と判断

- **agents/*.md 本体の runtime 差分は意図的に未修正** — Claude Code native ソースであり、SPEC Rule（runtime 差分は shared core か adapter で吸収）の思想から、PascalCase → snake_case 一括置換は Claude Code 側を壊すため不採用。retrospector N7/N8（hooks）も Claude Code では有効なため削除せず、FOOTER 不採用ルールで吸収済み
- **大規模リファクタは未着手**（instruction-refactor / pir2 ワークフロー向き）: retrospector 91KB・planner 51KB・reviewer 57KB の反復テンプレート解体、reviewer/refactor-advisor/ui-ux-reviewer の「呼び出し元運用ガイド」references/ 外出し、同一ルールの 3 エージェント間重複統合
- **pre-existing drift（本件と無関係・進行中マージの帰結）**: `check-shared-drift.sh` FAIL 1 件（dotfiles-autosync missing: cursor）、`test-cursor-contracts.sh` FAIL 1 件（legacy `cursor-*` dirs: cursor-dotfiles-autosync / cursor-field-notes）。いずれも cursor- プレフィックス廃止移行の途上状態で、`etc/link.sh` 等が UU（マージコンフリクト）のまま
