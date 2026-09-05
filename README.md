# dotfiles

個人用 dotfiles リポジトリ。macOS / Linux (Ubuntu) / WSL 対応。GitHub Codespaces での利用を主軸に設計。

## クイックスタート

```sh
# 新規マシン
curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/init.sh | sh

# Codespaces（install.sh が自動実行される）
bash install.sh

# シンボリックリンクの再展開のみ
sh etc/link.sh
```

## 特徴

- **モダンツール置き換え** — `eza`(ls), `bat`(cat), `procs`(ps), `rg`(grep), `zoxide`(cd), `fzf`
- **Neovim** — lazy.nvim + LSP (Mason) + Telescope + Treesitter + Copilot
- **tmux** — セッション自動保存/復元 (continuum + resurrect), fzf 連携, VS Code Dark テーマ
- **ターミナル** — WezTerm / Alacritty 対応、Cica + Nerd Font
- **冪等セットアップ** — `has()` チェックで何度実行しても安全
- **マルチアーキテクチャ** — amd64 / arm64 両対応の Docker イメージ
- **AI Coding Agent 統合** — Claude Code / Codex / OpenCode 向け PIR² ワークフロー、カスタムエージェント・スキル

## リポジトリ構造

```
dotfiles/
├── .zshrc                  # メイン zsh 設定（PATH, 補完, プロンプト, tmux 自動起動）
├── .zsh_alias              # エイリアス（モダンツール置き換え）
├── .zplugrc                # zplug プラグイン定義
├── .wezterm.lua            # WezTerm ターミナル設定
├── .vimrc                  # Vim 互換レイヤー
├── .tigrc                  # tig キーバインド
├── install.sh              # Codespaces 用セットアップ
├── mcp-servers.json        # MCP サーバー設定（user scope SSOT）
├── .mcp.json               # MCP project scope（このリポ用、serena 等）
│
├── .config/
│   ├── nvim/               # Neovim 設定
│   │   ├── init.lua        # エントリ（OS 分岐, VSCode 検出）
│   │   └── lua/            # プラグイン, LSP, キーマップ, カラー, 自動コマンド
│   ├── alacritty/          # Alacritty 設定
│   ├── wezterm/            # WezTerm 追加設定
│   └── ...                 # efm-langserver, procs, gitui, pyright 等
│
├── .tmux/
│   └── .tmux.conf          # tmux 設定（Prefix: C-q, ステータスバー, プラグイン）
│
├── .claude/                # Claude Code カスタマイズ
│   ├── agents/             # PIR² エージェント定義
│   ├── skills/             # カスタムスキル（/pir2, /ir, /debug 等）
│   └── settings.json       # 権限設定
├── AGENTS.md               # AI agent shared core guidance
├── AGENTS.override.md      # dotfiles 内 Codex 実行時の軽量 project guidance
├── AI-WORKFLOW-SPEC.md     # 各AI runtimeの shared core + native overlays 確定仕様
├── .codex/                 # Codex 設定・生成物
│   ├── AGENTS.md           # Codex generated guidance
│   ├── agents/             # Codex-native custom agents (*.toml)
│   ├── config.base.toml    # 手書き Codex 固有設定
│   └── motitan.config.toml # motitan Unity 専用の opt-in profile
├── .agents/                # AI agent shared skill core
│   └── skills/             # runtime 非依存に近い skill core
│
├── .devcontainer/
│   ├── Dockerfile          # Ubuntu 24.04 ベース, nvim・eza・procs 同梱
│   └── devcontainer.json   # Codespaces 設定
│
├── .github/workflows/
│   └── docker-publish.yml  # Docker イメージ自動ビルド & ghcr.io push
│
├── etc/
│   ├── init.sh             # 新規マシン初期セットアップ
│   ├── link.sh             # シンボリックリンク展開
│   ├── set.sh              # OS 別初期設定
│   ├── load.sh             # シェルユーティリティ関数ライブラリ
│   ├── sync-mcp.sh         # MCP を user scope に sync（冪等）
│   └── install/            # Homebrew, apt インストールスクリプト
│
├── bin/                    # CLI ユーティリティ（codex-motitan を含む）
├── .zsh/                   # Docker 補完, dircolors-solarized
└── options/                # clangd 用コンパイルフラグ
```

