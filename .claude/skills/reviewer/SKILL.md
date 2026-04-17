---
name: reviewer
description: reviewerエージェントにローカルの差分・ファイルをレビューさせる。バグ・セキュリティ・パフォーマンス・保守性・命名一貫性・リグレッション・データアクセス重複などの観点でレビューし VERDICT: PASS/FAIL を返す。「reviewerに見せて」「reviewer」「ローカルの差分を見て」といった要望に使う。PR番号・リモートブランチ・gh pr 経由のレビューは /review-pr を使うこと。ユーザーが /reviewer と入力したら必ずこのスキルを使う。
argument-hint: [レビュー範囲の指定（例: ファイルパス、ブランチ名、コミット範囲。省略時は未コミットの差分）]
---

# Reviewer — コードレビュー

reviewer エージェントにコードレビューを実行させます。

**レビュー範囲**: $ARGUMENTS

---

## ステップ 0: メモリパスの解決

```bash
claude_dir="${HOME}/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
echo "$claude_dir"
```

---

## ステップ 1: レビュー対象の特定

`$ARGUMENTS` の内容に応じてレビュー対象を決定する:

- 指定なし: `git diff --name-only HEAD` で未コミットの差分を取得
- ファイルパス: 指定されたファイルをそのまま対象とする
- ブランチ名: `git diff --name-only <branch>...HEAD` でブランチとの差分を取得
- コミット範囲（例: `HEAD~3..HEAD`）: `git diff --name-only <range>` で差分を取得

対象ファイルが0件の場合はユーザーに報告して終了する。

---

## ステップ 2: レビュー実行

`reviewer` サブエージェントを起動してください。

- Agent ツールで `reviewer` エージェントを起動する
- model: `sonnet`
- プロンプトに以下を含める:
  - PROJECT_MEMORY_DIR（ステップ0で取得したパス）
  - レビュー対象のファイル一覧
  - 差分の取得コマンド（ステップ1で使用したものと同じ git diff コマンド。`--name-only` を外したもの）
  - 「上記の差分コマンドで変更内容を確認し、変更されたファイルを Read してレビューしてください。」

---

## ステップ 3: 結果の提示

reviewer の VERDICT と問題一覧をそのままユーザーに提示してください。
