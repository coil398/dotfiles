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
- **AI Coding Agent 統合** — Claude Code / Codex / OpenCode 向け PIR² ワークフロー、共有スキル

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
│   ├── skills/             # Claude 入口（共有スキルへの symlink と native スキル）
│   └── settings.json       # 権限設定
├── AGENTS.md               # AI agent shared core guidance
├── AGENTS.override.md      # dotfiles 内 Codex 実行時の軽量 project guidance
├── AI-WORKFLOW-SPEC.md     # スキル配置・サブエージェント・生成配布の運用仕様
├── .codex/                 # Codex 設定・生成物
│   ├── AGENTS.md           # Codex generated guidance
│   ├── codex-native-supplement.md # Codex 固有の委譲・モデル選択方針
│   ├── config.base.toml    # 手書き Codex 固有設定
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
├── bin/                    # CLI ユーティリティ
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
| `etc/sync-opencode.sh` | AI ワークフロー SSOT から `~/.config/opencode/opencode.json` / `AGENTS.md` を生成 |
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

Claude Code のスキルは `.claude/skills/<name>` から共有原本 `.agents/skills/<name>` へのsymlinkを基本とし、`codex` / `deepthink` / `design-review` だけ native 入口を置く。カスタムエージェント定義は置かず、スキルが `general-purpose` サブエージェントへ手順ファイルのパスを渡して起動する。設定は `.claude/` を原本とし、`etc/link.sh` で `$HOME/.claude/` にリンクされる。各 runtime のスキル配置、サブエージェント、model / effort の決まり方は [AI-WORKFLOW-SPEC.md](AI-WORKFLOW-SPEC.md) を参照。

主なスキル: `/pir2`, `/ir`, `/review-pr`, `/debug`, `/tester`, `/brainstorm`, `/writing-plan`

## Codex 統合

Codex は `.agents/skills/*` を直接読む。モデル設定は [config base](.codex/config.base.toml)、委譲とモデル選択の方針は [native supplement](.codex/codex-native-supplement.md) が正本。詳細は [AI-WORKFLOW-SPEC.md](AI-WORKFLOW-SPEC.md) を参照。

- 生成: `bash ~/dotfiles/etc/sync-codex.sh`（生成物: `.codex/config.toml`, `.codex/AGENTS.md`）
- Codex/Cursorだけを生成・配布: `bash ~/dotfiles/etc/link.sh --codex-cursor-only`
- dotfiles 内実行: `AGENTS.override.md` が project guidance になり、global `~/.codex/AGENTS.md` と root `AGENTS.md` の二重ロードを避ける

## Cursor / Grok の分離

Cursor の全チャット共通指示は、Settings → Customize → Rules の User スコープに登録する。`etc/link.sh` は `~/.cursor/rules/shared-agents.mdc` を展開するが、ファイル配置だけで User Rules 登録済みとは扱わない。User Rule に「各セッション開始時に `~/dotfiles/AGENTS.md` と `~/.cursor/rules/shared-agents.mdc` を読み、作業先の AGENTS.md も適用する。Cursor スキルは `~/.cursor/skills` を優先する」と登録し、一覧の User Rule 表示を確認する。dotfiles が別の場所にある場合は実際の絶対パスを使う。以後の共有指示更新は参照先へ反映する。

Cursor の `.cursor/skills/*` は共有Skillを読む薄い入口で、`etc/link.sh` が `~/.cursor/skills` へ実体コピーする。Grok は `.grok/rules/runtime.md` を `~/.grok/rules` へリンクする。Task のモデル、Fable の例外、生成・配布経路は [AI-WORKFLOW-SPEC.md](AI-WORKFLOW-SPEC.md) を参照。

## OpenCode 統合

OpenCode は generated adapter 方針で運用する。生成内容は `AI-WORKFLOW-SPEC.md` の sync-opencode.sh Contract を参照。

- 生成: `bash ~/dotfiles/etc/sync-opencode.sh`
- 生成物: `~/.config/opencode/opencode.json`, `~/.config/opencode/AGENTS.md`, `~/.config/opencode/plugins/*`
- plugin: `.opencode/plugins/*`（repo 側 SSOT）。第一弾 `secret-guard.js` は read/edit/write と bash での credential 系パスアクセスを block
- 反映: config は opencode 起動時に一度だけ読まれるため、sync 後は opencode の再起動が必要

## 契約テスト

cursor / opencode / shared-drift / antigravity の各契約テストをまとめて実行する集約ランナー:

```sh
bash etc/test-all-contracts.sh
```

`bash etc/test-all-contracts.sh --full` は、通常のadapter確認に加えて、隔離fixtureでCodex設定生成、dotfiles同期、worker runner、記憶検索・同期、runtime別の更新対象選択、Antigravityの承認判定を検証する。本番の記憶DBや外部リポジトリ更新はテスト対象にしない。

`test-cursor-contracts.sh`（`sync-cursor --check` を含む）、`test-opencode-contracts.sh`（`sync-opencode --check`・冪等性・agent 変換契約・孤児削除を含む）、`check-shared-drift.sh`、`test-antigravity-contracts.sh`（生成・check・失敗時の保全）を実行し、どれが PASS/FAIL したかを集計表示する。テスト集約では、どれかが失敗しても残りを実行し（fail-fast しない）、1 本でも FAIL なら終了コード 1 を返す。この挙動はテスト結果の集計に限られ、実際の sync/link 失敗を成功扱いにはしない。

単独実行も可能:

```sh
bash etc/test-opencode-contracts.sh   # OpenCode 契約のみ
bash etc/sync-opencode.sh --check     # drift 検出のみ（書き込みなし）
```

## MCP サーバー管理

Claude Code の MCP (Model Context Protocol) サーバーは **2 系統** で管理する。Claude Code には「dotfiles から一元管理する公式ルート」が存在しないため、user scope 用の sync スクリプトと project scope 用の `.mcp.json` を併用する。

| スコープ | SSOT | 適用範囲 |
|---------|------|---------|
| **user** | `mcp-servers.json` → `etc/sync-mcp.sh` で `~/.claude.json` に sync | 全プロジェクト共通（Claude は `context7`。`openCodeOnly` のサーバーは OpenCode にのみ配布） |
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

対象リポの実行環境に合わせて `.mcp.json` を作成する。dotfiles にはコピー用の project MCP 設定を置いていない。

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
