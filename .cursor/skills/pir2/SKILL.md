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

- 子エージェントは `Task`（`subagent_type`）で起動します。Claudeの `Agent` / Agent Teamsは使いません。
- 通常のTaskで `model` は省略するか `inherit` とし、親Autoに従います。Cursor agent定義の `model` も `inherit`、仕事分類は `role: coding|reasoning` を使います。Codex用モデル名を流用しません。
- named exceptionはdeepplan/deepthinkの deliberator / synthesizer / gate だけです。選択したSkillの指示に従い、Task起動時だけ `claude-fable-5-1[effort=…]` を渡します。メインと他のTaskはAuto / `inherit` のままです。
- Taskが利用できない場合は、同じフェーズ境界でメインが直接実行し、未実行の独立判定を捏造しません。
- target repositoryを基準にSkill参照を組み立てません。読込済みの本SKILL.mdの実体pathから、その親ディレクトリの親を `CURSOR_SKILLS_DIR` として確定し、参照はそこから解決します。

## 1. 実行コンテキスト

`PROJECT_ROOT` は現在のGit root、`RUN_DIR` はこのrunの計画・実在reportの保存先とします。sanitized-cwdと安全なrun directory生成は `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` を読み、その手順を使います。

resumeが明示された場合だけ既存handoffの未完了項目を読み、現在の差分と照合して計画へ増分反映します。passiveなhandoffは存在を通知します。handoff、next-steps、各reportは長時間runや後続担当に必要な場合だけ作り、未生成pathを必須入力にしません。

## 2. 必要ならbrainstorm

要件の解釈が結果を変える、互いに排他的な設計判断がある、既存パターンからの逸脱やscope拡張をユーザーと決める必要がある場合だけ、`${CURSOR_SKILLS_DIR}/brainstorm/SKILL.md` を使います。

候補が複数あるだけでは停止しません。既存の多数派、要求されたscope、最小の正しい差分からメインが選べる場合は、根拠をplanへ記録して続行します。ユーザー確認は、意図が決められない選択、外部・本番操作、不可逆変更、OS/security/権限境界など実質的な判断に限定します。

## 3. 探索

メインが `rg` / `rg --files` / Readで入口、既存パターン、変更候補、テストを確認します。独立した複数領域や深い呼び出し経路がある場合だけ、read-onlyの `Task(subagent_type="explorer")` を起動します。

explorerには具体的な問い、担当範囲、既知の事実、実装・stage・commit禁止を渡します。独立領域だけを並列化し、モデルは指定せずagent定義へ委ねます。外部仕様や更新され得る挙動は一次資料で確認します。reportが後続担当に必要なら固有pathへ保存し、チャット要約で足りる場合はファイル生成を強制しません。

## 4. 計画

メイン Cursor agent（Auto / `inherit`）が対象コードと探索結果を照合し、計画担当Taskを起動せず次を確定します。

- 目標、確認済み事実、対象/禁止範囲、既存パターンとの整合
- 実装単位、排他的所有、依存順、完了条件
- 変更で生じる実害、必要なreview/test、権限確認と復旧方法
- 追加探索が必要なら具体的な問い

計画を `RUN_DIR/plan.md` と `docs/plans/YYYY-MM-DD-<feature>.md` に保存し、更新時は完了済み判断とユーザー決定を保持して影響箇所だけを増分修正します。

`--deepplan` / `deepplan` が明示された場合だけ `${CURSOR_SKILLS_DIR}/deepplan/SKILL.md` を同じRUN_DIRで実行します。deliberator / synthesizer / gateのFable overrideはdeepplanの指示に従い、それ以外はAuto / `inherit` を維持します。

実装前のユーザー確認は、複数案という語の出現ではなく、ユーザー意図なしに選べない排他的案、scope拡張、既存多数派からの重大な逸脱、外部依存の追加、危険な権限・不可逆操作がある場合だけ行います。該当時は `${CURSOR_SKILLS_DIR}/pir2/references/plan-choice-gate.md` をReadし、判断材料と選択結果を記録します。

## 5. リスクと権限

具体的な損害可能性から確認の強さを決めます。キーワードや変更ファイル数だけで固定工程を発火させません。

- 低リスク: 局所ロジック、文書、非実行設定。対象diffと焦点を絞った確認。
- 中リスク: 公開挙動、複数モジュール、API、生成物、永続化形式。影響する境界のreviewまたはtestを追加。
- 高リスク/破壊的: data loss、認証・認可、秘密情報、OS権限、security control、schema migration、互換性破壊、本番/外部操作。実装担当から独立した危険対応reviewと実動作確認、rollback確認。

OS/security/権限、本番・外部状態、不可逆操作を変更する前に、対象、影響、復旧方法を提示してユーザーの明示承認を得ます。破壊的変更でも全5観点を一律起動せず、実害に対応する観点を選びます。

