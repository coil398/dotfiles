# Claude Code (`claude`)

## 非対話実行

```bash
claude -p 'task'                                   # print モード
claude -p --output-format json 'task'              # JSON（stream-json もあり）
claude -p --output-format text 'task'              # 素テキスト明示
claude -c -p 'follow-up'                           # 直近会話の継続
claude -p --add-dir /extra/path 'task'             # 作業 dir 外へのアクセス許可
```

## 委譲で特に有用なフラグ

- **`--bare`**: hooks・LSP・plugin sync・auto-memory・keychain・CLAUDE.md
  自動発見を全部スキップする最小モード。認証は `ANTHROPIC_API_KEY` か
  `--settings` の apiKeyHelper のみ（OAuth/keychain は読まない）。
  「余計な設定を引きずらない使い捨て worker」に最適。Skill は
  `/skill-name` で解決される
- `--agents '<json>'`: その場でサブエージェント定義を注入
- `--agent <name>`: セッションの agent を指定
- `--allowedTools 'Bash(git *) Edit'`: ツール許可を絞る
- `--plugin-dir <path>`: plugin を追加ロード
- `--append-system-prompt` / `--system-prompt(-file)`: 指示の注入
- `--dangerously-skip-permissions`: 権限チェック全バイパス。
  外部 sandbox 済み環境限定で常用しない
- `--bg`: バックグラウンド agent として起動（`claude agents` で管理）

## 管理・診断

```bash
claude agents --json --all     # cloud agents 一覧（セッション在庫に使う）
claude auth status --json      # 認証状態（⚠ 無効 JSON を返すことがある。パース失敗を許容すること）
claude mcp add-json -s user '<json>'   # MCP サーバを user scope へ冪等登録
claude mcp add --transport http <name> <url>
```

## 実装上の注意（過去セッションから）

- spawn は **shell 文字列ではなく argv 配列**で組む（prompt 内の引用・
  改行で壊れない）。node なら `child_process.spawn('claude', argv)`
- timeout は wall-clock で管理し、exit code / signal / timeout を分けて
  retryable 判定に使う
- **subagent 内から Agent ツールは構造的に禁止**（LTM: "Error: Agent is not
  available inside subagents"）。planner→worker の二段委譲を Claude 内で
  組む設計は動かない。ネストするなら CLI 側 (`claude -p`) を子プロセスと
  して使う
- セッション ID は `session_` / `cse_` 系。transcript は
  `~/.claude/projects/<cwd エンコード>/<session>.jsonl`
