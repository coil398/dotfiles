---
name: codex
description: codex（OpenAI のコーディングエージェント）に codex CLI 経由で相談するスキル。第二意見・別アプローチ・難所のレビューを codex に求めるときに使う。CLI の実行と完走管理は codex-runner サブエージェントが担い、メインエージェントは codex-runner を background で起動して即座に別作業へ移る（何時間かかってもブロックされない）。タスクの重さに応じて reasoning effort と model（GPT-5.6 系）を毎回明示的に選び（既定任せにしない）、相談・レビューは sandbox=read-only。「codexに聞いて」「codexの意見」「codexに相談」「codexならどうする」「ask codex」「second opinion from codex」などで起動する。呼び出し元自身がタスク途中で codex に相談すると判断したときも、本スキルの手順が SSOT になる。ユーザーが /codex と入力したら必ずこのスキルを使う。
---

# /codex — codex への相談（codex-runner 経由）

`/codex <相談内容>` で codex に第二意見を求める。呼び出し元がタスク途中で「codex にも聞こう」と判断したときも本スキルの手順に従う（**これが codex 相談の SSOT**）。

> ℹ️ **codex は MCP を廃止し、codex CLI（`codex exec` / `codex exec resume`）に全面移行済み**。`mcp__codex__codex` は使わない。

## アーキテクチャ

**CLI 実行と完走管理は `codex-runner` サブエージェントが担う。メインエージェントは background で起動して即座に別作業へ移る。**

```
メインエージェント : codex-runner を background サブエージェントとして起動
                     → 即座に自由。他の作業を続ける / ターンを終える
codex-runner       : codex exec を background 起動
                     → 自分のターン内で完了マーカーが出るまで foreground ポーリング
                     → 待機コマンドの上限で切れたら同じポーリングを叩き直す（最大 20 ラウンド ≒ 3 時間）
                     → 結果を確定して報告し終了
メインエージェント : codex-runner の完了通知で起こされ、結果を受け取る
```

**この分業の要点**: ブロックする主体を codex-runner に隔離する。codex が何分走ろうとメインエージェントは止まらない。

> ⚠️ **メインエージェントが自分で foreground ポーリングしてはならない。** メインのターンが待機時間ぶん丸ごと停止し、この設計の意味が消える。長時間ジョブを foreground で抱えるのは codex-runner の仕事。

### なぜ codex-runner に background 完了通知を待たせないのか

background コマンドの完了通知**自体はサブエージェントにも届く**（2026-08-01 実測）。しかしサブエージェントはツール呼び出しを出さずにテキストを返した時点でターンが終了するため、「何もせず通知を待つ」状態が構造的に存在しない。だから待ち方は**ポーリング一択**になる。

2026-07-15〜07-21 に 5 回連続で失敗したのは、この点を取り違えて「通知を待ちます」と返る実装になっていたため（および 07-16 版でリトライ分岐を複雑にしすぎて途中で諦めていたため）。現行の codex-runner はポーリング条件を**完了マーカーファイルの出現ひとつ**に固定し、分岐を持たない。

## 呼び出し手順

### 1. codex-runner を background 起動する

サブエージェント起動機構で `codex-runner` を background 実行し、プロンプトに以下を渡す:

| 名前 | 内容 |
|---|---|
| `PROMPT` | 相談内容（背景・前提・聞きたい論点を具体的に） |
| `CWD` | codex の作業ディレクトリ（対象リポの絶対パス） |
| `SANDBOX` | **相談・レビューは `read-only`**。実装を任せる場合のみ `workspace-write` |
| `MODEL` / `EFFORT` | **毎回タスクの重さから明示的に選んで渡す**（下記ルブリック。省略・既定任せにしない） |
| `WORK_DIR` | 入出力ファイルの置き場（スクラッチパス等） |
| `RUN_ID` | この実行を一意に識別する文字列。**並列起動時は必ず別々の値**にする |
| `SESSION_FILE` | 任意。会話を継続したいとき用の thread_id 永続化ファイルパス |

### 2. 待たずに別作業へ移る

メインエージェントはブロックされない。他の作業を続けるか、やることが無ければターンを終える。codex-runner の完了通知で起こされる。

### 3. 結果を受け取る

codex-runner は `EXIT` / `thread_id` / 応答本文 / エラー / ポーリング総ラウンド数を報告する。**実データのみを根拠に**ユーザーへ報告する（捏造禁止）。

### 4. 会話の継続（resume）

続き質問は、同じ `SESSION_FILE` を渡して**新しい codex-runner を起動する**。codex-runner が `codex exec resume <thread_id>` で同一 thread に会話を積む。前の codex-runner インスタンスが生きていればそれに継続メッセージを送ってもよい。

## codex-runner が内部で実行するコマンド（参考）

```bash
# 1. 古い成果物を消す（必須。残骸があるとポーリングが即抜けして偽の成功になる）
rm -f "$OUT_LAST" "$OUT_EVENTS" "$OUT_ERR" "$DONE_FILE"

# 2. nohup でデタッチ起動。完了マーカーを必ず書く
nohup bash -c "cat '$PROMPT_FILE' | codex exec --json --skip-git-repo-check \
    -m '$MODEL' -c model_reasoning_effort='$EFFORT' \
    -s '$SANDBOX' -C '$CWD' \
    -o '$OUT_LAST' \
    '' > '$OUT_EVENTS' 2>'$OUT_ERR'; echo \"EXIT=\$?\" > '$DONE_FILE'" >/dev/null 2>&1 &

# 3. 起動できたか 1 回確認する（起動失敗に気づかずポーリングし続けるのを防ぐ）
sleep 15; wc -l < "$OUT_EVENTS"; pgrep -f 'codex exec' | wc -l

# 4. foreground でポーリング。切れたら同じコマンドを叩き直すだけ（分岐を増やさない）
i=0; until [ -f "$DONE_FILE" ]; do sleep 5; i=$((i+1)); [ $i -ge 115 ] && break; done
```

> ⚠️ **バックグラウンド実行機構（`run_in_background` 等）で codex を起動しない。** 起動から**ちょうど 60 分**で外部 kill される事例が観測されている（2026-08-01）。`nohup` でプロセスグループを切り離せばこの制約を受けない。

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

`MODEL` は**毎回 GPT-5.6 系から選ぶ**（既定任せにしない）。`codex debug models` で最新一覧・各 model の effort 上限を確認できる（増減しうる）。

| model | モデル既定 effort | 対応 effort |
|---|---|---|
| `gpt-5.6-sol` | low | low / medium / high / xhigh / max / ultra |
| `gpt-5.6-terra` | medium | low / medium / high / xhigh / max / ultra |
| `gpt-5.6-luna` | medium | low / medium / high / xhigh / max |

## 明示オーバーライド

- `/codex --effort xhigh <相談>` — effort を固定
- `/codex --model gpt-5.6-terra <相談>` — model を明示指定（GPT-5.6 系から選ぶ）

## 注意

- **相談・レビュー用途は必ず `SANDBOX=read-only`**。config.toml の既定は `workspace-write`（codex がリポを書ける）なので、明示的に read-only を渡さないと codex が勝手にファイルを変更しうる。実装を任せる時だけ `workspace-write`
- **codex の自己申告を鵜呑みにしない**。「実装した / テスト通した」等は、呼び出し元が git 等で実体検証してから採用する
- 応答待ちの間にメインエージェントの作業を止めない。結果は返ってきた**実データのみ**で報告し、待ち時間に予測で答えを書かない
- **MCP（`mcp__codex__codex` 系）は廃止済み**。必ず CLI 経由
