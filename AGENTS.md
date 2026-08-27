# Shared AI Agent Settings

## Output Language

- すべての出力・回答は日本語で行う

## Core Rules

- ツール結果を捏造しない。完了主張は実際のコマンド・ツール出力を受け取ってから行う
- ユーザーの未コミット変更を勝手に戻さない。`git restore` / `git checkout -- <file>` / `git reset --hard` は明示指示がない限り使わない
- `git add -A` / `git add .` は使わない。コミットする場合は対象ファイルを個別指定し、直前に `git diff --cached` を確認する
- Python は `uv` を優先する。既存プロジェクトに `pyproject.toml` / `uv.lock` があればそれに従う
- 機能実装では字義通りの最小スコープを守る。指示範囲を超える解釈が必要な場合は実装前に確認する
- 後方互換はユーザーが明示した場合にのみ維持する。明示がない限り、互換目的の旧フィールド・フォールバック・二重読み書き・legacy 分岐を追加・温存せず、互換性だけを理由に実装や dispatch を止めたり確認を求めたりしない
- デバッグでは、推測を重ねる前にログや再現コマンドで実測する

## Review Guidelines

- 指摘は correctness / security / behavioral regression / data loss / missing tests を優先する
- ファイル名・型名・関数名・テスト名が責務または検証する挙動を表すかを確認し、チケット番号・一時的な作業名・実装経緯だけに依存する命名を残さない
- reviewer / refactor-advisor / 外部botの指摘は仮説として扱い、差分・仕様・テスト・既存実装で自己照合してから採用または false-positive と判断する
- リファレンス実装から移植する場合は、通常のworkflow外でも explorer に完全抽出させ、`reference-fidelity` reviewer の照合を通す
- 生成物の差分は、生成元 SSOT または adapter script の差分と対応しているかを見る。ただし `.codex/agents/**` と `.codex/skills/**` は Codex native overlay として扱い、`.claude` / `.agents` との厳密一致を要求しない
- `.codex/AGENTS.md` / `.codex/config.toml` / `~/.config/opencode/**` / `.cursor/rules/**` / `.cursor/mcp.json` の生成物だけが変わっている場合は、手書き編集や再生成漏れを疑う
- ワークフロー変更では、対応する sync script・hook・生成物・README/CLAUDE.md / `AI-WORKFLOW-SPEC.md` の説明が揃っているか確認する。サブエージェント運用では、各作業単位と各担当エージェントが重複のない 1 対 1 対応になり、独立単位が並列実行され、書き込みファイルの所有が競合せず、root/main の統合責任が保たれていることも検査する

## Memory Auto-Activation

- `/ai-ltm`: セッション開始・再開・「前回の続き」で自動 recall。学び・失敗・意思決定・中断点が確定したら自動 record。ユーザーに毎回許可を取らない
- `/field-notes`: キャンペーン再開で INDEX→0〜3件を自動 recall。試行方針が変わったら自動 capture。MEMORY/LTM の代替にしない
- 二重書きしない。短期の方針差分は field-notes、横断検索したい経緯は ai-ltm、感想は ai-diary
- 毎ターン・毎コマンド成功での自動書き込みは禁止

## Shared Core And Native Overlays

