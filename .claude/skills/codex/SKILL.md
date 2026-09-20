---
name: codex
description: Codex CLIからread-onlyの第二意見を得る。「codexに聞いて」「codexに相談」、難所の別アプローチや独立レビューで使う。実装委譲は対象外。
---

# /codex — codex への相談（codex-runner 経由）

`/codex <相談内容>` で codex に第二意見を求める。Claude がタスク途中で「codex にも聞こう」と判断したときも本スキルの手順に従う（**これが codex 相談の SSOT**）。

Codex は `codex exec` / `codex exec resume` で呼び出す。`mcp__codex__codex` は使わない。

## アーキテクチャ

**CLI 実行と完走管理は `codex-runner` サブエージェントが担う。メイン Claude は `run_in_background: true` で起動して即座に別作業へ移る。**

```
メイン Claude : Agent(subagent_type: "codex-runner", run_in_background: true)
                → 即座に自由。他の作業を続ける / ターンを終える
codex-runner  : codex exec を nohup でデタッチ起動
                → 自分のターン内で完了マーカーが出るまで foreground ポーリング
                → 600 秒で切れたら同じポーリングを叩き直す（最大 20 ラウンド ≒ 3 時間）
                → 結果を確定して報告し終了
メイン Claude : codex-runner の完了通知で起こされ、結果を受け取る
```

> ⚠️ **codex 本体は `run_in_background` で起動せず、`nohup` でデタッチする。** Bash の background 実行は長尺ジョブの完了前に終了しうる。`Agent` 自体はメインを止めないため `run_in_background: true` で起動する。

**この分業の要点**: ブロックする主体を codex-runner に隔離する。codex が何分走ろうとメイン Claude は止まらない。

> ⚠️ **メイン Claude が自分で foreground ポーリングしてはならない。** メインのターンが待機時間ぶん丸ごと停止し、この設計の意味が消える。長時間ジョブを foreground で抱えるのは codex-runner の仕事。

### なぜ codex-runner に background 完了通知を待たせないのか

サブエージェントはテキストを返すとターンが終了するため、何もせず background Bash の通知を待つ状態を維持できない。codex-runner は完了マーカーファイルが現れるまで foreground でポーリングする。

## 呼び出し手順

### 1. codex-runner を background 起動する

`Agent({ subagent_type: "codex-runner", run_in_background: true, ... })` で起動し、プロンプトに以下を渡す:

| 名前 | 内容 |
|---|---|
| `PROMPT` | 相談内容。**cat/rg でファイル全文を取らせない。** 該当関数だけを本文に埋める |
| `CWD` | codex の作業ディレクトリ（対象リポの絶対パス） |
| `SANDBOX` | **相談・レビューは `read-only`**。実装を任せる場合のみ `workspace-write` |
| `MODEL` / `EFFORT` | **毎回タスクの重さから明示的に選んで渡す**（下記ルブリック。省略・既定任せにしない） |
| `WORK_DIR` | 入出力ファイルの置き場（スクラッチパス等） |
| `RUN_ID` | この実行を一意に識別する文字列。**並列起動時は必ず別々の値**にする |
| `SESSION_FILE` | 任意。会話を継続したいとき用の thread_id 永続化ファイルパス |

> ⚠️ **Windows: 素の `codex` を叩かせないこと。npm 版のフルパスを使うよう codex-runner に指示する。**
> winget 版（`~/AppData/Local/Programs/OpenAI/Codex/bin/codex`）が PATH で**先に解決される**が、
> `gpt-5.6-sol` に非対応で `The 'gpt-5.6-sol' model requires a newer version of Codex.` (400) で即失敗する。
> 必ず変数経由でフルパスを解決する:
>
> ```bash
> CODEX_CMD="$HOME/AppData/Roaming/npm/codex.cmd"
> [ -f "$CODEX_CMD" ] || CODEX_CMD="$(command -v codex)"
> ```
>
> 判定は必ず `-f`。`.cmd` は Git Bash 上で実行属性が立たず、`-x` では npm 版を選べない。

### 2. 待たずに別作業へ移る

メイン Claude はブロックされない。他の作業を続けるか、やることが無ければターンを終える。codex-runner の完了通知で起こされる。

### 3. 結果を受け取る

codex-runner は `EXIT` / `thread_id` / 応答本文 / エラー / ポーリング総ラウンド数を報告する。**実データのみを根拠に**ユーザーへ報告する（捏造禁止）。

### 4. 会話の継続（resume）

続き質問は、同じ `SESSION_FILE` を渡して**新しい codex-runner を起動する**。codex-runner が `codex exec resume <thread_id>` で同一 thread に会話を積む。前の codex-runner インスタンスが生きていれば `SendMessage` で継続してもよい。

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

## `codex exec` の正しい使い方（呼び出し元の義務）

経路は **`/codex` → `codex-runner` → `codex exec`**。メインが `codex` を直接叩かない。

**PROMPT に書く:** 問い・成功基準・パス・**関数単位の抜粋**・`Do not cat or rg whole files. Do not use MCP.`

**PROMPT に書かない:** ファイル全文 cat、vendor 横断 rg、Notion を使え。`--json` の tool 出力が次ターンのコンテキストを圧迫する。

**MCP:** `mcp__codex__codex` は使わない。Notion はオフ（`-c mcp_servers.notion.enabled=false`）にする。

## 注意

- **相談・レビュー用途は必ず `SANDBOX=read-only`**。config.toml の既定は `workspace-write`（codex がリポを書ける）なので、明示的に read-only を渡す。実装を任せる時だけ `workspace-write`
- **codex の自己申告を鵜呑みにしない**。「実装した / テスト通した」等は、git 等で実体検証してから採用する
- 応答待ちの間にメイン Claude の作業を止めない。結果は返ってきた**実データのみ**で報告し、待ち時間に予測で答えを書かない
- **MCP（`mcp__codex__codex` 系）は使わない**。必ず CLI 経由
