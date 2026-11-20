---
name: agy-claude-implement
description: Antigravity の Claude Sonnet 5.5 または Opus 5.5 に範囲と終了条件を決めた局所実装・修正を委譲する。
---

# Antigravity Claude 局所実装

Antigravity の `swarm` ツールで Claude Sonnet 5.5 または Opus 5.5 を 1 体起動し、範囲と終了条件が明確な局所実装・修正を委譲する。

## 起動

- 標準モデル: `claude-sonnet-5-5-high`
- 難所・高リスクの修正: `claude-opus-5-5-high`

`swarm` で 1 体追加し、変更と確認結果を受け取る。

- `action: "add"`
- `name`: 短い英小文字名（例: `claude-impl`）
- `model`: `"claude-sonnet-5-5-high"`（難所は `"claude-opus-5-5-high"`）
- `workspace`: 単一の編集担当なら `"inherit"`（他の編集担当と並列実行する場合のみ `"share"`）
- `brief`: 下記「渡す情報」を含める

親が差分と確認結果を照合した後に `swarm(action="kill", name="claude-impl")` で終了する（`workspace: "share"` を使った場合は変更を取り込んでから終了する）。

## 渡す情報

- 目的と採用する設計方針
- 変更してよいファイル範囲と、変更禁止範囲
- 守るべき挙動・型・既存規約
- 完了条件と、実行すべき確認コマンド（テスト・型チェック・lint）
- commit、push、PR を実行しないこと

## 受入

- 担当には変更ファイル、実行した確認コマンドと結果、未確認事項・blocker を返させる。
- 親は `git status`、実差分、確認コマンドの出力を直接照合して受入を判定する。
- commit、push、PR、最終受入は親が行う。
