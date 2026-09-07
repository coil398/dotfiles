# PIR² review の接続

この reference は、複数の review を実行する Codex runtime へ入力境界を渡すための補助資料です。レビューの観点、指定の解釈、担当の配分、結果の契約は、親が実体を確認した shared `reviewer/SKILL.md` と `code-review-guidance/references/` に委ねます。この reference で同じ規則を再定義しません。

同じ親が shared reviewer の手順を実行し、対象版、要件、実在する差分、受入条件、ユーザー指定、変更禁止範囲を渡します。別の進行担当を起動しません。shared reviewer が評価者を起動する場合、評価者には reviewer の進行手順を渡さず、実体の `code-review-guidance/SKILL.md` の絶対 path と対象に対応する reference だけを渡します。

レビューを分ける場合の書き込み所有、外部状態、権限境界、成果物 path は親が実在する値で確定します。実行者には担当する確認範囲、対象 diff、受入条件、禁止操作だけを渡し、未生成の plan・report・verdict を前提にしません。並列化はアクティブ設定と実行時空き枠、実測したファイル・契約の独立性から親が判断し、共有契約や同じファイルの書込みは直列化します。

親は reviewer から返った実在の結果を、要件・差分・再現結果と照合して受入に使います。未確認や判定不能を成功に変換せず、修正後は影響した確認だけを shared reviewer の手順で再確認します。refactor-advisor は必要な review が終わった後の任意提案として別に扱います。
