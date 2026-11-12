# inventory calibration

| 入力 | 公開passed/total | hidden passed/total |
|---|---:|---:|
| reference | 5/5 | 5/5 |
| baseline | 1/5 | 1/5 |

referenceをbench.grade_refの経路で10回実行し、公開・hiddenの全件通過と同一の集計結果を確認しています。hiddenは公開テストの同一コピーで、分野は`inventory`の1件です。baselineのパッケージと公開テスト、task.mdの意味は保持します。

| area | 公開仕様 | 単独mutation | hidden passed/total |
|---|---|---|---:|
| inventory | task.mdのBehavior required / Requirements implied by tests、およびそこから参照する公開テストの全assertion | `inventory.py`の`self.items[sku].qty += qty`を`self.items[sku].qty = qty`へ変更 | 4/5 |

採点結果とstdout/stderrは`/home/coil398/.ai-pir-runs/benchv2/B-legacy-calibration/inventory`に保存しています。
