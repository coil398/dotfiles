## 探索レポート: Claude Code 側の epic スキルと関連資産の Codex 移植・チューニング

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| `/Users/kawasetakumi/dotfiles/AI-WORKFLOW-SPEC.md` | shared core / native overlay 方針、生成物、各 runtime の責務境界、Codex / Cursor / OpenCode の扱いを定義する上位仕様 | 参照のみ |
| `/Users/kawasetakumi/dotfiles/AGENTS.md` | 全エージェント共通の日本語出力、スコープ厳守、git 操作制約、skills / generated files の運用ルール | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.agents/skills/epic/SKILL.md` | epic の shared-core 版。エピック分割、DAG 化、ネスト pir2、RUN_DIR の使い方を定義 | 変更あり候補 |
| `/Users/kawasetakumi/dotfiles/.codex/skills/epic/SKILL.md` | Codex native overlay 版。`.agents/skills/epic` を seed した実体。`--codex` 分岐や Codex 向けの文言調整を含む | 変更あり候補 |
| `/Users/kawasetakumi/dotfiles/.agents/skills/pir2/SKILL.md` | epic が下位で起動する基幹ワークフロー。探索/計画/実装/レビュー/テスト/再探索の SSOT | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.codex/skills/pir2/SKILL.md` | Codex native overlay 版 pir2。epic の下位起動先として参照される | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.agents/skills/pir2/references/experimental.md` | epic-orchestrator-nested-pir2 実験と implementer shard 実験の採否観測 SSOT | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.agents/skills/pir2/references/exploration-loop.md` | planner 追加探索ループの最大 5 回・topic 再探索の運用 | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.agents/skills/pir2/references/implementation-delegation.md` | shard / main fallback 判定、許可ファイル集合、共有契約の禁止条件 | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.agents/skills/pir2/references/plan-choice-gate.md` | 複数案・スコープ縮小・外部依存不足時のユーザー確認ゲート | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.agents/skills/pir2/references/fan-out-gate.md` | reviewer の並列起動ルールと宣言テンプレート | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.codex/agents/epic-planner.toml` | Codex 用 epic-planner agent。gpt-5.5 / high、README 的役割説明を含む | 変更あり候補 |
| `/Users/kawasetakumi/dotfiles/.codex/agents/planner.toml` | Codex planner agent。pir2 / writing-plan の計画策定用 SSOT | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.codex/agents/implementer.toml` | Codex implementer agent。実装完了レポート・自己検証・shard / main fallback を規定 | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.codex/agents/reviewer.toml` | Codex reviewer agent。VERDICT / role マッピング / 並列レビューの SSOT | 参照のみ |
| `/Users/kawasetakumi/dotfiles/etc/sync-codex.sh` | `.codex/config.toml` と `.codex/AGENTS.md`、一部の Codex 用参照ファイルを生成する同期スクリプト | 変更あり候補 |
| `/Users/kawasetakumi/dotfiles/etc/sync-opencode.sh` | OpenCode 用生成スクリプト。Claude 側 agent / settings / MCP を変換している | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.codex/config.base.toml` | Codex の手書き base config。sandbox / model / agents / tools の既定値 | 変更あり候補 |
| `/Users/kawasetakumi/dotfiles/mcp-servers.json` | MCP registry の SSOT。Codex / OpenCode / Cursor への生成元 | 参照のみ |

### 既存パターン・規約

- 命名規約: epic / pir2 / planner / implementer / reviewer / retrospector / gate / synthesizer など、役割ベースの短い名前で統一されている。Codex の native overlay は `.codex/agents/*.toml`、skills は `.codex/skills/<name>/SKILL.md` という配置に寄せられている。
- ディレクトリ構造: shared core は `AGENTS.md` と `.agents/skills/**`、Codex 固有は `.codex/agents/**` と `.codex/skills/**`。epic だけは shared core と Codex overlay の両方に存在し、overlay 側が「seed された編集可能コピー」として扱われる。
- コードスタイル: skills / agents は「日本語出力」「最終出力のフォーマット固定」「実装詳細は下位責務へ委譲」を強く要求する。同期スクリプトは hand-written と generated を区別し、generated 物に手書き編集を許さない。
- 共通ユーティリティ: epic から直接使う共通基盤は pir2 の references 群。特に `sanitized-cwd`、`run-dir-base`、`plan-choice-gate`、`fan-out-gate`、`exploration-loop`、`implementation-delegation`、`experimental` が重要。
- **構造投資領域 (structurally-invested area)**:
  - `AGENTS.md` / `.agents/skills/*` / `.codex/skills/*` は「同一ワークフローを runtime 別に展開する」構造投資領域。
  - `.codex/agents/*.toml` は agent ファミリーとして複数並び、`planner` / `epic-planner` / `implementer` / `reviewer` / `gate` / `thinker` / `synthesizer` / `retrospector` など、同型の役割定義が 3 個以上ある。
  - `pir2` references 群は、探索ループ・ゲート・分割・実装委譲・検証などの手順ファミリーとして 3 個以上が並ぶため、N+1 での追加は既存形式準拠が前提になる。

### 影響範囲

- 直接影響: `.agents/skills/epic/SKILL.md`、`.codex/skills/epic/SKILL.md`、`.codex/agents/epic-planner.toml`、`etc/sync-codex.sh`、`.codex/config.base.toml`
- 間接影響: `pir2` の references 群、`planner` / `implementer` / `reviewer` の Codex agent 定義、`AGENTS.md`、`AI-WORKFLOW-SPEC.md`、生成物としての `.codex/AGENTS.md` / `.codex/config.toml`
- epic の変更は単独では閉じず、下位の `pir2` 実行モデル、reviewer の役割分担、run-dir 生成ルール、ユーザー確認ゲートのどこまでを epic 本体に集約するかに波及する。
- Codex native overlay なので、`.claude/skills/epic/SKILL.md` と byte-for-byte 一致を目指す必要はないが、shared core から逸脱した設計を入れるなら理由を明示できる必要がある。

### 依存関係

- インポート関係:
  - epic skill は pir2 の `SKILL.md` と references を実質的な依存先としている。
  - Codex overlay の epic-planner は `gpt-5.5` 高推論、`planner` / `implementer` / `reviewer` の既存 agent 群と同じ運用原則に揃っている。
  - `sync-codex.sh` は `AGENTS.md`、`mcp-servers.json`、`.agents/skills/**`、`.claude/*` を入力に生成するため、epic の移植方針を変えるなら同期スクリプトの生成物説明と整合させる必要がある。
- 被参照関係:
  - `.agents/skills/epic/SKILL.md` と `.codex/skills/epic/SKILL.md` はいずれも /epic の実体として参照される。
  - `.codex/agents/epic-planner.toml` は epic 本体から起動される前提。
  - `AI-WORKFLOW-SPEC.md` と `AGENTS.md` は runtime 境界・生成物・編集可否の上位規約として参照される。

### 補足情報

- `.claude/skills/epic/SKILL.md` は探索上、内容が `.agents/skills/epic/SKILL.md` とほぼ同型で、Codex overlay 側は seed コメントと runtime 文言差分が中心だった。
- epic 本体の本文には、`--codex` のフラグ解釈、`EPIC_RUN_DIR` の命名、`pir2codex` への差し替え、L0→L1→L2 の三層制約、ユーザー対話を epic 本体へ集約する方針が明示されている。これらは移植時の主要な振る舞い境界になる。
- `sync-codex.sh` の現状では、`.codex/agents/*.toml` と `.codex/skills/**` は legacy mirror のみでしか再生成されず、default では shared core から更新されない。つまり epic を Codex ネイティブに調整する場合、手で `.codex/skills/epic/SKILL.md` を保守するか、同期スクリプト側の生成方針を変える必要がある。
- `sync-codex.sh` は `.claude/` 由来の文字列を `.codex/` に機械置換するため、Claude 固有残骸が入り込みやすい。特に `~/.claude/skills` → `~/.agents/skills`、`~/.claude/AGENTS.md` → `~/.codex/AGENTS.md` の置換線は移植差分の確認ポイント。
- `AGENTS.md` と `AI-WORKFLOW-SPEC.md` の整合上、Codex は `.codex/agents/*.toml` と `.codex/skills/*` を native overlay として扱う設計なので、epic だけ byte-for-byte 同期を求めるのは逆方向。むしろ shared core から runtime 機械を分離する方針に乗せるのが自然。
- 探索した範囲では、epic に関する「Claude 固有の不要残骸」は主に参照パス残存と文言上の `Claude` 表記で、機能ロジックの残骸よりは説明文・参照先の整理が中心だった。
- **チェック手順と keyword**: `rg --files -uu .agents .codex | rg '(^|/)(epic|pir2)(/|$)|/agents/|/skills/'` で対象資産を列挙し、`sed -n` で epic / pir2 / planner / sync scripts / config を精読した。さらに `rg -n "epic|pir2|planner|explorer|retrospector|codex-runner|pir2codex|Agent" ...` で参照関係と残骸を広く確認した。

### 参照した外部ソース（外部ドキュメント調査を行った場合のみ）

| ソース種別 | URL | 確認した内容 |
|-----------|-----|------------|
| なし | - | 今回はローカル資産の探索のみで、外部ドキュメント調査は未実施 |

### 呼び出し元への依頼（該当する場合のみ）

- `epic` の Codex ネイティブ移植では、`.codex/skills/epic/SKILL.md` の説明文と `epic-planner.toml` の実体が主な調整対象で、shared core 側の `.agents/skills/epic/SKILL.md` は source of truth として温存する方針がよい。
- `sync-codex.sh` が default で `.codex/skills/**` を再生成しないため、Codex overlay の epic を更新するなら「手修正維持」か「legacy mirror 再有効化」のどちらかを別 explorer / planner で判断してほしい。
- `epic` の下位 `pir2` 依存が強いので、`pir2` 自体の run-dir / user-gate / shard / reviewer ルールを変える場合は、epic 側と同時に再探索するのが安全。
- 共有リソース競合の観点では、`AGENTS.md`、`.codex/config.base.toml`、`mcp-servers.json`、`etc/sync-codex.sh` は他 runtime の生成物と連動するため、同一ターンで別枝の変更を並行させないでほしい。
