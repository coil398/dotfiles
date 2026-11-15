## 探索レポート: `.codex/skills` 残存参照監査

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| `.codex/skills/codex/SKILL.md` | Codex CLI 相談スキル。`gpt-5.6-*` の現行モデル表、MCP 廃止、read-only 相談方針を規定 | 参照のみ |
| `.codex/skills/worker-delegation/SKILL.md` | 全ワークフロー共通の実作業委譲契約。Luna/Terra の actor ladder と acceptance 分離を SSOT 化 | 参照のみ |
| `.codex/skills/pir2/SKILL.md` | 標準の Plan→Implement→Review→Retrospect フロー。レビュー・実装・再探索の横断 SSOT | 参照のみ |
| `.codex/skills/pir2async/SKILL.md` | PIR²async の Agent Teams 版。implementer/reviewer の直接対話を定義 | 参照のみ |
| `.codex/skills/debug/SKILL.md` | デバッグ用 PIR²。探索・planner・worker・reviewer/tester を分離 | 参照のみ |
| `.codex/skills/reviewer/SKILL.md` | ローカル差分レビューのハイブリッド並列ルール | 参照のみ |
| `.codex/skills/review-pr/SKILL.md` | PR/ブランチ差分レビューのハイブリッド並列ルール | 参照のみ |
| `.codex/skills/writing-plan/SKILL.md` | 実装計画＋追記＋レビューの作業記録スキル | 参照のみ |
| `.codex/skills/ir/SKILL.md` | 小規模変更向けの軽量 Implement→Review フロー | 参照のみ |
| `.codex/skills/deepthink/SKILL.md` | 探索→熟考→統合→gate の多エージェント熟考フロー | 参照のみ |
| `.codex/skills/research/SKILL.md` | 探索→集約→思考→仮説の研究フロー | 参照のみ |
| `.codex/skills/epic/SKILL.md` | 大規模タスクの DAG/wave オーケストレーション | 参照のみ |
| `.codex/skills/ai-ltm/README.md` | 長期記憶システムの利用説明。`~/.agents` 前提の旧導線を含む | 参照のみ |
| `.codex/skills/check-updates/SKILL.md` | skills/plugins 更新自動確認。`~/.agents` / `~/.claude` の検出ロジックを含む | 参照のみ |
| `.codex/skills/check-updates/scripts/check-updates.sh` | 更新確認の実体スクリプト。dotfiles 検出で `~/.claude/skills` コメントを残す | 参照のみ |
| `.codex/skills/instruction-refactor/SKILL.md` | instruction file 専用の肥大化・SSOT 整理スキル。直接 Edit/Write を明示 | 参照のみ |
| `.codex/skills/instruction-refactor/references/official-criteria.md` | Anthropic/AgentsSkills の公式基準を収集した基準集 | 参照のみ |
| `.codex/skills/ai-design-system/SKILL.md` | デザインシステム維持用 SSOT。Anthropic 公式の `frontend-design` との並列利用を説明 | 参照のみ |
| `.codex/skills/ai-design-system/README.md` | `frontend-design` との役割分担を説明する補助文書 | 参照のみ |
| `.codex/skills/sentinel-review/SKILL.md` | セキュリティ専用のカテゴリ別レビュー。書き込み禁止の読み取り専用設計 | 参照のみ |

### 既存パターン・規約

