# 能動的再探索と plan の増分更新（最大 5 回）

PIR² 系スキル（/pir2, /pir2async, /debug 等）共通の能動的再探索ループ仕様。

Sol が作成・更新した `{RUN_DIR}/plan.md` の `### EXPLORATION_NEEDED` セクションに、箇条書き topic（`- topic`）が1件以上含まれる（`- なし` 単独でない）場合だけ追加探索を行う。Sol は topic、担当範囲、必要な成果物を定義して explorer に渡し、返ったレポートを自ら Read して plan.md の該当箇所へ反映する。

`$ARGUMENTS` に `--deepplan` / `deepplan` が明示されている場合は、追加探索後の plan 策定も同じ `RUN_DIR` で deepplan を再実行する。指定がなければ Sol が既存 plan の該当箇所へ増分反映する。

`EXPLORATION_ROUND = 0` から開始する。これは追加探索の実行回数であり、plan再作成の回数ではない。

## 収束判定ロジック

Sol が更新した plan.md の `### EXPLORATION_NEEDED` セクションを見る:

- 見出しが存在しない、または直下が「なし」「- なし」のみ → **収束**。次のステップへ進む
- `- topic` 形式の項目が1件以上列挙されている → 追加探索へ

## ループ本体

1. `EXPLORATION_ROUND += 1`
2. `EXPLORATION_ROUND > 5` に到達した場合、ループを強制終了して次のステップへ進む。最終サマリーに「**Sol が依然追加探索を必要としている（ハードキャップ5回到達）**: [topic 一覧]」と明記する
3. Sol が定義した各 topic ごとに explorer を起動する（topic が独立なら最大 3 体並列）:
   - `EXPLORATION_INDEX` は `{RUN_DIR}/exploration-*.md` 既存ファイルの最大連番 + 1 から割り振る
   - プロンプトには topic 本文と共に「この topic の調査に集中する。既存探索レポート（`{RUN_DIR}/exploration-*.md` 参照可）の重複調査は不要」と指示
4. 追加探索が完了したら、Sol が新しい report を Read して根拠・scope・DAG・requirements・implementation shards の必要な箇所だけを plan.md に追記・修正する。既存計画を破棄・上書き再生成しない。
5. Sol が更新した plan.md の `EXPLORATION_NEEDED` をチェック → 収束していれば次のステップへ、topic が残っていれば 1. に戻る。

> **注**: 「既存パターン逸脱の事前申告」のユーザー承認判定はループ収束後、次ステップの直前に1回だけ行う（ループ中の中間プランに対しては承認を求めない）。
