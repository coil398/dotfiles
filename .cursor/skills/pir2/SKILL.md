---
name: "pir2"
description: "コーディングタスクを Plan → Implement → Review → Test → Retrospect で実行する。複雑な機能追加・リファクタリング・アーキテクチャ変更や「ちゃんと作りたい」「しっかり実装して」「品質重視で」に使う。`--deepplan` でFable熟考ループへ切り替える。ユーザーが /pir2 と入力したら必ず使う。"
argument-hint: "[タスクの説明] [--deepplan]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

# PIR² — Plan → Implement → Review → Test → Retrospect

タスク: $ARGUMENTS

メイン Cursor agent がオーケストレーターとして、探索の統合、計画、scope、所有境界、実装経路、受入、最終判断を持ちます。

## Cursor runtime

- 子エージェントは `Task`（`subagent_type`）で起動します。専用チーム lifecycle は使わず、必要な分担は通常の `Task` で行います。
- model / effortと必要なnative入口はAGENTSのruntime方針と公開起動schemaに従います。deepplan/deepthinkのモデル指定は各native入口からモデル正本を読み、このSkillで再定義しません。
- Taskが利用できない場合は、同じフェーズ境界でメインが直接実行し、独立性が要求されている範囲は共有reviewerの手順で未完了として扱います。
- target repositoryを基準にSkill参照を組み立てません。読込済みの本SKILL.mdの実体pathから、その親ディレクトリの親を `CURSOR_SKILLS_DIR` として確定し、参照はそこから解決します。共有資料は `${CURSOR_SKILLS_DIR}/../../.agents/skills` の実体を確認し `SHARED_SKILLS_DIR` とします。別配置では親が検証した共有rootを使い、対象repoや未確認HOMEから推測しません。

## 1. 実行コンテキスト

