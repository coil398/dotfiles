# ledger calibration

| 入力 | 公開passed/total | hidden passed/total |
|---|---:|---:|
| reference | 5/5 | 5/5 |
| baseline | 0/5 | 0/5 |

referenceをbench.grade_refの経路で10回実行し、公開・hiddenの全件通過と同一の集計結果を確認しています。hiddenは公開テストの同一コピーで、分野は`ledger`の1件です。baselineのパッケージと公開テスト、task.mdの意味は保持します。

| area | 公開仕様 | 単独mutation | hidden passed/total |
|---|---|---|---:|
| ledger | task.mdのBehavior required / Requirements implied by tests、およびそこから参照する公開テストの全assertion | `ledger/parse.py`の`Decimal(rec["amount"].strip())`を`float(rec["amount"])`へ変更 | 1/5 |

採点結果とstdout/stderrは`/home/coil398/.ai-pir-runs/benchv2/B-legacy-calibration/ledger`に保存しています。

baselineのhiddenは0/5です。import/collection errorはなく、5件とも要求された振る舞いのassertionまたは処理で失敗します。公開テストを同一コピーする条件では、baselineを概ね10–40%にする目安を満たしません。