- Definitive architecture spec: `AI-WORKFLOW-SPEC.md`
- Shared instructions for Codex/OpenCode/Cursor adapters: `AGENTS.md`
- Shared skill core: `.agents/skills/*/SKILL.md`
- MCP servers: `mcp-servers.json`
- Tool-specific native overlays are allowed and expected. Do not force exact behavioral parity when Claude Code, Codex, OpenCode, and Cursor benefit from different mechanics
- Claude Code remains native and keeps using `.claude/*` directly
- Codex may use `.agents/skills` as shared core and `.codex/agents` / `.codex/skills` as Codex-native overlays
- OpenCode may use generated config plus native agent/skill choices where its runtime differs
- Cursor may use `.agents/skills` as shared core and `.cursor/agents` / `.cursor/skills` as Cursor-native overlays; generated adapters are `.cursor/rules/**` and `.cursor/mcp.json` (summary Rules, not a full `AGENTS.md` copy)
- **Cursor skill precedence**: In Cursor sessions, prefer `.cursor/skills/<name>/` (materialized under `~/.cursor/skills/<name>` by `link.sh` — Cursor does not discover symlinked personal skills). `.cursor/skills` takes precedence over `.claude/skills` and `.agents/skills`, so the basename matches the shared skill (no `cursor-` prefix). Treat `.agents/skills` as the shared-core seed/source of truth for cross-runtime promote, not as the Cursor runtime path. Overlay bodies must reference `.cursor/skills/<name>/references/` (not `~/.agents/skills/...`). Edit SSOT in `dotfiles/.cursor/skills`, then re-run `link.sh` to refresh the home copy
- **Cursor skill slash names**: Overlay directory and frontmatter `name` must both match the shared basename (e.g. folder `epic/`, slash `/epic`). Cursor requires `name` == parent folder name. Normalize with `bash etc/normalize-cursor-skill-names.sh` (also run from `seed-cursor-overlay.sh` on new seeds)

## Tool Ownership

- Claude Code native: `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/agents/*`, `.claude/skills/*`, `.claude/settings.json`
- Codex generated adapters: `.codex/AGENTS.md`, `.codex/config.toml`
- Codex native overlays: `.codex/agents/*.toml`, `.codex/skills/*`
- Cursor generated adapters: `.cursor/rules/**`, `.cursor/mcp.json` (via `etc/sync-cursor.sh`)
- Cursor native overlays: `.cursor/agents/**`, `.cursor/skills/**`
- OpenCode generated adapters: `~/.config/opencode/AGENTS.md`, `~/.config/opencode/opencode.json`
- OpenCode native/adapter agents: `~/.config/opencode/agents/*`

## ユーザーが実行するコマンドの提示形式

ユーザーがプロンプトに `!` プレフィックスを付けてシェルで実行するコマンドを案内するときは、**コピペ時の崩れに強い形** に正規化してから出すこと。

### 禁則

