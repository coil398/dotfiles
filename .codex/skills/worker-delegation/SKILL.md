---
name: worker-delegation
description: Solが判断・計画した具体的な作業をLuna/Terraまたは例外的なSol workerへ委譲するCodex-native契約。acceptanceと品質・動作判定はSolと別系統のreviewer/testerが所有する。
argument-hint: "[具体化済みの委譲タスク]"
---

# Worker Delegation

Codexの全workflowで共通利用する実作業委譲契約です。親/main Solは司令塔として判断・計画・委譲・受入を所有し、具体的なリポジトリ実装は必ずworker subagentへ渡します。workerの自己申告やrunnerの終了コードだけで完了判定をしません。

## 責任境界

- **親/main Sol commander**: ユーザーとの対話、探索、設計・要件の判断、所有範囲、具体的なtask/requirements、actorとeffortの選択、昇格理由、acceptance、review/testのオーケストレーション、集約、最終判定を所有する。親/main Solは具体的なリポジトリ実装を行わない。
- **Luna Max worker**: Solが十分に具体化した実作業の既定actor。指定された範囲とrequirementsに従って作業するだけで、判断、スコープ拡張、別actorの起動、完了判定をしない。
- **Terra High/Max worker**: Lunaの能力または局所推論不足をSolが実測した場合の明示昇格先。Terra Maxは後述の証拠がある場合だけ選択する。
- **Sol High/Max worker**: Terraの能力または局所推論不足をSolが実測した場合だけ使える例外的なSol worker subagent。親/main Solの実装回収ではない。
- **reviewer / tester**: workerとは別系統で、それぞれ品質と動作を判定する。workerの自己申告はacceptanceやPASSの根拠にしない。

要件の曖昧さ・入力不足、環境またはツールの失敗、権限不足、外部状態の失敗は、より強いactor/effortへの昇格理由になりません。Solへ制御を戻し、判断・入力・環境・権限・外部状態を解消してから再計画します。

## Actor ladder

actorとeffortの選択、昇格理由、同じ原因に対する試行回数の記録はSolが行います。runnerは明示されたactorとeffortをそのまま実行し、model・effortを変更せず、自動fallbackもしません。

段階は optional-stage であり、毎段階を訪問する必要はありません。標準の順序は **Luna Max → measured Terra High → evidence-only Terra Max → exceptional Sol High worker → evidence-only Sol Max** です。

1. **Luna Maxを既定として起動する**。対象ファイル、禁止範囲、手順、requirements、必要な検証コマンドを先に具体化する。
2. **Terra Highへ測定済み昇格する**。task/requirementsが十分な状態で、Lunaの能力または局所推論の不足を差分・検証結果・再現結果で実測できた場合だけ、同じ要件を`--actor terra --effort high`で明示実行する。
3. **Terra Maxを証拠がある場合だけ使う**。次の少なくとも1つをSolが記録した場合に限る: multi-stage causality、design contradiction、cross-module invariants、security/data-integrity risk、またはTerra High insufficiencyの文書化。Terra Maxは同じ原因に対して高々1回とする。
4. **Sol High workerへ例外的に昇格する**。Terraの能力または局所推論不足を実測した後だけ、`--actor sol --effort high`でSol worker subagentを起動する。要件不足や起動不能を理由に親/main Solが実装を引き取ってはいけない。
5. **Sol Maxを証拠がある場合だけ使う**。highest-complexity/high-risk evidence、またはSol High insufficiencyを文書化した場合に限り、`--actor sol --effort max`を同じ原因に対して高々1回使う。

Terra MaxとSol Maxは routine final stageではありません。LunaやTerraの結果が要件不足・判断不足・権限不足・CLI error・起動不能であっただけなら、runnerから次actorへ進めずSolへ戻します。要件不足や起動不能を理由に親/main Solが実装を引き取ってはいけません。runnerにもworkerにも自動fallback、自己判断によるactor変更、強いeffortへの自動変更を実装しません。

## 委譲契約

Solはworker起動前に、次を一時ファイルへ用意します。リポジトリ内に作業用taskや結果を残す必要がない場合は`mktemp -d`を使います。

`task.md`には目的、作業範囲、具体的な実装指示、禁止事項を書きます。`requirements.md`にはファイル、差分、コマンド出力などで真偽を判定できる`R1`から始まる要件を書きます。「良い感じ」のような抽象的要件だけで起動しません。

既定のLuna Max:

