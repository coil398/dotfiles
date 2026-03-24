# CLAUDE.md

このファイルはリポジトリ内で作業する Claude Code (claude.ai/code) へのガイダンスを提供する。

## このリポジトリの目的

個人用 dotfiles リポジトリ。macOS / Linux (Ubuntu) / WSL 対応。GitHub Codespaces での利用を主軸に設計されている。

## セットアップコマンド

```sh
# 新規マシン (curl で init)
curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/init.sh | sh

# シンボリックリンクの再展開
sh etc/link.sh

# Codespaces 初回セットアップ (install.sh が自動実行される)
bash install.sh
```

## リポジトリ構造と役割

### ディレクトリ概観

```
dotfiles/
├── シェル設定          .zshrc, .zsh_alias, .zplugrc
├── ターミナル          .wezterm.lua, .config/alacritty/
├── エディタ            .config/nvim/, .vimrc
├── tmux                .tmux/.tmux.conf, bin/tmuxx
├── AI/IDE 統合         .claude/, mcp-servers.json
├── セットアップ        install.sh, etc/
├── コンテナ            .devcontainer/, .github/workflows/
├── ユーティリティ      bin/, options/
└── パッケージ定義      .default-npm-packages, .default-golang-pkgs
```

### シェル設定

- `.zshrc` — メインの zsh 設定。PATH（cargo, ghcup, anyenv, Go, snap, CUDA 等）、補完、プロンプト（vcs_info による Git 情報表示）、fzf / direnv / zoxide 統合、tmux 自動起動（VSCode 除外）。`etc/load.sh` と `.zsh_alias` を source する
- `.zsh_alias` — エイリアス定義。`eza`(ls), `bat`(cat), `procs`(ps), `rg`(grep), `nvim`(vim), `kubectl`(k), `docker-compose`(dc), `terraform`(tf) 等。グローバルエイリアス（`L`, `H`, `G`, `GI`）も定義。`claude` コマンドに `--mcp-config` を付与
- `.zplugrc` — zplug プラグイン定義。zsh-completions, zsh-syntax-highlighting, zsh-autosuggestions, zsh-history-substring-search, fzf, anyframe, git-conflict 等
- `.zsh_secret.template` — 環境変数のシークレット定義テンプレート（`.zsh_secret` は gitignore 対象）
- `.zsh/` — Docker 補完スクリプト、dircolors-solarized カラーパレット

### セットアップスクリプト

- `install.sh` — **Codespaces 専用**。apt パッケージ（zsh, tmux, ripgrep, fd, bat, colordiff, tig, fzf 等）、prebuilt バイナリ（nvim, eza, procs — amd64/arm64 対応）、zplug のインストール。`etc/link.sh` の実行、zsh のデフォルトシェル設定、Neovim プラグインのヘッドレスインストール。冪等設計（`has()` チェックで既インストール時はスキップ）
- `etc/link.sh` — `$HOME/dotfiles/.??*` を `$HOME/` にシンボリックリンク展開（`.git`, `.gitignore`, `.DS_Store`, `.claude` は除外）。`.tmux/.tmux.conf` → `$HOME/.tmux.conf`。`.claude/` は `settings.json`, `.mcp.json`, `CLAUDE.md`, `statusline-command.sh`, `agents/`, `skills/` を個別に `$HOME/.claude/` へリンク
- `etc/init.sh` — 新規マシン向け。dotfiles を git clone → `etc/install/homebrew/install.sh` → `etc/set.sh` → `etc/link.sh` を実行
- `etc/set.sh` — OS 判定（Darwin/Linux）。Linux: GNOME Terminal Solarized 配色、apt install、`~/.config` バックアップ＆symlink 化
- `etc/load.sh` — シェル共通ユーティリティ関数ライブラリ（約450行）。OS 判定（`is_osx`, `is_linux`, `is_bsd`）、テキスト操作（`lower`, `upper`, `contains`）、PATH 操作（`path_remove`）、出力ヘルパー（`e_error`, `e_warning`, `e_done`, `ink`, `logging`）、条件判定（`is_login_shell`, `is_git_repo`, `is_ssh_running`）
- `etc/install/homebrew/` — Homebrew インストール（macOS / LinuxBrew）
- `etc/install/apt/` — apt パッケージインストール

