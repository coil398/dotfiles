# refactor-advisor 提案ゲート

PIR² の必須 review で未解決の correctness、security、data loss、behavioral
regression がなく、なお構造改善を別担当に検討させる価値がある場合の任意フローです。
refactor-advisor の起動回数、固定 report path、`PROPOSALS` 行、全 reviewer PASS
といった形式を一律 gate にはしません。必要な review を未解決のまま提案フェーズへ
進めてはいけません。

## 提案を求める場合

変更 diff、plan/要件、実行済みの確認、既知のリスクを渡し、`refactor-advisor` を
read-only で起動します。分離価値が小さければ Astra が同じ判断を行うか、このフェーズを
省略できます。提案には少なくとも次を含めます。

- 対象箇所と現状の問題
- 提案する変更と根拠
- correctness、機能退行、security/data loss、互換性へのリスク
- 既存 test/golden/check が覆う範囲と、適用時に必要な追加確認

候補がなければそのまま次の必要な確認へ進みます。候補があれば、Astra は重複や
スコープ外を除き、判断に必要なリスク情報とともにユーザーへ提示します。

## ユーザー承認

リファクタ提案は自動適用しません。ユーザーは全件、選択した候補、修正版、または
適用なしを選べます。承認された候補と範囲だけを実装し、提案にない拡張を混ぜません。
承認が必要なまま応答がない場合は、この任意リファクタを保留し、元タスクの必要な
安全・検証条件を勝手に緩めません。

## 適用経路

Astra が承認済み候補を具体的な scope と受入条件へ変換し、ロード済み
`worker-delegation` skill の現行経路を選びます。

- 小さく密結合した変更は Astra が直接実装できます。
- 独立した通常変更は worker（Luna Max）へ渡します。
- 原因・状態・競合・性能・厳しい整合性などの難所は expert/expert_max
  （Sol high/max）を初手から選べます。
- Terra は workload-specific な実測根拠がある場合だけです。Luna からの能力昇格は
  `luna→sol` を許可し、Terra の事前失敗を要求しません。

機能要件を変えないこと、承認された候補、許可/禁止範囲、必要な focused checks を
明示します。runner は artifact/provenance が必要な job だけに使います。

## 適用後の確認

Astra は実 diff と確認出力から承認候補だけが適用されたこと、機能要件が変わって
いないことを確認します。その後、影響した reviewer 観点と必要な回帰テストだけを
再実行します。変更が security、data loss、OS 権限、安全境界、本番操作、runtime、
データ整合性へ影響する場合、その review/test/承認を省略しません。

固定の REVIEWER_SET 全件、Fan-Out 形式、tester、refactor-advisor の再実行を一律に
要求しません。再提案は、適用によって新しい独立した改善判断が必要になり、ループする
価値と終了条件が明確な場合だけです。同じ提案を無条件に反復しません。確認で FAIL が
出た場合は、原因を実測して PIR² の修正経路へ戻し、別手段で迂回しません。
