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

- `.zshrc` — メインの zsh 設定。PATH（cargo, ghcup, mise, Go, snap, CUDA 等）、補完、プロンプト（vcs_info による Git 情報表示）、fzf / direnv / zoxide 統合、tmux 自動起動（VSCode 除外）。`etc/load.sh` と `.zsh_alias` を source する
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

dotfiles を SSOT として管理するが、Claude Code には「dotfiles から MCP を一元管理する公式ルート」が存在しないため、**user scope に sync する仕組み**＋**project scope は各リポに `.mcp.json` を commit** の2系統で運用する。

- `mcp-servers.json` — **user scope 用 SSOT**。個人グローバルに効かせたい MCP（fileSystem, github, brave-search, codex, sequential-thinking, context7, playwright）を定義
- `etc/sync-mcp.sh` — `mcp-servers.json` を読み、`claude mcp add-json -s user` 経由で `~/.claude.json` に登録する冪等スクリプト。JSON を編集したら再実行する
- `.mcp.json`（dotfiles リポ直下） — **project scope の例**。`${PWD}` に依存する `serena` のように user scope と相性が悪いものを置く。このファイルは `etc/link.sh` の除外対象で `~/.mcp.json` にはリンクされない
- 他プロジェクトで serena 等を使いたい場合は、該当リポに `.mcp.json` を commit する
- `claude` コマンドに alias は張らない（`--mcp-config` 方式は非対話シェル・サブプロセス起動で破綻するため廃止済み）

### その他設定ファイル

- `.vimrc` — Vim 互換レイヤー（Neovim へリダイレクト）
- `.tigrc` — tig（Git UI）キーバインド
- `.ctags` — Universal Ctags 対象言語設定
- `.imwheelrc` — マウスホイール設定
- `.gitignore_global` / `.globalgitignore` — グローバル gitignore
- `.default-npm-packages` — Node.js インストール時の自動グローバルパッケージ（dockerfile-language-server-nodejs, neovim, npm-check-updates）
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

フェーズ構成（スキル本体がオーケストレーター）：
1. **スキル本体（メイン Claude）** — PIR²オーケストレーター。`.claude/skills/pir2/SKILL.md` に書かれた手順に従い、explorer → planner → implementer → reviewer → tester → retrospector を `Agent` ツールで順に起動・制御する。レビューループ（max 3回）・テストループ（max 3回）の管理もスキル本体が行う
   - Claude Code はサブエージェント内からの `Agent` ツール呼び出しを禁止しているため、オーケストレーションは必ずスキル本体（= サブエージェントでないメイン Claude）に置く。サブエージェント（planner 等）にオーケストレーション責務を持たせてはならない
2. **planner** (Opus) — プラン策定専任。スキル本体から探索レポートを受け取り、implementer が実行できる実装プランを返す
3. **retrospector** — パターンをグローバルレジストリ (`~/.claude/memory/pir_pattern_registry.md`) に記録し、複数プロジェクトで繰り返されたパターンのみエージェント定義に還流する

### エージェント定義 (`.claude/agents/`)

| ファイル | 役割 |
|---------|------|
| `planner.md` | プラン策定専任。スキル本体から探索レポートを受け取り、実装プランを返す（オーケストレーション責務は持たない） |
| `implementer.md` | プランに基づきコードを書く（プラン外変更禁止） |
| `reviewer.md` | PASS/FAIL 判定と問題の構造化出力 |
| `retrospector.md` | パターン汎化とエージェント定義の自動改善 |
| `tech-validator.md` | ライブラリ選定・技術検証 |
| `tester.md` | 動作検証（テスト実行・アドホック確認） |
| `explorer.md` | コードベース探索と構造化探索レポートの出力 |

`<!-- CORE --> 〜 <!-- /CORE -->` セクションは retrospector による自動改善でも変更禁止。

> 例外: 2026-04-18 のオーケストレーション移管リファクタで `explorer.md` CORE 内の「planner から受け取った」等、旧設計（planner がオーケストレーター）を前提とした表現を呼び出し元抽象名に修正した。また同リファクタで `planner.md` CORE の役割記述を「PIR²オーケストレーター（全フェーズ一貫制御）」から「プラン策定専任（スキル本体が起動・結果を受け取る）」に書き換え、出力フォーマット指定も統合レポートからプランレポートに変更した。この種の「動かない旧設計の残骸を実態に合わせる修正」は意図的な例外であり、retrospector がメタモードでロールバックしてはならない。

### スキル (`.claude/skills/`)

各スキルの詳細は SKILL.md フロントマターを参照。

| スキル | 用途 |
|--------|------|
| `/pir2` | Plan → Implement → Review → Retrospect フルワークフロー |
| `/ir` | 軽量 Implement → Review（Plan なし） |
| `/review-pr` | PR・ブランチ・差分のコードレビュー |
| `/refactor-advisor` | refactor-advisor 単体実行（Medium/Low 相当のリファクタ提案。/pir2 外で使う） |
| `/debug` | エラー診断 → 修正 → レビュー |
| `/tester` | 動作検証（テスト実行・アドホック確認） |
| `/brainstorm` | 対話で設計を固める（`docs/brainstorm/` に保存） |
| `/writing-plan` | 計画 → ステップ実装 → 記録（`docs/plans/`） |
| `/walkthrough` | コードリーディング支援（差分・ファイル・PR・ブランチ対応。詳細化対話ループ付き） |
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
- Neovim 設定（`.config/nvim/`）で `vim.lsp.*` を呼ぶコードを追加・変更するときは、**採用予定 API が現行 Neovim（本リポジトリが対応する最低版〜最新版の範囲）で deprecated ではない**ことを公式 runtime doc と `:checkhealth vim.deprecated` 相当の廃止予定リストで確認する。特に 0.11→0.12 で handler 系（`vim.lsp.with()` / `vim.lsp.handlers` 直上書き）、`make_range_params` の引数、`execute_command`、`get_active_clients` などが段階的に deprecated になっているため、新規コードに古い呼び出し方式を書かないこと。hover/signature_help に `border` を渡す用途は `vim.lsp.buf.hover({ border = "rounded" })` のキーマップ経由方式を採用する
