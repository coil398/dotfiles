---
name: codex
description: Codex CLIへ相談（read-only）または実装（workspace-write）を委譲する。「codexに聞いて」「codexに相談」「Codexで実装」、難所の別アプローチ、独立レビュー、/pir2 の実装を Codex に任せるときに使う。
---

# /codex — Codex への相談と実装委譲（runner 経由）

ロード済みの本 Skill の実体から共有原本 `../../../.agents/skills/codex/SKILL.md` を解決して先に Read し、相談と実装委譲の契約（経路、model / effort、runner へ渡す入力、相談・実装の境界と受入）を使う。本ファイルは Claude 固有の起動方式・model/effort ルブリック・CLI 契約の差分だけを書く（共有原本と重複する説明はここに複製しない）。

`/codex <相談内容>` で codex に第二意見を求め、`/codex <実装タスク>` で実装を任せる。Claude がタスク途中で「codex にも聞こう」「実装は codex に任せよう」と判断したときも本スキルの手順に従う（**これが Claude から Codex を使うときの SSOT**）。Codex は `codex exec` / `codex exec resume` で呼び出す。`mcp__codex__codex` は使わない。

## アーキテクチャ（Claude 固有）

**CLI 実行と完走管理は runner（`general-purpose` サブエージェント）が担う。メイン Claude は runner を `run_in_background: true` で起動して即座に別作業へ移る。**

```
メイン Claude : Agent(subagent_type: "general-purpose", run_in_background: true)
                → 即座に自由。他の作業を続ける / ターンを終える
runner        : codex exec を nohup でデタッチ起動
                → 自分のターン内で完了マーカーが出るまで foreground ポーリング
                → 1 回の Bash が返るたび同じポーリングを叩き直す（起動から 3 時間が上限）
                → 結果を確定して報告し終了
メイン Claude : runner の完了通知で起こされ、結果を受け取る
```

**この分業の要点**: ブロックする主体を runner に隔離する。codex が何分走ろうとメイン Claude は止まらない。

> ⚠️ **codex 本体は `run_in_background` で起動せず、`nohup` でデタッチする。** Bash の background 実行は長尺ジョブの完了前に終了しうる。`Agent` 自体はメインを止めないため `run_in_background: true` で起動する。メイン Claude 自身が foreground ポーリングしてはならない（待機時間ぶんターンが丸ごと止まり設計の意味が消える）。

サブエージェントはテキストを返すとターンが終了するため、何もせず background Bash の通知を待つ状態を維持できない。runner が完了マーカーファイルが現れるまで foreground でポーリングする実装詳細は共有 `../../../.agents/skills/codex/references/runner.md` を SSOT とする。

## 呼び出し手順

`Agent({ subagent_type: "general-purpose", run_in_background: true, prompt: ... })` で起動する。`model` は渡さず親のモデルを継承する。プロンプト先頭に「次の手順ファイルを先にReadし、その範囲だけ行う: <共有 runner の絶対path>」（本 Skill の実体から `../../../.agents/skills/codex/references/runner.md` を解決した path。通常は `~/.agents/skills/codex/references/runner.md`）を置き、続けて共有原本「runner へ渡す入力」の表（`PROMPT` / `CWD` / `SANDBOX` / `MODEL` / `EFFORT` / `WORK_DIR` / `RUN_ID` / `SESSION_FILE`）をそのまま渡す。runner の polling は Bash の `timeout: 590000` と `MAX_ITERS=115` を使う。runner は Codex CLI の実行と `WORK_DIR` 配下の入出力・証跡ファイルの書込を行う。`RUN_ID` は並列起動時に必ず別々の値にする。

起動後、メイン Claude はブロックされない。他の作業を続けるか、やることが無ければターンを終える。runner の完了通知で起こされたら、`EXIT` / `thread_id` / 応答本文 / エラー / ポーリング総ラウンド数を実データのみで受け取る（捏造禁止）。

続き質問は、同じ `SESSION_FILE` を渡して**新しい runner を同じ方法で起動する**（`codex exec resume <thread_id>` で同一 thread に会話を積む）。前の runner インスタンスが生きていれば `SendMessage` で継続してもよい。

Windows で npm 版 codex のフルパスを解決する手順（winget 版を避ける `CODEX_CMD`）は共有 runner に含まれる。

## 相談の effort 選択ルブリック（Claude 固有）

実装の model / effort は共有原本の worker・expert・expert_max 表に従う（既定は `gpt-6-luna` / `max`）。以下は相談・レビューの選び方。

`EFFORT`（= `model_reasoning_effort`）は**毎回タスクの重さから選ぶ**（固定既定に流さない）:

| effort | 場面 |
|---|---|
| `low` | ごく軽い事実確認・大量の軽い確認（下げるのはこの用途だけ） |
| `medium` | 軽い確認・小差分レビュー・事実寄りの質問 |
| `high` | 非自明なデバッグ・複数ファイル設計レビュー・トレードオフ判断 |
| `xhigh` | 難しい根本原因究明・複雑アルゴリズム/設計・詰まった時の深掘り |
| `max` / `ultra` | 最難関（`ultra` は `gpt-6-sol` のみ対応。滅多に使わない） |

`MODEL` は**毎回 GPT-6 系から選ぶ**（既定任せにしない）。`codex debug models` で最新一覧を確認できる。

| model | モデル既定 effort | 対応 effort |
|---|---|---|
| `gpt-6-sol` | medium | low / medium / high / xhigh / max / ultra |
| `gpt-6-luna` | medium | low / medium / high / xhigh / max |

**明示オーバーライド**: `/codex --effort xhigh <相談>`、`/codex --model gpt-6-sol <相談>`（GPT-6 系から選ぶ）。

## `codex exec` の呼び出し規約

経路は **`/codex` → runner → `codex exec`**。メインが `codex` を直接叩かない。実際の quoting・デタッチ・完了マーカー・ポーリングは共有 `../../../.agents/skills/codex/references/runner.md` が SSOT（本ファイルで CLI コマンド文字列を複製しない）。

**PROMPT に書く:** 問い・成功基準・パス・**関数単位の抜粋**・`Do not cat or rg whole files. Do not use MCP.`
**PROMPT に書かない:** ファイル全文 cat、vendor 横断 rg、Notion を使え。`--json` の tool 出力が次ターンのコンテキストを圧迫する。
**MCP:** `mcp__codex__codex` は使わない。Notion はオフ（`-c mcp_servers.notion.enabled=false`）にする。

## 注意

- **相談・レビュー用途は必ず `SANDBOX=read-only`**。config.toml の既定は `workspace-write`（codex がリポを書ける）なので、明示的に read-only を渡す。実装を任せる時だけ `workspace-write`
- **codex の自己申告を鵜呑みにしない**。「実装した / テスト通した」等は、git 等で実体検証してから採用する
- 応答待ちの間にメイン Claude の作業を止めない。結果は返ってきた**実データのみ**で報告し、待ち時間に予測で答えを書かない
