---
name: "writing-plan"
description: "実装計画を作り、各ステップの実施結果を追記して実装記録として残す。「計画を立てて」「ステップバイステップで進めて」「段階的に実装して」「実装記録を残したい」に使う。`--deepplan` でFable熟考ループへ切り替える。ユーザーが /writing-plan と入力したら必ず使う。"
argument-hint: "[タスクの説明] [--deepplan]"
---

<!-- Cursor native overlay: seeded from .agents/skills; edit here for Cursor mechanics -->

# ライティングプラン — 計画 → 実装 → 記録

タスク: $ARGUMENTS

メイン Cursor agent が計画、scope、実装順、受入、記録の更新を所有します。成果物は `docs/plans/YYYY-MM-DD-<feature>.md` で、各ステップの実測結果を追記します。

## Cursor runtime

- 子エージェントは `Task`（`subagent_type`）で起動します。通常のTaskで `model` は省略するか `inherit` とし、親Autoに従います。Cursor agent定義も `model: inherit` と `role: coding|reasoning` を使い、Codex用モデル名を流用しません。
- named exceptionはdeepplan/deepthinkの deliberator / synthesizer / gateだけです。選択したSkillの指示に従い、Task起動時だけ `claude-fable-5-1[effort=…]` を指定します。
- Taskが利用できない場合や小さく密結合したステップはメインが直接実行できます。未起動Taskの結果を捏造しません。
- target repository内のSkill pathを仮定しません。読込済みの本SKILL.md実体pathから、その親ディレクトリの親を `CURSOR_SKILLS_DIR` として確定し、参照はそこから解決します。run path が必要な場合は `${CURSOR_SKILLS_DIR}/pir2/references/sanitized-cwd.md` の `sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | sed 's|[^a-zA-Z0-9]|-|g')"` を使い、親から渡された実在値は再計算しません。

## 1. 計画

メイン Cursor agent（Auto / `inherit`）がユーザー要件、既存設計、対象コードを読み、計画担当Taskを起動せず次を確定します。

- 目標、要件、対象/禁止範囲、既存パターン
- bite-sizedな実装ステップ、依存順、排他的所有
- 各ステップの完了条件、焦点を絞った確認
- 変更リスク、必要なreview/test、権限確認
- 意図的に今回scopeから外す事項

`--deepplan` / `deepplan` が明示された場合だけ `${CURSOR_SKILLS_DIR}/deepplan/SKILL.md` を使います。Fable overrideはdeepplan内の3 roleだけに適用し、メインと他TaskはAuto / `inherit` を維持します。

候補が複数あるだけでは停止しません。既存多数派、要求scope、最小の正しい差分から選べる場合は根拠を記録して続行します。ユーザー確認は、意図が決められない排他的案、scope拡張、重大な既存パターン逸脱、OS/security/権限、本番・外部状態、不可逆操作に限定します。

## 2. 実装記録を初期化する

`docs/plans/` に次の骨格で保存し、パスをユーザーへ提示します。

```markdown
# [タスク名] 実装記録

_作成: YYYY-MM-DD | ステータス: 進行中_

## 目標
[タスクの概要]

## 実装計画
- [ ] ステップ 1: [ステップ名]
- [ ] ステップ 2: [ステップ名]

## 設計詳細
[対象、変更理由、依存順、完了条件、検証方法、リスク]

## 実装ログ
[各ステップ完了時に追記]

## 未確認事項
[なければなし]
```

長時間runや複数Taskで別の状態保存が必要な場合だけ、privateなRUN_DIRとplan.mdを作ります。小さいrunのために固定index、空report、handoffを先行生成しません。

## 3. ステップごとに実装・確認・追記する

依存順に一つずつ進めます。小さく全体文脈と密結合したステップはメインが直接実装できます。所有範囲と終了条件を分離できる通常ステップは `Task(subagent_type="implementer")` へ渡します。

