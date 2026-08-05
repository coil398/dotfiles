---
name: codex
description: codex（OpenAI のコーディングエージェント）に codex CLI 経由で相談するスキル。第二意見・別アプローチ・難所のレビューを codex に求めるときに使う。メイン Claude が直接 codex exec を background Bash で実行する（codex-runner サブエージェントは経由しない）。タスクの重さに応じて reasoning effort と model（GPT-5.6 系）を毎回明示的に選び（既定任せにしない）、相談・レビューは sandbox=read-only。「codexに聞いて」「codexの意見」「codexに相談」「codexならどうする」「ask codex」「second opinion from codex」などで起動する。Claude 自身がタスク途中で codex に相談すると判断したときも、本スキルの手順が SSOT になる。ユーザーが /codex と入力したら必ずこのスキルを使う。
---

# /codex — codex への相談（codex CLI 直接実行）

`/codex <相談内容>` で codex に第二意見を求める。Claude がタスク途中で「codex にも聞こう」と判断したときも本スキルの手順に従う（**これが codex 相談の SSOT**）。

> ℹ️ **codex は MCP を廃止し、codex CLI（`codex exec` / `codex exec resume`）に全面移行済み**。`mcp__codex__codex` は使わない。

## アーキテクチャ

**メイン Claude が codex exec を直接 Bash で実行する**。codex-runner サブエージェントは経由しない。

理由: サブエージェント（sonnet）は background Bash の完了通知を待てずターンを終える問題が再現性 100% で発生した（2026-07-15〜07-21 に 5 回連続失敗）。メイン Claude なら background Bash の通知を正しく受け取れる。中間レイヤーを挟む意味がない。

## 呼び出し手順

### 1. プロンプトをファイルに書く

長いプロンプトを CLI 引数で渡すと shell 引数長制限で silent fail する。**必ず Write でファイルに書き、stdin pipe で渡す**。

```bash
# scratchpad にプロンプトを Write しておく
PROMPT_FILE="/path/to/scratchpad/codex-prompt.md"
```

### 2. codex exec を background Bash で実行

> ⚠️ **素の `codex` を叩かないこと。必ず npm 版のフルパスを使う。**
> Windows では winget 版（`~/AppData/Local/Programs/OpenAI/Codex/bin/codex`）が PATH で**先に解決される**が、これは `gpt-5.6-sol` に非対応で
> `The 'gpt-5.6-sol' model requires a newer version of Codex.` (400) で即失敗する。
> 2026-07-11 / 07-13 / 07-27 と**3 回同じ罠に嵌っている**ため、コマンドは必ず変数経由でフルパス解決する。

```bash
# npm グローバル版を明示。存在しなければ PATH の codex にフォールバック。
# ⚠️ 判定は必ず `-f`。`.cmd` は Git Bash 上で実行属性が立たず `-x` は常に false になる
#    （2026-07-27 にこれで再び winget 版を掴んで 400 で落ちた）。
CODEX_CMD="$HOME/AppData/Roaming/npm/codex.cmd"
[ -f "$CODEX_CMD" ] || CODEX_CMD="$(command -v codex)"
"$CODEX_CMD" --version   # codex-cli 0.144.1 以上であることを毎回確認する

OUT_LAST="/path/to/scratchpad/codex-result.md"
OUT_EVENTS="/path/to/scratchpad/codex-events.jsonl"

cat "$PROMPT_FILE" | "$CODEX_CMD" exec --json --skip-git-repo-check \
  -m "$MODEL" -c model_reasoning_effort="$EFFORT" \
  -s "$SANDBOX" -C "$CWD" \
  -o "$OUT_LAST" \
  "" > "$OUT_EVENTS" 2>/dev/null
```

Bash ツールの `run_in_background: true` + `timeout: 600000` で起動する。メイン Claude は codex の応答を**待たずに他の作業を続ける**。

### 3. 完了通知を受け取ったら結果を Read

Bash の background 完了通知が来たら `$OUT_LAST` を Read して結果を確認・報告する。

- `$OUT_LAST` が空 or 存在しない → タイムアウトまたは codex エラー。`$OUT_EVENTS` の行数だけ確認して報告
- 結果がある → 実データのみを根拠に報告（捏造禁止）

### 4. 会話の継続（resume）

続き質問は thread_id を使って resume する:

```bash
# events.jsonl から thread_id を抽出
THREAD_ID="$(grep -m1 '"thread.started"' "$OUT_EVENTS" | jq -r '.thread_id')"

# 続きの質問を PROMPT_FILE に Write してから
cat "$PROMPT_FILE" | "$CODEX_CMD" exec resume "$THREAD_ID" --json --skip-git-repo-check \
  -m "$MODEL" -c model_reasoning_effort="$EFFORT" \
  -s "$SANDBOX" -C "$CWD" \
  -o "$OUT_LAST" \
  "" > "$OUT_EVENTS" 2>/dev/null
```

## effort 選択ルブリック

`EFFORT`（= `model_reasoning_effort`）は**毎回タスクの重さから選ぶ**（固定既定に流さない）:

| effort | 場面 |
|---|---|
| `low` | ごく軽い事実確認・大量の軽い確認（下げるのはこの用途だけ） |
| `medium` | 軽い確認・小差分レビュー・事実寄りの質問 |
| `high` | 非自明なデバッグ・複数ファイル設計レビュー・トレードオフ判断 |
| `xhigh` | 難しい根本原因究明・複雑アルゴリズム/設計・詰まった時の深掘り |
| `max` / `ultra` | 最難関（`gpt-5.6-sol` / `-terra` のみ対応。滅多に使わない） |

## model の選択

`MODEL` は**毎回 GPT-5.6 系から選ぶ**（既定任せにしない）。`codex debug models` で最新一覧を確認できる。

| model | モデル既定 effort | 対応 effort |
|---|---|---|
| `gpt-5.6-sol` | low | low / medium / high / xhigh / max / ultra |
| `gpt-5.6-terra` | medium | low / medium / high / xhigh / max / ultra |
| `gpt-5.6-luna` | medium | low / medium / high / xhigh / max |

## 明示オーバーライド

- `/codex --effort xhigh <相談>` — effort を固定
- `/codex --model gpt-5.6-terra <相談>` — model を明示指定（GPT-5.6 系から選ぶ）

## Codex の MCP アクセス

**Codex はプロジェクトに設定された MCP ツールにアクセスできる**（`collab_tool_call` として実行される）。ユーザーが「Codex にやらせろ」と言ったら、MCP の可否を議論せず即座にプロンプトを書いて `codex exec` を実行する。メイン Claude が「Codex には MCP が使えないから自分がやる」と判断して横取りすることは**禁止**。

## 注意

- **相談・レビュー用途は必ず `SANDBOX=read-only`**。config.toml の既定は `workspace-write`（codex がリポを書ける）なので、明示的に read-only を `-s` で上書きする。実装を任せる時だけ `workspace-write`
- **codex の自己申告を鵜呑みにしない**。「実装した / テスト通した」等は、git 等で実体検証してから採用する
- 応答待ちの間にメイン Claude の作業を止めない。結果は返ってきた**実データのみ**で報告し、待ち時間に予測で答えを書かない
- **MCP（`mcp__codex__codex` 系）は廃止済み**。必ず CLI 経由
