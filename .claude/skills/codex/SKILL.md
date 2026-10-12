---
name: codex
description: Codex app-serverへ相談（read-only）または実装（ユーザーのCodex設定）を委譲する。「codexに聞いて」「codexに相談」「Codexで実装」、難所の別アプローチ、独立レビュー、/pir2 の実装を Codex に任せるときに使う。
---

# /codex — Codex への相談と実装委譲（runner 経由）

ロード済みの本 Skill の実体から共有原本 `../../../.agents/skills/codex/SKILL.md` を解決して先に Read し、相談と実装委譲の契約（起動方式、model / effort、runner へ渡す入力、相談・実装の境界と受入）を使う。本ファイルは Claude 固有の起動方式・model/effort の補助説明・tool 契約の差分だけを書く（共有原本と重複する説明はここに複製しない）。

`/codex <相談内容>` で codex に第二意見を求め、`/codex <実装タスク>` で実装を任せる。Claude がタスク途中で「codex にも聞こう」「実装は codex に任せよう」と判断したときも本スキルの手順に従う。Claude CodeからCodexを使うときの起動方式は本ファイルの差分に従う。runner を通じて Codex app-server を呼び出す。`mcp__codex__codex` は使わない。

## アーキテクチャ（Claude 固有）

**Codex app-server の実行と完走管理は runner（`general-purpose` サブエージェント）が担う。メイン Claude は runner を `run_in_background: true` で起動して即座に別作業へ移る。**

```
メイン Claude : Agent(subagent_type: "general-purpose", run_in_background: true)
                → 即座に自由。他の作業を続ける / ターンを終える
runner        : Codex app-server を nohup でデタッチ起動
                → 自分のターン内で完了マーカーが出るまで foreground ポーリング
                → 1 回の Bash が返るたび同じポーリングを叩き直す（起動から 3 時間が上限）
                → 結果を確定して報告し終了
メイン Claude : runner の完了通知で起こされ、結果を受け取る
```

**この分業の要点**: ブロックする主体を runner に隔離する。codex が何分走ろうとメイン Claude は止まらない。

> ⚠️ **codex 本体は `run_in_background` で起動せず、`nohup` でデタッチする。** Bash の background 実行は長尺ジョブの完了前に終了しうる。`Agent` 自体はメインを止めないため `run_in_background: true` で起動する。メイン Claude 自身が foreground ポーリングしてはならない（待機時間ぶんターンが丸ごと止まり設計の意味が消える）。

サブエージェントはテキストを返すとターンが終了するため、何もせず background Bash の通知を待つ状態を維持できない。runner が完了マーカーファイルが現れるまで foreground でポーリングする実装詳細は共有 `../../../.agents/skills/codex/references/runner.md` を SSOT とする。

## 呼び出し手順

`Agent({ subagent_type: "general-purpose", run_in_background: true, prompt: ... })` で起動する。`model` は渡さず親のモデルを継承する。プロンプト先頭に「次の手順ファイルを先にReadし、その範囲だけ行う: <共有 runner の絶対path>」（本 Skill の実体から `../../../.agents/skills/codex/references/runner.md` を解決した path。通常は `~/.agents/skills/codex/references/runner.md`）を置き、続けて共有原本「runner へ渡す入力」の表（`PROMPT` / `CWD` / `SANDBOX` / `MODEL` / `EFFORT` / `WORK_DIR` / `RUN_ID` / `SESSION_FILE`）をそのまま渡す。相談・レビューは `SANDBOX=read-only`、実装では `SANDBOX` を省略する。runner の polling は Bash の `timeout: 590000` と `MAX_ITERS=115` を使う。runner は Codex app-server の実行と `WORK_DIR` 配下の入出力・証跡ファイルの書込を行う。`RUN_ID` は並列起動時に必ず別々の値にする。

起動後、メイン Claude はブロックされない。他の作業を続けるか、やることが無ければターンを終える。runner の完了通知で起こされたら、`EXIT` / `thread_id` / 応答本文 / エラー / ポーリング総ラウンド数を実データのみで受け取る（捏造禁止）。

継続時の `SESSION_FILE` / `RUN_ID` は共有原本の[契約](../../../.agents/skills/codex/SKILL.md)に従う。前の runner インスタンスが生きていれば `SendMessage` で継続してもよい。

Windows で npm 版 codex のフルパスを解決する手順（winget 版を避ける `CODEX_CMD`）は共有 runner に含まれる。

## Codexのmodel / effort選択

相談・レビュー・実装の `MODEL` / `EFFORT` は、Claude固有の表を重ねず、共有原本 `../../../.agents/skills/codex/SKILL.md` の配分に従う。メインClaudeがrunner起動前に組合せを選び、指定値をそのまま渡す。

## Codex app-server の呼び出し規約

経路は **`/codex` → runner → Codex app-server**。メインが `codex` を直接叩かない。実際の quoting・デタッチ・完了マーカー・ポーリングは共有 `../../../.agents/skills/codex/references/runner.md` が SSOT（本ファイルで CLI コマンド文字列を複製しない）。

## 注意

- Claude からの `turn/steer` と `turn/interrupt` 操作は現時点で未対応です。中断は `PID_FILE` に記録された helper 自身の PID へ SIGTERM を送り、helper が実行中 turn に `turn/interrupt` を要求します。
- 応答待ちの間にメイン Claude の作業を止めない。結果は返ってきた**実データのみ**で報告し、待ち時間に予測で答えを書かない
