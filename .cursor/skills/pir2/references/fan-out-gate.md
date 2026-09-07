# PIR² review の接続

この reference は、複数の review を実行する Cursor runtime へ入力境界を渡すための補助資料です。レビューの観点、指定の解釈、担当の配分、結果の契約は、親が実体を確認した `${CURSOR_SKILLS_DIR}/reviewer/SKILL.md` と `${CURSOR_SKILLS_DIR}/code-review-guidance/references/` に委ねます。この reference で同じ規則を再定義しません。

同じ親が shared reviewer の手順を実行し、対象版、要件、実在する差分、受入条件、ユーザー指定、変更禁止範囲を渡します。別の進行担当を起動しません。shared reviewer が評価者を起動する場合、評価者には reviewer の進行手順を渡さず、`${CURSOR_SKILLS_DIR}/code-review-guidance/SKILL.md` の実体絶対 path と対象に対応する reference だけを渡します。Cursor の起動は通常の `Task(subagent_type="reviewer")` とし、Task の `model` は省略または `inherit` にします。

レビューを分ける場合の書き込み所有、外部状態、権限境界、成果物 path は親が実在する値で確定します。実行者には担当する確認範囲、対象 diff、受入条件、禁止操作だけを渡し、未生成の plan・report・verdict を前提にしません。並列化は、runtime の実容量と実測したファイル・契約の独立性から親が判断します。

親は reviewer から返った実在の結果を、要件・差分・再現結果と照合して受入に使います。未確認や判定不能を成功に変換せず、修正後は影響した確認だけを shared reviewer の手順で再確認します。
