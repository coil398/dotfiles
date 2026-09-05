# Codex Astra 移行記録

仕様: `/Users/kawasetakumi/Downloads/Codex_Astra_Migration_2026-09-05.md`

## 対象・保全

- 対象: dotfiles の Codex 設定生成元、native 指示・agents・Skills、そこから参照する起動経路。
- 追加対象: `/Users/kawasetakumi/ghq/github.com/astran-jp/motitan-automata`。launchd が直接呼ぶ同期 runner・対応テストと Codex のモデル配分指示が対象。毎日04:20の同期ログで旧引数による exit 2 を確認。
- 参照関係のみ確認: sibling `motitan_app` / `motitan-api` / `motitan-spec` と `uniskill`。アプリ・DB・Unity の実装や本番処理は対象外。
- CLI: standalone 0.153.4、`~/.local/bin/codex`。Desktop 26.825.32147 はインストール済み・未起動。
- 認証: ChatGPT Pro。認証値は記録・複製しない。
- `~/.codex/config.toml`、AGENTS.md、agents は dotfiles へのリンク。
- 変更前の実効モデルは Astra medium、生成元は Sol high。生成で旧モデルへ戻る不整合あり。
- 既存の workspace-write / on-request / auto_review / network 設定を維持する。
- 未コミット変更あり。開始時の差分と状態を保存し、今回と重なる変更も保持する。
- 復元用保存先: `/Users/kawasetakumi/.local/state/codex-migrations/2026-09-05-astra`（0700）。`before.tar` に設定と対象指示・Skills、`support-before.tar` に補助生成文書、`working-before.patch` と `status-before.txt` に開始状態。認証・履歴・記憶 DB は含めない。
- 作業・検証用一時領域: `/private/tmp/codex-astra-migration.pR4Rg0`。

## 完了条件と進捗

- [x] 仕様書全体、実機 CLI、設定の生成元、サインイン区分を確認。
- [x] 変更前バックアップと features 一覧を保存。
- [x] 親 Astra high、worker Luna max、expert Sol high、expert_max Sol max を設定。
- [x] native 指示・Skills・専門roles・生成プロトコルを新しい実行経路へ整理。
- [x] 設定生成・hook 信頼保持・重複発見・自動実行を監査して必要変更。
- [x] 構文・現行キー認識・対象scriptのfocused testsを確認（意味的整合は独立レビューと実行追跡で確認）。
- [x] 新規セッションで親子の実モデルと推論量、限定実装と並列処理を確認。
- [x] 機能の変更前後、未対応項目、復元方法を結果として記録。

## 分担

root は要件・統合、Codex native supplement、運用仕様、移行記録を所有。
設定生成、worker-delegation、他 Skills、agents はファイル所有を分けて委任する。
生成物の再生成は所有するソース変更が揃ってから root が実行する。

## 初期診断

`codex doctor --json` は設定・認証・通信・CLI バージョン確認に成功。
診断全体は sandbox 内の memories DB open エラーで終了 1。正式な host 実行で `sqlite3 -readonly ... 'PRAGMA quick_check;'` は `ok`。破損は確認されず、DB の削除や再生成は実施しない。
`--strict-config` は `features` サブコマンドでは未対応のため、起動検証で確認する。