破壊的影響または動作変更を含む場合は、実装前に `${CURSOR_SKILLS_DIR}/pir2/references/destructive-change-check.md` をReadして該当リスクを記録します。直前のユーザーfeedbackと実装案が競合し得る場合は `${CURSOR_SKILLS_DIR}/pir2/references/feedback-conflict-gate.md` をReadし、実際の矛盾だけを解消します。語句一致だけで停止しません。

## 6. 実装

小さく全体文脈と密結合した変更はメインが直接実装できます。所有範囲と終了条件を分離できる通常実装は `Task(subagent_type="implementer")` へ渡します。

委譲には目的、確認済み事実、排他的所有ファイル、維持/変更してよい契約、終了条件、焦点を絞った確認、変更禁止範囲を含めます。複数実装単位を使う場合は `${CURSOR_SKILLS_DIR}/pir2/references/implementation-delegation.md` を先にReadします。独立単位は所有ファイルと共有契約が競合しない場合だけ並列化し、共有ファイル・schema・lockfile・生成物を複数writerへ同時に渡しません。実装Taskは別Taskを起動せず、scopeを自己変更しません。

完了後、メインが `git status -sb`、対象diff、実在する変更ファイル、完了条件ごとの確認結果を実測します。実装者の自己申告やreport pathだけで受け入れません。

## 7. レビュー

最低限、メインが要求と対象diffを照合します。独立reviewerは変更リスクと分離価値に応じて選びます。

- correctness: 挙動、境界条件、回帰の実害
- consistency: 既存パターン・生成元との不整合
- quality: 公開挙動や保守性への具体的影響
- security: 認証、入力、秘密情報、権限、外部境界
- architecture: API、DB schema、責務境界、複数レイヤー

`--reviewers=<roles>` / `--all-reviewers` があれば指定を満たします。未指定では該当観点だけをREVIEWER_SETにし、低リスクでメインのdiff確認が十分なら `Task(subagent_type="reviewer")` を起動しません。複数の独立観点を起動する場合は `${CURSOR_SKILLS_DIR}/pir2/references/fan-out-gate.md` をReadして同じTask waveで並列化しますが、固定人数や人数不一致だけを理由とする完了取消は行いません。

起動したreviewerのreportと明示VERDICTだけを集約します。non-PASS時は指摘を要件・diff・テストで自己照合し、実際の原因に関係する最小修正へ戻します。再reviewは失敗原因と変更範囲に関係する観点だけに限定し、以前PASSだった全観点を機械的に再実行しません。変更範囲が広がった場合だけ観点を追加します。

同じ呼び出しが2回続けて失敗したら、原因を特定せず3回目を試しません。原因が特定され、変更で成功する合理的根拠がある場合だけ再試行し、それ以外はblockerと選択肢を報告します。続行判断が必要なら `${CURSOR_SKILLS_DIR}/pir2/references/continuation-gate.md` をReadします。回数到達だけで成功扱いにしません。

refactor-advisorはユーザーが求めた場合、または完了を妨げない具体的改善を分離して提示する価値がある場合だけ起動します。提案は任意であり、適用前にユーザー承認を得ます。

## 8. テスト

変更した挙動に対応する既存テスト、構文・設定検証、必要なad-hoc確認を実行します。テスト範囲は防ぐ実害に比例させ、無関係な全suiteを一律実行しません。

runtime、データ整合性、生成物、外部境界、高リスク/破壊的変更、またはユーザーが明示した確認では、`${CURSOR_SKILLS_DIR}/pir2/references/tester-prompt.md` をReadし、実装担当と別系統の `Task(subagent_type="tester")` を使います。documentation/config-onlyや局所変更は、メインまたはimplementerの焦点を絞った確認で十分ならtesterを起動しません。

FAIL時は再現可能な原因を修正経路へ戻し、影響するreviewerとtesterだけを再実行します。未実行のtester VERDICTやreportを作りません。

## 9. 記録・振り返り・完了

実装記録へ、実際の変更ファイル、実行した確認、起動したTaskと結果、未確認事項を追記します。未生成artifact、未起動actor、架空VERDICTを記録しません。

振り返りはメインが行います。runが大きくログ分析を分離する価値がある場合だけ `Task(subagent_type="retrospector")` を起動し、モデルはAuto / `inherit` のままです。handoffが必要なら未完了項目と実在artifactだけを残します。

完了報告には次を含めます。

- planと実装記録のpath
- 実diffで確認した変更ファイル
- 実行した確認と結果
- 実際に起動したreviewer/testerとVERDICT。未実行なら未実行
- 未確認事項、blocker、handoff
- 簡潔なウォークスルー
