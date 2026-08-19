# PIR² Final Summary Template

ステップ12で以下の内容をユーザーに提示する。

```markdown
## PIR² 完了サマリー

### タスク
[タスクの説明]

### 実装記録
docs/plans/YYYY-MM-DD-<feature>.md

### 変更ファイル
[実装完了レポートから抜粋]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL]
- 内側ループ回数: [INNER_LOOP_COUNT]
- [主な指摘事項があれば記載]

### リファクタ提案（refactor-advisor）
- 提案件数: [N]件（Medium: X / Low: Y）
- 適用件数: [M]件
- 未適用件数: [N-M]件
- 未適用の内訳: [ユーザーが none を選択 / 番号指定から漏れた候補 等]

### テスト結果
- テスト VERDICT: [PASS/FAIL]
- 外側ループ回数: [OUTER_LOOP_COUNT]

### 再探索ループ回数
- REPLAN_COUNT: [回数]
- [ハードキャップ到達時のみ]: planner が依然追加探索を要求中: [topic 一覧]

### 作業ディレクトリ
{RUN_DIR}

### 振り返り
[retrospector の改善内容の要約]

### メタ改善推奨（retrospector レポートに含まれていた場合のみ）
[内容を転記し、`/retro --meta` の実行をユーザー判断に委ねる旨を添える]
```
