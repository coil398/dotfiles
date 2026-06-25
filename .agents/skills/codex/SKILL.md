---
name: "codex"
description: "codex（OpenAI のコーディングエージェント）に MCP 経由で相談するスキル。第二意見・別アプローチ・難所のレビューを codex に求めるときに使う。タスクの重さに応じて reasoning effort（medium/high/xhigh）を選び、model は gpt-5.5 固定、必ず background Agent 経由で呼んでメイン作業を止めない。「codexに聞いて」「codexの意見」「codexに相談」「codexならどうする」「ask codex」「second opinion from codex」などで起動する。Codex 自身がタスク途中で codex に相談すると判断したときも、本スキルの手順（effort 選択・gpt-5.5 固定・background）が SSOT になる。ユーザーが /codex と入力したら必ずこのスキルを使う。"
---

# /codex — codex への相談（effort 自動選択・background）

`/codex <相談内容>` で codex に第二意見を求める。Codex がタスク途中で「codex にも聞こう」と判断したときも本スキルの手順に従う（**これが codex 相談の SSOT**）。

## 呼び出し手順

1. **必ず background Agent 経由で呼ぶ。** `mcp__codex__codex` を直接呼ぶとメイン Codex がブロックする（MCP ツールに `run_in_background` は無い）。Codex subagentを `run_in_background: true` で起動し、その subagent の中で `mcp__codex__codex` を呼ばせる。
2. 呼び出す前に **effort を選ぶ**（下表）。`config: { model_reasoning_effort: "<選んだ値>" }` で渡す。
3. **model は gpt-5.5 固定**（指定省略で `~/.codex/config.toml` の既定）。軽量/高速で十分な明示ケースだけ下げる。
4. codex の応答を**待たずにメイン作業を続ける**。結果が返ったら**実データのみ**を根拠に報告する（応答の捏造は禁止）。

## effort 選択ルブリック（既定 high）

| effort | 場面 |
|---|---|
| `medium` | 軽い確認・小差分レビュー・事実寄りの質問 |
| `high`（既定） | 非自明なデバッグ・複数ファイル設計レビュー・トレードオフ判断 |
| `xhigh` | 難しい根本原因究明・複雑アルゴリズム/設計・詰まった時の深掘り |

迷ったら `high`。明確に難問なら `xhigh`。`low` は使わない（それなら codex に相談しない）。

## 明示オーバーライド

- `/codex --effort xhigh <相談>` — effort を固定
- `/codex --model gpt-5.4-mini <相談>` — 軽量/高速モデルに下げる（大量の軽い確認を投げる時だけ。難問では下げない）

現行の選択肢: `gpt-5.5`（フロンティア・既定）/ `gpt-5.4` / `gpt-5.4-mini` / `gpt-5.3-codex-spark`。增減しうるので確証が要れば `codex debug models` で確認する。

## 呼び出しの形

background Agent を起動し、その中で次を実行させる:

```jsonc
mcp__codex__codex({
  prompt: "<相談内容。背景・前提・聞きたい論点を具体的に書く>",
  config: { model_reasoning_effort: "high" }   // タスクに応じて選択
  // model は省略（gpt-5.5 既定）。下げる時だけ明示
})
```

継続質問は `mcp__codex__codex-reply({ threadId, prompt })`。

## 注意

- codex 側の sandbox / approval は `~/.codex/config.toml`（workspace-write）に従う。本スキルは effort/model/呼び出し方だけを制御する。
- 応答待ちの間にメイン Codex の作業を止めない。結果は返ってきた**実データのみ**で報告し、待ち時間に予測で答えを書かない。
