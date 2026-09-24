# OpenCode (`opencode`)

## 非対話実行

```bash
opencode run -m provider/model 'task'          # ヘッドレス実行
opencode run --format json 'task'              # 生 JSON イベント
opencode run -c 'follow-up'                    # 直近セッション継続
opencode run -s <sessionId> 'follow-up'
opencode run --fork -c 'follow-up'             # fork して継続
opencode run --dir /path 'task'
opencode run --agent <name> 'task'
```

- `--share` でセッション共有、`--title` で名前付け、`-f/--file` で添付

## 常駐サーバ（複数委譲の集約）

```bash
opencode serve --port 4096                     # headless サーバ
opencode run --attach http://localhost:4096 'task'   # 既存サーバへ投げる
opencode attach <url>                          # TUI から接続
opencode acp                                   # ACP サーバとしても起動可
```

同一サーバに複数セッションを集約できる。`--username`/`--password`
（`OPENCODE_SERVER_USERNAME`/`OPENCODE_SERVER_PASSWORD`）で basic auth。

## 承認の罠（LTM 確定済み）

- 対話中の "always" 承認は **セッション限定**。永続化しない
- 作業 dir 外へのアクセスは `external_directory` 権限設定が必要。
  この dotfiles では `etc/sync-opencode.sh` が `~/**` allow を生成
  `opencode.json` に含めて恒久解消している。生成物を手で直さない
- 承認地獄（毎回聞かれる）に陥ったら設定側を疑う。プロンプトで
  誤魔化さない

## 管理

```bash
opencode session list       # セッション管理
opencode export <id>        # JSON export
opencode models             # provider/model 一覧
opencode stats              # token 使用量・コスト
opencode providers auth     # credential 管理
```
