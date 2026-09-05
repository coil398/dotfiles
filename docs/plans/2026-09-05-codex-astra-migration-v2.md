# Codex Astra 第2版の実装・検証記録

## 対象と取得証拠

- 対象: `/Users/kawasetakumi/dotfiles` の開発運用。Cursor・Grokを含む。アプリ本体・他リポジトリの変更・別タスクのhandoffは対象外。
- 基準commit: `6141f79d168d103995da5a87020d6baa5f1305b7`。開始時clean、origin/master一致。
- 指定原本: `/Users/kawasetakumi/Downloads/Codex_Astra_Migration_2026-09-05_v2.md`。
- Computer Use公式MCPでFinderに接続し、選択された原本をコピーして一時ディレクトリへ貼り付けた。OS権限・アプリ承認・sandbox設定を変更していない。node_replはこのセッションでは未公開。
- 取得コピー: `/private/tmp/codex-astra-v2-read.2tqSOC/Codex_Astra_Migration_2026-09-05_v2.md`。83,667 bytes、1,063行を全文読了。
- コピーのSHA-256: `625074aababee59979d9082f4a62385c54a1aa30acdd4322be0c1c6f97d6d356`。原本自体のhashは未取得であり、hash同士の一致を主張しない。
- 旧版の実装と実測は [既存記録](2026-09-05-codex-astra-migration.md) を継承し、再実装しない。

## 要求と分担

| 要求 | 実施内容 | 所有 |
|---|---|---|
| R1: 第7章・8.4 | 実行継続、承認前の準備、Skill優先関係、停止理由、検証の比例、報告を共通指示へ統合 | root |
| R2: Cursor・Grok | global Ruleへ共通規則の要約、Grok代替操作規則の整合、固有モデル境界を維持 | Cursor generatorは専任worker、Grokはroot |
| R3: 第9.4章・付録B | 公式Docs利用、API連携の実コード調査、CodexとAPI標準Multi-agentの区分 | API監査担当、文書はroot |
| R4: 第16・17章 | 既存証拠を照合し、変更した指示・生成・実環境を検証。直接作業を含む計測方針を記録 | runtime監査担当、検証統合はroot |
| R5: 配布・同期 | SSOTから再生成、独立レビュー、必要な既存テスト、実環境配布、autosyncでcommit・push | root |

独立監査3単位を並列実行。計画・設計・受入はrootが所有し、生成はソース変更の統合後に実行する。調査担当にUI操作、追加agent、他repo変更、commit/pushを許可しない。

## バックアップと復元

`/private/tmp/codex-astra-v2-read.2tqSOC` は0700の専有作業領域。`common-before.tar` に共通指示・Codex supplement・仕様/README・Cursor generator・Grok rule・worker-delegation Skillを元の相対パスで保存した。`features-before.txt` と `status-before.txt` に開始状態を保存。認証、セッション、記憶DB、キャッシュ全体は複製しない。

復元時はarchiveを別の専有ディレクトリへ展開して対象差分を確認し、戻す必要のあるSSOTだけを反映してadapterを再生成する。現行の未コミット変更やruntime-owned設定を上書きせず、`.codex`全体削除やGit hard resetは使わない。commit後は基準commitと本変更の差分からも対象を特定できる。

## 進捗

- [x] v2原本の取得・全文確認。
- [x] 開始状態、バックアップ、機能一覧の保存。
- [x] 共通指示への第7章・8.4の不足統合。
- [x] Cursor・Grokの監査結果と必要変更を統合。
- [x] API連携の適用判断を実コードで確定。
- [x] 新規指示・生成物・実環境と必要テストを確認。
- [x] 独立レビューを完了（correctness / consistency / security、PASS、要修正指摘なし）。

公開は `bash etc/dotfiles-autosync.sh /Users/kawasetakumi/dotfiles` の正規経路を使う。commit・pushとリモート一致の結果は、この記録を含むGit履歴と最終報告で示す。

## 現時点の観測と限界

Computer Useはインストール済みかつ接続・Finder操作成功。Downloadsの通常シェル読取拒否とComputer Useの接続可否は別であり、未公開node_replを未インストールと扱わない。前セッションの失敗操作は繰り返していない。