## セットアップスクリプトの役割

| スクリプト | 用途 |
|-----------|------|
| `install.sh` | **Codespaces 専用**。apt パッケージ・prebuilt バイナリ・zplug のインストール、symlink 展開、zsh デフォルト化、Neovim プラグインインストール |
| `etc/init.sh` | 新規マシン向け。dotfiles を clone → `set.sh` → `link.sh` を実行 |
| `etc/cloud-bootstrap.sh` | **クラウド専用**（Claude Code on the web / Cursor Cloud Agents）。環境の setup script または `install` から呼ぶ。dotfiles リポ上ならその場の checkout、他リポなら `~/dotfiles` に clone して `link.sh` を実行。詳細は [AISETUP.md](AISETUP.md) |
| `etc/link.sh` | `$HOME/dotfiles/.??*` を `$HOME/` に symlink。`.claude/` / `.codex/` は個別にリンク。`.mcp.json` は除外 |
| `etc/set.sh` | OS 判定、GNOME Terminal カラー設定、ディレクトリ構成の整理 |
| `etc/load.sh` | OS 判定 (`is_osx`, `is_linux`)、テキスト操作、出力ヘルパー等のシェル関数 |
| `etc/sync-mcp.sh` | `mcp-servers.json` を読み、`claude mcp add-json -s user` で `~/.claude.json` に登録。`install.sh` / `etc/init.sh` 末尾で自動実行 |
| `etc/sync-opencode.sh` | AI ワークフロー SSOT から `~/.config/opencode/opencode.json` / `AGENTS.md` / agents を生成 |
| `etc/sync-codex.sh` | SSOT から Codex の `.codex/config.toml` / `AGENTS.md` と補助文書を生成。native agents / Skills は保持 |

各 runtime の sync は、必須入力・生成・公開に失敗すると非ゼロで終了する。`etc/link.sh` はその終了状態を伝播し、失敗した runtime の展開と後続処理を完了扱いにしない。手書き生成物を保護するため警告だけで維持する個別分岐は、各 adapter の契約に従う。

## シェルエイリアス（抜粋）

```sh
ls    → eza          # モダンな ls
cat   → bat          # シンタックスハイライト付き cat
ps    → procs        # モダンな ps
grep  → rg           # ripgrep
vim   → nvim
k     → kubectl
dc    → docker-compose
tf    → terraform
```

## Neovim プラグイン構成

lazy.nvim で管理。主要プラグイン：

- **LSP**: Mason + nvim-lspconfig + nvim-cmp（補完）
- **検索**: Telescope（files, grep, symbols, git）
- **ファイル**: Neo-tree
- **Git**: Neogit, Gitsigns
- **UI**: Lualine, Navic, WhichKey, Noice
- **AI**: Copilot.lua
- **構文**: Treesitter
- **言語**: Rust, Python, Go, Haskell 等

## Docker / Codespaces

prebuilt イメージ `ghcr.io/coil398/dotfiles:latest` が利用可能。

他プロジェクトで使う場合：

```json
{
  "image": "ghcr.io/coil398/dotfiles:latest",
  "remoteUser": "vscode"
}
```

イメージは master push 時と毎週月曜に自動ビルド（linux/amd64 + linux/arm64）。

## クラウドでの自動展開（Claude Code / Cursor）

新しいクラウドセッションを立ち上げるたびに、どのリポジトリでも dotfiles（Cursor スキル含む）を自動展開できる。登録先だけがランタイムで違う。

- Claude Code on the web → 環境の **setup script**
- Cursor Cloud Agents → 環境の **`install`**（任意で `start`）

手順・仕組み・オプション・トラブルシュートは **[AISETUP.md](AISETUP.md)** を参照。

