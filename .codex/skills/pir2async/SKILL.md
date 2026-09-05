---
name: "pir2async"
description: "PIR² の実験的な Codex collaboration workflow。spawn_agent / send_message / followup_task で独立担当を連携し、Astraが計画・統合・受入を所有する。通常の /pir2 との比較用で、/pir2async と入力されたときだけ使う。"
argument-hint: "[タスクの説明] [--deepplan]"
---

# PIR² Async — experimental Codex collaboration workflow

タスク: $ARGUMENTS

pir2async は、Codex native collaboration で独立した担当を連携させ、通常の `/pir2` と比較する明示的な実験です。Astraが対話、探索統合、計画、DAG、scope、所有境界、受入、最終判断を所有します。実験であることは品質・安全・権限境界を弱める理由になりません。

target repositoryへ移動する前に、このSKILL.mdの実体pathを起点に、その親ディレクトリの親を`CODEX_SKILLS_DIR`としてAstraが確定します。`${CODEX_SKILLS_DIR}/worker-delegation/SKILL.md`を全文 Read し、target repositoryの`.codex/skills`が存在するとは仮定しません。CLI runnerのreferenceはrunner固有のartifact/provenanceが必要な場合だけ読みます。

## collaboration API と成果物

| 手段 | 用途 | 成果物 |
| --- | --- | --- |
| `spawn_agent` | 独立した explorer / worker / expert / reviewer / tester / retrospector の起動 | 返却メッセージ。必要なrunだけ固有report |
| `send_message` | 稼働中担当への境界、追加事実、保存先の通知 | 既存担当の返却またはreport |
| `followup_task` | 同じ担当への、原因と範囲が明確な再調査・再確認 | 新しい実測結果。必要なら新しい固有report |

`RUN_DIR/plan.md` は計画をファイルで保持する規模のrunで作成します。`exploration-*`、`review-*`、`test-*`、handoff、runner report、provenance、台帳は、その担当・機能を実際に使う場合だけ作ります。後段は実在する成果物だけを入力にし、未生成path、固定index、架空VERDICTを要求しません。

## 境界

- 本スキルは `/pir2async` が明示された実験用途に限定します。通常の実装は `/pir2` を使います。
- 小さく全体文脈と密結合した変更はAstraが直接実装できます。独立した通常実装はworker、難所はexpert / expert_maxへ渡します。
- 書き込み担当には排他的なファイル所有を割り当て、同じファイルや共有契約を複数担当へ同時に渡しません。explorer / reviewer / tester は対象実装を変更しません。
- Astraはworkerの自己申告、終了コード、API応答だけでacceptanceやPASSを決めず、実際のdiffとタスク相応の確認結果を測定します。
- commit、push、destructive git操作は、ユーザーが明示的に要求した範囲を除き行いません。
- OS設定、security control、認証・権限、本番/外部状態、不可逆操作を変更する前に、対象、影響、復旧方法を提示してユーザーの明示承認を得ます。

runtimeに必要なcollaboration APIがない場合、小さいread-only調査・実装・確認はAstraが行えます。この実験の中心となる担当連携が成立しない場合は、別ツールへ迂回せず正確なblockerとして報告します。

## 1. 実行コンテキスト

`PROJECT_ROOT="$(pwd)"` を基準に対象repositoryと既存差分を確認します。長時間、複数担当、再開可能性、レポート保存のいずれかがある場合だけ、標準artifact root配下にprivateな`RUN_DIR`を作り、実在する成果物のpathを担当へ渡します。小さいrunのために全index、report path、台帳、handoffを先行初期化しません。

resume / handoffが明示された場合は既存handoffの未完了項目だけを読み、現在の差分と照合して計画へ増分反映します。既存handoffがあるだけなら存在を通知し、依頼がなければ新runとして扱います。

## 2. 探索と担当連携