API仕様の照合には導入済み公式OpenAI Docs skillを利用し、[Astra guide](https://developers.openai.com/api/docs/guides/latest-model) と [Multi-agent](https://developers.openai.com/api/docs/guides/responses-multi-agent) を取得。API機能名をCodex設定へ追加しない。

モデル/推論量は既存実行記録と現在のruntime情報で確認する。モデルの自己申告、設定ファイルだけの生成、未計測の費用削減を成功証拠にしない。

## 実装した差分

- `AGENTS.md` と `.claude/CLAUDE.md`: 許可継続、必要承認前の準備、Skillとユーザー指示の優先、停止理由6項目、秘密・非公開指示の保護、検証範囲と終了基準。
- `.codex/codex-native-supplement.md`: 共通規則と公式Docsへの経路、Codex/API範囲の区別。`.codex/AGENTS.md` は正規生成。
- `.codex/skills/worker-delegation/SKILL.md`: Astra直接作業も含む実測比較、親子往復・再試行・未計測の扱い。runner schemaや新しい台帳は追加しない。
- `etc/sync-cursor.sh`: summary + pointerを維持してglobal Ruleへ実行・停止理由・公式Docs・計測方針を追加。既存のdeepthink/deepplanのFable例外と生成Ruleのモデル文言を整合。`.cursor/rules/shared-agents.mdc` は正規生成。
- `.grok/rules/runtime.md`: 新共通方針をGrokへ適応。「別手段へ無断で迂回しない」の広い禁止を、同じ依頼範囲・権限境界で目的を満たせる操作の継続へ訂正。Grok固有機能を別物で満たしたという虚偽の完了は許さない。
- `AI-WORKFLOW-SPEC.md` と `README.md`: 指示の所有、API適用範囲、同一モデルのAPI標準Multi-agentとCodex分担の区別、既存log/reportでの比較を説明。

## API連携の適用判断

`.codex`、`.claude`、`.cursor`、`.agents`、`.config`、`.opencode`、`.github`、`bin`、`etc`、MCP登録とpackage manifestを監査。OpenAI SDK依存、直接Responses/Chat Completions呼出、Astra向けHTTP payloadは見つからない。`run-worker.sh`、各`codex-runner`、`bin/codex-motitan`はCodex CLIを起動する実装であり、API payloadを所有しない。

| 項目 | 状態 | 判断 |
|---|---|---|
| B.1/B.8の方式区分 | APPLIED_AND_VERIFIED | 実装・設定の所有境界と公式本文を照合し、運用文書へ反映 |
| B.2のAstra送信パラメーター | NOT_APPLICABLE | 対象となる直接API requestなし |
| B.3 Async / B.4 steering | NOT_APPLICABLE | background CLIやresumeをAPI機能に読み替えない |
| B.5 configuration_update | NOT_APPLICABLE | 導入対象なし。Codex context管理へ挿入しない |
| B.6 API cache設定・計測 | NOT_APPLICABLE | 自前API payload/usage集計なし。CLIで取得可能なusageは独立して記録 |
| B.7 Programmatic Tool Calling | NOT_APPLICABLE | 既存scripts/CIを置き換える要件なし |

Claudeの`temperature`、Docker BuildKitのcache、外部CLIの内部実装はAstra requestとして改修しない。他リポジトリのアプリ/APIコードは変更していない。

## 配布と検証

証拠ファイルは以下すべて `/private/tmp/codex-astra-v2-read.2tqSOC/` 配下。

| 確認 | 状態・結果 | 証拠 |
|---|---|---|
| Codex設定generator | APPLIED_AND_VERIFIED、既存隔離fixture PASS | `test-codex-config.log` |
| 正規runtime配布 | APPLIED_AND_VERIFIED、`link.sh --ai-runtimes-only` exit 0 | `deploy.log` |
| OpenCode生成 | APPLIED_AND_VERIFIED、`sync-opencode.sh` exit 0 | `sync-opencode.log` |
| adapter集約 | APPLIED_AND_VERIFIED、Cursor/OpenCode/shared drift/motitan/AntigravityすべてPASS | `test-all-contracts.log` |
| Codex指示読込 | APPLIED_AND_VERIFIED、shared coreと新節は各1回、停止理由とDocs経路あり | `prompt-checks.json` |
| 新規通常セッション | APPLIED_AND_VERIFIED、strict-config起動成功、Astra/high、READY | `smoke-model-record.json`、`smoke.jsonl` |
| 実配置参照 | APPLIED_AND_VERIFIED、Codex/Claude/Cursor/GrokはSSOT参照、OpenCodeは新節あり | `runtime-links.json` |
| Grok発見 | APPLIED_AND_VERIFIED、Grok 1.0.13のinspectで専用Rule発見 | `grok-inspect.json` |
| 機能フラグ | UNCHANGED、before/afterのdiffは空 | `features-before.txt`、`features-after.txt` |
| Cursor/Grokの新規応答 | APPLIED_AND_VERIFIED、両実runtimeが共有停止理由の先頭ラベルを回答、exit 0 | `cursor-grok-check/` |
| Codexフック実発火 | APPLIED_AND_VERIFIED、実ファイル作成1回に開始・正常終了各1回 | `hooks-check/live-hook-after.jsonl` |
| スリープ防止実効 | APPLIED_AND_VERIFIED、Codexのactive-turn assertionをmacOSで観測 | `sleep-after-agent.txt` |

新規通常セッションのthreadは`01a071a3-9fec-7b61-a74d-82e5780017b9`。model/effortはruntimeのthreadsメタデータから読み取り、自己申告を使っていない。起動時にmodel・effort・sandbox・approvalの上書きを渡していない。新規出力のusageはinput 31,428、cached input 0、cache write input 0、output 5、reasoning output 0。これは小さな起動確認1件の利用量であり、移行全体の利用量・費用・品質改善を示さない。

source shell構文と`git diff --check`はPASS。Cursor監査では配布前の既存契約103件と配置監査4件がPASS、更新後は集約から対応契約を再実行した。変更していないworker/LTM/auto-gate等の追加private fixture群（`--full`）は反復しない。既存の旧版全体PASSと今回の必要範囲を区別する。

通常sandboxで`codex debug prompt-input`がOS error 1になったため、同じ公式コマンドを正式な昇格経路で実行して成功した。権限設定の編集や審査回避は行っていない。監査テストが生成した未追跡pycは同じ専有一時領域へ退避し、commit対象から除外した。

## 追加受入検証とフック修正

初回の差分レビューと設定確認だけでは、第16章の「hooksが実際に動く」という必須条件を満たしていなかった。追加の受入監査でこの不足を特定し、既存の設定・認証・信頼状態を使った公式app-serverの実イベントで検証した。

変更前は試験ファイル1件の作成に対してhookが1回発火したが、`hook returned invalid post-tool-use JSON output` で失敗した。`etc/sync-codex.sh`の診断ログがstdoutへ出ており、実機Codex 0.153.4のhook出力解釈と衝突していた。

修正は同scriptの`log()`をstderrへ出す1行。診断を捨てず、生成処理と終了コードは維持する。hook定義・コマンド・信頼状態・承認方式は変更しない。新しいwrapperや例外分岐は追加していない。既存の`etc/test-codex-config.sh`でstdoutが空、診断がstderrに残ることを確認する。

| 確認 | 修正前 | 修正後 |
|---|---|---|
| 既存fixture＋出力契約 | `sync diagnostics must not enter hook JSON stdout` でFAIL | PASS |
| 実PostToolUse | 開始1回・終了1回、status=`failed` | 開始1回・終了1回、status=`completed`、error entriesなし |
| 試験ファイル | `HOOK_PROBE_OK`＋改行を作成 | 同じ内容を作成、turn正常終了 |
| 信頼・重複 | userはtrusted/enabled、project重複はdisabled | 同じ状態で検証、観測turn内の重複・再帰なし |

証拠は`hooks-check/test-before.log`、`test-after.log`、`live-hook.jsonl`、`live-hook-after.jsonl`。修正後のthreadは`01a071bf-aedb-7a91-ac4e-5844f72ee659`。テスト用のモデル・推論量・sandbox・承認・Codex home・hook trustの上書きを渡していない。承認要求を自動的に承認する処理も設けていない。

Cursorは`cursor-agent --print --mode ask --sandbox enabled`、Grokは単一turnの`--permission-mode plan`で新規応答を確認した。回答そのものをpromptに含めず、共有規則の停止理由の最初のラベルを尋ね、両方が`対象の操作:`を返した。モデルは既存設定を使用。Cursorは51秒・exit 0、Grokは通常sandboxでセッション作成が拒否された後、正式な昇格経路で同条件を実行し16秒・exit 0。設定・認証ファイルとリポジトリは変更していない。この小試験を一般的な遵守率の証明にはしない。

`pmset -g assertions`ではCodex PID 28510が`PreventUserIdleSystemSleep`を取得し、active turnの間に持続していることを確認した。OS全体の省電力設定は変更していない。

## 受入範囲と環境診断

- `context_management`は対応アカウント、実効設定、新規実行での機能読込を確認済み。境界越えの負荷試験や数週間の品質比較は、第16章が分離している運用評価であり、構成適用の追加必須条件にはしない。
- 旧版で修正済みのautomata定期runnerは、対象試験12件・subtest 6件PASS。登録環境・引数・モデル・排他・出力先を照合済み。別リポジトリの実運転は今回の対象外。検証起動は自動審査で拒否され、実行していない。OS書込禁止を追加した案も範囲外として拒否されたため、再試行せず、不要な追加許可の確認を取り下げた。他リポジトリの未コミット変更を維持した。
- `codex doctor`をホスト側と通常sandbox側で再診断し、両方exit 0、失敗項目0、`state.paths`正常、全DB integrity=`ok`を確認。前回のopen code 14は再現せず、原因は断定しない。全体は既存のstale rollout索引1,932件による`warning`で、DBの削除・修復は行っていない。証拠は`doctor-host.json`と`doctor-sandbox.json`。
- Astra直接作業と委譲の品質・時間・費用の比較方針は実装済み。運用比較を新しい受入gateにせず、実作業の記録で評価する。未計測の費用削減は主張しない。