委譲には目的、確認済み事実、排他的所有ファイル、維持する制約、変更してよい契約、終了条件、焦点を絞った確認、変更禁止範囲を含めます。独立ステップは所有ファイルと共有契約が競合しない場合だけ並列化し、同じファイル・schema・lockfile・生成物を複数writerへ同時に渡しません。実装Taskは別Taskを起動せず、scopeを自己変更しません。

各ステップ後、メインが次を実測します。

1. `git status -sb`、対象diff、実在する変更ファイルを確認する。
2. 完了条件と焦点を絞ったテスト・構文・設定確認を実行する。
3. 必要なreview/testを§4に従って実行する。
4. 満たした場合だけcheckboxを `[x]` にし、実装ログへ変更ファイル、変更内容、確認結果、実際に使ったTaskを追記する。
5. 未達なら `[ ]` のまま、原因、未確認事項、次の修正を記録する。

実装者の自己申告やreportの存在だけでステップを完了にしません。

## 4. リスク相応のreview/test

最低限、メインが要求と対象diffを照合します。独立reviewer/testerは、そのステップの変更リスクと検出価値に応じて選びます。

- 低リスク: 文書、局所ロジック、非実行設定。メインのdiff確認と焦点を絞った確認で足りればTaskを起動しない。
- 中リスク: 公開挙動、複数モジュール、API、生成物、永続化形式。correctnessを中心に、consistency、quality、security、architectureから影響する観点だけをreviewerへ渡すか、境界を確認するtesterを使う。
- 高リスク/破壊的: data loss、認証・認可、秘密情報、OS権限、security control、schema migration、互換性破壊、本番/外部操作。実装担当から独立した危険対応reviewと実動作確認、rollback確認を行う。security境界にはsecurity観点を含める。
- ユーザーが `--reviewers=<roles>` / `--all-reviewers` またはテストを明示した場合は指定を満たす。

reviewer/testerは `Task(subagent_type="reviewer")` / `Task(subagent_type="tester")` で起動します。複数の独立観点を起動する場合は `${CURSOR_SKILLS_DIR}/pir2/references/fan-out-gate.md` をReadして同じTask waveで並列化します。REVIEWER_SETはステップごとの影響に応じて決め、全ステップで固定しません。固定全5観点や人数不一致だけを理由とする完了取消は行いません。reviewer/testerには対象diff、当該ステップ、完了条件を渡し、必要な場合だけ固有report pathを割り当てます。

non-PASS時は指摘を要件・diff・テストで自己照合し、実際の原因に関係する最小修正へ戻します。再review/testは失敗原因と変更範囲に関係する担当だけに限定し、以前PASSだった全担当を機械的に再実行しません。

同じ呼び出しが2回続けて失敗したら、原因を特定せず3回目を試しません。原因が特定され、変更で成功する合理的根拠がある場合だけ再試行し、それ以外はblockerと選択肢を記録・報告します。続行判断が必要なら `${CURSOR_SKILLS_DIR}/pir2/references/continuation-gate.md` をReadします。未解決のcorrectness/security/data loss問題があるステップを完了扱いにして次へ進みません。

OS/security/権限、本番・外部状態、不可逆操作を変更する前に、対象、影響、復旧方法を提示してユーザーの明示承認を得ます。

## 5. 記録を最終化する

全ステップの完了条件を満たした場合だけヘッダーを `ステータス: 完了` に更新し、総括へ次を記録します。

- 完了ステップ数
- 実diffで確認した変更ファイル
- 実行した確認と結果
- 実際に起動したreviewer/testerとVERDICT。未実行なら未実行
- 未確認事項、意図的なscope外

未完了ならステータスを進行中またはblockedのまま保ち、次セッションへの引継ぎとして、完了済み、未完了、前提、設計変更、blockerを記録します。完了していないステップをサマリーだけで成功扱いにしません。

最後にユーザーへ実装記録のpath、完了/未完了ステップ、確認結果、起動したTask、未確認事項を提示します。記録の削除はユーザー判断に委ねます。
