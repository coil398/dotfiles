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
├── Git hooks           .githooks/ (グローバル pre-commit dispatcher)
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

- `install.sh` — **Codespaces 専用**。apt パッケージ（zsh, tmux, ripgrep, fd, bat, colordiff, tig, fzf 等）、prebuilt バイナリ（nvim, eza, procs, **gitleaks** — amd64/arm64 対応）、zplug のインストール。`etc/link.sh` の実行、zsh のデフォルトシェル設定、Neovim プラグインのヘッドレスインストール。冪等設計（`has()` チェックで既インストール時はスキップ）
- `etc/link.sh` — `$HOME/dotfiles/.??*` を `$HOME/` にシンボリックリンク展開（`.git`, `.gitignore`, `.DS_Store`, `.claude`, `.mcp.json` は除外）。`.tmux/.tmux.conf` → `$HOME/.tmux.conf`。`.claude/` は `settings.json`, `.mcp.json`, `CLAUDE.md`, `format.md`, `pir-handoff.md`, `agents/`, `skills/`, `lib/` を個別に `$HOME/.claude/` へリンク。さらに `git config --global core.hooksPath ~/.githooks` を冪等に設定し、グローバル pre-commit dispatcher を有効化する
- `etc/init.sh` — 新規マシン向け。dotfiles を git clone → `etc/install/homebrew/install.sh` → `etc/set.sh` → `etc/link.sh` を実行
- `etc/set.sh` — OS 判定（Darwin/Linux）。Linux: GNOME Terminal Solarized 配色、apt install、`~/.config` バックアップ＆symlink 化
- `etc/load.sh` — シェル共通ユーティリティ関数ライブラリ（約450行）。OS 判定（`is_osx`, `is_linux`, `is_bsd`）、テキスト操作（`lower`, `upper`, `contains`）、PATH 操作（`path_remove`）、出力ヘルパー（`e_error`, `e_warning`, `e_done`, `ink`, `logging`）、条件判定（`is_login_shell`, `is_git_repo`, `is_ssh_running`）
- `etc/install/homebrew/` — Homebrew インストール（macOS / LinuxBrew）と `brew_install.sh` によるパッケージ一括インストール（gitleaks 含む）
- `etc/install/apt/` — apt パッケージインストール（デスクトップ向けツール）。apt 公式に無い `gitleaks` は prebuilt binary を `/usr/local/bin/` に DL する

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
- `etc/sync-mcp.sh` — `mcp-servers.json` を読み、`claude mcp add-json -s user` 経由で `~/.claude.json` に登録する冪等スクリプト。JSON を編集したら再実行する。**user scope は dotfiles SSOT で完全管理**する設計のため、SSOT に存在しないサーバー（手動 `claude mcp add -s user` で登録した残骸など）と `openCodeOnly:true` のサーバーは sync 実行時に user scope から自動削除される。プロジェクト固有のサーバー（`serena` など）は user scope に手動追加せず、各リポの `.mcp.json` (project scope) に書くこと
- `.mcp.json`（dotfiles リポ直下） — **project scope の例**。`${PWD}` に依存する `serena` のように user scope と相性が悪いものを置く。このファイルは `etc/link.sh` の除外対象で `~/.mcp.json` にはリンクされない
- 他プロジェクトで serena 等を使いたい場合は、該当リポに `.mcp.json` を commit する
- `claude` コマンドに alias は張らない（`--mcp-config` 方式は非対話シェル・サブプロセス起動で破綻するため廃止済み）

### OpenCode 互換

Claude Code の使用量制限（Max x20）回避のため、OpenCode (anomalyco/opencode) を併用する設定を整備している。SSOT は dotfiles で、`~/.config/opencode/` 配下は `etc/sync-opencode.sh` が生成する。

- **SSOT** —
  - `mcp-servers.json` (MCP) — `claudeCodeOnly` / `openCodeOnly` キーで片側限定可
  - `.claude/settings.json#permissions` (権限ルール)
  - `.claude/agents/*.md` (エージェント定義)
  - `.claude/CLAUDE.md` (グローバルルール — OpenCode 側でも `~/.claude/CLAUDE.md` フォールバックで読まれる)
