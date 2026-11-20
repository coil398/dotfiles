---
name: agy-claude-implement
description: Antigravity の Claude Sonnet 5.5 または Opus 5.5 に範囲と終了条件を決めた局所実装・修正を委譲する。
---

# Antigravity Claude 局所実装

Antigravity の Claude Sonnet 5.5 または Opus 5.5 を実装担当として呼び出し、範囲と終了条件が明確な局所実装・修正を委譲する。

## 起動

- 標準モデル: `claude-sonnet-5-5-high`
- 難所・高リスクの修正: `claude-opus-5-5-high`

```bash
agy -p --model claude-sonnet-5-5-high --mode auto \
  "<目的・変更許可範囲・禁止範囲・終了条件・確認コマンド>"
```

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
