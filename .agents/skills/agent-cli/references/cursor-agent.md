# Cursor Agent CLI (`cursor-agent`)

## 非対話実行

```bash
cursor-agent -p 'task'                                  # print モード
cursor-agent -p --output-format stream-json 'task'      # text | json | stream-json
cursor-agent -p --stream-partial-output 'task'          # stream-json の delta 逐次
cursor-agent -p --force 'task'                          # コマンド自動承認（--yolo 同義）
cursor-agent -p --mode plan 'task'                      # plan / ask = read-only
cursor-agent -p --trust 'task'                          # workspace trust をスキップ
cursor-agent --resume <chatId> -p 'follow-up'
cursor-agent --continue -p 'follow-up'                  # 直近セッション継続
```

- `--workspace <path|name>`: 作業 workspace。`--add-dir` で追加 root。
  `-w [name]` で `~/.cursor/worktrees/` 下の git worktree に隔離
- `--model <name>`: `claude-opus-4-8[context=1m,effort=high,fast=false]`
  のような bracket パラメータ可。`--list-models` で一覧
- `--auto-review`: サーバ側分類器が安全な呼出しだけ自動実行するモード
- `--sandbox enabled|disabled`、`--approve-mcps`

## 認証

- `CURSOR_API_KEY` env または `--api-key`
- `--endpoint` / `CURSOR_API_ENDPOINT` で API endpoint 変更
- `--use-system-ca`: 社内 CA 等で必要な場合に

## 罠（実測）

- **存在しないサブコマンド・引数は TUI 起動に落ちる**。`cursor-agent ls`
  は存在しないのに非対話 stdin で Ink raw mode エラー＋ハングした。
  委譲では必ず `-p` を付け、子プロセスは timeout 必須
- セッション列挙の CLI は無い。`--resume` / `--continue` は ID か
  直近指定。クラウド側の一覧は Cursor API（`api2.cursor.sh`）を使う