```sh
# 登録する1行（両ランタイム共通）
curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/cloud-bootstrap.sh | sh
```

## Claude Code 統合

Claude Code は既存のネイティブ運用を維持する。PIR² ワークフロー（Plan → Implement → Review → Retrospect）やカスタムスキルは `.claude/` で管理し、Codex/OpenCode 向け adapter から逆生成しない。`etc/link.sh` で `$HOME/.claude/` にリンクされるため、全プロジェクトで共有される。

主なスキル: `/pir2`, `/ir`, `/review-pr`, `/debug`, `/tester`, `/brainstorm`, `/writing-plan`

## Codex 統合

Codex は `AI-WORKFLOW-SPEC.md` の **shared core + native overlays** 方針で運用する。移植可能な共通ルールは `AGENTS.md`, `.agents/skills/*`, `mcp-servers.json` に置き、Codex 固有の実行最適化は `.codex/agents/*` / `.codex/skills/*` に置く。Claude Code 専用の深い運用は `.claude/` に残す。

通常の親は Astra / high、範囲が明確な実装は `worker`（Luna / max）、難所は `expert`（Sol / high）、特に難しい解析は `expert_max`（Sol / max）を使う。小変更や全体設計と密接な修正は Astra が直接処理する。子の並列数はアクティブ設定の `max_concurrent_threads_per_session` と実行時の空き枠の低い方に従い、設定値を埋めることは要求しない。完了済みを空き枠と推測せず、各担当の編集ファイルを分ける。Terra は実測で有効な用途だけの例外とする。

モデル・機能の生成元は `.codex/config.base.toml`、実行原則は `.codex/codex-native-supplement.md`、委任の詳細は `.codex/skills/worker-delegation/SKILL.md`。設定後は新規セッションで確認する。実験的コンテキスト管理と Memories は独立して扱う。

許可済みの作業を継続し、必要な承認の前に確認可能な成果物を準備する。Skillで停止する場合は、実際に読んだ規則とエージェントの解釈、実環境の制約を区別して報告する。共通規則は `AGENTS.md` の `Execution And Skill Priority` を参照。

OpenAI仕様は利用可能な公式 `openai-docs` skill、または公式ドキュメントで確認する。Codex運用設定とアプリのAPI移行は別範囲。Responses API標準Multi-agentは同じリクエストのモデルを共有するため、CodexのAstra/Luna/Sol分担とは区別する。実作業の計測はAstra直接処理と委任を同じ合格条件で比較し、親の説明・確認・再試行も含める。詳しい境界と計測項目は `AI-WORKFLOW-SPEC.md` を参照。

- 生成: `bash ~/dotfiles/etc/sync-codex.sh`
- 生成物: `.codex/config.toml`, `.codex/AGENTS.md`
- Codex native overlays: `.codex/agents/*.toml`, `.codex/skills/*`
- legacy mirror 再生成（通常は使わない）: `SYNC_CODEX_LEGACY_MIRROR=1 bash ~/dotfiles/etc/sync-codex.sh`
- 共通スキル: `.agents/skills/*` が shared skill core。Codex 固有の調整は `.codex/skills/*` 側で行う
- dotfiles 内実行: `AGENTS.override.md` が project guidance になり、global `~/.codex/AGENTS.md` と root `AGENTS.md` の二重ロードを避ける
- 自動追従: `.claude/settings.json` の PostToolUse hook が `~/.claude/lib/sync-codex-hook.sh` を呼ぶ
- 展開: `etc/link.sh` は `~/.codex` の設定・agents をリンクし、`.agents/skills` は dotfile ループで `~/.agents/skills` として展開する
- motitan Unity 専用入口: `codex-motitan` は `motitan-automata` root からだけ起動でき、`-p motitan` と sibling の `motitan_app` を Codex に渡す。専用 profile は `danger-full-access` + `approval_policy = "never"` だが、通常の `codex` 設定は変更しない。launcher は両リポジトリの `AGENTS.md` と automata 側 `scripts/unity-cli.sh` を起動前に検証し、Unity 操作はその wrapper 経由に限定する
- launcher 展開: `bash etc/link.sh --codex-motitan-only` は既存の `$HOME/bin` directory と対象外コマンドを保持したまま、`$HOME/bin/codex-motitan` と `~/.codex/motitan.config.toml` だけを管理 symlink にする。同名の非 symlink target は上書きせず fail closed。通常の `bash etc/link.sh` も同じ2点を全体展開の一部として配布する

