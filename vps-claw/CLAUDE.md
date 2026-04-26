# /home/claw — OpenClaw 用 VPS

このホームディレクトリは **OpenClaw プロジェクト**専用の作業 VPS。Claude Code がこの環境で作業する際の前提と注意点をまとめる。

グローバル規約（探索の explorer 委譲、エージェント運用、書式ルール等）は `~/.claude/CLAUDE.md` を参照。本ファイルは VPS 固有の情報のみを記す。

## 環境の素性

- **OpenClaw とは**: Captain Claw（ゲーム）の再実装ではなく、**マルチチャンネル AI ゲートウェイ**（Discord / Telegram / Slack 等への AI ルーティング基盤）
- **GitHub**: https://github.com/openclaw/openclaw
- **言語**: TypeScript (ESM, strict) + 一部 Python
- **モノリポ**: pnpm workspace (`src/` `extensions/` `packages/` `apps/` `ui/` `skills/` `docs/`)
- **ビルド**: `pnpm build`（`tsdown` / `tsgo`）
- **エントリ**: `openclaw.mjs`（Node 22.12+ 必須）
- **バージョニング**: 日付ベース（例: `2026.4.25`）

## 主要パス

| パス | 用途 |
|------|------|
| `/home/claw/openclaw/` | OpenClaw 本体リポジトリ（メインの作業対象） |
| `/home/claw/.openclaw/` | OpenClaw のランタイムデータ（`credentials/` `workspace/` `agents/` `memory/` `openclaw.json`）。**`credentials/` は中身を読まない** |
| `/home/claw/dotfiles/` | `~/.claude/` 等の dotfiles 実体（`~/.claude` は symlink） |
| `/home/claw/.ai-pir-runs/` | PIR² 系スキル成果物 |

`openclaw/CLAUDE.md` は `AGENTS.md` への symlink で、プロジェクト固有の AI エージェント設定が記述されている。OpenClaw 内部で作業する際はそちらも参照する。

## 稼働中サービス（**本番扱い**）

- **`claw.coil398.io`** (HTTPS / 443) → nginx → `127.0.0.1:18789` の OpenClaw ゲートウェイへリバースプロキシ
- **18789**: OpenClaw ゲートウェイ本体（外部公開中）
- **18790**: OpenClaw（用途未確認）
- TLS は Let's Encrypt、Cloudflare Tunnel と Tailscale も併用

⚠️ **これらのプロセスの restart / kill / 設定変更・nginx 設定変更・証明書系の操作はユーザーに必ず確認してから実行**。外部に公開されているため `auto` モードでも自動で触らない。

## 利用可能なツール

| ツール | 状況 |
|--------|------|
| Node.js | v25.8.1（nvm 管理）。`source ~/.nvm/nvm.sh` してから使う |
| npm | v11.11.0 |
| pnpm | nvm 経由で利用可（OpenClaw のビルド・依存管理はこれ） |
| python3 | システム標準 |
| gcc / g++ | Ubuntu 14.2.0 |
| make | あり（実体は `pnpm build` のラッパー） |
| Docker | あり（`docker-compose.yml` がリポジトリにある） |
| **未インストール** | clang / cmake / cargo / go / dotnet / SDL2 |

## システム情報

- Ubuntu 25.04 (Plucky Puffin) / Linux 6.14.0-37 / x86_64
- AMD EPYC-Milan 4 コア / RAM 7.7 GiB（実空き約 1.1 GiB、buff/cache 込みで 5.4 GiB）
- ルートディスク 96 GB 中 71 GB 使用（**残り 25 GB / 75% 使用**）

⚠️ ビルド成果物・`node_modules`・ログの肥大に注意。大きな依存導入や巨大ファイル生成の前に `df -h /` で残量確認。

## 作業時のルール（VPS 固有）

1. **稼働中サービスへの影響**: ゲートウェイ・nginx・cloudflared・Tailscale 等の常駐プロセスを止めたり再起動したりする操作は必ずユーザー確認。`systemctl` / `pkill` / `docker stop` 等は auto モードでも自動承認しない
2. **クレデンシャル**: `~/.openclaw/credentials/` `~/.ssh/` `~/.cloudflared/` `~/.docker/config.json` は中身を読まない・書かない・コピーしない（存在確認のみ）
3. **ディスク**: 1 GB を超えるダウンロード・ビルドの前に `df -h /` を確認。`node_modules` の重複作成や `--no-cache` 系の濫用を避ける
4. **環境変数**: nvm が PATH にいないシェルだと `node`/`pnpm` が見つからない。スクリプトを書くときは `. ~/.nvm/nvm.sh` を入れるか、絶対パスで叩く
5. **公開ドメイン経由のテスト**: `claw.coil398.io` を叩く動作確認はネット越しに見えるので、デバッグ用の冗長ログや個人情報を流さない

## 推奨ワークフロー

- OpenClaw の機能変更・バグ修正は `/home/claw/openclaw/` 配下で行い、その配下の `CLAUDE.md` (= `AGENTS.md`) のルールに従う
- 大きめのタスクは `/pir2`、軽いタスクは `/ir`、デバッグは `/debug`、コードリーディングは `/walkthrough`
- ホームディレクトリ全域に影響する設定変更（このファイル含む）はそれと分かるよう commit を分ける。`/home/claw/dotfiles/` は git 管理されていないので、変更の履歴は手元で意識しておく
