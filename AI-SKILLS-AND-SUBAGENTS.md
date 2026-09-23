# スキルとサブエージェント

各 runtime で、スキルがどこに置かれてどう読み込まれるか、親エージェントが子（サブエージェント）をどう起動し、model と effort がどこで決まるかをまとめる。生成物の所有範囲と配布契約の詳細は [AI-WORKFLOW-SPEC.md](AI-WORKFLOW-SPEC.md) を参照する。

## スキル

### 3つの層

| 層 | 置き場所 | 中身 |
|---|---|---|
| 共有原本 | `.agents/skills/<name>/` | `SKILL.md`（手順本体）、`references/`（子に渡す専門手順）、`scripts/`、`assets/` |
| runtime 入口 | `.claude/skills/`、`.codex/skills/`、`.cursor/skills/` | その runtime から起動するための入口。本文は共有原本を読む |
| ホーム配備 | `~/.agents/skills`、`~/.claude/skills`、`~/.cursor/skills` など | `etc/link.sh` が配置する |

- 手順の本体は共有原本に1つだけ書く。runtime 入口には、その runtime 固有の起動方法（子の起動 API、model 指定、CLI 連携など）の差分だけを書く。
- 子に渡す専門手順（例：`research/references/explorer.md`、`code-review-guidance/references/<観点>.md`）も共有原本の `references/` に置く。親はそのファイルの絶対パスを子に渡し、子が自分で Read する。

### runtime ごとの入口

| runtime | 入口の形 | 共有原本がない runtime 専用スキル | ホーム配備 |
|---|---|---|---|
| Claude Code | `.claude/skills/<name>` → `../../.agents/skills/<name>` の symlink（29本）。固有の起動機構が要るものだけ native：`codex`、`deepthink`、`design-review` | `deepthink` | `~/.claude/skills` → repo の `.claude/skills`（ディレクトリごと symlink） |
| Codex | `.agents/skills/*` を直接読む。Codex 固有の実行処理が要るものだけ `.codex/skills/*` に native overlay（`codex`、`pir2`、`worker-delegation` の3つ） | `worker-delegation` | `~/.agents/skills` → repo の `.agents/skills`。`~/.codex` は管理対象だけ個別にリンク |
| Cursor | `.cursor/skills/<name>/SKILL.md` を全スキル分置く。多くは数十行の薄い入口で、本文は共有原本を読む。frontmatter の `name` はディレクトリ名と一致させる | `deepthink`、`geminify` | `~/.cursor/skills/<name>` へ実体コピー（`bash etc/link.sh --codex-cursor-only`） |
| OpenCode | 登録を生成しない。`~/.agents/skills/*` と `~/.claude/skills/*` から発見する | なし | `~/.agents/skills` を共用 |

- Claude の `~/.claude/skills` はリポジトリの中を指しているため、Claude Code が `~/.claude/skills/synced/` に書くアカウント skill のキャッシュも repo に入る。これは `.gitignore` で除外している。
- Claude で無効にしているスキルは `.claude/settings.json` の `skillOverrides` で管理する（`ai-design-system`、`chat`、`writing-plan`）。
- 入口と共有原本の整合は `python3 etc/audit-skill-agent-layout.py`（`/overlay-audit`）と `bash etc/check-shared-drift.sh` で確認する。

### スキルを追加・変更するとき

1. 手順本体は `.agents/skills/<name>/SKILL.md` に書く。子に渡す手順は同じスキルの `references/` に置く。
2. Claude は `.claude/skills/<name>` → `../../.agents/skills/<name>` の相対 symlink を作る。固有の起動機構が要る場合だけ native の `SKILL.md` を置き、共有原本を読む形にする。
3. Cursor は `bash etc/seed-cursor-overlay.sh` で入口を作り、`bash etc/link.sh --codex-cursor-only` でホームへ配備する。
4. Codex は、固有の実行処理が要る場合だけ `.codex/skills/<name>` を置く。
5. `bash etc/test-cursor-contracts.sh` と `bash etc/check-shared-drift.sh` を通す。