- **生成先（AUTO-GENERATED、手動編集禁止）** —
  - `~/.config/opencode/opencode.json` (`mcp` + `permission` + 必要に応じ `tools`)
  - `~/.config/opencode/agents/<name>.md` (frontmatter を OpenCode 形式に変換)
- **再生成コマンド** — `bash etc/sync-opencode.sh`（手動実行）
- **Claude Code 上での自動再生成** — SSOT を Claude Code の Edit/Write/MultiEdit ツールで編集した時、PostToolUse hook (`~/.claude/lib/sync-opencode-hook.sh`) が SSOT パスマッチで `sync-opencode.sh` を自動実行する。SSOT 以外のファイル編集では何もしない（早期リターン）。
- **手動 CLI 編集（vim 等）後** — `bash etc/sync-opencode.sh` を手動実行する（hook は Claude Code 経由でのみ発火）
- **`git pull` 後** — `etc/link.sh` を実行すれば再生成される（`bash etc/sync-opencode.sh` を直接打っても OK）
- SSOT に該当するファイル — `mcp-servers.json` / `.claude/settings.json` / `.claude/agents/*.md`
- **同期方向** — Claude Code → OpenCode の片方向のみ（OpenCode 側 → Claude Code は対応しない設計）
- **完全互換は目指さない設計** — 以下は **意図的に対応外** とし、Claude Code 側でのみ動作するスキル群とする
  - hooks (foreign-project-name-guard) — OpenCode 未対応 (Issue #12472)
  - statusLine (`npx ccusage`) — OpenCode 非対応
  - Agent Teams (`TeamCreate`) — OpenCode 非対応
  - PIR² 系スキルの `Agent` ツール起動 — OpenCode のサブエージェント機構と互換性なし、`/pir2` 等は Claude Code 側で実行
  - MCP の per-tool permission — OpenCode 側はバグ Issue #6892 のため default allow
- 単純スキル（`/chat`, `/walkthrough`, `/brainstorm`）と CLAUDE.md / agents / skills / MCP 設定は OpenCode でも利用可能
- **モデル選定** —
  - 2026-04 以降、Anthropic Pro/Max サブスク経由は使用不可。OpenCode で Anthropic モデルを使うには API キー（従量課金）必須
  - 設定構造の整備のみがスコープで、モデル選定は dotfiles では介入しない
  - OpenCode は `claude-*` モデル ID を `anthropic/claude-*` プレフィックス付きで受理する
- **手動編集禁止** — `~/.config/opencode/opencode.json` および `~/.config/opencode/agents/` 配下は AUTO-GENERATED ヘッダ付きで生成される。編集する場合は SSOT (`mcp-servers.json` / `.claude/settings.json` / `.claude/agents/*.md`) を変更し `bash etc/sync-opencode.sh` を再実行
- **OpenCode 専用ルールを追加したい場合** — `~/.config/opencode/AGENTS.md` を手動で実ファイルとして配置する（sync-opencode.sh は生成しないので上書き競合しない）

### Git hooks (`.githooks/`)

個人マシンで触る**全リポジトリに対して** pre-commit でシークレット漏洩を防ぐためのグローバル dispatcher を配置している。マネーフォワードの GitHub ソース流出事案 (2026-05) を契機に導入。多層防御の最前線（pre-commit）の役割。

- **有効化方法** — `etc/link.sh` が `git config --global core.hooksPath ~/.githooks` を冪等に設定する。`.githooks/` 自体は同 link.sh の `for f in .??*` ループで `~/.githooks` にシンボリックリンクされる
- **gitleaks のインストール経路** — 環境別に分担している:
  - macOS: `etc/install/homebrew/brew_install.sh` の `brew install gitleaks`
  - Linux (一般): `etc/install/apt/install.sh` の prebuilt binary DL（apt 公式に無いため）
  - Codespaces: ルートの `install.sh` の prebuilt binary DL
  - いずれも未インストール時は dispatcher が warning だけ出して通すので、初回 commit が hook で詰まることはない
- **`.githooks/pre-commit`** — POSIX sh の dispatcher。
  1. `gitleaks protect --staged --redact --no-banner` で stage されたシークレット候補を検出（未インストール時は warning だけ出して通す）
  2. リポローカルの `.husky/pre-commit` と `.githooks/pre-commit` が `+x` で存在すれば順次実行（**husky 等のリポ固有 hook を尊重する**ため）
  3. 自己再帰防止: dispatcher 自身（`~/.githooks/pre-commit` の symlink 先）と同じ実体パスを呼び出さない（dotfiles リポで commit するときに無限ループしないため）
- **bypass** —
  - `GITLEAKS_DISABLE=1 git commit ...` で gitleaks のみ無効化
  - `git commit --no-verify` で hook 全体を無効化（Git built-in）
- **CI/履歴スキャン側との関係** — pre-commit は最前線で push 後の検知ではない。public リポでは GitHub Secret Scanning Push Protection（リポ Settings → Code security）を別途有効化すべき。過去履歴の一括チェックは `gitleaks detect --source . --log-opts="--all"` を手動で回す
- **編集時の注意** — このスクリプトは全リポの commit に介入する。終了コード非ゼロは即 commit ブロックなので、誤検知時の bypass 経路（`GITLEAKS_DISABLE` / `--no-verify`）は必ず残しておくこと。`pre-commit` framework や lefthook を使うリポは独自に `.git/hooks/pre-commit` を書き換えるか `core.hooksPath` をローカル上書きするので、グローバル dispatcher は無効化される（その場合はリポ側 framework に gitleaks を組み込む）

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
- **`.claude/lib/` 配下のスクリプトは symlink 経由で実行されるため `cd -P` を必須**にすること。`etc/link.sh` の `for claude_dir in agents skills lib` ループで `~/.claude/lib/` がリポジトリ実体への symlink になるため、Claude Code hook からは `~/.claude/lib/<script>.sh` 経由で呼ばれる。スクリプト内で `SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` のように **論理パス**を取得すると `~/.claude/lib` が返り、相対 `../..` で `~/` に着地して dotfiles SSOT に届かず常時 no-op になる。必ず `cd -P "$(dirname "${BASH_SOURCE[0]}")"` のように **物理パス**を返させること。一方 `etc/` 配下のスクリプト（`sync-mcp.sh`, `sync-opencode.sh` 等）は symlink 化されないため `-P` なしでも動くが、混在を避けるなら全シェルスクリプトで `-P` を既定としてもよい
- **`hooks.PostToolUse` 設定済みの SSOT パスマッチパターン** — Claude Code の `.claude/settings.json#hooks.PostToolUse` で Edit/Write 全件にマッチさせ、hook script 側で `tool_input.file_path` を SSOT 絶対パスと case マッチさせて早期 return する設計を採用している。hook script は `~/.claude/lib/sync-opencode-hook.sh`（symlink 経由実行）。SSOT は `mcp-servers.json` / `.claude/settings.json` / `.claude/agents/*.md`。SSOT を増減する場合は (1) hook script の case パターン、(2) `etc/sync-opencode.sh`、(3) 本ファイルの SSOT リスト の 3 箇所を必ず同時更新する
- **方針転換時の「廃案残骸」確認** — PIR² や手動編集で「○○方式 → ××方式」と途中で方針を切り替えた場合、廃案側で作られたディレクトリ・設定追記・hook 登録が残骸として残ることがある。廃案ディレクトリは `etc/link.sh` のリンク条件分岐や git status の untracked リストに紛れ込みやすいので、方針転換直後に `git status -uall` で残骸を列挙して削除/退避を判断する習慣をつけること
- **`.githooks/pre-commit` を編集する場合** — 全リポジトリの `git commit` に介入するため、終了コード非ゼロは即 commit ブロックになる。誤検知時の bypass 経路（`GITLEAKS_DISABLE=1` / `git commit --no-verify`）を**必ず残す**こと。リポローカル hook の dispatch 先（`.husky/pre-commit` / `.githooks/pre-commit`）を増やす場合は、自己再帰防止（dispatcher 自身と同じ実体パスを呼び出さない `target = SELF` 比較）を必ず通すこと。dotfiles リポ自身で commit したときに無限ループする
