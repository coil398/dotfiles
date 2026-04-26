# vps-claw

VPS 固有のホスト設定スナップショット。`coil398/dotfiles` 内のサブディレクトリだが、汎用 dotfiles のように `$HOME` へ symlink で展開する形式ではない。**Claw VPS（OpenClaw を動かしているこのホスト）専用** の絶対パス前提のファイル群を、紛失防止と再構築用にここに置いている。

## 含まれているもの

| ファイル | 設置先 | 役割 |
|---------|-------|------|
| `CLAUDE.md` | `/home/claw/CLAUDE.md` | VPS 全体の overview。Claude Code が読み込む |
| `bin/claw-memory-sync.sh` | `/home/claw/bin/claw-memory-sync.sh` | claw-memory skill repo の自動 push (毎 30 分) |
| `bin/openclaw-workspace-sync.sh` | `/home/claw/bin/openclaw-workspace-sync.sh` | OpenClaw agent workspace の自動 push (毎時 :15, :45) |
| `bin/dotfiles-sync.sh` | `/home/claw/bin/dotfiles-sync.sh` | この dotfiles repo の自動 pull (毎時 :05) |
| `crontab.txt` | crontab | host cron 登録 3 本 |
| `openclaw/docker-compose.override.yml` | `/home/claw/openclaw/docker-compose.override.yml` | OpenClaw 公式 compose への上書き（browser サービス・bind mount・env 注入） |
| `openclaw/.env.example` | コピー元 → `/home/claw/openclaw/.env` | 環境変数のキー名のみ（値は秘密、別途投入） |

## 復元手順（新規 VPS 立ち上げ時）

```bash
# 1. dotfiles を取得
ghq get git@github.com:coil398/dotfiles.git
cd $(ghq root)/github.com/coil398/dotfiles/vps-claw

# 2. ファイル配置
cp CLAUDE.md ~/CLAUDE.md
mkdir -p ~/bin && cp bin/*.sh ~/bin/ && chmod +x ~/bin/*.sh

# 3. cron 登録
crontab crontab.txt

# 4. OpenClaw 設定
cp openclaw/docker-compose.override.yml ~/openclaw/docker-compose.override.yml
cp openclaw/.env.example ~/openclaw/.env
$EDITOR ~/openclaw/.env  # 実際のシークレットを埋める

# 5. (新規 VPS なら) docker compose up -d
cd ~/openclaw && docker compose up -d
```

## ここに含めない（意図的に除外）

| パス | 除外理由 |
|------|---------|
| `~/openclaw/.env` (実値) | Token/key の生値、git に残したくない |
| `~/.claude.json` | Claude Code の OAuth 認証、refresh で頻繁に変わる ephemeral 状態 |
| `~/.openclaw/openclaw.json` | OpenClaw gateway が秒オーダーで書き戻す runtime state |
| `~/.openclaw/cron/jobs.json` | OpenClaw 内部 cron 状態 |
| `~/.openclaw/credentials/*` | channel/provider creds、OpenClaw 流儀でローカル管理 |
| `~/.openclaw/agents/*/agent/auth-profiles.json` | model auth profile（OAuth token 等） |
| `~/.openclaw/workspace/*` | 別 repo (`coil398/OpenClaw`) で自動 push |
| `~/.openclaw/workspace/skills/claw-memory/*` | 別 repo (`coil398/claw-memory`) で自動 push |
