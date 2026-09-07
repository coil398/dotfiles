---
name: "tester"
description: 実装済みコードを、親から渡された受入条件と検証範囲に沿って確認する。既存テストと必要なアドホック確認の結果を、共通のCOVERAGE/VERDICT契約で返す。ユーザーが /tester と入力したら必ず使う。
argument-hint: "[検証対象の説明]"
---

# Tester — 動作検証

実装済みコードの動作を検証します。親はこのSkillを読み、対象、受入条件、実害に対応する検証範囲を決めます。必要なら現在のランタイムの委譲primitiveで独立した実行者を使い、実行者には`references/test-procedure.md`と`code-review-guidance/references/result-contract.md`の実体絶対path、TEST_SCOPE、コマンド、許可された出力範囲を渡します。詳細な検証手順は`references/test-procedure.md`、返却の意味は`result-contract`を使います。起動方式や担当数をこの共有スキルで固定しません。

**検証対象（省略時は直近の実装）**: $ARGUMENTS

---

## ステップ 0: 対象と検証範囲の確認

対象repo、現在のstatus/diff、受入条件、変更した挙動、失敗時に防ぐ具体的な実害を確認する。`TEST_SCOPE`、実在する対象・plan/report path、親が渡したproject memory pathだけを使い、特定runtimeのhomeや保存先を推測しない。

---

## ステップ 1: 動作検証

小さく局所的な変更は親が直接確認できる。独立した検証に価値がある場合は、現在のランタイムのtester/delegation primitiveを使い、対象、受入条件、変更禁止範囲、検証コマンド、期待結果、外部・本番・不可逆操作の権限境界を渡す。`references/test-procedure.md`の実行・静的代替・IaC・データ取扱いを適用する。親が明示的に許可したlocal/ephemeralのtest outputとlocal fixtureだけを生成・変更し、対象実装・既存データ・既存fixtureは変更しない。

---

## ステップ 2: 結果の提示

実際に実行した検証結果、COVERAGE、VERDICT、未確認事項、blockerを親が差分と受入条件に照合して提示する。テスト失敗・期待外の挙動はFAIL、必須検証の未実施はINCOMPLETEとし、未起動の担当や未実行の確認を成功として補完しない。親が許可したlocal/ephemeralのtest outputとlocal fixture以外の変更、対象実装・既存データ・既存fixtureの変更、commit、push、記憶追記は行わない。report保存は親が行う。
