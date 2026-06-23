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
├── AI-WORKFLOW-SPEC.md     # Claude/Codex/OpenCode の shared core + native overlays 確定仕様
├── .codex/                 # Codex 設定・生成物
│   ├── AGENTS.md           # Codex generated guidance
│   ├── agents/             # Codex-native custom agents (*.toml)
│   └── config.base.toml    # 手書き Codex 固有設定
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
├── bin/                    # tmux ステータスバー用ユーティリティ
├── .zsh/                   # Docker 補完, dircolors-solarized
└── options/                # clangd 用コンパイルフラグ
```

## セットアップスクリプトの役割

| スクリプト | 用途 |
|-----------|------|
| `install.sh` | **Codespaces 専用**。apt パッケージ・prebuilt バイナリ・zplug のインストール、symlink 展開、zsh デフォルト化、Neovim プラグインインストール |
| `etc/init.sh` | 新規マシン向け。dotfiles を clone → `set.sh` → `link.sh` を実行 |
| `etc/link.sh` | `$HOME/dotfiles/.??*` を `$HOME/` に symlink。`.claude/` / `.codex/` は個別にリンク。`.mcp.json` は除外 |
| `etc/set.sh` | OS 判定、GNOME Terminal カラー設定、ディレクトリ構成の整理 |
| `etc/load.sh` | OS 判定 (`is_osx`, `is_linux`)、テキスト操作、出力ヘルパー等のシェル関数 |
| `etc/sync-mcp.sh` | `mcp-servers.json` を読み、`claude mcp add-json -s user` で `~/.claude.json` に登録。`install.sh` / `etc/init.sh` 末尾で自動実行 |
| `etc/sync-opencode.sh` | AI ワークフロー SSOT から `~/.config/opencode/opencode.json` / `AGENTS.md` / agents を生成 |
| `etc/sync-codex.sh` | AI ワークフロー SSOT から Codex native `.codex/config.toml` / `AGENTS.md` / TOML agents / skill mirror を生成 |

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

## Claude Code 統合

Claude Code は既存のネイティブ運用を維持する。PIR² ワークフロー（Plan → Implement → Review → Retrospect）やカスタムスキルは `.claude/` で管理し、Codex/OpenCode 向け adapter から逆生成しない。`etc/link.sh` で `$HOME/.claude/` にリンクされるため、全プロジェクトで共有される。

主なスキル: `/pir2`, `/ir`, `/review-pr`, `/debug`, `/tester`, `/brainstorm`, `/writing-plan`

## Codex 統合

Codex は `AI-WORKFLOW-SPEC.md` の **shared core + native overlays** 方針で運用する。移植可能な共通ルールは `AGENTS.md`, `.agents/skills/*`, `mcp-servers.json` に置き、Codex 固有の実行最適化は `.codex/agents/*` / `.codex/skills/*` に置く。Claude Code 専用の深い運用は `.claude/` に残す。

- 生成: `bash ~/dotfiles/etc/sync-codex.sh`
- 生成物: `.codex/config.toml`, `.codex/AGENTS.md`
- Codex native overlays: `.codex/agents/*.toml`, `.codex/skills/*`
- legacy mirror 再生成（通常は使わない）: `SYNC_CODEX_LEGACY_MIRROR=1 bash ~/dotfiles/etc/sync-codex.sh`
- 共通スキル: `.agents/skills/*` が shared skill core。Codex 固有の調整は `.codex/skills/*` 側で行う
- dotfiles 内実行: `AGENTS.override.md` が project guidance になり、global `~/.codex/AGENTS.md` と root `AGENTS.md` の二重ロードを避ける
- 自動追従: `.claude/settings.json` の PostToolUse hook が `~/.claude/lib/sync-codex-hook.sh` を呼ぶ
- 展開: `etc/link.sh` は `~/.codex` の設定・agents をリンクし、`.agents/skills` は dotfile ループで `~/.agents/skills` として展開する

## MCP サーバー管理

Claude Code の MCP (Model Context Protocol) サーバーは **2 系統** で管理する。Claude Code には「dotfiles から一元管理する公式ルート」が存在しないため、user scope 用の sync スクリプトと project scope 用の `.mcp.json` を併用する。

| スコープ | SSOT | 適用範囲 |
|---------|------|---------|
| **user** | `mcp-servers.json` → `etc/sync-mcp.sh` で `~/.claude.json` に sync | 全プロジェクト共通（`context7`, `github`, `sequential-thinking` 等） |
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
