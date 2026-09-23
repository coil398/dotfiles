# Dotfiles project guidance

macOS / Linux / WSL 向けの個人用dotfiles。共有の作業境界を次のimportで読み込み、Claude固有の操作は `.claude/` の原本に従う。

@AGENTS.md

## 作業に応じて読む原本

| 作業 | 原本 |
|---|---|
| Agent / Skillの責任・配布・runtime間の接続を変える | [AI-WORKFLOW-SPEC.md](AI-WORKFLOW-SPEC.md) |
| クラウド環境のbootstrap・初回展開を変える | [AISETUP.md](AISETUP.md) |
| MCP構成を変える | `mcp-servers.json` と対象runtimeの `etc/sync-*.sh` |
| Claude設定・hookを変える | `.claude/settings.json` と対象hookの実装 |
| 個別workflowを使う・直す | 選択した `.claude/skills/<name>/SKILL.md` と、その用途で指定される参照 |
| モデル・担当の選択を変える | 対象runtimeの設定・native定義と公開起動引数 |

ファイル構成、モデル表、全スキル一覧、workflowの担当順・周回数をここへ複製しない。選択した原本と実装で確認する。

## セットアップと配布

- 一般の新規セットアップは `etc/init.sh`、Codespaces専用セットアップは `install.sh`。リンクの再展開は `sh etc/link.sh`。
- Codex/Cursorだけの反映は `bash etc/link.sh --codex-cursor-only`。Grok・Geminiも含める場合は `bash etc/link.sh --ai-runtimes-only`。OpenCodeは `bash etc/sync-opencode.sh` で別途反映する。
- クラウドbootstrapは、このrepo上では現在のcheckoutを使い、別repoではdotfilesを取得して展開する。設定・オプションはAISETUPを読む。
- setup/linkスクリプトは冪等性を維持する。新しいdotfileや `.claude/` 直下の原本を追加したら、`etc/link.sh` の除外・allowlistと実際のhome配置を確認する。
- `link.sh` は `~/dotfiles` がなければ自身の物理位置からrepoを解決する。任意のcheckout位置でも動くことを保つ。
- `link_dir` は既存の実ディレクトリを置換せず、ネストsymlinkを作らない。組込みスキル・クラウド側の設定を保全する。
- `~/.codex` 全体をsymlinkにせず、管理対象だけを個別配置する。認証・履歴・組込み/個人スキルを保全する。
- Cursorスキルはhomeへ実体コピーする。配置と保全の実装は `etc/link.sh` を使う。

## 原本と生成物

Codexの `.codex/AGENTS.md`・`.codex/config.toml` は `etc/sync-codex.sh` の生成物。`.codex/codex-native-supplement.md` は生成 `.codex/AGENTS.md` へ連結されるnative原本で、直接編集できる。Codexは `.agents/skills` を直接読む。生成物の一覧と補助文書の生成元はsyncスクリプトを読む。

Cursorの生成Rules・MCPは `etc/sync-cursor.sh`、OpenCodeのhome設定・AGENTSは `etc/sync-opencode.sh` が生成する。Devinの `~/.config/devin/mcp_config.json` (user scope MCP) と `config.json` の managed keys (permissions・read_config_from・Stop hook) は `etc/sync-devin.sh` が生成・jq merge する。生成物は手編集せず原本を直す。Claude native原本を他runtimeの内容から再生成しない。

生成入力を変えたら対象syncとhookの選択条件を照合し、`etc/test-sync-hooks.sh` で必要な生成と対象外no-opを確認する。手動CLIで編集した場合も必要なsyncを実行する。マシン依存パスだけの生成差分を、実質的な設定変更と混同しない。

## MCPの変更

`mcp-servers.json` はuser scopeの原本。実際のエントリとruntimeフィルタはJSONとsync実装から確認する。Claudeの反映入口は `bash etc/sync-mcp.sh`。この処理は管理対象のuser scopeを揃え、原本にない登録も除去するため、対象と副作用を確認する。

プロジェクト固有のMCPは対象repoの `.mcp.json` に置く。repoの `.mcp.json` はhomeへリンクしない。`claude` をMCP設定用のaliasへ置き換えない。

## Git hook・Claude設定の変更

- `.githooks/pre-commit` は全repoへ作用するdispatcher。既存のsecret/SSOT/layout検査、ローカルhookへのdispatch、同じ物理pathを呼ばない再帰防止を保つ。検査と明示bypassの正本はスクリプトにあり、通常修復でbypassを使わない。
- Codex / Cursor / Devin / Grok の任意Jev hooksの原本・送信範囲・設定・利用量と推定費用は `jev-hooks/README.md`。
- gitleaks導入経路は環境別のinstallスクリプトを読む。未導入時の警告と、検出・検査失敗による非ゼロ終了を混同しない。
- `.claude/lib/` はhomeのsymlink経由で実行される。`SCRIPT_DIR` の解決には `cd -P` を使い、相対参照がdotfilesの実体へ届くことを確認する。
- `.claude/settings.json` を変更したらhomeのリンクと内容を照合する。UIのatomic renameで実ファイルになっていた場合はhome側の変更を保全・統合してから既存の配布手順で直す。設定の起動時キャッシュは新しいセッションで確認する。
- `.claude/` の変更は全プロジェクトに届く。エージェントの `<!-- CORE -->` 保護領域を通常の自動改善で変更しない。

## 個別設定の変更

- Neovimプラグインは `.config/nvim/lua/init.lua`、lockは既存の更新手順に従う。`vim.lsp.*` の追加・変更では対象版の公式runtime docとdeprecated一覧を確認する。hover/signatureのborder指定は対応する `vim.lsp.buf` のオプションを使う。
- Dockerイメージは `.devcontainer/Dockerfile`、自動build条件はCIを確認する。
- `.zshrc` のPATH追加はOS分岐を考慮する。tmux設定は `tmux source-file ~/.tmux.conf` で反映を確かめる。
- `.devin/` はlink.shの `.??*` ループで `~/.devin` へ誤リンクされるためリポに置かない。project config が必要になったら link.sh の除外リストへ追加してから置く。
- 設計に入るときは既存実装・status・必要な履歴を確認する。方針変更後はその作業で不要になった生成物・設定・hook登録を差分で確認し、ユーザーの既存変更と区別して整理する。
