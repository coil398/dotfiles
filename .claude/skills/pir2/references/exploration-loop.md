# 能動的再探索ループ（最大 5 回）

PIR² 系スキル（/pir2, /pir2async, /debug 等）共通の能動的再探索ループ仕様。

planner の返り値要約に `### EXPLORATION_NEEDED` セクションがあり、かつ箇条書き項目（`- topic`）が1件以上含まれる（`- なし` 単独でない）場合、追加探索 → planner 再起動を繰り返す。

> **ハイブリッド注記（v2.1.172〜）**: planner は `tools` に `Agent` を持ち、**軽微な追加確認は自分で explorer をネスト起動して完結する**（その場合 EXPLORATION_NEEDED には出さない）。本ループが扱うのは **(b) プラン方針が変わる規模の再探索**（EXPLORATION_NEEDED で要求されたもの）のみ。`REPLAN_COUNT` 管理・収束判定をメインの SSOT に残すための経路。詳細は `~/.claude/agents/planner.md`「能動探索（explorer ネスト起動）と EXPLORATION_NEEDED の使い分け」を参照。

`REPLAN_COUNT = 0` から開始。

## 収束判定ロジック

planner の返り値要約テキストの `### EXPLORATION_NEEDED` セクションを見る:

- 見出しが存在しない、または直下が「なし」「- なし」のみ → **収束**。次のステップへ進む
- `- topic` 形式の項目が1件以上列挙されている → 追加探索へ

## ループ本体

1. `REPLAN_COUNT += 1`
2. `REPLAN_COUNT > 5` に到達した場合、ループを強制終了して次のステップへ進む。最終サマリーに「**planner が依然追加探索を要求中（ハードキャップ5回到達）**: [topic 一覧]」と明記する
3. planner が出した各 topic ごとに explorer を起動する（topic が独立なら最大 3 体並列）:
   - `EXPLORATION_INDEX` は `{RUN_DIR}/exploration-*.md` 既存ファイルの最大連番 + 1 から割り振る
   - プロンプトには topic 本文と共に「この topic の調査に集中する。既存探索レポート（`{RUN_DIR}/exploration-*.md` 参照可）の重複調査は不要」と指示
4. 追加探索が完了したら planner を再起動する:
   - プロンプトは初回と同じだが、`{RUN_DIR}/exploration-*.md` のパス一覧に新しく追加されたものも含める
   - `plan.md` は上書き更新される（planner は同じパスに Write する）
5. planner の新しい返り値要約の EXPLORATION_NEEDED をチェック → 収束していれば次のステップへ、まだ要求が残っていれば 1. に戻る

> **注**: 「既存パターン逸脱の事前申告」のユーザー承認判定はループ収束後、次ステップの直前に1回だけ行う（ループ中の中間プランに対しては承認を求めない）。