- 命名規約: スキル名は短い英小文字ハイフン表記で、`SKILL.md` が入口。補助資料は `references/` に外出しする形が多い。
- ディレクトリ構造: 1 スキル 1 ルートを保ちつつ、`references/`、`scripts/`、`README.md`、`init.sql` などを分離している。
- コードスタイル: ループ・ゲート・レポート出力の手順を明文化し、`RUN_DIR` 配下に中間成果物を集約する。`worker-delegation` は全ワークフロー共通 SSOT として再利用される。
- 共通ユーティリティ: `worker-delegation/scripts/run-worker.sh`、`pir2` 系の `fan-out-gate.md`、`sanitized-cwd.md`、`next-steps-queue.md` が横断利用されている。
- **構造投資領域 (structurally-invested area)**:
  - `worker-delegation` とそれを参照する `pir2` / `writing-plan` / `debug` / `ir` / `epic` は、同一の actor ladder と acceptance 分離を何度も使う構造投資領域。
  - `reviewer` / `review-pr` / `writing-plan` / `ir` / `pir2` / `pir2async` は、ハイブリッド並列レビューの同型パターンが並ぶ領域。
  - `deepthink` / `research` / `debug` は、探索→統合→再探索のループ構造が共通する領域。
  - `ai-design-system` は SSOT・Aesthetic・Audit の文書ファミリーを持つ領域。

### 影響範囲

- 直接影響: `.codex/skills/**` 全体、特に `pir2` / `debug` / `writing-plan` / `reviewer` / `review-pr` / `worker-delegation` / `deepthink` / `research` / `epic`
- 間接影響: `~/.agents/skills` 側の互換インストール、`~/.claude` 系の移行導線、`run-worker.sh` を使う全実装ワークフロー

### 依存関係

- インポート関係: `pir2` 系は `worker-delegation` と `references/*.md` に強く依存する。`debug` / `writing-plan` / `ir` / `epic` は `worker-delegation` を共通実作業契約として参照する。
- 被参照関係: `worker-delegation` は `pir2` / `debug` / `writing-plan` / `ir` / `epic` から SSOT として参照される。`fan-out-gate.md`、`sanitized-cwd.md`、`next-steps-queue.md` は複数スキルから参照される。

### 補足情報

- `Claude` / `Anthropic` / `Opus` / `Sonnet` / `Haiku` の残存参照は大半が歴史的互換ラベル、公式基準の出典名、または旧環境への移行ガイドとして意図的に残されている。特に `instruction-refactor/references/official-criteria.md` は公式引用の保管庫として妥当。
- `~/.agents` / `~/.claude` の残存参照も、互換インストールや dotfiles 検出、旧導線の説明として明示されており、単独では runtime defect ではない。
- `SendMessage` / `Agent` / `spawn_agent` / `followup_task` の記述は、ワークフロー内での起動責任を明文化するためのオーケストレーション規約であり、現状では設計意図に沿っている。
- `gpt-5.5` の固定は多くのスキルで残っているが、ほとんどが「explorer / reviewer / planner の既定モデル」という意味で使われており、すぐに壊れる参照ではない。一方で `worker-delegation` だけは `gpt-5.6-*` 固定の現行実作業系と明確に世代差があるため、将来のモデル統一時には最優先で再照合が必要。
- `instruction-refactor` は「改善実施まで」を目的にしており、`Edit/Write` をメイン Codex が直接持つのは意図的な例外。worker-delegation の bypass ではなく、対象が instruction file だから成立する設計。
- `check-updates` の `git add` / `git commit` / `git reset` / `git checkout` は更新・衝突解決のための意図的なリポジトリ操作で、探索や実装の迂回ではない。
- `sentinel-review` の「書き込み権限なし」は安全設計であり、`suggested_patch` に止めるのは意図的。実装系への流用はしない前提。

### 参照した外部ソース（外部ドキュメント調査を行った場合のみ）

| ソース種別 | URL | 確認した内容 |
|-----------|-----|------------|
| なし | - | 外部ドキュメント調査は実施していない |

### 呼び出し元への依頼（該当する場合のみ）

- `gpt-5.5` を前提にした各スキルのモデル指定は、現行の `gpt-5.6-*` 体系と整合させるかを別途棚卸しするとよい。
- `~/.claude` / `~/.agents` の残存参照は互換導線として妥当だが、将来は「旧環境向けの互換案内」か「現行 runtime の正式パス」かを分離して明示した方が混乱が減る。
- `instruction-refactor` のような「直接 Edit/Write する例外」については、worker-delegation を通さない理由を冒頭でさらに短く明示すると、横断監査時の誤解が減る。
