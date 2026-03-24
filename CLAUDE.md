# CLAUDE.md

このファイルはリポジトリ内で作業する Claude Code (claude.ai/code) へのガイダンスを提供する。

## このリポジトリの目的

個人用 dotfiles リポジトリ。macOS / Linux (Ubuntu) 両対応。GitHub Codespaces での利用を主軸に設計されている。

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

### シェル設定
- `.zshrc` — メインの zsh 設定。`etc/load.sh` と `.zsh_alias` を source する
- `.zsh_alias` — エイリアス定義。`eza`(ls), `bat`(cat), `procs`(ps), `rg`(grep) 等モダンツールへの置き換えを含む
- `.zplugrc` — zplug プラグイン定義

### インストール・リンク
- `install.sh` — **Codespaces 専用**。`apt` パッケージ・prebuilt バイナリ (nvim, eza, procs) のインストール、`etc/link.sh` の実行、zsh のデフォルトシェル設定、Neovim プラグインのヘッドレスインストールを行う。冪等設計（`has()` チェックで既インストール時はスキップ）
- `etc/link.sh` — `$HOME/dotfiles/` 配下の `.??*` を `$HOME/` にシンボリックリンク展開する。`.claude/` は個別に `settings.json`, `.mcp.json`, `CLAUDE.md`, `agents/`, `commands/`, `skills/` を `$HOME/.claude/` へリンクする
- `etc/init.sh` — 新規マシン向け。dotfiles を git clone してから `etc/set.sh` と `etc/link.sh` を実行する
- `etc/set.sh` — OS 判定して gnome-terminal カラー設定等を行う。`~/.config` が通常ディレクトリならバックアップしてから symlink に置き換える

### Codespaces / Docker
- `.devcontainer/Dockerfile` — Codespaces 用ベースイメージ定義。`mcr.microsoft.com/devcontainers/base:ubuntu-24.04` をベースに nvim・eza・procs・各種 apt ツールを焼き込む。amd64/arm64 両対応
- `.devcontainer/devcontainer.json` — dotfiles リポジトリ自体を Codespaces で開く際の設定。`ghcr.io/coil398/dotfiles:latest` を参照
- `.github/workflows/docker-publish.yml` — master push / 週次スケジュールで Docker イメージをビルドして `ghcr.io/coil398/dotfiles:latest` に push する

他のプロジェクトリポジトリで prebuilt イメージを使う場合は以下の `devcontainer.json` を追加する：
```json
{
  "image": "ghcr.io/coil398/dotfiles:latest",
  "remoteUser": "vscode"
}
```

### Neovim
- `.config/nvim/init.lua` — エントリポイント。macOS/Linux で `mac.lua`/`linux.lua` を分岐読み込み。VSCode 検出時はプラグインを無効化
- `.config/nvim/lua/` — `init.lua`(プラグイン), `keymappings.lua`, `lsp.lua`, `color.lua`, `auto.lua`

## `.claude/` — Claude Code カスタマイズ

`etc/link.sh` によって `$HOME/.claude/` にシンボリックリンクされるため、dotfiles リポジトリで一元管理される。

### PIR² ワークフロー (`/pir2`)

コーディングタスクを **Plan → Implement → Review → Retrospect** の4フェーズで実行するカスタムワークフロー。

```
/pir2 <タスク>
```

フェーズ構成：
1. **planner** (Opus) — 実装プランを作成
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

`<!-- CORE --> 〜 <!-- /CORE -->` セクションは retrospector による自動改善でも変更禁止。

### その他のスキル（`.claude/skills/`）

各スキルの詳細は SKILL.md フロントマターを参照。

| スキル | 用途 |
|--------|------|
| `/ir` | 軽量 Implement → Review（Planなし） |
| `/review-pr` | PR・ブランチ・差分のコードレビュー |
| `/debug` | エラー診断 → 修正 → レビュー |
| `/tester` | 動作検証（テスト実行・アドホック確認） |
| `/brainstorm` | 対話で設計を固める（`docs/brainstorm/` に保存） |
| `/writing-plan` | 計画 → ステップ実装 → 記録（`docs/plans/`） |
| `/retro` | retrospector 単体実行 |
| `/check-updates` | git管理スキル・プラグインの更新チェック＆自動pull |
