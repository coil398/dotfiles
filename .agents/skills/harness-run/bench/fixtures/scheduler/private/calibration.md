# scheduler calibration

| 入力 | 公開passed/total | hidden passed/total |
|---|---:|---:|
| reference | 21/21 | 21/21 |
| baseline | 8/21 | 8/21 |

referenceをbench.grade_refの経路で10回実行し、公開・hiddenの全件通過と同一の集計結果を確認しています。hiddenは公開テストの同一コピーで、分野は`scheduler`の1件です。baselineのパッケージと公開テスト、task.mdの意味は保持します。

| area | 公開仕様 | 単独mutation | hidden passed/total |
|---|---|---|---:|
| scheduler | task.mdのBehavior required / Requirements implied by tests、およびそこから参照する公開テストの全assertion | `scheduler/simulate.py`の`run["end"]`を`run["end"] + 1`へ変更 | 11/21 |

採点結果とstdout/stderrは`/home/coil398/.ai-pir-runs/benchv2/B-legacy-calibration/scheduler`に保存しています。
