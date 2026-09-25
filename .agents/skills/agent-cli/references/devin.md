# Devin CLI (`devin`)

## 非対話実行

```bash
devin -p --respect-workspace-trust false --model swe-2-high --prompt-file prompt.md
devin -p -- 'fix the failing test'      # `--` で prompt を明示分離
devin --config /path/config.json -p '…' # --config はグローバルオプション。サブコマンドより前
```

- `-p` / `--print`: 最終 assistant メッセージを stdout に出して終了
- `--prompt-file <FILE>`: 長いプロンプトは argv ではなくファイル経由
- `--respect-workspace-trust false`: 非対話では trust prompt を出せず
  untrusted dir で即死するので、scratch dir 等では必須
- `--permission-mode auto|accept-edits|smart|dangerous`、`--model`、`--export`
- セッションは cwd 単位。`devin list [--format json]` / `-c`（直近継続）/
  `-r [id]`（再開）

### 出力の注意（実測・過去セッション）

- stdout の最終メッセージ以外に tool/progress 行や code fence で包まれた
  envelope が混ざることがある。機械処理は「全文パース」ではなく
  「最終メッセージ or JSON 部分を抽出」にする
- `devin -p` は webfetch を自動拒否する（interactive 専用ツールのため）
- worker が **イベントも journal も残さず静かに死ぬ** ケースが観測されている。
  監視は出力ファイルだけでなくプロセス生存（PID 確認）を見る

## 認証

- `devin auth login`（ブラウザ PKCE / 手動トークン）。
  資格は `~/.local/share/devin/credentials.toml` の `windsurf_api_key`
  （`devin-session-token$<JWT>` 形式）
- **`devin auth status` の "Not logged in" と実際の利用可否は一致しない**
  ことがある（過去セッションでも今回も観測）。status が NG でも
  session token が API に通る経路がある。判定は実際に `session/new` or
  `-p` を打ってみること
- 未認証の `devin -p` は即 `Error: Not logged in` で死ぬ。
  親セッションの認証を引き継ぐ `run_subagent` / IDE 側 transport を
  代替にする手が過去に使われた

## ACP（プログラムからの正攻法）

`devin acp` = stdio NDJSON の JSON-RPC サーバ。

```text
→ initialize        {protocolVersion:1, clientCapabilities:{}, clientInfo:{...}}
→ session/new       {cwd:"/path", mcpServers:[]}
→ session/set_mode  {sessionId, modeId:"bypass"}   # accept-edits/smart/ask/plan/bypass
→ session/prompt    {sessionId, prompt:[{type:"text",text:"..."}]}
← session/update    notification（tool_call / tool_call_update /
                    agent_message_chunk / agent_thought_chunk / usage_update）
← session/prompt result: {stopReason:"end_turn"|"refusal"|"cancelled", usage:{...}}
```

- `session/request_permission` リクエストが来たらクライアント側で
  outcome を返す（bypass mode では来ない）
- カスタムメソッド: `_cognition.ai/*`（hooks/list、mcp/listServers、
  skills/list、session/share 等がバイナリ内に存在）

### `ACP_BACKEND` の罠（実測）

Devin/IDE セッション内から `devin acp` を spawn すると、env 継承の
`ACP_BACKEND` が効いて **「ACP host が唯一の credential 源」モード**になり、
local credential（env・credentials.toml）を一切使わず `authenticate` を要求する。
`env -u ACP_BACKEND devin acp` で stored credential にフォールバックして
`session/new` が通る。**子プロセスへ親エージェントの env をそのまま
継承させない**のが原則。

## 権限と hook

- `permissions.deny` 直撃は **agent の発話なしにターン終了**（実測:
  tool_call failed → end_turn、agent_message_chunk 0 件）
- `hooks.PreToolUse` の `decision:"block"` + `reason` は reason が
  tool 結果として agent に返り、ターンは継続する（v3000.6.2+、実測）
- この dotfiles では `etc/devin-deny-guard.py` が deny ルールを先に評価して
  reason 付き block を返す（`etc/sync-devin.sh` が config.json に登録）
- bypass mode でも deny は有効（権限緩和 ≠ deny 解除）

## その他

- ログ: `~/.local/share/devin/cli/logs/devin_<ts>_<pid>.log`（ACP の
  initialize/session 内部処理もここに出る。hook 読み込みは
  `hooks discovery ... loaded=N` 行で確認できる）
- `devin acp --agent-type summarizer`: summarizer 専用プロセスとして起動
- `devin cloud drs blueprint-*`: 環境 blueprint 管理。`devin sandbox`:
  exec の sandbox（bwrap+seccomp on Linux）
- `devin doctor`: 設定診断（現状チェック項目は少ない）