## サブエージェント

### 共通の考え方

- 専門手順は Skill の `SKILL.md` と `references/` に置く。役割ごとの専用エージェント定義は作らない。
- 親は runtime 標準の汎用担当を起動し、読むべき手順ファイルの絶対パスをプロンプトで渡す。子はそれを自分で Read してから作業する。
- 子の model と effort の既定値は runtime の設定で一度だけ決める。Skill には model 表を持たせない。例外は「そのモデルであること自体が目的」の場合だけ（`deepthink` の Fable、Cursor の探索担当の composer-2.5）。
- 難しい作業は、親が起動時に model・effort を明示して上書きする。入力不足・権限・環境の失敗はモデル不足として扱わない。

### runtime ごとの比較

| | Claude Code | Codex | Cursor | OpenCode |
|---|---|---|---|---|
| 親 | 起動時のモデル（`/model`） | `gpt-6-astra` / `low` | Auto | 有効設定 |
| 子の既定 model | 親と同じ（`CLAUDE_CODE_SUBAGENT_MODEL` 未設定） | `gpt-6-luna` | `inherit`（親の Auto） | OpenCode 標準 |
| 子の既定 effort | 親セッションの effort | `max` | Cursor の公開オプション | OpenCode 標準 |
| 既定の置き場所 | `.claude/CLAUDE.md` の方針（`env` の `CLAUDE_CODE_SUBAGENT_MODEL` は未設定） | `.codex/config.base.toml` の `[agents]` | 標準Task は model 省略。探索だけ `.cursor/agents/explorer.md` | `~/.config/opencode/opencode.json`（生成） |
| 呼び出しごとの上書き | Agent tool の `model` 引数（effort は不可） | `spawn_agent` の model / reasoning_effort | Task 起動時に公開されている指定 | `task` tool の公開引数 |
| 専用エージェント定義 | なし | なし（`.codex/agents/` は空） | `explorer` の1本だけ（探索用、composer-2.5・readonly） | なし |
| Skill の置き場所 | `.claude/skills/*` → `.agents/skills/*` への symlink。native は `codex` / `deepthink` / `design-review` | `.agents/skills/*` を直接使う。native overlay は `.codex/skills/*` | `.cursor/skills/*`（ほぼ全 Skill の薄い入口。本文は `.agents/skills/*`） | `~/.agents/skills/*` / `~/.claude/skills/*` から発見 |

### Claude Code

- 子は `Agent({ subagent_type: "general-purpose", model?, prompt })` で起動する。custom agent 定義（`.claude/agents/`）は置かない。
- **model** の優先順位：
  1. Agent tool の `model` 引数
  2. agent 定義の frontmatter
  3. `CLAUDE_CODE_SUBAGENT_MODEL`
  4. 親のモデル
- **effort** は呼び出しごとに指定できない。agent 定義の frontmatter に `effort` がなければ、親セッションの effort をそのまま使う。担当ごとに effort を変えたいときは、その作業の前に親で `/effort` を変える。
- 未確認：子を別モデル（例：`sonnet`）で起動したとき、そのモデル用の `modelSettings` の effort が使われるかどうかはドキュメントに書かれていない。
- Claude から GPT 系を使うには Codex CLI を経由する。Agent tool の `model` には Claude のモデルしか指定できない。
  - 相談：`/codex <相談内容>`（read-only）
  - 実装：`/codex <実装タスク>`、または `/pir2 --codex`（計画・レビュー・テストは Claude、実装だけ Codex）。既定は `gpt-6-luna` / `max`、難所は `gpt-6-sol` / `high`・`max`
  - どちらも runner（`general-purpose`、model 省略）が共有の `.agents/skills/codex/references/runner.md` に従って CLI を起動し、完了まで待つ。親は結果と実差分を照合する