```sh
.codex/skills/worker-delegation/scripts/run-worker.sh \
  --actor luna \
  --effort max \
  --cwd <対象リポジトリの絶対パス> \
  --task-file <task.md> \
  --requirements-file <requirements.md> \
  --output-file <worker-result.md>
```

TerraまたはSol workerへの昇格時も、actorとeffortをSolが明示します。runnerは次のmodelをactorに正確に対応させます。

| actor | model | effortの既定値 | 有効なeffort |
| --- | --- | --- | --- |
| `luna` | `gpt-5.6-luna` | `max` | `max`のみ |
| `terra` | `gpt-5.6-terra` | `high` | `high` / `max` |
| `sol` | `gpt-5.6-sol` | `high` | `high` / `max` |

runnerは選択したeffortを`-c model_reasoning_effort="..."`でCodexへそのまま渡し、worker prompt に期待 actor/model/effort を注入します。未知actor、未知effort、actorとeffortの不正な組み合わせはexit 2で拒否し、Codexを起動しません。`--help`はactor、effort、各既定値と有効な組み合わせを説明します。

すべてのactorに、次の安全規則をrunnerが注入します。

- 他エージェントの変更やユーザーの既存変更を戻さない。
- commit / pushをしない。
- 別agent、別worker、reviewer、testerを起動しない。
- 指示や権限が不足している場合、独断で補わずblockerとしてSolへ返す。
- 指定された所有範囲を越えない。

runnerは既存の入力検証に加えて、物理的に解決したcwdがGitの物理的なトップレベルと一致すること、cwd直下の実体ある非シンボリックリンク`.codex`がcwd内に留まること、`.codex`配下のsymlinkは同じGit root内のcurrent UID所有・group/world非writableな実体へ1段だけ解決するものに限って許可し、外部・broken・nested・`.git`向けを拒否すること、portable inventoryにPerl coreの`File::Find`・`Cwd`・`Digest::SHA`を使い、利用不能なら明示的にfail-closedすること、空でないtask/requirements、`- R<number>:`形式のrequirementsを検証します。出力親はcanonicalなcwd内、または標準Sol artifact root `$HOME/.ai-pir-runs`内だけを許可します。cwd内の出力はartifact rootの有無に依存しませんが、外部artifact出力では標準artifact root自体が実体ある非シンボリックリンクのディレクトリでなければなりません。選択した許可root以下のシンボリックリンク成分も拒否します。祖先の物理alias（例えば`/var`）はcanonicalizeして許可します。最終outputとその`${output_file}.provenance.tsv` sidecarが未作成であることも起動前に確認します。許可rootからoutput parentまでの全ディレクトリ成分について、初回にsymlink不存在、current UID所有、group/world非writableを検証し、device/inode/uid/mode identityを記録します。`pre-codex`、`post-codex`、`pre-publish`の各時点で全成分を再検証し、repo-local outputではrepo rootから、外部artifact outputではartifact rootからの中間成分置換をfail-closedで拒否します。CodexにはJSON mode、workspace-write sandbox、canonicalな`-C`と`--add-dir`、stdin promptを渡し、Codexの`-o`には選択した出力親で排他的に作った一時ファイルだけを渡します。Codex終了後、raw worker reportは未信頼入力として、8 canonical fields（`ACTOR`、`ACTUAL_MODEL`、`ACTUAL_EFFORT`、`STATUS`、`CHANGED_FILES`、`OBSERVED_RESULTS`、`BLOCKERS`、`ESCALATION_REASON`）の存在・一意性・値を検証します。`ACTOR`、`ACTUAL_MODEL`、`ACTUAL_EFFORT`はrunnerの選択値と一致し、`STATUS`は`completed|blocked|failed`だけを許可します。欠落、重複、空値、enum不正、runner値との不一致があればfailし、final raw reportを公開しません。検証結果にかかわらず、runnerは`timestamp`、`actor`、`model`、`effort`、`codex_exit`、`validation_status`のheaderとattempt 1行を持つrunner-owned sidecarを、同一filesystemのno-replace hard linkで`${output_file}.provenance.tsv`へ公開します。sidecarも同じ境界・競合検査の対象で、既存なら起動前に拒否します。raw report内の自己申告を実測identityとして扱わず、canonical化・監査ではrunner-owned provenance sidecarを優先します。raw reportの公開も同一filesystemのno-replace hard linkで行うため、競合した既存ファイルやシンボリックリンクを上書きしません。この追加ディレクトリはファイルシステム上の限定的なアクセスであり、source ownership（taskで指定した所有範囲）が書き込みの境界です。`.codex`へのアクセス自体は、所有範囲外のファイルを書き込む認可ではありません。runnerは`danger-full-access`やsandbox bypassを使わず、権限調整のために`chmod`もしません。起動失敗やworker blockerのときも別modelへ切り替えません。

