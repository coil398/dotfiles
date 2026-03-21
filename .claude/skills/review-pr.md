# Review PR — コードレビュー

変更差分をレビューします。

**対象**: $ARGUMENTS（PR番号、ブランチ名、またはファイルパス。省略時は現在のステージング差分）

---

## ステップ 0: プロジェクトメモリパスの確認

```bash
claude_dir="${HOME}/.claude/projects/$(pwd | sed 's|/|-|g')/memory"
echo "$claude_dir"
```

取得したパスを `PROJECT_MEMORY_DIR` として以降で使用してください。

---

## ステップ 1: 差分の取得

以下のルールで差分を取得してください:

- **PR番号が指定された場合**: `gh pr diff <番号>` で差分を取得する
- **ブランチ名が指定された場合**: `git diff <ブランチ名>...HEAD` で差分を取得する
- **ファイルパスが指定された場合**: 該当ファイルを Read する
- **引数なし**: `git diff HEAD` でステージング済み＋未ステージの差分を取得する

取得した差分を `DIFF_CONTENT` として保持してください。

---

## ステップ 2: レビュー (Sonnet)

`reviewer` サブエージェントを起動してください。

- Agent ツールで `reviewer` エージェントを起動する
- model: `sonnet`
- プロンプトに以下を含める:
  - PROJECT_MEMORY_DIR
  - DIFF_CONTENT（差分全文）
  - 変更ファイル一覧
  - 「これはコードレビューです。実装は行わず、レビューのみ行ってください。」

`VERDICT: PASS` または `VERDICT: FAIL` とレビュー結果を受け取ってください。

---

## ステップ 3: 結果の提示

reviewer の出力をそのままユーザーに提示してください。
