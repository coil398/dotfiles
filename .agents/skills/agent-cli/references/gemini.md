# Gemini CLI (`gemini`)

## 非対話実行

```bash
gemini 'task'                                # positional = one-shot
gemini -o json 'task'                        # text | json | stream-json
gemini --approval-mode yolo 'task'           # 全自動承認（-y 同義）
gemini --approval-mode auto_edit 'task'      # 編集だけ自動承認
gemini -m <model> 'task'
```

- **`-p`/`--prompt` は deprecated**。positional query を使う
- stdin は prompt に append される
- `-i`/`--prompt-interactive` は対話継続モードなので委譲では使わない
- `-s`/`--sandbox`: サンドボックス有効化

## セッション

```bash
gemini -r latest 'follow-up'        # 直近セッション再開（番号指定も可）
gemini --list-sessions              # 一覧
gemini --delete-session <N>
```

## その他

- `--include-directories <a,b>`: workspace 外の追加読み込み dir
- `--allowed-tools` / `--allowed-mcp-server-names`: 許可リスト絞り込み
- `--experimental-acp`: ACP モード（Zed 等からの接続用）
- `gemini extensions` / `gemini mcp`: 拡張・MCP 管理
