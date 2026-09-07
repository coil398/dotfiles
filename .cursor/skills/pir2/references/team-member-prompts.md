# PIR² async — Cursor の委譲境界

Cursor runtime では、pir2async も通常の `Task(subagent_type=...)` を使います。実装・レビュー・テストの起動、順序、ループ、ユーザー確認、最終受入は、同じメインが `${CURSOR_SKILLS_DIR}/pir2/SKILL.md` の手順で保持します。専用の進行担当や別 lifecycle を起動しません。

## 実装担当

親は、目的、対象版、確認済み事実、排他的な許可ファイル、禁止範囲、依存、完了条件、focused check、必要なら実在する plan・handoff・report path を渡します。Task の `model` は省略または `inherit` とし、担当は親の scope・受入条件・ユーザー判断を変更しません。追加調査や判断が必要なら親へ返します。

## reviewer への接続

同じメインが `${CURSOR_SKILLS_DIR}/reviewer/SKILL.md` を Read してその手順を実行します。親は対象版、要件、ユーザー指定、実在する差分・計画、必要な確認範囲を渡し、shared reviewer に選定・配分・判定を委ねます。shared reviewer が評価者を起動する場合、評価者へ reviewer の進行手順を渡さず、`${CURSOR_SKILLS_DIR}/code-review-guidance/SKILL.md` の実体絶対 path と対象に対応する reference だけを渡します。

## tester への接続

同じメインが `${CURSOR_SKILLS_DIR}/tester/SKILL.md` を Read してその手順を実行します。親は対象版、要件、実在する差分、`TEST_SCOPE`、期待結果、禁止範囲を渡し、実行担当へ `${CURSOR_SKILLS_DIR}/tester/references/test-procedure.md` と結果契約の実体 path を渡します。未生成の plan・report・verdict を前提にしません。

## 返却

担当は、実際に変更・確認したファイル、コマンドと出力、未確認事項、blocker、必要なら実在する記録 path だけを返します。親は status、diff、確認結果を照合し、実行していない担当・成果物・結果を補いません。縮退や容量不足を理由に安全境界を弱めません。