- **heredoc (`<< EOF ... EOF`) は使わない**。ユーザーの入力環境（プロンプト・エディタの autoindent）が行頭にスペースを差し込み、`EOF` が終端として認識されず破綻する
- 行末バックスラッシュ (`\`) による複数行継続も避ける。同様の理由で改行・インデント混入で壊れる
- 複数行のシェル構文（`for` / `if` / 関数定義 等）も極力避け、必要なら一度ファイルに保存させてから実行する形にする

### 推奨

- ファイル作成は `printf '...\n...\n' > path` か `echo '...' >> path` を **1行で** 提示する（heredoc 不要）
- 連続操作は `&&` で連結した1行コマンドにまとめる
- どうしても複数行が必要なら、Claude 側の Bash ツールで直接実行する選択肢を提示する

### Why

2026-05-20、ユーザーに `tee << 'EOF' ... EOF` 形式の heredoc を `!` 経由で案内した際、コピペ後のターミナル表示で各行頭に 2 スペースが入り `EOF` 終端が効かず、ファイル作成が 2 回失敗した。1 行 `printf` に切り替えて解決した経緯がある。

### How to apply

ユーザーに `!` 付きで打たせるコマンドを書く前に「これは 1 行で書けるか？」を自問する。`<<` / `\` の改行継続を書きそうになったら、`printf` / `&&` 連結に書き直してから提示する。

## 問題の迂回禁止

- 正しい設計に従ったコードが期待通りに動かない場合、勝手に別の手段で迂回しない
- ツールやインフラが使えない場合も、勝手に代替手段で進めない
- 同一のツール呼び出し・コマンドが 2 回続けて失敗したら、3 回目を試さず止める（ブラインドリトライ禁止）。原因が特定でき、かつ再試行で直る合理的根拠があるときのみ再試行してよい
- いずれの場合も原因を報告してユーザーの判断を仰ぐ

## Subagent Operation

- Before starting a non-trivial task, split it into concrete, bounded work units. When multiple delegable units exist, assign each unit to its own distinct subagent, assign each subagent exactly one unit, and launch independent units in parallel across investigation, implementation, review, and testing; serialize only genuine dependencies
- Keep a small indivisible task as one unit; agent count never justifies artificial subdivision
- The root/main agent owns user dialogue, scope, dependency and file-ownership planning, progress, integration, conflict avoidance, verification, and final decisions. Subagents return concise findings, changed-file references, and verification evidence for root/main integration
- Give every write-capable unit exclusive file ownership. When units would touch the same file, assign that file to one writer and make the other units read-only, or serialize those writes
- If a runtime does not support subagents or nested delegation, preserve the same unit boundaries and ordering in the main agent. In Codex, repository-changing work also follows `~/.codex/skills/worker-delegation/SKILL.md`

## Skills Operation

- Skills are discovered from `SKILL.md` metadata. Keep `description` concise and put trigger phrases near the front
- Skill bodies should assume progressive disclosure: only the selected skill is read deeply
- One skill should do one job. Large procedures, references, scripts, and assets belong in `references/`, `scripts/`, or `assets/`
- `/pir2`, `/debug`, `/ir`, and `/writing-plan` mean Plan -> Implement -> Review -> Test across agents. Tool-specific adapters may implement that with native subagents, sequential execution, or the main agent
- `/pir2async` is experimental and may degrade to the normal sequential workflow when agent-team primitives are unavailable

## Exploration And Design

- 複数ファイルにまたがる調査では `rg` / `rg --files` を優先する
- 既存パターンを調べたら、その事実を設計判断に反映する
- 新規ディレクトリ・新規構造を作る前に、同一レイヤーの既存構造を確認する
- 既存多数派から逸脱する場合は、差分・理由・既存パターンに合わせた代替案を提示してから実装する
- ライブラリ選定・最新仕様・価格・規約・公開情報は一次ソースで確認する

## Generated Files

- `.codex/AGENTS.md` and `.codex/config.toml` are generated by `etc/sync-codex.sh`
- `.codex/agents/*.toml` and `.codex/skills/*` are Codex-native overlays. They are not regenerated by default. The old strict mirror can be invoked only with `SYNC_CODEX_LEGACY_MIRROR=1 bash etc/sync-codex.sh`
- `~/.config/opencode/AGENTS.md`, `~/.config/opencode/opencode.json`, and `~/.config/opencode/agents/*` are generated by `etc/sync-opencode.sh`
- `.cursor/rules/**` and `.cursor/mcp.json` are generated by `etc/sync-cursor.sh`
- Generated files must not be hand-edited. Change `AGENTS.md`, `mcp-servers.json`, `.codex/config.base.toml`, or the relevant adapter script instead
- Native overlays may be edited directly when optimizing for that runtime. If the same rule should apply everywhere, put the shared part in `AGENTS.md` or `.agents/skills` and let native overlays reference or adapt it

## Cursor Task Model Policy

- Default is **Auto / `inherit`** (`Task` `model` omitted or set to `inherit`)
- Do not pin vendor model names in `.cursor/skills` dispatch prompts
- Cursor agent frontmatter `model` is Cursor-spec only: `inherit` (default) or a real model ID. Job class belongs in `role: coding` / `role: reasoning`, not in `model`
- Check the contract with `/overlay-audit` (`etc/audit-skill-agent-layout.py`). Do not add a second skill that restates the same rules. Cursor discovers the skill from `~/.cursor/skills/overlay-audit` (materialized by `etc/link.sh`). Home copy drift is a FAIL.
- Difficulty alone is not a reason to override. Parent Auto (current reasoning default) is usually strong enough. Pass an explicit Task `model` only when the user names one
- Codex CLI bridges (`/codex`, `codex-runner`, `/pir2codex`) may still name Codex-side model IDs; that exception does not apply to Cursor Task launches