PowerShellからGit for Windowsのrunnerへ渡す絶対パスは、`C:\Users\...`、`C:/Users/...`、Git Bash内部の`/c/Users/...`を同じパスへ正規化してから処理します。WSLはこの実行経路に含めません。drive-relative（`C:foo`）、UNC/double-slash、`.`/`..`を含む曖昧な表記はfail-closedで拒否します。cwdとoutputのsymlink境界検査は候補の物理leafから開始し、選択した許可rootに到達した時点で停止します。許可rootより上位の祖先aliasは許可しますが、許可root自身またはその下のsymlink/reparse成分は、リンク先が同じroot内であっても拒否します。

### runnerの脅威モデルと限界

runnerのハードニングが防ぐ対象は、設定ミス、静的なシンボリックリンク、他UIDまたは信頼できないgroupによる書き込み、そして検出可能な偶発的競合です。起動前にrepo root、`.codex`、選択したoutput allowed root、output parent、および許可rootからoutput parentまでの全中間ディレクトリのdevice/inode/owner/mode identityを記録し、Codexの直前と終了直後（成功・失敗のどちらでも）、公開直前にsymlink不存在、`.codex` descendant scan、identity/owner/modeを再検証します。raw reportと`${output_file}.provenance.tsv`の最終slotも各再検証で未占有であることを確認します。group/world writableは拒否し、`umask 077`と親identity一致時だけの単一temp file cleanupを使います。

これは、malicious same-UID host processや完全に信頼できないsame-UID workerからの完全なTOCTOU防止を主張するものではありません。Codex CLIはpath文字列しか受け取らず、runnerはdirectory/file descriptor capabilityを渡せないため、`openat`やatomic openを追加してもこのpath境界を完全には解決できません。したがって、runnerがatomic/openatで完全保護したとは記載・解釈しません。完全な同一UID分離が必要な場合は、別UID、OS sandbox、mount isolation、またはfd-capabilityを持つCLIを採用します。

## 決定論的完了ゲート（全 workflow 共通）

各 concrete worker job と correction は、起動直前に pre-set を記録し、worker report を受け取った直後（Sol acceptance、reviewer、tester の前）に canonical report、post-set、delta、CLAIMED を照合します。完全なプロトコル、8 fixture、PHANTOM_CLAIM / UNDECLARED_CHANGE の判定は次の common SSOT だけを参照してください。

`${PROJECT_ROOT}/.codex/skills/worker-delegation/references/deterministic-completion-check.md`

検証スクリプトは次です。

```sh
bash "${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh"
```

PHANTOM_CLAIM は hard fail として worker に原因を返し、reviewer/tester/acceptance へ進めません。UNDECLARED_CHANGE は warn として Sol が実差分を確認します。判定 report と pre/post/delta のパスを acceptance evidence と reviewer/tester 起動記録へ保存してください。workflow ごとの next-step/index 名は各 SKILL が定めますが、プロトコル本文を複製してはいけません。

## Worker observability の共通実装

run 単位の観測台帳（`worker-observations-v1.tsv`、`sol-acceptance-v1.tsv`、`independent-verdicts-v1.tsv`）の schema と責務は `${PROJECT_ROOT}/.codex/skills/pir2/references/worker-observability.md` が SSOT です。各 concrete workflow は Phase 0 で helper の `init` だけを一度実行し、worker raw 完了後に Sol acceptance または blocker の実測を確定してから `worker` を一度だけ append します。各 requirement の acceptance 確定直後に `acceptance`、各 concrete reviewer/tester の独立 verdict 確定直後に `verdict` を append します。worker 完了直後に actor 行を先行 append してはなりません。helper の引数、固定 header、artifact-root 境界、sidecar の authoritative identity、TSV injection 拒否を再実装してはいけません。