公式照合: [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)、[Models](https://learn.chatgpt.com/docs/models)、[Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)。

## 新規セッションでの実測

主な変更ファイル:

- `.codex/config.base.toml`、`etc/sync-codex.sh`、`etc/test-codex-config.sh`: モデル・機能、生成と機械固有設定の保全、Skills重複抑制。
- `.codex/codex-native-supplement.md`、`AI-WORKFLOW-SPEC.md`、`README.md`、`.codex/agent-delegation.md`: Astraの実行責任、直接作業と委任、native所有。
- `.codex/agents/worker.toml`、`expert.toml`、`expert_max.toml`、`epic-planner.toml`、`implementer.toml`: custom役の追加と親の責務訂正。
- `.codex/skills/worker-delegation/**`: native/runnerの分離、Luna→Solの観測、runner固有安全契約のreference化、対象テスト。開始前のmutable-path関連変更は保持。
- `.codex/skills/ir/SKILL.md`、`pir2/SKILL.md`、`writing-plan/SKILL.md`、`debug/SKILL.md`、`instruction-refactor/SKILL.md`、`pir2async/SKILL.md`: native経路とリスクに応じた確認へ整理。`epic`・相談`codex`・`deepplan`の関連参照も整合。
- 生成物 `.codex/config.toml`、`.codex/AGENTS.md`、`.codex/pir-handoff.md`、`.codex/pir2-protocol.md`: sourceから再生成。handoff/protocolはnative referencesを生成元とし、Claude由来のplanner・固定artifact手順が戻らないようにした。generated-onlyの手編集ではない。
- 外部repoの `AGENTS.md`、`AGENTS.override.md`、`README.md`、`scripts/run-automata-sync-background.sh`、`scripts/tests/test_automata_sync_background.py`、`.agents/skills/automata-sync/SKILL.md`。

開始時からのai-ltm、Antigravity、zsh、全体契約test等のユーザー差分は保持した。`etc/link.sh` は既存変更に加えて今回のGrok安全配布処理を含むため、必要な生成元として変更・同期対象に含める。

CLI 0.153.4 の新規 `codex exec --strict-config --json` を使用。親の model/effort はCLIで上書きせず通常設定から読み込ませ、子は `worker` / `expert` / `expert_max` のcustom定義を指定した。非対話の限定試験だけ `approval_policy="never"` と一時試験ディレクトリの書込範囲を指定し、通常設定は変更していない。

| 担当 | 実行記録の model / effort | thread ID |
|---|---|---|
| 親 | gpt-6-astra / high | 01a06fea-3ef3-7eb3-a3f0-9b1d15bf78c5 |
| worker | gpt-5.6-luna / max | 01a06fea-82d8-7870-85bd-a4a31514f2ab |
| expert | gpt-5.6-sol / high | 01a06fea-ac12-7783-b878-98c04c08b677 |
| expert_max | gpt-5.6-sol / max | 01a06fea-dd72-7371-acfb-f121bec5cce0 |

証拠は `state_5.sqlite` の対象4件を読み取り専用で取得した `smoke-model-records.json` と `smoke-run.jsonl`。モデル自身の名称申告は証拠にしていない。3子を開始後、workerは加算、expertは順序保持の重複除去を別々の一時ファイルへ実装。expert_maxは独立した所有権解析を返した。最後に親が統合チェックを一度実行し `MIGRATION_SMOKE_PASS`、終了0。実リポジトリのアプリコードは試験対象にしていない。

公式 `config/read` / `skills/list` でも、Astra high、子の既定Luna max、同時上限6、深さ2、既存のworkspace-write/on-request/auto_reviewを確認。有効なSkillsは82件から38件へ、nativeと重なるshared44件だけを無効化。同名の有効重複は0、読込errorsは0。元ファイルは削除していない。

`debug prompt-input` では新Astra commander指示、共有core1回、旧Sol commanderなしを確認した。

## 機能の変更前後

`features-before.txt` / `features-after.txt` は復元用保存先に保全。差分は以下の2項目のみ。

| 設定・機能 | 変更前 → 変更後 | 確認範囲 |
|---|---|---|
| context management | false → true | Pro、nested `experimental_mode=true`、実効読込、新規promptのcontext-window guidanceまで確認。実際の境界越え検索は未試験 |
| prevent_idle_sleep | false → true | 実効設定の有効化を確認。Codex処理中のOS assertionは未捕捉 |
| memories | false → false | UNCHANGED。既存の独立ai-ltmスキルは保持 |
| fast_mode | true → true | UNCHANGED。通常の `service_tier="fast"` 強制はなし |
| その他内部機能 | 変更なし | 一括有効化・警告抑制・独自context窓指定は追加しない |

## 自動実行

関連repo `motitan-automata` の毎朝04:20 launchd runnerを変更。Codex 0.153.4で失敗する `--ask-for-approval never` を現行 `--config 'approval_policy="never"'` に更新し、Astra highとJSON出力を明示。既存のworkspace-write、対象cwd、排他lock、verify-once、終了コード伝播を維持。

fake Codex subprocessを使う対象テストは `13 passed, 6 subtests passed`。Skill説明更新後の対象確認は `6 passed`。shell構文とdiff checkも通過。実際のpull/commit/pushを伴う自動同期、本番処理、DB更新は試験のために起動していない。全scripts/testsの追加試験はhttpx未導入で1件収集不能、その対象を除いた実行は222 passed / 10 failed / 1 skipped。これら10失敗は対象外で今回との因果未確認、移行の成功証拠には用いない。

約92KBのAGENTS.mdは本文を削らず、短いAGENTS.override.mdから分割して末尾まで読む入口を追加。Codexモデル分担の節のみ更新した。cron登録はなし。manual motitan profileの意図的Full Accessは変更していない。

## フック

`hooks/list` で同じ同期フックがuser/project両layerから読まれることを確認。configのsymlinkが同じ実体でもhook定義は加算される。既存のhook定義とhashを保ったまま、公式 `config/batchWrite` でproject由来の重複キーだけ `enabled=false` にした。user由来は `enabled=true` / `trustStatus=trusted`、project由来は `enabled=false` / trusted、warnings/errorsなしを再確認。新hashの合成やtrust bypassは使用していない。

生成scriptは既存のruntime-owned hooks.stateを保全する。移行途中の旧生成処理で失われた元2件は、バックアップとhook定義一致を確認して公式APIで復元した。同期script自体のhost実行は成功。非対話の試験ログからイベントdispatchそのものの実行証拠は抽出できていないため、フック呼出し回数の実測は未確認とする。

## 実装・統合した内容

ユーザーの継続指示後、保留していた手順整理を実施。「一律必須」はユーザー要件ではなく既存手順の記述だったため、その区別を訂正した。必要な正しさ・安全・権限・データ保全の確認は維持し、固定人数・任意artifact・キーワードだけの停止/反復を整理した。

- Codex: Astra直接実装、native worker、初手expert、明示CLI runnerを分離。runnerのpath/provenanceと既存v1台帳schemaは保持。
- PIR²/IR/debug/writing-plan/instruction-refactor/pir2async/epicと関連referencesを更新。reviewer/tester/retrospectorにも残っていた未生成implementation必須・固定人数推測・任意feedbackファイル不在による違反登録を修正。
- Skills所在を対象アプリrepoと分離。読込済みSkill実体から兄弟Skill/referenceへ到達する。
- 実測で見つかった初回親directory不足による無限loop、同秒RUN_DIR衝突、handoff親未作成、symlink境界、通常時のdeepplan分岐、未起動reviewerの架空VERDICT要求を修正。
- Codexのhandoff/protocolをnative sourceから生成。親が実測受入と引継ぎを管理し、完了handoffは専有runへ回復可能に保管する。
- Cursor: TaskのAuto/inherit、deepthink/deepplanのFable例外を保持。Codex CLI bridgeは通常Luna max・難所Sol high/max・Terra実測例外へ。Cursor自体にAstraモデルを指定しない。
- Cursor: 通常PIR²関連Skills、references、reviewer/tester/retrospectorを実リスクによる確認へ整合。pir2asyncは利用不能なTeamCreate本文を実行させず、通常pir2への明示縮退だけを残す。
- Cursor Codex runner: 非空stdin、SESSION_ID導出、resumeのcwdとsandbox、stale session拒否、既存成果物衝突拒否、実時間deadlineを修正。requested値とobserved/unavailableを区別。
- Cursorの既存チェックが有効なslash flagをモデル指定と誤認して停止していたため、検出をモデル代入に限定。実際の無効modelは拒否し、inherit/Fable例外と無関係なflagを誤検知しないことを確認。
- Grok: CLI 1.0.13の同梱docs/help/inspectで実在経路を確認。実効Skillsは共有.agentsとClaude互換が中心で、Cursor Skills/.mdcルールはこのinspectでは未選択。専用runtime ruleを追加し、固有APIと共有意図を分離。
- Grokの認証、モデル、権限、MCP、hooks、compat設定を変更していない。別名agent binary 1.0.5の更新・削除もしていない。

## 検証結果と範囲

- Codex設定fixture: PASS。native Skills保全、hook state、重複抑制、native protocol生成の確認を含む。
- 公式runtime API: Astra high、子Luna max、同時6、深さ2、workspace-write/on-request/auto_reviewを維持。有効Skills38/総82、同名重複0、errors0。
- hooks API: user hook enabled/trusted、project重複hook disabled/trusted、errors0。
- TOML22件構文、変更SkillsのYAML、shell構文、git diff check: PASS。quick_validate.pyは既存argument-hint非対応またはPyYAML未導入で一部実行不能。成功と偽らず、実際に通した構文・参照・挙動確認を証拠とする。
- 最終構文確認: TOML22件、変更Skills21件とCursor agents4件のYAML計25件がPASS。Cursor reviewer/testerのdescriptionにあった未引用のコロンを引用符で修正し、再検証した。
- Cursor実効配置: バックアップ済み10ディレクトリ中、変更22ファイルだけを反映して全件source一致。agentsは既存symlinkで反映。`bash etc/test-cursor-contracts.sh` は29 passed / 0 failed、配置監査もPASS。
- 独立Codex統合レビュー: PASS。no-op、native report不在、未知reviewer、必要test未実行のcaseを実行追跡。
- private run fixture: 初回生成、同秒衝突suffix、mode700、symlink親・artifact root外拒否、epic slug正規化: PASS。
- Cursor Codex bridge fake subprocess: fresh/resume成功、指定cwd、resume sandbox指定、異cwd/stale session拒否、成果物衝突拒否、timeout後の既存process非破壊: PASS。外部モデル呼出しの再試験は行っていない。
- Grok inspect: native runtime ruleをproject ruleとして認識。個人用rulesへのリンクも確認。
- Grok配布fixture: 初回、冪等、既存実ファイル/別symlink、root実ファイル/root symlink/rules symlinkの保全: PASS。
- worker runner安全境界・Luna→Sol観測・deterministic verifierの8fixtureは変更対象として実行しPASS。通常jobへの一律要求にはしていない。

### 意図的に未実施・未確認

| 対象 | 範囲 |
|---|---|
| コンテキスト境界越え検索・OS sleep assertion | 設定と新規prompt適用まで確認。長時間の境界挙動は未試験 |
| 次回launchdの本番同期 | 対象runnerのfake試験のみ。外部Git同期や本番DBを試験目的で起動しない |
| Cursor UIの新タスク・Grokの新モデルセッション | 配布・discoveryとローカルCLI契約を確認。実際のUI/モデル応答を成功と仮定しない |
| Cloud/PRレビュー・他端末 | ローカル設定からの反映を仮定せず、リモート設定を変更しない |
| 外部repo全test | 既述の既存失敗・依存不足を、今回の成功証拠として扱わない |

検証中に残ったconfig一時ファイル6件は、削除せず保存先の intermediate-configs に退避した。認証・履歴・記憶DBの削除、既存Git差分の破棄は行っていない。初回実装時点ではcommit/pushを行わず、後続のユーザー明示指示で同期対象にした。

## push指示後の追加仕上げ

- 全体契約検証を再実行。Cursor29件、OpenCode30件、shared drift64件、Codex motitan契約、Antigravity8件がすべてPASS。
- Antigravity既存追加scriptのSkillsリンク未生成を確認。正しい相対パス `../../.agents/skills` で生成し、単なる存在確認でなくリポジトリ共有Skillsへの実体一致、既存ファイル保全、check modeの非書込みを検証する。途中のrootによる1階層余分な修正は独立fixtureで誤りと判明し訂正。個人用の新しい権限・MCP・hooksは配布しない。
- Codex設定fixture、worker mutable-path/actor routing回帰、ai-ltm23試験、差分・shell構文検査がPASS。
- 中央同期の本番preflightで、終了済みrebaseの残留 `REBASE_HEAD` 単独を進行中と誤認する問題を実測。実際のrebaseディレクトリとmerge/cherry-pick/revert状態を対象repoの絶対Git directoryで確認するよう修正し、stale許容・active拒否・拒否時HEAD保全のfixtureがPASS。実repoのGit状態ファイルは削除していない。
- 明示追加済みignoredファイルはindex登録済みpathとして `git add --update` で保全し、未追跡ignoredファイルを勝手に追加しない。同期中の短命Git処理とのindex.lock競合も実測し、対象を明示したindexed/untrackedのbatch stageへ集約する。ロック削除・自動retry・force addによる迂回はしない。
- dotfilesは中央autosync engineで既存差分を含めて保全commitし、通常merge・再生成・pushする。移行記録はこの1件のみ個別にGit管理へ追加する。
- dotfilesの中央同期は `AUTOSYNC_STATUS:SUCCESS`。保全commit `b542e32ff9a4b6b9c78b0123e6eb305e93f68fc8` とsubmodule3件のpush、再生成後の差分なし・behind0を確認。構文テストが作ったPythonキャッシュ1件は回復可能に退避し、テストをbytecodeを生成しない構文検証へ修正して仕上げの同期対象とする。
- motitan-automataは今回の6ファイルだけをcommit `5777b1a8` に保存。上流14コミットとの非破壊merge計算で競合なしを確認して通常mergeし、`ce8935b5adef595063306e4995f1338f8537b1cc` をpushした。live origin/mainとの一致・ahead/behind 0/0、merge後focused pytest6件とadapter checkのPASSを確認。既存のTalk診断資料とQA helper変更はunstagedのまま内容hash不変。

## 全体監査後の是正

ユーザーの全面修正指示により、配布保全、同期・生成、共有指示、Cursor指示、記憶検索、shell/承認判定を独立単位で修正する。設定・既存fixtureのPASSだけでは実効配置と境界条件の不具合を捉えられていなかったため、実処理の回帰試験とhome配置確認までを完了条件とする。

進行記録: `/Users/kawasetakumi/.ai-pir-runs/workflow-repair.hW9Sej/plan.md`。

### 是正内容と検証

- 配布: 既存Cursor treeを専有backupへ保全してmaterializeし、失敗時に復元する。必須mkdir・rsync・ln・generatorの失敗は非zeroで伝播する。独立fixtureで既存SKILL・追加file保持と完了表示なしを確認。
- 同期・生成: staged deletion/rename・空白path・ignored trackedを保全し、4adapterを同期する。producerが部分出力後に失敗しても既存生成物を置き換えない。中間cat失敗を含む独立再現と中央Git同期fixtureがPASS。
- 指示: sharedはruntime-neutral、CodexはAstra親の実効容量・所有・受入責任、CursorはAuto/Fable例外と実体起点の参照へ整合。通常小変更へ全担当・固定report・形式だけの承認を一律要求しない。高リスクの独立review・動作確認・権限境界は維持する。
- 記憶: 3runtimeのread-only検索、壊れたFTS/configの明示拒否、未push履歴にDB外変更が含まれる場合の同期拒否を回帰確認。検索・同期の独立fixtureがPASS。本番DBをfixtureとして使用していない。
- 更新チェック: shared/Codex/Cursorは明示root内の独立cloneだけをclean fast-forwardする。別runtime・dotfilesの暗黙同期、commit/pushを行わない。3scriptを直接使う10fixtureが独立検証でPASS。
- Claude native: 既存の不正YAML23件はdescription/argument-hintの引用符だけ修正。値と本文は修正前後一致し、47件のmetadata parseがPASS。ネイティブ本文・モデルは変更していない。
- 反映後の `bash etc/test-all-contracts.sh --full` は終了0、`ALL PASS`。ログ: `/Users/kawasetakumi/.ai-pir-runs/workflow-repair.hW9Sej/full-contracts.log`。

### 実効配置と追加依頼

- `link.sh --ai-runtimes-only`、OpenCode同期、共有skills配置変更後のCodex再生成を正式実行し、全て終了0。home配置auditはfails=0。
- バックアップは同RUN_DIRの `runtime-before.tar`、`opencode-before.tar`、`shared-skills-before`、`gemini-scripts-before`、`link-backups/`。削除せず保全し、認証・履歴・本番DBは変更していない。
- 配置後の新規app-server `config/read` はAstra high、`features.context_management.experimental_mode=true`。有効skills38件、読込errors0、有効同名重複0。追加依頼のコンパクション機能は既にONのため保持。境界越え履歴検索の発火自体はこの設定確認とは別であり未計測。
- Grok、Cursor、Antigravityの実CLIは各readonly/plan/sandbox設定でREADY応答を確認。Geminiの実配置先hookコマンドは正規payloadでallow/askを確認した。実モデル応答だけで全workflowの意味的正しさを証明したとは扱わない。

### 未完了の承認事項

Codex `retrospector.toml` 本文に残る固定手続き・他runtime由来の架空権限設定の整理は、自動審査が安全・検証・承認制御の喪失と判定して拒否したため未反映。実際のsandbox・承認・データ保全を維持する限定修正についてユーザー承認を求めており、迂回編集は行わない。他の検証済み変更のGit同期と、この未承認部分の完了判定は分ける。

中央Git同期も公開送信の自動審査で2回拒否され、プロセスは起動していない。`gh api user` はcoil398、`coil398/dotfiles`はPUBLIC・ADMIN・default master、origin一致を確認済み。ステージ済み182ファイルはgitleaks無検出、cached diff確認済みだが、この具体的payloadの公開承認が追加で必要と判定された。commit/pushは未実施で、変更をstage済みのまま保持する。gate fixtureの固定ダミー文字列検出は実行時の合成入力へ変更し、7testを再実行してPASS。最終metadataはSKILL118・agent YAML36・Codex TOML20が全てparse成功、Cursor home30packageの内容差分0件。

## 復元方法

保存先は `/Users/kawasetakumi/.local/state/codex-migrations/2026-09-05-astra`。開始時点の未コミット変更を含む実ファイルを保存しており、HEADへ戻す操作ではない。

| バックアップ | 復元対象 |
|---|---|
| before.tar | dotfilesの設定生成元、native supplement、agents/Skills、開始時の生成config等 |
| support-before.tar | 開始時のCodex補助文書。agent-delegation.mdも含む |
| cursor-runtime-before.tar / cursor-research-runtime-before.tar | Cursor実効Skillsの更新前コピー（10ディレクトリ） |
| automata-before.tar | 外部repoのAGENTS.md、同期runner、対応テスト |
| automata-readme-before.tar | 外部repoのREADME.md |
| automata-sync-skill-before.tar | 外部repoのautomata-sync/SKILL.md |
| working-before.patch / status-before.txt | dotfilesの開始時未コミット差分・状態の照合用 |

1. 新しい一時ディレクトリへ必要なarchiveを展開し、現在の差分と比較する。作業後に増えたユーザー変更がないか先に確認する。
2. 戻す対象の生成元・nativeファイルだけを選択して復元する。新規のworker/expert/expert_max、runner-contract、今回追加テスト、外部AGENTS.override.mdは元不存在なので、使用停止する場合だけ対象を個別に退避する。ディレクトリ丸ごと削除しない。
3. dotfilesの生成元を戻した後に `bash etc/sync-codex.sh` を実行する。機械固有のtrust/stateは既存値を維持し、必要な変更だけ公式API/UIで行う。重複projectフックを元に戻す場合は、その1キーだけenabled=trueにする。
4. 新しいCodexタスクで実効モデル・設定を確認する。実験機能だけ戻すなら `.codex/config.base.toml` の `experimental_mode=false` → sync → 新規タスクで足り、他の移行を戻す必要はない。

認証の再作成、履歴/記憶DBの削除、リポジトリ全体のresetは行わない。Git同期後の復元も対象変更の比較・個別revertを基本とし、開始時のユーザー変更をまとめて破棄しない。