### Neovim

- `.config/nvim/init.lua` — エントリポイント。macOS/Linux で `mac.lua`/`linux.lua` を分岐読み込み。VSCode 検出時はプラグインを無効化
- `.config/nvim/lua/init.lua` — プラグイン設定（lazy.nvim）。Mason（LSP/DAP/Formatter 自動インストール）、Telescope（ファジーファインダ）、Neo-tree（ファイルエクスプローラ）、nvim-lspconfig、Treesitter、Copilot.lua、Neogit、Gitsigns、Lualine、Navic、WhichKey、Noice 等
- `.config/nvim/lua/keymappings.lua` — キーバインド定義
- `.config/nvim/lua/lsp.lua` — LSP 設定（Mason, nvim-cmp 補完）
- `.config/nvim/lua/color.lua` — カラースキーム（VS Code / Tokyonight）
- `.config/nvim/lua/auto.lua` — 自動コマンド
- `.config/nvim/lua/mac.lua` / `linux.lua` — OS 固有設定

### tmux

- `.tmux/.tmux.conf` — Prefix: `C-q`。ペイン操作（Alt+hjkl 移動, `|` 縦分割, `-` 横分割）。ステータスバー上部表示（Git リポ/ブランチ/ダーティ状態, CPU/メモリ使用率, 日時）。VS Code Dark テーマ。プラグイン: tmux-resurrect（セッション復元）, tmux-continuum（15分自動保存）, tmux-yank（クリップボード）, tmux-fzf（`C-f` ランチャー）, tmux-mem-cpu-load
- `bin/tmuxx` — tmux セッション管理スクリプト
- `bin/` — tmux ステータスバー用ユーティリティ（battery, cpu, gpu_temp, wifi, volume 等）

### ターミナル

- `.wezterm.lua` — WezTerm 設定。Cica + Symbols Nerd Font (10pt)、Tab 無効、VS Code Dark+ テーマ、WSL: Arch、macOS: IME 設定
- `.config/alacritty/` — Alacritty ターミナル設定

### Codespaces / Docker

- `.devcontainer/Dockerfile` — `mcr.microsoft.com/devcontainers/base:ubuntu-24.04` ベース。nvim・eza・procs・各種 apt ツールを焼き込み。amd64/arm64 両対応
- `.devcontainer/devcontainer.json` — dotfiles リポジトリ自体を Codespaces で開く際の設定。`ghcr.io/coil398/dotfiles:latest` を参照
- `.github/workflows/docker-publish.yml` — master push（Dockerfile 変更時）/ 毎週月曜 AM 2:00 JST / 手動実行で Docker イメージをマルチプラットフォーム（linux/amd64, linux/arm64）ビルドして `ghcr.io/coil398/dotfiles:latest` に push

他のプロジェクトリポジトリで prebuilt イメージを使う場合は以下の `devcontainer.json` を追加する：
```json
{
  "image": "ghcr.io/coil398/dotfiles:latest",
  "remoteUser": "vscode"
}
```

### MCP サーバー設定

- `mcp-servers.json` — Claude Code 用 Model Context Protocol サーバー定義。fileSystem（~/ghq）、github、brave-search、serena（IDE 補助）、codex、sequential-thinking、context7、playwright

### その他設定ファイル

- `.vimrc` — Vim 互換レイヤー（Neovim へリダイレクト）
- `.tigrc` — tig（Git UI）キーバインド
- `.ctags` — Universal Ctags 対象言語設定
- `.imwheelrc` — マウスホイール設定
- `.gitignore_global` / `.globalgitignore` — グローバル gitignore
- `.default-npm-packages` — anyenv 用グローバル npm パッケージ（dockerfile-language-server-nodejs, neovim, npm-check-updates）
- `.default-golang-pkgs` — デフォルト Go パッケージ（golang.org/x/tools, ghq, efm-langserver）
- `options/compile_flags_{linux,mac}.txt` — clangd 用コンパイルフラグ
- `package.json` — 空ファイル（npm workspace 互換用）

