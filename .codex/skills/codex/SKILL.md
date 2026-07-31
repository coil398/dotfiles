---
name: codex
description: codex（OpenAI のコーディングエージェント）に codex CLI 経由で相談するスキル。第二意見・別アプローチ・難所のレビューを codex に求めるときに使う。メインエージェント本体が codex exec を直接 background 実行する（中継サブエージェントは挟まない。MCP は廃止）。タスクの重さに応じて reasoning effort と model（GPT-5.6 系）を毎回明示的に選び（既定任せにしない）、相談・レビューは sandbox=read-only、必ず background で呼んでメイン作業を止めない。「codexに聞いて」「codexの意見」「codexに相談」「codexならどうする」「ask codex」「second opinion from codex」などで起動する。呼び出し元自身がタスク途中で codex に相談すると判断したときも、本スキルの手順が SSOT になる。ユーザーが /codex と入力したら必ずこのスキルを使う。
---

# /codex — codex への相談（codex CLI 直接実行・effort 選択・background）

`/codex <相談内容>` で codex に第二意見を求める。呼び出し元がタスク途中で「codex にも聞こう」と判断したときも本スキルの手順に従う（**これが codex 相談の SSOT**）。

> ℹ️ **codex は MCP を廃止し、codex CLI（`codex exec` / `codex exec resume`）に全面移行済み**。`mcp__codex__codex` は使わない。

## アーキテクチャ

**メインエージェント本体が codex exec を直接 Bash で実行する**。CLI 実行を中継するサブエージェントは挟まない。

理由: 中継サブエージェントは background コマンドの完了通知を待てずターンを終える問題が再現性 100% で発生した（2026-07-15〜07-21 に 5 回連続失敗）。メインエージェント本体なら background の通知を正しく受け取れる。中間レイヤーを挟む意味がない。

## 呼び出し手順

### 1. プロンプトをファイルに書く

長いプロンプトを CLI 引数で渡すと shell 引数長制限で silent fail する。**必ずファイルに書き出し、stdin pipe で渡す**。

```bash
PROMPT_FILE="/path/to/scratch/codex-prompt.md"
```

### 2. codex exec を background で実行

```bash
OUT_LAST="/path/to/scratch/codex-result.md"
OUT_EVENTS="/path/to/scratch/codex-events.jsonl"

cat "$PROMPT_FILE" | codex exec --json --skip-git-repo-check \
  -m "$MODEL" -c model_reasoning_effort="$EFFORT" \
  -s "$SANDBOX" -C "$CWD" \
  -o "$OUT_LAST" \
  "" > "$OUT_EVENTS" 2>/dev/null
```

シェル実行ツールの background 実行（タイムアウトは長め、目安 600 秒）で起動する。メインエージェントは codex の応答を**待たずに他の作業を続ける**。

- `SANDBOX`: **相談・レビューは必ず `read-only`**（codex にリポを書き換えさせない）。実装を任せる場合のみ `workspace-write`
- `CWD`: codex の作業ディレクトリ（対象リポの絶対パス）
- `MODEL` / `EFFORT`: **毎回タスクの重さから明示的に選ぶ**（下記「model の選択」「effort 選択ルブリック」。省略・既定任せにしない）

### 3. 完了通知を受け取ったら結果を読む

background の完了通知が来たら `$OUT_LAST` を読んで結果を確認・報告する。

- `$OUT_LAST` が空 or 存在しない → タイムアウトまたは codex エラー。`$OUT_EVENTS` の行数だけ確認して報告
- 結果がある → 実データのみを根拠に報告（捏造禁止）

### 4. 会話の継続（resume）

続き質問は thread_id を使って resume する:

```bash
# events.jsonl から thread_id を抽出
THREAD_ID="$(grep -m1 '"thread.started"' "$OUT_EVENTS" | jq -r '.thread_id')"

# 続きの質問を PROMPT_FILE に書き出してから
cat "$PROMPT_FILE" | codex exec resume "$THREAD_ID" --json --skip-git-repo-check \
  -m "$MODEL" -c model_reasoning_effort="$EFFORT" \
  -s "$SANDBOX" -C "$CWD" \
  -o "$OUT_LAST" \
  "" > "$OUT_EVENTS" 2>/dev/null
```

thread_id をファイル（`*.session`）に永続化しておけば、セッションをまたいでも同じ会話に積める。

## effort 選択ルブリック

`EFFORT`（= `model_reasoning_effort`）は**毎回タスクの重さから選ぶ**（固定既定に流さない）:

| effort | 場面 |
|---|---|
| `low` | ごく軽い事実確認・大量の軽い確認（下げるのはこの用途だけ） |
| `medium` | 軽い確認・小差分レビュー・事実寄りの質問 |
| `high` | 非自明なデバッグ・複数ファイル設計レビュー・トレードオフ判断 |
| `xhigh` | 難しい根本原因究明・複雑アルゴリズム/設計・詰まった時の深掘り |
| `max` / `ultra` | 最難関（`gpt-5.6-sol` / `-terra` のみ対応。滅多に使わない） |

軽い確認は `low`/`medium`、非自明な設計・デバッグは `high`、難問は `xhigh` を**都度選ぶ**。

## model の選択

`MODEL` は**毎回 GPT-5.6 系から選ぶ**（既定任せにしない）。`codex debug models` で最新一覧・各 model の effort 上限を確認できる（増減しうる）。選択肢:

| model | モデル既定 effort | 対応 effort |
|---|---|---|
| `gpt-5.6-sol` | low | low / medium / high / xhigh / max / ultra |
| `gpt-5.6-terra` | medium | low / medium / high / xhigh / max / ultra |
| `gpt-5.6-luna` | medium | low / medium / high / xhigh / max |

## 明示オーバーライド

- `/codex --effort xhigh <相談>` — effort を固定
- `/codex --model gpt-5.6-terra <相談>` — model を明示指定（GPT-5.6 系から選ぶ）

## 注意

- **相談・レビュー用途は必ず `SANDBOX=read-only`**。config.toml の既定は `workspace-write`（codex がリポを書ける）なので、明示的に read-only を `-s` で上書きしないと codex が勝手にファイルを変更しうる。実装を任せる時だけ `workspace-write`。
- **codex の自己申告を鵜呑みにしない**。「実装した / テスト通した」等は、呼び出し元が git 等で実体検証してから採用する。
- 応答待ちの間にメインエージェントの作業を止めない。結果は返ってきた**実データのみ**で報告し、待ち時間に予測で答えを書かない。
- **MCP（`mcp__codex__codex` 系）は廃止済み**。必ず CLI 経由。