まずAstraが対象、既存差分、入口、既存パターンを確認します。そのうえで実験として意味のある独立単位を選び、少なくとも一つのcollaboration担当を使います。例は、独立領域のexplorer、所有分離できるworker/expert、または実装担当と独立したreviewer/testerです。人工的にタスクを分割しません。

- explorerを使う場合は、担当領域、既知の事実、具体的な問い、実装/git変更禁止を渡します。
- 独立領域だけを同じwaveで並列化し、共有ファイル・共有schema・生成物・lockfileなど競合する単位は直列化します。
- 追加調査は未解決の具体的な問いがある場合だけ、元担当へ`followup_task`するか新しい独立担当を起動します。
- `send_message` は、所有境界、追加事実、対象diff、必要なreport pathが変わったときに使います。起動直後の定型再送を必須にしません。

探索reportが必要なら固有pathを割り当て、Astraが対象コードと照合します。チャットの要約だけで足りるrunではreportを強制しません。

## 3. Astraによる計画

Astraが探索結果、対象コード、ユーザー要件を照合して次を確定します。

- 目標、確認済み事実、対象/禁止範囲、依存DAG、実装手順
- 書き込み単位ごとの排他的所有、終了条件、焦点を絞った確認
- 追加調査が必要な場合の具体的な問い
- 影響度、必要なreview/test、権限確認、復旧方法

`--deepplan` / `deepplan` が明示された場合だけ `${CODEX_SKILLS_DIR}/deepplan/SKILL.md` を同じ文脈で実行し、結果をAstraが対象コードと再照合します。planファイルが有用な規模では`RUN_DIR/plan.md`を作成・増分更新し、ユーザー方針変更で計画全体を破棄しません。局所的なrunではチャット内の具体化で足り、後段に存在しないplan pathを渡しません。

## 4. リスクと権限

キーワードや変更数だけで固定gateを発火せず、具体的な損害可能性から確認を選びます。

- 低リスク: 局所ロジック、文書、非実行設定。対象diffと焦点を絞った確認を中心にする。
- 中リスク: 公開挙動、API、複数モジュール、生成物、永続化形式。影響する境界のreviewまたはtestを追加する。
- 高リスク/破壊的: data loss、認証・認可、秘密情報、OS権限、security control、schema migration、互換性破壊、本番/外部操作。危険に対応する独立reviewと実動作確認を計画し、権限・rollbackを確認する。

破壊的変更では、実装担当と独立した検証を省略しません。ただしreviewer 5観点、tester、全生成物検査を一律には課さず、実際の危険に対応する観点・コマンド・環境だけを選びます。ユーザー確認は検証担当数の調整ではなく、OS/security/本番/外部/不可逆な変更の権限取得に使います。

## 5. 実装経路

計画と所有境界が確定したら、次から選びます。

- Astra直接: 小さく密結合し、独立した委譲単位に分ける価値がない変更。
- `worker`（`gpt-5.6-luna` / `max`）: 所有範囲と終了条件が明確な通常実装。
- `expert`（`gpt-5.6-sol` / `high`）: 原因推論、状態・所有権、競合、性能、厳しい整合性が中心の難所。
- `expert_max`（`gpt-5.6-sol` / `max`）: 高リスクで複数仮説比較や長い推論が必要な難所。
- Terra: 標準経路外。同種workloadの実測で明確な利点がある場合だけ、Astraがactor/effortと理由を明示する例外。

難所には最初からexpert / expert_maxを選べます。Solを使うためにLunaやTerraを先に失敗させません。委譲には目的、確認済み事実、所有/禁止範囲、維持する制約、終了条件、焦点を絞った確認、返却項目を短く渡します。担当はスコープ・actor・effortを自己変更せず、別agentを勝手に起動しません。

独立したimplementation shardは、所有ファイルが重ならず、共有契約の変更順序と統合確認が明確な場合だけ並列化します。条件が成立しなければ単一担当またはAstra直接実装へ戻します。