`PROJECT_ROOT` は現在のGit rootです。長時間runで再開・後段共有・計画記録が必要な場合だけ、親またはCursorが解決して実在を確認した `RUN_DIR` を使います。短いrunで保存先が不要ならrun directory、plan、reportを作りません。run pathを新規予約する場合は `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を読み、その手順を使います。手順内の `sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` は決定論的な SSOT として扱い、呼び出し元から実在値を受け取った場合は再計算しません。

resumeが明示された場合だけ既存handoffの未完了項目を読み、現在の差分と照合して計画へ増分反映します。passiveなhandoffは存在を通知します。handoff、next-steps、各reportは長時間runや後続担当に必要な場合だけ作り、未生成pathを必須入力にしません。

## 2. 必要ならbrainstorm

要件の解釈が結果を変える、互いに排他的な設計判断がある、既存パターンからの逸脱やscope拡張をユーザーと決める必要がある場合だけ、`${CURSOR_SKILLS_DIR}/brainstorm/SKILL.md` を使います。

候補が複数あるだけでは停止しません。既存の多数派、要求されたscope、最小の正しい差分からメインが選べる場合は、根拠をplanへ記録して続行します。ユーザー確認は、意図が決められない選択、外部・本番操作、不可逆変更、OS/security/権限境界など実質的な判断に限定します。

## 3. 探索

メインが `rg` / `rg --files` / Readで入口、既存パターン、変更候補、テストを確認します。独立した複数領域や深い呼び出し経路がある場合だけ、標準Taskへ探索を委任します。

探索担当には具体的な問い、担当範囲、既知の事実、変更禁止と `${SHARED_SKILLS_DIR}/research/references/explorer.md` の実体pathを渡し、担当自身が読みます。独立領域だけを並列化し、外部仕様は一次資料で確認します。担当は結果を返し、必要なreportは親が保存します。親が直接専門探索する場合は同じreferenceを読みます。

## 4. 計画

メイン Cursor agentが対象コードと探索結果を照合し、計画担当Taskを起動せず次を確定します。

- 目標、確認済み事実、対象/禁止範囲、既存パターンとの整合
- 実装単位、排他的所有、依存順、完了条件
- 変更で生じる実害、必要なreview/test、権限確認と復旧方法
- 追加探索が必要なら具体的な問い

計画ファイルは、長時間runの再開、後段担当への引き渡し、またはユーザーが記録を求めた場合だけ、親が安全性を確認した実在の保存先へ作成します。既存の `RUN_DIR/plan.md` がある場合はそれを更新し、別の `docs/plans/YYYY-MM-DD-<feature>.md` を無条件に複製しません。保存する場合も、完了済み判断とユーザー決定を保持して影響箇所だけを増分修正します。

`--deepplan` / `deepplan` が明示された場合だけ `${CURSOR_SKILLS_DIR}/deepplan/SKILL.md` を実行します。run pathを使う場合は親が渡した同じ `RUN_DIR` を使い、未指定ならdeepplanの保存を推測しません。起動指定はdeepplanのnative手順に従います。

実装前のユーザー確認は、複数案という語の出現ではなく、ユーザー意図なしに選べない排他的案、scope拡張、既存多数派からの重大な逸脱、外部依存の追加、危険な権限・不可逆操作がある場合だけ行います。該当時は `${CURSOR_SKILLS_DIR}/pir2/references/plan-choice-gate.md` をReadし、判断材料と選択結果を記録します。

## 5. リスクと権限

具体的な損害可能性から確認の強さを決めます。キーワードや変更ファイル数だけで固定工程を発火させません。

- 低リスク: 局所ロジック、文書、非実行設定。対象diffと焦点を絞った確認。
- 中リスク: 公開挙動、複数モジュール、API、生成物、永続化形式。影響する境界のreviewまたはtestを追加。
- 高リスク/破壊的: data loss、認証・認可、秘密情報、OS権限、security control、schema migration、互換性破壊、本番/外部操作。実装担当から独立した危険対応reviewと実動作確認、rollback確認。

OS/security/権限、本番・外部状態、不可逆操作を変更する前に、対象、影響、復旧方法を提示してユーザーの明示承認を得ます。レビューとテストの範囲は、実害に対応する shared skill の手順へ渡します。

破壊的影響または動作変更を含む場合は、実装前に `${CURSOR_SKILLS_DIR}/pir2/references/destructive-change-check.md` をReadして該当リスクを記録します。直前のユーザーfeedbackと実装案が競合し得る場合は `${CURSOR_SKILLS_DIR}/pir2/references/feedback-conflict-gate.md` をReadし、実際の矛盾だけを解消します。語句一致だけで停止しません。

## 6. 実装

小さく全体文脈と密結合した変更はメインが直接実装できます。所有範囲と終了条件を分離できる通常実装は 標準の実装Taskへ渡します。

委譲には目的、確認済み事実、排他的所有ファイル、維持/変更してよい契約、終了条件、焦点を絞った確認、変更禁止範囲を含めます。複数実装単位を使う場合は `${CURSOR_SKILLS_DIR}/pir2/references/implementation-delegation.md` を先にReadします。独立単位は所有ファイルと共有契約が競合しない場合だけ並列化し、共有ファイル・schema・lockfile・生成物を複数writerへ同時に渡しません。実装Taskは別Taskを起動せず、scopeを自己変更しません。

完了後、メインが `git status -sb`、対象diff、実在する変更ファイル、完了条件ごとの確認結果を実測します。実装者の自己申告やreport pathだけで受け入れません。

## 7. レビュー

最低限、メインが要求と対象diffを照合します。独立 reviewer が必要な場合は、同じメインが `${CURSOR_SKILLS_DIR}/reviewer/SKILL.md` を Read してその手順を実行します。別の進行担当を起動せず、対象版、要件、ユーザー指定、実在する計画・差分、必要な確認範囲を渡して選定・配分・判定を委ねます。`--reviewers=<roles>` と `--all-reviewers` の解釈も shared reviewer に委ね、この workflow で複製しません。

shared reviewer が評価者を起動する場合、評価者には reviewer の進行手順を渡さず、`${SHARED_SKILLS_DIR}/code-review-guidance/SKILL.md` の実体絶対 path と対象に対応する reference だけを渡します。評価者へ実在する対象、受入条件、変更禁止範囲を渡し、未生成の plan・report・verdict を前提にしません。保存が必要な report はメインが実在 path を確定します。返却された実在の結果を要件・diff・確認結果と照合し、未確認を成功へ変換しません。

refactor-advisorはユーザーが求めた場合、または完了を妨げない具体的改善を分離して提示する価値がある場合だけ起動します。提案は任意であり、適用前にユーザー承認を得ます。

## 8. テスト

変更した挙動に対応する既存テスト、構文・設定検証、必要なad-hoc確認を実行します。テスト範囲は防ぐ実害に比例させ、無関係な全suiteを一律実行しません。

runtime、データ整合性、生成物、外部境界、高リスク/破壊的変更、またはユーザーが明示した確認では、同じ親が `${CURSOR_SKILLS_DIR}/tester/SKILL.md` をReadし、その手順で実装担当と別系統の実行担当へ配分します。親は対象版、要件、`TEST_SCOPE`、実在する計画・差分、禁止範囲、`${SHARED_SKILLS_DIR}/tester/references/test-procedure.md` の実体pathを渡し、実行担当自身が専門資料をReadします。親が直接検証する場合は同資料を読みます。documentation/config-onlyや局所変更は、焦点を絞った確認で十分なら別担当を起動しません。

shared reviewer/tester の返却が要件未達または未確認を示した場合、メインが実差分・要件・再現結果を照合して根本原因を特定し、影響する最小修正へ戻します。修正後は影響する確認だけを各 shared skill の手順で再実行し、未実行の verdict や report を作りません。

## 9. 記録・振り返り・完了

記録が必要なrunでは、親が安全性を確認した実在する実装記録へ、実際の変更ファイル、実行した確認、起動したTaskと結果、未確認事項を追記します。保存先がない場合はチャット返却とし、未生成artifact、未起動actor、架空VERDICTを記録しません。

振り返りは同じ親が `${CURSOR_SKILLS_DIR}/retro/SKILL.md` の手順を使い、直接分析時と委任時の資料読込・返却・保存を接続します。handoffが必要なら未完了項目と実在artifactだけを残します。

完了報告には次を含めます。

- 実在するplanと実装記録のpath（未生成ならその旨）
- 実diffで確認した変更ファイル
- 実行した確認と結果
- 実際に起動したreviewer/testerとVERDICT。未実行なら未実行
- 未確認事項、blocker、handoff
- 簡潔なウォークスルー
