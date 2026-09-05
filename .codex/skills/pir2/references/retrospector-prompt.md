# 振り返りの入力と観測

小規模 run は Astra が短く振り返る。複数担当や失敗の分析を分離する価値がある場合に retrospector role を使う。

## 入力

- タスク、PROJECT_ROOT、実行した workflow、実際の結果と未確認事項。
- 実在する plan、review/test report、必要な差分と再現記録。
- 方針変更や反復が判断に関係した場合、その根拠と実際の回数。
- META_MODE=false。メタ改善の実施はユーザーが明示した場合に限る。

native collaboration や直接実装に runner 台帳を作らない。runner の観測を扱う場合だけ同じ references directory の worker-observability.md を読み、存在する次の記録を渡す。

- worker-observations-v1.tsv: actor の attempt、実モデル、時間、実行結果。
- sol-acceptance-v1.tsv: Astra parent が測定した requirement 別 acceptance。ファイル名は runner schema の既存名であり、親モデルを指定するものではない。
- independent-verdicts-v1.tsv: reviewer/tester の独立 verdict。

実行結果、親の受入、独立判定は別々に扱う。台帳は append-only の事実記録であり、振り返りで編集・再作成しない。実測した観測を記録する場合だけ experimental.md の現行責務に従う。

## 出力

再利用できる学びと必要な改善だけを返す。通常の実装の振り返りからワークフロー骨格や権限ゲートを無断で変更しない。メタ改善推奨があれば最終サマリーで通知し、/retro --meta の実行判断をユーザーに委ねる。
