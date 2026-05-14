# refactor-advisor 提案ゲート

PIR² 系スキル（/pir2, /pir2async, /debug）が共有する refactor-advisor 起動と任意適用フロー。reviewer 全員 PASS 後に **直列で 1 回のみ** 起動する設計（無限リファクタループ防止）。

## 起動条件

全体 VERDICT が PASS の場合のみ実行。FAIL で `INNER_LOOP_COUNT` 上限到達の場合はスキップしてテストフェーズへ直接進む。

## 7.5-1: refactor-advisor を起動

`refactor-advisor` エージェントを `Agent` ツールで **1 体だけ起動** する（reviewer は全員 PASS で確定済み）:

- **model**: `sonnet`
- **プロンプト**:
  - `PROJECT_MEMORY_DIR=[パス]`
  - `RUN_DIR=[パス]`
  - `REVIEW_INDEX=[最新 REVIEW_INDEX]`（reviewer の最新値をそのまま使う）
  - `{RUN_DIR}/plan.md` のパス
  - `{RUN_DIR}/implementation-{最新 IMPL_INDEX}.md` のパス
  - 「リファクタ提案レポート本体は `{RUN_DIR}/refactor-{REVIEW_INDEX}.md` に書き出し、チャットには PROPOSALS 数 + 要約のみ返してください」

## 7.5-2: 提案の存在確認

1. `{RUN_DIR}/refactor-{最新 REVIEW_INDEX}.md` を Read する
2. 冒頭の `PROPOSALS: N件` の N を確認する
3. `N == 0` の場合はスキップしてテストフェーズへ進む
4. `N >= 1` の場合は 7.5-3 へ

## 7.5-3: ユーザーへの提示

提案一覧をユーザーに提示する。**リスク情報（機能退行の可能性、golden カバレッジ等）はユーザーの適用判断に必須なので必ず含める**。フォーマット:

```
## リファクタ提案（refactor-advisor、Medium/Low）

N 件の改善候補があります:

1. [M|L] `ファイル名:行番号` — 提案タイトル
   現状: [要約]
   提案: [改善後の形]
   根拠: [既存先例、改善理由]
   リスク: [機能退行リスクの有無、golden カバレッジの状況]

2. [M|L] ...

適用する？
- all: 全件適用
- 1,3 のように番号カンマ区切り: 指定候補のみ適用
- none: 何も適用しない（そのままテストフェーズへ）
- custom: 個別にコメント書き換えたい等
```

## 7.5-4: ユーザー選択の処理

- **none**: テストフェーズへ進む
- **all / 番号指定**: 選択された候補を implementer に渡して修正させる（7.5-5 へ）
- **custom**: ユーザーから追加指示を受け取り、それを implementer に渡す（7.5-5 へ）

## 7.5-5: リファクタ適用の implementer 再起動

1. `IMPL_INDEX` をインクリメント
2. `implementer` を起動:
   - プロンプトに「リファクタ提案の適用。機能要件変更なし。退行させないこと」を明示
   - `{RUN_DIR}/refactor-{最新}.md` のパスと **選択された候補番号** を渡す
   - implementation レポートには「適用した候補 / スキップした候補 / 理由」を記録させる
3. implementer 完了後、**Fan-Out Gate（SKILL.md 7-2A の宣言 → 7-2B の並列発火）** で reviewer のみ同じ REVIEWER_SET で再起動（`REVIEW_INDEX` をインクリメント、退行検知のため。refactor-advisor は再起動しない = 2 周目のゲートを開かず無限ループ防止。**再レビュー時も Fan-Out Gate を省略しないこと**）
4. 再 reviewer で VERDICT FAIL が出た場合は、SKILL.md 7-4 の FAIL フローに合流して差し戻しループを回す（`INNER_LOOP_COUNT` は継続インクリメント、上限到達時はテストフェーズへ強制移行）。差し戻し成功後に再度 7.5 に戻ることはしない（refactor-advisor は初回 PASS 時の 1 回のみ）
5. 再 reviewer で PASS の場合、テストフェーズへ進む
