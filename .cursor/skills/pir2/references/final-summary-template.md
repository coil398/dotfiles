# PIR² Final Summary Template

ステップ 12 では、実際に確認できた差分・コマンド結果・reviewer / tester の報告だけを使ってユーザーへ提示する。実行していない工程、存在しない report、固定のループ回数や担当人数を補完しない。該当しない項目は省略または「未実施」とし、未確認の重大リスクは PASS と扱わない。

```markdown
## PIR² 完了サマリー

### タスク
[タスクの説明]

### 実装記録
[実在する plan / 実装記録のパス。なければ未生成]

### 変更ファイル
[実際の diff から確認したファイル一覧]

### レビュー結果
- 最終 VERDICT: [PASS/FAIL/UNVERIFIED]
- [起動した reviewer Task の観点、実在する report、主な指摘と対応]
- [未実施・未確認の観点と、残る実害または理由]

### リファクタ提案（refactor-advisor）
[実行した場合だけ、実在する提案・適用・未適用の結果を記載]

### テスト結果
- テスト VERDICT: [PASS/FAIL/UNVERIFIED/未実施]
- [実行コマンド、終了結果、未確認範囲、必要な権限・復旧確認]

### 探索・判断
- [実施した探索、根拠、plan の増分更新]
- [ユーザー判断が必要だった内容と、実際の決定。なければ省略]

### 作業ディレクトリ
[実在する RUN_DIR。なければ省略]

### 振り返り
[実行した場合だけ retrospector の改善内容を要約]

### メタ改善推奨（retrospector レポートに含まれていた場合のみ）
[retrospector report に実際に含まれる場合だけ転記し、実行はユーザー判断に委ねる]

### 残余リスク・次の判断
[未解決の correctness / security / data loss / permission リスク、blocker、または「なし」]
```
