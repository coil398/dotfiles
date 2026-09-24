# 委譲の設計 — transport・監視・隔離

CLI 別の詳細は各 reference。ここは「別エージェントに仕事を渡す」共通の
設計判断。

## transport の選び方

| transport | 向くケース | 注意 |
|---|---|---|
| 親の subagent 機構（Task / run_subagent 等） | 同一ランタイム内で完結する作業 | 親の認証・コンテキストを継承。新規プロセス不要で最も手軽 |
| CLI 子プロセス（`-p`/`exec`/`run`） | **別ランタイムの能力**が要るとき（別モデル・別権限・別ワークスペース） | 認証は子プロセス側で完結させる必要がある（下記） |
| ACP / serve+attach | 継続セッション・イベント購読が要るとき | 実装コストは高いが自由度最大 |

子プロセス化すると **親の認証は継承されない**のが普通。
「親セッションは動くのに `xxx -p` が Not logged in で死ぬ」は定番
（devin で実測・過去セッションでも再発）。回避策は:
`env -u` で親固有 env を落として stored credential にフォールバックさせる、
素直に subagent transport を使う、または当該 CLI のログインを済ませる。

## env 隔離

親エージェントの env が子の挙動を変える例（全部実測）:

- `ACP_BACKEND` → `devin acp` が local credential を拒否する
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` 系 → 子が意図しない provider/課金経路を拾う可能性

委譲 spawn では `env -u` で親固有のものを落とすか、必要な env だけを
明示して渡す。

## 監視

- **出力ファイルだけでなくプロセス生存を見る**。イベント・journal を
  残さず死ぬ worker が観測されている（devin -p）
- timeout 分類の例: exit code ≠0 は非 retryable、signal / wall-clock は
  retryable、明示 cancel は非 retryable
- 無音終了の原因候補: レート上限、認証切れ、sandbox 拒否。
  「出力が空」は「失敗」と区別して扱う

## プロンプト・入出力の受け渡し

- 長い・整形済みのプロンプトは **ファイル経由**（`--prompt-file`、
  `-o`/`--output-last-message`、stdin）。argv に直接埋めると
  エスケープと長さで壊れる
- spawn は **argv 配列**で。shell 文字列を組まない
- 構造化応答が要るなら codex `--output-schema`、各 CLI の
  `--output-format json` を使い、素テキストの正規表現パースに頼らない

## ネストの制限

- **Claude Code の subagent は Agent ツールを呼べない**（構造的禁止、
  LTM 確定）。二段委譲を Claude 内に組まない。ネストが要るなら
  CLI 子プロセスとして起動する
- worker がさらに worker を増やせない設計（SuperAIAgent 等）は
  意図的な不変条件なので尊重する

## セッション在庫（一覧コマンド）

| runtime | 一覧 |
|---|---|
| Devin | `devin list [--format json]`（cwd 単位） |
| Codex | `codex agents`（ローカル）、`codex cloud list --json`（cloud） |
| Claude | `claude agents --json --all`（cloud）、`~/.claude/projects/*/…jsonl` |
| Cursor | CLI に一覧なし。`--resume`/`--continue` のみ。cloud は Cursor API |
| OpenCode | `opencode session list` |
| Gemini | `gemini --list-sessions` |
| Grok | `grok sessions list --json`（cloud） |