native collaborationが通常経路です。Astra直接実装とnative jobにはCLI runner、task/requirementsファイル、canonical 8 fields、pre/post/CLAIMED、8 fixture、台帳を要求しません。Astraが明示的なCLI実行、artifact identity、model/effort、変更集合の厳密なprovenanceを必要とするjobだけrunnerを選び、worker-delegationのrunner契約をそのjobに限って適用します。

## 6. 受入

各書き込みwaveの後、Astraが次を実測します。

1. `git status -sb`、対象diff、実在する変更ファイルを確認する。
2. 所有/禁止範囲と終了条件を差分・コマンド結果で照合する。
3. 実装担当の確認を必要に応じて再実行し、統合後の挙動を確認する。
4. 未実行の確認、未対応事項、環境・権限・外部blockerを分ける。

runner jobではrunner reportを未信頼入力として照合します。deterministic gateや台帳は、そのrunner jobの厳密なprovenanceが受入条件の場合だけ使用します。native jobを証明するためにrunnerで再実行したり、全jobでverifierの8 fixtureを実行したりしません。

## 7. 非同期review/test

レビューとテストはリスク、変更範囲、実験で測りたい担当連携に応じて選びます。

- 低リスク: Astraのdiff確認と焦点を絞った確認で足りれば、reviewer/testerは不要。
- 中リスク: correctnessを中心に、consistency、quality、security、architectureから影響する観点だけをreviewerへ渡すか、境界を実行確認するtesterを使う。
- 高リスク/破壊的: 実装担当と独立したreviewerを危険に対応する観点で起動し、データ・認証・schema・生成物・本番境界に合うtesterまたは安全な事前検証を行う。security境界にはsecurity観点を含める。
- ユーザーがreviewer/testerを明示した場合はその指定を満たす。

reviewer/testerには実在するplan/report pathだけを渡し、ない場合は対象diff、要件、受入条件を直接渡します。各担当は固有の観点・範囲だけを判定します。起動した担当の明示的な結果と未解決Critical/HighをAstraが集約し、起動していない担当のVERDICTや台帳行を作りません。

non-PASS時はreportと実差分を自己照合し、実際の原因に関係する最小修正をAstra直接またはworker/expertへ戻します。再review/testは失敗原因と変更範囲に関係する担当だけに限定し、以前PASSだった全担当を機械的に再実行しません。修正で影響範囲が広がった場合だけ観点を追加します。

同じ呼び出しが2回続けて失敗したら、原因を特定せず3回目を試しません。原因が特定され、変更で成功する合理的根拠がある場合だけ再試行し、それ以外は実測したblockerと選択肢を報告します。回数到達だけで成功扱いにも機械的な全面停止にもせず、correctness/security/data lossを損なう未解決事項があれば完了にしません。

## 8. 振り返り・handoff・実験サマリー

比較価値があるrunでは、Astraまたはread-only retrospectorが次を振り返ります。

- collaborationを使った担当と、その分離・並列化の効果
- 実際に起動したreviewer/testerと、Astra受入との差異
- 手戻り、blocker、未実行確認、次回の改善

長時間runまたは未完了項目がある場合だけhandoffを更新します。振り返りやhandoffのために未生成artifactを要求しません。retrospectorへは実在するpathと実測値だけを渡します。

最終結果は次の形式で提示します。

```markdown
## PIR² Async 実験サマリー

- タスク: [説明]
- workflow: pir2async（experimental）
- collaboration: [実際に使ったspawn_agent / send_message / followup_taskと担当]
- 実装経路: [Astra直接 / worker / expert / expert_max / Terra例外 / runner]
- 変更ファイル: [Astraが実diffで確認した一覧]
- 確認: [実行したコマンドと結果]
- reviewer / tester: [実際に起動した担当と結果、未実行なら未実行]
- artifact / handoff: [実在する場合だけpath]
- blocker / 未解決事項: [なければ none]
- 比較所見: [通常の /pir2 と比べた担当連携・手戻り・品質]
```
