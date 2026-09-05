---
name: "pir2codex"
description: "PIR²の計画・レビュー・テスト・振り返りを保ち、ImplementだけをCodex CLI bridgeへ差し替えるCursor用ワークフロー。/pir2codex で使う。"
argument-hint: "[タスクの説明]"
---

<!-- Cursor native overlay: PIR² with Codex CLI implementation -->

> **Cursor 固有ルール**
> - メインCursor agent（Auto）が計画、scope、所有範囲、受入、統合、ユーザー対話を所有する
> - 子agentの `Task.model` は省略または `inherit`。ベンダーmodelを固定しない
> - `deepthink` / `deepplan` の deliberator・synthesizer・gateだけは各SSOTのFable指定を許す
> - Codex CLIへ渡すmodelは [codex skill](../codex/SKILL.md) のbridge契約に従って明示する
> - CLIの実行・長時間待機・証跡は `codex-runner` に隔離し、native collaborationへ置換しない

# PIR² Codex

**タスク**: $ARGUMENTS

通常のPIR²のうちImplementだけをCodex CLIへ差し替えます。計画やscope判断をCodexへ委譲しません。

参照先は対象リポジトリではなく、読込済みの本 `SKILL.md` の実体から解決します。親はその絶対パスを `THIS_SKILL_PATH` として確定し、`CURSOR_SKILLS_DIR="$(cd "$(dirname "$THIS_SKILL_PATH")/.." && pwd -P)"` を使います。PIR²の共通手順は `${CURSOR_SKILLS_DIR}/pir2/SKILL.md` と同skillの `references/` がSSOTです。

## 1. 共通フロー

探索、brainstorm、計画、plan保存、handoff、破壊的変更確認、直前feedback照合、レビュー、テスト、walkthrough、memory、retrospect、後処理は、読込時点のPIR² SSOTに従います。pir2codexはその手順を複製せず、以下の実装差分だけを上書きします。

- メインCursor agentが探索結果を読み、`{RUN_DIR}/plan.md` を直接作成・増分更新する
- 計画には目的、非目標、対象ファイル、排他的所有範囲、禁止範囲、依存関係、測定可能なrequirements、影響する挙動と検証を含める
- 完全に独立した変更だけ `IMPLEMENTATION_SHARDS`、大きく結合して順序依存する変更だけ `IMPLEMENTATION_UNITS` として記録する。両者は排他
- 曖昧な分割は単一sessionにする
- 既存の決定、完了ステップ、ユーザー判断を保持し、影響箇所だけを更新する

`PROJECT_ROOT`、`RUN_DIR`、`PROJECT_MEMORY_DIR`、`HANDOFF_PATH`、`RESUME_MODE` はPIR² SSOTの現行手順で確定します。対象リポジトリに `.cursor/skills` があることを要求しません。

## 2. Codex担当の選択

Codex実装は次から選び、`plan.md` に理由を記録します。

| 担当 | Codex CLI model / effort | 用途 |
| --- | --- | --- |
| worker | `gpt-5.6-luna` / `max` | scope・所有範囲・終了条件が明確な通常実装 |
| expert | `gpt-5.6-sol` / `high` | 原因、状態、競合、性能、複数module整合など推論中心の難所 |
| expert_max | `gpt-5.6-sol` / `max` | 高リスク、複数仮説、特に難しい根本原因・設計 |

難所はexpert / expert_maxを最初から選べます。Sol利用のためにLunaやTerraを先に失敗させません。Terraは同種workloadの実測でLunaより手戻りが少なくSolより総費用が低い場合だけ、model・effort・根拠を明示する例外です。

入力不足、requirements未決定、権限、環境、CLI failureは能力不足ではありません。自動fallbackやrunner側のmodel変更を行わず、メインが入力またはblockerを処理します。

## 3. 実装形態

- `codex-single`: 1つのcodex-runnerが計画した実装scopeを担当する既定経路
- `codex-shards`: 所有ファイルが重ならず、共有状態・順序依存がないshardだけを別RUN_IDで並列実行
- `codex-sequential`: 順序付きunitをUNIT_ID順にfresh sessionで直列実行し、後続promptへ実在する先行diffと決定を渡す

shardやunitごとに目的、許可ファイル、禁止ファイル、終了条件を明示します。同じファイルを複数sessionへ同時に割り当てません。shardの全結果とunit間の接続は、メインが実diffから統合確認します。問題があれば原因を特定し、単一sessionの限定修正へ戻します。

## 4. codex-runner起動

`Task({ subagent_type: "codex-runner", run_in_background: true, model: "inherit", ... })` を使います。各jobへ次を渡します。

| 入力 | 値 |
| --- | --- |
| `PROMPT` | 下記templateへplanと当該scopeを埋めた非空本文 |
| `CWD` | `PROJECT_ROOT` のcanonical絶対パス |
| `SANDBOX` | `workspace-write` |
| `MODEL` / `EFFORT` | ステップ2の選択 |
| `SELECTION_REASON` | standardまたは難度・Terra実測根拠 |
| `WORK_DIR` | `RUN_DIR` |
| `RUN_ID` | jobごとに一意な `impl-<attempt>[-<shard|unit>]` |
| `SESSION_FILE` | resumeが必要な単一jobだけ。shard/unitのfresh sessionでは省略 |

メインはrunner完了通知まで受入・レビューへ進みません。メイン自身がCodexをforegroundで起動・pollingしません。