```sh
OBS_HELPER="${PROJECT_ROOT}/.codex/skills/worker-delegation/scripts/record-observation.sh"
"$OBS_HELPER" init --run-dir "$RUN_DIR"
"$OBS_HELPER" worker --run-dir "$RUN_DIR" \
  --raw-output "$WORKER_RAW_OUTPUT" \
  --provenance "$WORKER_RAW_OUTPUT.provenance.tsv" \
  --job-id "$JOB_ID" --index "$REPORT_SUFFIX" --status "$WORKER_STATUS" \
  --sol-measurement-result "$SOL_MEASUREMENT_RESULT" --mismatch "$MISMATCH_RESULT" \
  --mismatch-reason "$MISMATCH_REASON" \
  --escalation-from "$ESCALATION_FROM" --escalation-to "$ESCALATION_TO" \
  --effort-escalation-from "$EFFORT_ESCALATION_FROM" --effort-escalation-to "$EFFORT_ESCALATION_TO" \
  --escalation-reason "$ESCALATION_REASON" \
  --insufficiency-class "$INSUFFICIENCY_CLASS" --input-sufficient "$INPUT_SUFFICIENT" \
  --measured-insufficiency-ref "$MEASURED_INSUFFICIENCY_REF" \
  --report-ref "$IMPLEMENTATION_REPORT_PATH"
"$OBS_HELPER" acceptance --run-dir "$RUN_DIR" \
  --job-id "$JOB_ID" --index "$REPORT_SUFFIX" \
  --requirement-id R1 --verdict PASS --evidence-ref "$ACCEPTANCE_REF"
"$OBS_HELPER" verdict --run-dir "$RUN_DIR" \
  --job-id "$JOB_ID" --target-attempt-index "$REPORT_SUFFIX" --cycle "$REVIEW_OR_TEST_INDEX" \
  --role "$REVIEW_ROLE" --verdict "$REVIEW_VERDICT" --report-ref "$REVIEW_REPORT_PATH" \
  --model "$VERDICT_ACTUAL_MODEL" --effort "$VERDICT_ACTUAL_EFFORT" --evidence-ref "$VERDICT_EVIDENCE_REF"
```

`worker` が読む `${WORKER_RAW_OUTPUT}.provenance.tsv` は runner-owned sidecar であり、raw report の ACTOR/MODEL/EFFORT を採用しません。worker の自己申告を Sol acceptance または reviewer/tester verdict にコピーしてはならず、reviewer/tester を起動しなかった場合は helper を使って捏造行を追加してはいけません。

actor 昇格では `escalation_from/to` に `luna→terra` または `terra→sol` の実値を渡し、effort fields は `none/none` とします。Terra High→Max または Sol High→Max では actor fields を `none/none`、`effort_escalation_from/to` を `high/max` とします。非昇格 attempt は両組とも `none/none` です。actor と effort の同時昇格は禁止し、どちらの昇格にも Sol が実測した reason、`input_sufficient=yes`、insufficiency class、evidence ref が必要です。

## Solによる実測と判定

workerの完了報告、自己申告、runnerの終了をacceptance PASSの根拠にしません。Solは実行後に`git status -sb`、対象差分、変更ファイル、requirementsごとの検証コマンド出力を確認し、各`Rn`について「満たす / 満たさない」と実測根拠を記録します。昇格した場合は、どの要件・ファイル・差分・コマンド出力から能力または局所推論不足と判断したか、Maxを選んだ場合は証拠トリガーと同じ原因の試行回数も記録します。

acceptanceはSolの責任であり、reviewer/testerの判定とは分離します。acceptance後に必要なら別系統のreviewerで品質（correctness、security、regression、保守性など）を、testerで動作を判定します。reviewer/testerのFAILはSolがrequirementsと計画に反映し、具体的な修正作業をworker ladderへ渡します。品質・動作判定そのものをworkerに代行させません。

全requirementsを実測して満たした場合だけ、Solが最終PASSとします。

## 完了報告

Solへの報告には、少なくとも次を含めます。

```text
ACTOR: luna|terra|sol
ACTUAL_MODEL: 実測したモデル名
ACTUAL_EFFORT: high|max
STATUS: completed|blocked|failed
CHANGED_FILES: <実測したファイル一覧>
OBSERVED_RESULTS: <実行した検証と出力の要約>
BLOCKERS: <なければ none>
ESCALATION_REASON: <昇格なし、または実測した理由>
```

`ACTUAL_MODEL` / `ACTUAL_EFFORT` は runner が注入した期待値と一致する実測値を記載します。`CHANGED_FILES` はリポジトリ相対の実在パスだけです。編集不要の場合は `NO_OP_JUSTIFIED: <理由>` を明記します。task-scoped の静的検証、型チェック、ビルド、コード生成、焦点を絞ったチェックは許可しますが、独立した tester の verdict を worker report に代入してはいけません。

この報告は事実の引き渡しであり、acceptanceの最終判定ではありません。