## Cursor / Grok の分離

Cursor は通常の Task モデル継承を維持し、`deepthink` / `deepplan` の指定された思考担当だけ Fable を使う。Cursorからの `/codex` / `/pir2codex` は明示的なCLI連携で、通常作業はLuna max、難所はSol high/maxを選ぶ。Cursor自身のモデル設定とは別管理。

Grok は `.grok/rules/runtime.md` で共有の作業方針と固有の実行機構を分離する。`etc/link.sh` が個別ルールを `~/.grok/rules` へリンクし、既存の実ファイル・別リンクを保全する。Grokのモデル・権限・認証・MCPは変更しない。Cursor/Claude互換で見つかったSkillsも、実際のGrokのツール・設定で利用できる範囲だけ使う。

設定の所有範囲と生成・配布経路は [AI-WORKFLOW-SPEC.md](AI-WORKFLOW-SPEC.md) を参照。

## OpenCode 統合

OpenCode は generated adapter 方針で運用する（`AI-WORKFLOW-SPEC.md` の Migration State 参照）。共通ルール・エージェント・MCP・permission は shared core から機械生成し、OpenCode 固有の調整（ツール名読み替え・スキル可否分類・互換ギャップ）は生成 `AGENTS.md` 末尾の補足ルールセクションに集約する。native overlay 化は runtime 需要が分化するまで見送り。

- 生成: `bash ~/dotfiles/etc/sync-opencode.sh`
- 生成物: `~/.config/opencode/opencode.json`, `~/.config/opencode/AGENTS.md`, `~/.config/opencode/agents/*.md`, `~/.config/opencode/plugins/*`
- SSOT: `mcp-servers.json`（`claudeCodeOnly` / `codexOnly` を除外）+ `AGENTS.md` + `.claude/agents/*.md`。permission は OpenCode 専用ポリシー（bash allow 既定 + 危険操作 ask、edit allow、read は settings.json の deny リストを継承、external_directory は `~/**` allow — OpenCode 既定 ask + "always" 承認がセッション限定のため cwd 外参照で承認地獄になるのを恒久解消）を sync script 内で生成。`lsp: true` も明示設定（OpenCode はデフォルト無効のため）
- plugin: `.opencode/plugins/*`（repo 側 SSOT、手書き編集可）を `~/.config/opencode/plugins/` へベリファイコピー。OpenCode に settings.json 形式の hooks はないため、PreToolUse / PostToolUse / Stop 相当は plugin の `tool.execute.before` / `tool.execute.after` / `session.idle` で実現する。第一弾 `secret-guard.js` は read/edit/write と bash での credential 系パスアクセスを block。孤児削除・手書き保護ルールは agents と同一
- エージェント: `.claude/agents/*.md` から frontmatter を `description` / `mode: subagent` / `model` に縮約して生成。バラ alias（sonnet/opus/fable）は `anthropic/<id>` 形式に変換。frontmatter の `tools:` 制限は引き継がないため、本文の権限線引きは補足ルールの読み替えに依存する
- スキル: `opencode.json` に `skills` キーは書かず、OpenCode 外部スキル自動発見（`~/.agents/skills/*` / `~/.claude/skills/*`）に全依存。`link.sh` が展開する `~/.agents` symlink が前提で、切れると全共有スキルが沈黙する
- 反映: config は opencode 起動時に一度だけ読まれるため、sync 後は opencode の再起動が必要