## `.claude/` — Claude Code カスタマイズ

`etc/link.sh` によって `$HOME/.claude/` にシンボリックリンクされるため、dotfiles リポジトリで一元管理される。

### PIR² ワークフロー (`/pir2`)

コーディングタスクを **Plan → Implement → Review → Retrospect** の4フェーズで実行するカスタムワークフロー。

```
/pir2 <タスク>
```

フェーズ構成：
1. **planner** (Opus) — 実装プランを構造化フォーマットで出力
2. **implementer** (Sonnet) — プランを実行してコードを書く
3. **reviewer** (Sonnet) — `VERDICT: PASS/FAIL` を判定
4. レビューループ — FAIL の場合は implementer → reviewer を最大3回繰り返す
5. **retrospector** — パターンをグローバルレジストリ (`~/.claude/memory/pir_pattern_registry.md`) に記録し、複数プロジェクトで繰り返されたパターンのみエージェント定義に還流する

### エージェント定義 (`.claude/agents/`)

| ファイル | 役割 |
|---------|------|
| `planner.md` | 実装プランを構造化フォーマットで出力 |
| `implementer.md` | プランに基づきコードを書く（プラン外変更禁止） |
| `reviewer.md` | PASS/FAIL 判定と問題の構造化出力 |
| `retrospector.md` | パターン汎化とエージェント定義の自動改善 |
| `tech-validator.md` | ライブラリ選定・技術検証 |
| `tester.md` | 動作検証（テスト実行・アドホック確認） |

`<!-- CORE --> 〜 <!-- /CORE -->` セクションは retrospector による自動改善でも変更禁止。

### スキル (`.claude/skills/`)

各スキルの詳細は SKILL.md フロントマターを参照。

| スキル | 用途 |
|--------|------|
| `/pir2` | Plan → Implement → Review → Retrospect フルワークフロー |
| `/ir` | 軽量 Implement → Review（Plan なし） |
| `/review-pr` | PR・ブランチ・差分のコードレビュー |
| `/debug` | エラー診断 → 修正 → レビュー |
| `/tester` | 動作検証（テスト実行・アドホック確認） |
| `/brainstorm` | 対話で設計を固める（`docs/brainstorm/` に保存） |
| `/writing-plan` | 計画 → ステップ実装 → 記録（`docs/plans/`） |
| `/retro` | retrospector 単体実行 |
| `/check-updates` | git 管理スキル・プラグインの更新チェック＆自動 pull |

### Claude Code 設定 (`.claude/settings.json`)

- 権限: Read, Grep, Glob, 限定 Bash, WebSearch 等を許可。`rm -rf`, `git push --force`, `sudo` 等は拒否
- プラグイン: gopls, rust-analyzer, skill-creator
- `alwaysThinkingEnabled: true`, `temperature: 0`
- ステータスライン: `npx ccusage` で使用量表示

## 編集時の注意事項

- シェルスクリプト (`install.sh`, `etc/*.sh`) は **冪等性** を維持すること。`has()` や `command -v` チェックを使う
- `install.sh` は Codespaces 専用。一般的な Linux/macOS セットアップは `etc/init.sh` を使う
- `etc/link.sh` に新しい dotfile を追加する場合、除外リスト（`.git`, `.gitignore`, `.DS_Store`, `.claude`）を確認する
- `.claude/` 配下の変更は全プロジェクトに影響する（グローバルにリンクされるため）
- Neovim プラグインの追加・変更は `.config/nvim/lua/init.lua` で行う。`lazy-lock.json` は自動更新される
- Docker イメージの変更は `.devcontainer/Dockerfile` を編集し、master push で自動ビルドされる
- `.zshrc` の PATH 追加は OS 分岐（`is_osx` / `is_linux`）を考慮する
- tmux 設定変更後は `tmux source-file ~/.tmux.conf` で反映確認
