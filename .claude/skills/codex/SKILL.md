---
name: codex
description: Codex CLIからread-onlyの第二意見を得る。「codexに聞いて」「codexに相談」、難所の別アプローチや独立レビューで使う。実装委譲は対象外。
---

# /codex — codex への相談（runner 経由）

ロード済みの本 Skill の実体から共有原本 `../../../.agents/skills/codex/SKILL.md` を解決して先に Read し、bounded consultation の契約（経路、runner へ渡す入力、受入、read-only 境界）を使う。本ファイルは Claude 固有の起動方式・model/effort ルブリック・CLI 契約の差分だけを書く（共有原本と重複する説明はここに複製しない）。

`/codex <相談内容>` で codex に第二意見を求める。Claude がタスク途中で「codex にも聞こう」と判断したときも本スキルの手順に従う（**これが codex 相談の SSOT**）。Codex は `codex exec` / `codex exec resume` で呼び出す。`mcp__codex__codex` は使わない。

## アーキテクチャ（Claude 固有）

**CLI 実行と完走管理は runner（`general-purpose` サブエージェント）が担う。メイン Claude は runner を `run_in_background: true` で起動して即座に別作業へ移る。**

```
メイン Claude : Agent(subagent_type: "general-purpose", model: "sonnet", run_in_background: true)
                → 即座に自由。他の作業を続ける / ターンを終える
runner        : codex exec を nohup でデタッチ起動
                → 自分のターン内で完了マーカーが出るまで foreground ポーリング
                → 600 秒で切れたら同じポーリングを叩き直す（最大 20 ラウンド ≒ 3 時間）
                → 結果を確定して報告し終了
メイン Claude : runner の完了通知で起こされ、結果を受け取る
```

**この分業の要点**: ブロックする主体を runner に隔離する。codex が何分走ろうとメイン Claude は止まらない。

> ⚠️ **codex 本体は `run_in_background` で起動せず、`nohup` でデタッチする。** Bash の background 実行は長尺ジョブの完了前に終了しうる。`Agent` 自体はメインを止めないため `run_in_background: true` で起動する。メイン Claude 自身が foreground ポーリングしてはならない（待機時間ぶんターンが丸ごと止まり設計の意味が消える）。

サブエージェントはテキストを返すとターンが終了するため、何もせず background Bash の通知を待つ状態を維持できない。runner が完了マーカーファイルが現れるまで foreground でポーリングする実装詳細は `~/.claude/skills/codex/references/runner.md` を SSOT とする。

## 呼び出し手順

`Agent({ subagent_type: "general-purpose", model: "sonnet", run_in_background: true, prompt: ... })` で起動する。プロンプト先頭に「次の手順ファイルを先にReadし、その範囲だけ行う: ~/.claude/skills/codex/references/runner.md」を置き、続けて共有原本「runner へ渡す入力」の表（`PROMPT` / `CWD` / `SANDBOX` / `MODEL` / `EFFORT` / `WORK_DIR` / `RUN_ID` / `SESSION_FILE`）をそのまま渡す。runner は Codex CLI の実行と `WORK_DIR` 配下の入出力・証跡ファイルの書込を行う。`RUN_ID` は並列起動時に必ず別々の値にする。

起動後、メイン Claude はブロックされない。他の作業を続けるか、やることが無ければターンを終える。runner の完了通知で起こされたら、`EXIT` / `thread_id` / 応答本文 / エラー / ポーリング総ラウンド数を実データのみで受け取る（捏造禁止）。

続き質問は、同じ `SESSION_FILE` を渡して**新しい runner を同じ方法で起動する**（`codex exec resume <thread_id>` で同一 thread に会話を積む）。前の runner インスタンスが生きていれば `SendMessage` で継続してもよい。

> ⚠️ **Windows: 素の `codex` を叩かせないこと。npm 版のフルパスを使うよう runner に指示する。**
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

## effort 選択ルブリック（Claude 固有・`references/runner.md` の SSOT）

`EFFORT`（= `model_reasoning_effort`）は**毎回タスクの重さから選ぶ**（固定既定に流さない）:

| effort | 場面 |
|---|---|
| `low` | ごく軽い事実確認・大量の軽い確認（下げるのはこの用途だけ） |
| `medium` | 軽い確認・小差分レビュー・事実寄りの質問 |
| `high` | 非自明なデバッグ・複数ファイル設計レビュー・トレードオフ判断 |
| `xhigh` | 難しい根本原因究明・複雑アルゴリズム/設計・詰まった時の深掘り |
| `max` / `ultra` | 最難関（`gpt-5.6-sol` / `-terra` のみ対応。滅多に使わない） |

`MODEL` は**毎回 GPT-5.6 系から選ぶ**（既定任せにしない）。`codex debug models` で最新一覧を確認できる。

| model | モデル既定 effort | 対応 effort |
|---|---|---|
| `gpt-5.6-sol` | low | low / medium / high / xhigh / max / ultra |
| `gpt-5.6-terra` | medium | low / medium / high / xhigh / max / ultra |
| `gpt-5.6-luna` | medium | low / medium / high / xhigh / max |

**明示オーバーライド**: `/codex --effort xhigh <相談>`、`/codex --model gpt-5.6-terra <相談>`（GPT-5.6 系から選ぶ）。

## `codex exec` の呼び出し規約

経路は **`/codex` → runner → `codex exec`**。メインが `codex` を直接叩かない。実際の quoting・デタッチ・完了マーカー・ポーリングは `~/.claude/skills/codex/references/runner.md` が SSOT（本ファイルで CLI コマンド文字列を複製しない）。

**PROMPT に書く:** 問い・成功基準・パス・**関数単位の抜粋**・`Do not cat or rg whole files. Do not use MCP.`
**PROMPT に書かない:** ファイル全文 cat、vendor 横断 rg、Notion を使え。`--json` の tool 出力が次ターンのコンテキストを圧迫する。
**MCP:** `mcp__codex__codex` は使わない。Notion はオフ（`-c mcp_servers.notion.enabled=false`）にする。

## 注意

- **相談・レビュー用途は必ず `SANDBOX=read-only`**。config.toml の既定は `workspace-write`（codex がリポを書ける）なので、明示的に read-only を渡す。実装を任せる時だけ `workspace-write`
- **codex の自己申告を鵜呑みにしない**。「実装した / テスト通した」等は、git 等で実体検証してから採用する
- 応答待ちの間にメイン Claude の作業を止めない。結果は返ってきた**実データのみ**で報告し、待ち時間に予測で答えを書かない
