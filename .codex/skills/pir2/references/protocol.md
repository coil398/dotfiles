# Codex PIR² 内部プロトコル

PIR²系の進行は共有Skillsを正とし、Codexの委譲機構と明示CLI runnerだけnative手順に従う。共有の安全・Git・ユーザー権限の方針は `AGENTS.md` に従う。

## 親と委譲

Astraが探索の統合、計画、要件、所有、受入、最終判断を持つ。小さく密結合した変更は直接行い、独立単位はnative collaborationへ委譲する。通常のmodel・推論量と難所での起動時指定は、親が読み込んだ Codex Native Runtime Supplement をSSOTとし、専門役のmodel表をこのreferenceへ複製しない。難所を初手から別modelで起動する場合も、親が実際の公開引数とtask contextを明示する。詳細は読込済み `worker-delegation/SKILL.md` に従う。

各担当には一つの独立単位、排他的所有、禁止範囲、受入条件を渡す。アクティブ設定の `max_concurrent_threads_per_session` と実行時空き枠の低い方を上限に独立単位を並列化し、完了済みを空き枠と推測しない。利用可能な既存 thread は `followup_task` で再利用し、共有契約や同じファイルの書込みは直列化する。チーム連携は `spawn_agent`、`send_message`、`followup_task` 等の実際の collaboration API を使う。

## 成果物と引継ぎ

直接実装・native collaborationでは差分、変更ファイル、実行結果、未確認事項を返す。後段で全文が必要な場合だけ実体のある固有reportへ保存する。存在しないreport、固定index、runner台帳を補完しない。

run記録を使う場合は、親が実在を確認して渡した runtime artifact root と専有 RUN_DIR だけを使う。対象repo内の固定 `.ai-pir-runs`、HOME配下の固定path、sanitize手順を推測しない。再開時は親が渡した実在の plan または handoff を読み、完了済み・決定済みを保ったまま未完了項目だけを増分更新する。明示CLI runnerの証跡・安全境界だけはworker-delegationのrunner契約を適用する。

handoffは親が管理し、親が実在を確認して渡した path と共有の handoff 手順に従う。既存の別タスクのhandoffを変更せず、再開時は未完了項目だけを増分更新し、完了時は検証済みrunへ回復可能な形で保管する。

## 計画と追加探索

親が具体的な未確認topicと成功条件を定め、必要な追加探索を行う。報告を親が照合し、既存計画の影響箇所だけを更新する。計画をサブエージェントへ丸ごと委ねたり、単なる反復回数で未確認事項を成功扱いしたりしない。追加探索・停止条件は選択したSkillの手順に従う。

## レビューとテスト

同じ親が実体を確認した shared `reviewer/SKILL.md` または `tester/SKILL.md` を読み、その手順を実行する。別の進行担当を起動せず、親は対象版、要件、ユーザー指定、実在する差分・計画、必要な確認範囲を渡し、選定・配分・判定を委ねる。この protocol では観点、未知指定、担当間の分離、判定規則を複製しない。shared reviewer が評価者を起動する場合は、評価者へ reviewer の進行手順を渡さず、実体の `code-review-guidance/SKILL.md` の絶対 path と対象に対応する reference だけを渡す。shared tester には `tester/references/test-procedure.md` と結果契約の実体、`TEST_SCOPE`、禁止範囲を渡す。

必要な正しさ・安全性・データ保全とプロジェクト必須確認を維持する。固定人数、宣言形式、任意artifactの有無だけを完了条件にせず、未確認や判定不能を成功に変換しない。

UI変更を含む場合も、親が実差分と実害から必要な観点を選ぶ。UI/UXの評価者を使うときは、共有 `code-review-guidance` のUI/UX基準と指定されたプロジェクト原本の実体pathを親が渡し、固定roleの起動を要求しない。存在しないHOME pathを推測しない。

リファレンス実装からの移植では完全抽出とreference-fidelity照合を維持する。通常の不具合レビューと任意refactor提案を分け、refactor-advisorの提案はユーザーが選んだものだけ適用する。

## 指摘の自己照合

- 指摘を実コード、仕様、再現・テスト結果、ユーザーの明示判断で照合する。自分のplanやプロンプトは、争われている主張の正しさの証拠にしない。
- 誤検知と判断した場合は外部の一次情報と根拠を残す。未解決の正しさ・安全性を推測で閉じない。親が依頼と実測から決められる通常の詳細は解消し、ユーザーが留保した判断や権限外の変更だけを確認する。
- 修正後は影響した観点と確認だけを再実行し、無関係な成功済み結果を取り消さない。実装者の自己申告を親の受入や独立VERDICTとして扱わない。
