---
name: agent-cli
description: >-
  ある AI エージェントから別の AI CLI（devin / codex / claude / cursor-agent /
  opencode / gemini / grok）を非対話で呼び出すときの実行規則。print モードの
  選び方、認証・権限・cwd の罠、出力フォーマット、ACP 起動の注意をまとめる。
  「codex に投げて」「devin を CLI から呼んで」「別エージェントに委譲」
  といった依頼で使う。ユーザーが /agent-cli と入力したら使う。
---

# agent-cli

別エージェントを呼ぶときの共通原則と CLI 別の勘所。**対話 TUI を起動しない**
ことが第一。必ず print / exec / run / acp 系の非対話モードを使う。

## 共通ルール

- **非対話モード必須**。引数なし起動や不明なサブコマンドは TUI を開いて
  non-tty でハングする（実測: `cursor-agent ls` は存在しないのに TUI 化した）
- **cwd を固定する**。セッション・設定・権限はディレクトリ単位。`cd` するか
  `-C` / `--dir` / `--workspace` / `--cd` で指定する
- **timeout を必ず付ける**。応答なしのまま無期限に待たない
- **機械処理は JSON 系フォーマット**（`--output-format json` / `--json` /
  `--format json` / ACP events）
- **env を汚染しない**。親エージェント固有の env が子の挙動を変える
  （実測: `ACP_BACKEND` 継承で `devin acp` が local credential を拒否）
- **委譲プロンプトは自己完結に**。子は親の会話文脈を見ない。
  目的・対象 path・完了条件を全部書く
- **権限緩和フラグは deny を無効化しない**。`--yolo` / bypass /
  `--dangerously-*` は確認の自動承認で、deny 系の強制拒否は残る（実測済み）
- **長いプロンプトはファイル経由**。argv の長さ・エスケープ問題を避ける
  （`--prompt-file` / stdin / `-` など）

## CLI 別詳細

| CLI | reference | 非対話の入口 |
|---|---|---|
| Devin | [references/devin.md](references/devin.md) | `devin -p` / `devin acp`（ACP） |
| Codex | [references/codex.md](references/codex.md) | `codex exec` |
| Claude Code | [references/claude.md](references/claude.md) | `claude -p` |
| Cursor | [references/cursor-agent.md](references/cursor-agent.md) | `cursor-agent -p` |
| OpenCode | [references/opencode.md](references/opencode.md) | `opencode run` / `serve`+`attach` / `acp` |
| Gemini | [references/gemini.md](references/gemini.md) | positional `gemini 'task'` |
| Grok | [references/grok.md](references/grok.md) | `grok -p` |

委譲の設計（transport 選定・監視・env 隔離・ネスト制限）は
[references/delegation.md](references/delegation.md)。

## 呼び分けの目安

| 用途 | 向いてるもの |
|---|---|
| 定型の非対話タスク | `codex exec` / `claude -p` / `cursor-agent -p` / `gemini` |
| 継続セッション・状態を持つ委譲 | `devin acp` / `opencode serve` + `attach` / `codex exec resume` |
| 最小副作用の相談 | `claude -p --bare`、各 CLI の plan/ask モード |
| 出力を機械処理 | `claude --output-format json`、`cursor-agent --output-format stream-json`、`opencode --format json`、`gemini -o json`、codex `--json`（JSONL）/`-o`、devin ACP events |
| 構造化された最終応答 | codex `--output-schema` + `-o` |