- モデルの使い分けは `.claude/CLAUDE.md` の「Claude Agent運用」に書く：
  - 手を動かす実装・修正は Codex（`gpt-6-luna` / `max`、難所は `gpt-6-sol`）
  - Codex を使えないとき（使用量切れなど）は `general-purpose` を `model: "sonnet"` で起動して実装させる
  - それ以外（探索・レビュー・テスト・熟考）は model を省略して親を引き継ぐ
- model を固定している Claude native Skill：

  | Skill | 担当 | model | 理由 |
  |---|---|---|---|
  | `deepthink` | deliberator / synthesizer / gate | `claude-fable-5-1`（`--opus-panel` 時は `opus`） | Fable での熟考そのものが目的 |

- 参照：https://code.claude.com/docs/en/sub-agents.md 、https://code.claude.com/docs/en/model-config.md

### Codex

- 親 Astra が計画・統合・受入を持つ。子は built-in の `default` / `worker` / `explorer` を使い分ける（[codex-native-supplement](.codex/codex-native-supplement.md)）。
- 子の既定は `.codex/config.base.toml` の `[agents]` で決める：

  ```toml
  default_subagent_model = "gpt-6-luna"
  default_subagent_reasoning_effort = "max"
  ```

- 難しい独立推論は、親が起動時に Sol（`gpt-6-sol`）と `high` / `max` を明示して選べる。
- 委譲はすべて [worker-delegation](.codex/skills/worker-delegation/SKILL.md) の契約で行う。子の model は `[agents]` の既定に任せる。探索だけを渡すときは編集禁止を明示し、`.agents/skills/research/references/explorer.md` のパスを渡す。

- 使えるモデルは `codex debug models` で確認する。CLI が古いと新しいモデルが一覧に出ないので、先に `codex update` する。

### Cursor

- 共有 Skill の本文は `.agents/skills/*` に置き、`.cursor/skills/*` は Cursor から起動するための薄い入口にする。`etc/link.sh` が `~/.cursor/skills` へ実体コピーする。
- Task の model は、基本的に省略して親の Auto を引き継ぐ。例外は次の2つ：
  - `explorer`：`composer-2.5`
  - `deepthink` / `deepplan`：思考担当に Fable を使う（`.cursor/skills/deepthink/references/fable-model.md`）
- 委譲は標準 Task（`subagent_type: "generalPurpose"`、model 省略）で起動し、手順ファイルの絶対パスを渡す。
- 探索だけは `Task({ subagent_type: "explorer" })` で起動する。`.cursor/agents/explorer.md`（`model: composer-2.5`、`readonly: true`）が適用される。Cursor のエージェント定義はこの1本だけ。
- `readonly` は agent 定義でしか設定できないため、探索以外の read-only 担当（reviewer など）は、プロンプトで編集禁止を明示し、親が返却後に `git status` / diff を確認する。

### OpenCode

- エージェントは生成しない。委譲には OpenCode 標準の担当と `task` tool を使う。
- `etc/sync-opencode.sh` は、以前生成した `~/.config/opencode/agents/*.md`（AUTO-GENERATED ヘッダ付き）を削除する。

## 変更するとき

| 変えたいもの | 編集する原本 | 反映 |
|---|---|---|
| Claude の子の既定 model | `.claude/settings.json` の `env.CLAUDE_CODE_SUBAGENT_MODEL` | 新しいセッション |
| Claude の担当ごとのモデル方針 | `.claude/CLAUDE.md` の「Claude Agent運用」 | 新しいセッション |
| Claude の Skill ごとの model | 該当 native Skill の `SKILL.md` | 即時 |
| Codex の子の既定 | `.codex/config.base.toml` の `[agents]` | `bash etc/sync-codex.sh` |
| Cursor の探索担当の model | `.cursor/agents/explorer.md` の `model:` | `bash etc/link.sh --codex-cursor-only` |
