---
name: agy-opus-review
description: Antigravity の Claude Opus 5.5 に差分・コード・設計の独立レビューを依頼する（読み取り専用）。
---

# Antigravity Opus 5.5 独立レビュー

Antigravity の `swarm` ツールで Claude Opus 5.5 を 1 体起動し、独立したレビュー担当として使う。実装担当と別系統のモデルで、欠陥・回帰・セキュリティ上の問題を確認する。

## 起動

`swarm` で 1 体追加し、レビュー結果を受け取ったら終了する。

- `action: "add"`
- `name`: 短い英小文字名（例: `opus-review`）
- `model`: `"claude-opus-5-5-high"`
- `workspace`: `"inherit"`
- `brief`: 下記「渡す情報」と参照資料パスを含める

結果を確認したら `swarm(action="kill", name="opus-review")` で終了する。

## 独立性と参照資料

- 評価手順と合否契約は共有原本を使う。`brief` に次の実体絶対パスを含め、担当自身が読むようにする。
  - `~/.agents/skills/code-review-guidance/SKILL.md`
  - `~/.agents/skills/code-review-guidance/references/result-contract.md`
- 実装者の会話履歴や、他の評価者の結論は渡さない。
- 編集・修正はさせず、指摘と根拠の返却だけを求める。

## 渡す情報

- 対象リポジトリ、比較範囲（base/head または対象ファイル・差分）
- 要件と受入条件
- 重点的に確認したい観点（例: correctness、security、regression、仕様準拠）
- 上記の共有レビュー資料の実体パス

## 受入

親は返却された `COVERAGE` / `VERDICT` と各指摘を実差分・仕様・テスト結果と照合し、採否を判断する。