## 契約テスト

cursor / opencode / shared-drift / codex-motitan / antigravity の各契約テストをまとめて実行する集約ランナー:

```sh
bash etc/test-all-contracts.sh
```

`bash etc/test-all-contracts.sh --full` は、通常のadapter確認に加えて、隔離fixtureでCodex設定生成、dotfiles同期、worker runner、記憶検索・同期、runtime別の更新対象選択、Antigravityの承認判定を検証する。本番の記憶DBや外部リポジトリ更新はテスト対象にしない。

`test-cursor-contracts.sh`（`sync-cursor --check` を含む）、`test-opencode-contracts.sh`（`sync-opencode --check`・冪等性・agent 変換契約・孤児削除を含む）、`check-shared-drift.sh`、`test-codex-motitan-contract.sh`（専用 profile / launcher / runtime link / `$HOME/bin` の非破壊展開）、`test-antigravity-contracts.sh`（生成・check・失敗時の保全）を実行し、どれが PASS/FAIL したかを集計表示する。テスト集約では、どれかが失敗しても残りを実行し（fail-fast しない）、1 本でも FAIL なら終了コード 1 を返す。この挙動はテスト結果の集計に限られ、実際の sync/link 失敗を成功扱いにはしない。

単独実行も可能:

```sh
bash etc/test-opencode-contracts.sh   # OpenCode 契約のみ
bash etc/sync-opencode.sh --check     # drift 検出のみ（書き込みなし）
```

## MCP サーバー管理

Claude Code の MCP (Model Context Protocol) サーバーは **2 系統** で管理する。Claude Code には「dotfiles から一元管理する公式ルート」が存在しないため、user scope 用の sync スクリプトと project scope 用の `.mcp.json` を併用する。

| スコープ | SSOT | 適用範囲 |
|---------|------|---------|
| **user** | `mcp-servers.json` → `etc/sync-mcp.sh` で `~/.claude.json` に sync | 全プロジェクト共通（現行は `context7` / `notion`。実体は `mcp-servers.json` を参照） |
| **project** | 各リポ直下の `.mcp.json` を git commit | そのリポでのみ有効（`${PWD}` に依存する `serena` など） |

### 新規マシンでの初回セットアップ

`install.sh` / `etc/init.sh` が最後に `sync-mcp.sh` を自動実行するため、通常は何もしなくてよい。ただし **Claude Code CLI が未インストールの状態で初回セットアップを走らせた場合は sync が skip される**（冪等設計）。後から手動で叩く:

```sh
bash ~/dotfiles/etc/sync-mcp.sh
```

### `mcp-servers.json` を編集したあと

同じコマンドを再実行すれば差分が反映される（既存登録を remove してから再 add する冪等動作）:

```sh
bash ~/dotfiles/etc/sync-mcp.sh
```

### 他プロジェクトで serena を使いたい

このリポの `.mcp.json` をコピーして、対象リポ直下に置いて commit する:

```sh
cp ~/dotfiles/.mcp.json <target-repo>/.mcp.json
```

### 注意事項

- `claude` コマンドに alias（`--mcp-config` 注入）は張らない。非対話シェル・サブプロセス起動で破綻するため廃止済み
- `~/.claude.json` は sync 結果が書き込まれる **生成物** なので git 管理しない
- dotfiles 直下の `.mcp.json` は `etc/link.sh` の除外対象で `~/.mcp.json` にはリンクされない（ホーム直下に置くと全 cwd に影響するため）

## 前提条件

- **GitHub CLI (gh)**: Neovim の telescope-github.nvim で使用
  - macOS: `brew install gh`
  - Ubuntu: `sudo apt install gh`

## Notes

- 絶対パスを含むシンボリックリンクをリポジトリにコミットしない
- Neovim 設定のリンク: `sh etc/link.sh` または `ln -snfv "$PWD/.config/nvim" "$HOME/.config/nvim"`
- Linux は Ubuntu をターゲット、apt ベースのツールを優先
