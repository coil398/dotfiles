---
name: agy-opus-consult
description: Antigravity の Claude Opus 5.5 に設計相談、第二意見、詰まった不具合の原因切り分けを依頼する（読み取り専用）。
---

# Antigravity Opus 5.5 相談

Antigravity の Claude Opus 5.5 を読み取り専用の相談担当として呼び出す。設計判断の相談、第二意見、不具合の原因切り分けに使う。

## 起動

- 標準モデル: `claude-opus-5-5-high`
- 軽い相談: `claude-opus-5-5-medium`

```bash
agy -p --model claude-opus-5-5-high --mode plan \
  "<問い・対象ファイル・確認済み事実・制約>"
```

## 渡す情報

- 問いと、答えで決めたい判断
- 対象リポジトリ、関連ファイルの絶対パス、必要に応じて対象版やエラーログの抜粋
- 親が確認済みの事実と制約
- 読み取り専用であること（ファイル編集や git 操作をしないこと）

## 返却契約

担当には次の見出しで簡潔に返させる。

- `ANSWER`: 結論と推奨案
- `EVIDENCE`: 読んだファイルやログの `path:line` 根拠
- `RISKS`: 見落としやすい副作用や前提の弱点
- `NEXT_CHECKS`: 親が確認すべき最小の手順（情報不足で判断できない場合は `BLOCKED` と不足事項）

親は返却を実コードと照合して最終判断を行う。