### 実装prompt

```text
あなたは実装担当です。以下の確定済み計画と担当範囲に従い、対象リポジトリを実際に編集してください。

制約:
- 許可されたscopeだけを変更し、既存の未コミット変更を戻さない
- 計画・要件・所有範囲を変更しない。不足はblockerとして返す
- 外部送信、本番操作、破壊的操作、権限昇格を行わない
- 既存パターンに合わせ、根本原因を修正する
- 指定された焦点を絞った確認だけを実行し、無関係な全テストを走らせない
- 変更ファイル、実装内容、確認結果、未確認事項、blockerを簡潔に返す

--- 計画 ---
{plan.mdの関連部分}

--- 担当範囲 ---
{single / shard / unit の所有範囲・許可ファイル・禁止ファイル}

--- 受入条件 ---
{requirements と実行する確認}

--- 修正時の実測結果 ---
{FAILした観点・テスト・diff。初回はなし}
```

plan全体のverbatim転送が安全・正確性に必要なら含めます。巨大な無関係情報は渡しません。

## 5. CLI証跡と受入

CLI境界に必要な証跡は省略しません。codex-runnerがjobごとに作るprompt、last response、JSONL events、stderr、done marker、実行state、job固有PID、thread/session metadataを実行証拠として保持します。固定台帳、全job共通fixture、実行と無関係な追加artifactは作りません。

workspace-write jobの前後で、メインが対象scopeの `git status` とdiffを確認します。runnerの `EXIT`、観測したprocess cwd、CLIへ渡したrequested model / effort / sandbox、観測可能な実効値、done marker、stderr、最終応答を読み、申告変更ファイルを実在diffと照合します。runnerの終了やCodexの自己申告だけをacceptanceにしません。CLI eventsから観測できない実効値は `unavailable` のまま扱います。並列jobではRUN_IDと成果物pathの衝突がないことも確認します。

メインは受入後、`{RUN_DIR}/implementation-<attempt>[-<shard|unit>].md` を作成します。後段へ渡すreportはこの実在pathに統一し、次を記録します。

- job、requested MODEL / EFFORT / SANDBOX、観測可能な実効値、RUN_ID、session/thread
- 実測した変更ファイルと実装内容
- 実行した確認と結果
- runner証跡path
- 未確認事項とblocker

Codexが変更不要と返した場合も、メインがrequirementsとdiffから理由を確認してNO-OPとして記録します。未生成indexや存在しないreportを後段入力にしません。

resumeは同じSESSION_FILEを使い、codex-runnerが保存済みcanonical CWD・sandboxとの一致を確認できる場合だけ行います。不一致時は黙ってfallbackせず、メインがfresh sessionにするかblockerとして扱います。

## 6. 修正・レビュー・テスト

実装後のreview、test、retrospectはPIR² SSOTの現行フローを使います。ただし確認の選択は実差分と失敗時の具体的な実害に比例させます。

- correctness: 挙動、データ、requirements、Codex申告とdiffの不一致
- security: 認証、認可、秘密情報、入力境界、依存、sandbox・権限
- consistency / architecture: 公開契約、SSOT、生成元と生成物、複数module
- quality: 保守性がcorrectnessや安全な変更へ具体的に影響する場合
- ui-ux: UI、状態表示、操作、アクセシビリティ

必要なreviewerが複数ならTaskを並列起動します。Task modelは省略またはinheritです。全5観点、Fan-Out宣言、固定回数、PASS済み全観点の再実行を一律に要求しません。

テストは変更が影響する挙動を検証します。焦点を絞った既存テスト、静的・構文・設定検証、必要な回帰テストを選びます。独立testerが具体的な実害を検出できる変更ではtesterを使います。無関係な全テスト、固定fixture、tester起動を全jobへ強制しません。OS・security・権限、データ損失、公開契約、生成物に影響する場合は対応する安全・回帰検証を省略しません。

FAIL時は根本原因を特定し、planとrequirementsの影響箇所だけを増分更新します。修正promptには関連するreview/test reportと実測diffを渡し、影響を受けた観点・挙動だけを再確認します。入力が十分な同一threadならresumeでき、文脈汚染やscope変更がある場合はfresh sessionを選びます。

refactor-advisorの提案は任意であり、適用前にユーザー承認を得ます。適用した場合も影響する確認だけを行います。

本番変更、外部送信、破壊的操作、OS・security・権限境界の変更は、planに含まれていても必要な明示承認を別途得ます。

## 7. 最終サマリー

PIR² SSOTの完了条件を満たした場合だけ完了とし、次を提示します。

```markdown
## PIR² Codex 完了サマリー

- タスク: [...]
- 実装形態: codex-single / codex-shards / codex-sequential
- Codex job: [requested MODEL / EFFORT / SANDBOX、観測可能な実効値、RUN_ID / session数]
- 実装記録: [実在する implementation report path]
- 変更ファイル: [実測一覧]
- レビュー: [選んだ観点と結果。不要ならなし]
- テスト: [影響する挙動と結果]
- CLI証跡: [runner成果物path]
- 未確認事項 / blocker: [なければなし]
```

retrospectには `ワークフロー種別: pir2codex`、Codex担当・requested model / effort / sandbox・観測可能な実効値・session数、CLI failure、手戻り、通常PIR²との差を実測値で渡します。
