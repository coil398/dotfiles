## 探索レポート: 「完璧な多エージェント・オーケストレーション」参照アーキテクチャの外部一次情報収集

### 関連ファイル一覧

本探索は外部一次情報収集が主目的のため、コードベース側で参照したのは `epic` ワークフロー自体の設計文書のみ（変更対象ではなく、外部パターンの適用可能性を評価するための前提情報として参照）。

| ファイルパス | 役割・内容 | 変更の必要性 |
|------------|-----------|------------|
| `/Users/kawasetakumi/dotfiles/.claude/skills/epic/SKILL.md` | epic オーケストレーターの Phase 1〜3 手順、L0/L1/L2 の3階層ネスト設計、DEFERRED_USER_DECISIONS のbubble-up設計 | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.claude/agents/epic-planner.md` | エピック分割専任エージェントの分割レポートフォーマット、DAG生成・暗黙依存の直列化ロジック | 参照のみ |
| `/Users/kawasetakumi/dotfiles/.claude/skills/pir2/references/experimental.md` | `epic-orchestrator-nested-pir2` 実験の仮説・品質ガードレール・採用/廃止条件（Evidence Summary はまだ全項目0件） | 参照のみ |

### 既存パターン・規約

- epic は L0（epic 本体）→ L1（ネスト pir2 ランナー、`subagent_type=general-purpose` + `model=opus` + SKILL.md Read）→ L2（各 pir2 が起動する explorer/planner/implementer/reviewer/tester）の3階層ネスト。L2 配下の再ネスト（L3 相当）は明示的に抑制し、深さ超過時は inline フォールバックする設計（`SKILL.md` 15行目・99行目）
- ユーザー対話は L0 に一極集中。L1/L2 では保守的デフォルト選択 + `deferred-decisions.md` 記録 + 呼び出し元への `DEFERRED_USER_DECISIONS` 列挙という「非ブロッキングの委譲」方式（`SKILL.md` 101-103行目）
- 観測可能性は現状ファイルベースのみ：`epic-plan.md` / `epic-runs.md`（Ti→サブRUN_DIR対応）/ `deferred-decisions.md` を人間可読の markdown で書き出す運用（`SKILL.md` 105-109行目）。外部トレーシングツールとの連携は未検討
- 依存グラフの「暗黙依存（共有リソース競合）」は辺として直列化するのみで、失敗時の補償（compensation）ロジックは epic-planner / SKILL.md のどちらにも明記されていない
- **構造投資領域**: `~/.claude/agents/*.md` に explorer / planner / implementer / reviewer / tester / retrospector / epic-planner 等、同一「呼び出し元からプロンプトを受け取り構造化レポートを Write して要約を返す」という共通インターフェースの一族が7個以上並んでいる。今回の探索テーマ（堅牢設計要素の追加）を epic に組み込む場合も、この既存インターフェース形式（フォーマット固定＋書き出しパス＋要約のみ返す）に載せる形が既存構造との整合性が高い

### 影響範囲

本探索自体はコード変更を伴わないが、収集した外部パターンは今後の deepthink（epic 完成形設計）が参照する設計語彙になる。想定される波及先:

- 直接影響（deepthink の検討対象になりうる）: `.claude/skills/epic/SKILL.md`（Phase間の状態受け渡し・失敗時ハンドリング・観測可能性設定）、`.claude/agents/epic-planner.md`（DAGへの補償/コンペンセーション記述の要否）
- 間接影響: `.claude/skills/pir2/references/experimental.md` の `epic-orchestrator-nested-pir2` 実験セクション（Adoption/Rejection Criteria に「durable resume」「補償」「typed contract」観点を追加するかの判断材料になりうる）

### 依存関係

- 本探索は Claude Code のネスト Agent 機構（v2.1.172〜）に強く依存した文脈で読むべき。Temporal/Restate/LangGraph はいずれも「専用ランタイムプロセスが常駐し、外部からのクラッシュ検知・自動再試行を行う」構成が前提であり、Claude Code の Agent ツールにはそれに相当する外部監視プロセスが存在しない点が最大の環境差
- Claude Code 自体が OpenTelemetry（ベータ）でネスト構造を計装できることが判明（後述）。これは epic の観測可能性設計にとって既存 SSOT（`SKILL.md` のファイルベース観測）を補完する候補になる

---

## 1. Durable execution / checkpoint & resume

### 一次情報から確認した事実

| ソース | 仕組み | 決定論的リプレイ vs 台帳ベース復元 |
|---|---|---|
| Temporal | ワークフロー実行を **Event History** に記録し、障害時は「ワークフローコードを最初から再実行し、記録済みイベントに合わせて同じ Command 列を再現できるか検証する」= **決定論的コードリプレイ型**。非決定的操作（外部API・LLM呼び出し等）は Workflow ではなく Activity に隔離し、リプレイ対象から除外する | 決定論的リプレイ型。ワークフローコードが同じ入力に対し必ず同じ Command 列を生成する制約を課す |
| Restate | 実行中の全ステップ（外部API呼び出し・DB書き込み・タイマー・メッセージ送信）を **journal** に記録し、クラッシュ時は journal を再生して完了済みステップをスキップし中断点から再開。冪等キーによるリクエスト重複排除も標準機能 | ジャーナル/台帳型に近いが、記録された「結果」を差し戻す点はTemporalの「コード再実行して検証」とは異なる= 実装結果を直接ショートカットして返す方式 |
| LangGraph | **Checkpointer** が「super-step」ごとにグラフの状態スナップショット（`StateSnapshot`）を `thread_id` 単位で永続化。resume は保存済み状態オブジェクトを復元するだけで、コード再実行もジャーナル再生も行わない = **スナップショット復元型** | どちらでもない第三の型（状態スナップショット直接復元） |

> ⚠️ **確度を下げるべき情報**: LangGraph の checkpointer が「durable execution ではない」という批判は Diagrid（Dapr を売る競合ベンダー）のブログ記事に基づく（[diagrid.io](https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows)）。ベンダーバイアスがあるため事実関係（「自動失敗検知がない」「`invoke(None, config)` を正しい `thread_id` で手動呼び出しする必要がある」「同一 `thread_id` の並行再開で重複実行を防ぐ調整機構がない」）は LangChain公式ドキュメントの記述（checkpointer は「persist a thread's graph state」「fault tolerance」を謳うのみで、自動再試行やクラッシュ検知の言及がないこと）と整合するため事実自体は妥当だが、「Temporal/Restate級のランタイム保証が必須」という規範的主張は割り引いて読むべき

### epic への適用可能性

| パターン名 | 何を保証するか | epic への適用可能性 |
|---|---|---|
| Temporal型：決定論的コードリプレイ + Activity分離 | ワークフロープロセスが何度クラッシュしても「効果的に一度だけ」実行完了する | **本環境では不可**。Claude Code の Agent ツールにはワーカープロセス・Event History・外部監視の仕組みが存在しない。L1 ランナー（general-purpose subagent）はステートレスな1回のプロンプト実行であり、途中終了を検知して自動リプレイする外部ランタイムは無い |
| Restate型：ジャーナル + 冪等キー + 自動リプレイ | 各副作用ステップをrecord-and-skip方式で再現し、冪等キーで重複実行を防ぐ | **本環境では不可**（同上の理由）。ただし冪等キーの「発想」自体（後述 Saga セクション参照）は部分的に転用可能 |
| LangGraph型：thread_id単位のスナップショット + 手動resume | 明示的な `thread_id` 指定での状態復元。人間/呼び出し元が明示的にresumeを起動する運用が前提 | **要適応（既に部分的に存在）**。epic は既に `EPIC_RUN_DIR/epic-plan.md` `/epic-runs.md` `/deferred-decisions.md` をディスクに書き出しており、これは「スナップショット」に相当する。ただし LangGraph の checkpointer と違い、epic 側には「このファイル群からDAG進捗を読み取って次に実行すべき未完了サブタスクを特定し再開する」という **明文化されたresumeプロトコルが存在しない**。もし epic 本体セッションが中断された場合、次セッションは `epic-runs.md` を Read してどの Ti まで完了したかを機械的に判定し、そこから再開できる余地がある。これは低コストで導入可能な改善であり、真の自動durable executionではなく「マニュアル版チェックポイント&リジューム」として位置づけるのが正確 |

---

## 2. Orchestrator-worker の型付き契約（typed contract / structured return）

### 一次情報から確認した事実

- Anthropic strict tool use: `strict: true` を tool 定義に付けると grammar-constrained sampling によって `input` が JSON Schema に厳密準拠することを保証する（`additionalProperties: false`・全フィールド`required`が要件）。「Function receives correctly-typed arguments every time」と明記 — [Strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use)
- Anthropic `tool_result` の `is_error` フィールド: ツール実行エラーを構造化された形でオーケストレーター（呼び出し側）に伝える標準機構。「Write instructive error messages」の推奨あり — [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)
- OpenAI structured outputs: `response_format` に `json_schema` を渡すことで「JSON mode」を超えたスキーマ厳密準拠を保証。strict モードの function calling では同様に `additionalProperties: false` と全フィールド必須化が要求される — [Structured model outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- Anthropic 多エージェント研究システム: サブエージェントには「objective, output format, tool/source guidance, task boundaries」の4要素を明示するのが定石とされ、artifact system（サブエージェントが外部システムに直接結果を保存し、オーケストレーターには軽量な参照だけを返す）でトークンオーバーヘッドと情報損失を防ぐ — [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

### epic への適用可能性

| パターン名 | 何を保証するか | epic への適用可能性 |
|---|---|---|
| Strict JSON Schema 出力（OpenAI/Anthropic tool use strict mode） | ツール呼び出しの引数が**必ず**スキーマに準拠。境界での機械検証が可能 | **本環境では不可（直接）**。Claude Code の `Agent` ツールにはサブエージェントの**返り値**に対する strict schema バインディングが存在しない（サブエージェントの返り値は自由形式テキスト）。tool_use/tool_result はモデル↔ツール間の契約であり、エージェント↔エージェント間（epic 本体 ↔ ネスト pir2、pir2 ↔ explorer 等）の契約には直接適用できない |
| リテラルキーワード契約（`VERDICT: PASS/FAIL` 的な固定トークン） | 自然文の中に人間にも機械にも解釈可能な固定フィールドを埋め込み、呼び出し元がgrep等で機械的に判定できる | **既に部分的に採用済み・要拡張**。PIR²の reviewer は既に `VERDICT: PASS/FAIL` という固定トークン契約を持つ。epic 側も `USER_DECISION_REQUIRED` / `EXPLORATION_NEEDED` / `DEFERRED_USER_DECISIONS` という同種のキーワードを使っているが、**これらは呼び出し元が「自然言語の要約」から目視で拾う運用**であり、strict tool use のような「機械的に必ず検出できる」保証は無い。改善余地としては、これらのキーワードを「出力必須の固定見出し（例: 常に `### DEFERRED_USER_DECISIONS` セクションを出力し、無ければ本文に `なし` と明記する）」として書式規約を強め、epic 本体がファイルを Read した後 grep 相当のパターンマッチで存在確認するプロトコルに寄せることで、性能の近似値は得られる |
| Artifact system（サブエージェントが外部ストレージに直接保存し軽量参照だけ返す） | 大出力のトークンオーバーヘッド削減・情報損失防止 | **既に採用済み**。epic/pir2 系は既に「本体は `{RUN_DIR}/xxx.md` に書き出し、呼び出し元には要約のみ返す」という設計をコア規約として持つ（explorer.md 含む全エージェント共通）。Anthropic の一次情報はこの既存設計の正当性を裏付ける外部エビデンスとして使える |

---

## 3. Trust-but-verify / deterministic verification gate

### 一次情報から確認した事実

- LLM-as-judge の限界: 非決定的（同一入力でも再実行で判定が変わりうる）、位置バイアス・冗長性バイアス・自己選好バイアスを持つ、事実検証を根拠なしに求めると「もっともらしさ」で採点してしまう、コスト（判定に元呼び出しの約3倍のトークンを消費）— [CogniSwitch: LLM-as-a-Judge vs. Deterministic Verification](https://cogniswitch.ai/guides/llm-as-a-judge-vs-deterministic-verification)、[Braintrust: What is an LLM-as-a-judge?](https://www.braintrust.dev/articles/what-is-llm-as-a-judge)
- 決定論的検証: 「同じ入力には常に同じ判定を返し、判定根拠となった規則を名指しできる」— テスト・lint・型チェック・diff等。CogniSwitch は「code-based checks（フォーマット・スキーマ）+ LLM-as-judge（質的評価）+ human review（サンプリング）」の三層構成を推奨
- Anthropic strict tool use も「機械検証で防げるものはリトライ判断から排除する」という同じ精神（型不一致・欠落フィールドはそもそも発生させない）

### epic への適用可能性

| パターン名 | 何を保証するか | epic への適用可能性 |
|---|---|---|
| 三層構成（決定論的チェック＋LLM判定＋人間サンプリング） | 各層が別種の誤りを捕捉し、コストの高い層（人間）を最小限のサンプリングに絞る | **既に部分的に採用済み（L2レベル）**。PIR²は既に reviewer（LLM judge、`VERDICT`）+ tester（決定論的テスト実行）の2層構成を各サブ pir2 内部（L2）で持つ。三層目の「人間サンプリング」は epic の Phase 1.5（分割確認ゲート）と DEFERRED_USER_DECISIONS 集約が担っている |
| Phase 3 統合確認への決定論的ゲート追加 | 複数サブタスクの結合点をLLMの目視diffレビューだけに頼らず、機械的な検証（ビルド・テスト実行）で裏付ける | **要適応（現状ギャップあり）**。`SKILL.md` ステップ4「Phase 3」は「epic 本体が `git diff` で結合点の整合を確認」とあるのみで、これは純粋な LLM-as-judge（epic 本体自身が diff を読んで判断）であり、決定論的バックストップ（例: 全サブタスク完了後にプロジェクトのビルド/テストスイートを一度通す）が明記されていない。各サブ pir2 内部の tester は「自分の変更範囲」しかテストしないため、複数サブタスクを跨いだ統合バグ（例: T1が変更したインターフェースをT3が誤用）を tester レベルでは捕捉できない可能性がある。Phase 3 に「プロジェクト全体のビルド/テストコマンドを一度実行する」決定論的ゲートを追加する余地がある（ただし具体的なコマンドはプロジェクト依存であり、epic 自体が汎用スキルである以上ハードコードはできない点に注意） |

---

## 4. Saga / compensation / partial-failure recovery

### 一次情報から確認した事実

- Saga パターン: 分散トランザクションを「一連のローカルトランザクション」として実装し、途中で失敗したら**逆順に補償トランザクション（compensating transaction）を実行**して意味的に取り消す。ACID的な自動ロールバックは無いため、**開発者が手動で補償ロジックを設計する必要がある** — [microservices.io: Pattern: Saga](https://microservices.io/patterns/data/saga.html)
- Orchestration（中央のオーケストレーターが参加者に実行/補償を指示）vs Choreography（各サービスがイベント駆動で自律的に反応）の2方式。epic は明確に Orchestration 型（epic 本体が全サブタスクを指示）
- 冪等性: 「副作用を持つノードは全て冪等性のストーリー（例: 入力のハッシュを冪等キーにする）を持つべき」— これはAI agentワークフロー文脈の二次情報（[AI Workflow Lab, 2026](https://aiworkflowlab.dev/article/ai-workflow-orchestration-in-production-building-durable-agent-pipelines-with-langgraph-and-temporal)、[Medium: Agent Workflows Are Rediscovering Durable Execution](https://nittikkin.medium.com/agent-workflows-are-rediscovering-durable-execution-be110661ed8c)）に基づくもので、確度はSagaパターン自体（一次情報＝microservices.io）より低い

### epic への適用可能性

| パターン名 | 何を保証するか | epic への適用可能性 |
|---|---|---|
| 補償トランザクション（サブタスク失敗時の巻き戻し定義） | 途中失敗時にそれまでの変更を意味的に取り消す明確な手順がある | **要適応（現状ギャップあり）**。epic-planner の DAG は「先行成果が必要」という順方向の依存しか定義しておらず、「T3 が reviewer/tester ループを使い切って FAIL のまま完了できなかった場合、既にコミット/適用済みの T1・T2 の変更をどうするか」という補償ロジックが `SKILL.md` にも `epic-planner.md` にも存在しない。現状は「ネスト pir2 は自前でコミットしない」（working tree に uncommitted な差分が残るのみ）という設計上、**「補償＝ working tree の差分を revert する」がそのまま自然な compensating action になりうる**。ただしこれは CLAUDE.md の git ルール（`git restore` はユーザー明示指示なしに実行禁止）と衝突しない形——つまり「epic 本体が補償の要否をユーザーに確認してから restore する」——で設計する必要があり、Saga の「自動補償」とは異なり **人間ゲート付き補償** になる点が本環境特有の制約 |
| 冪等キーによる重複実行防止 | 同じノードが複数回実行されても副作用が重複しない | **本環境では確度低い適用（推測）**。サブ pir2 は毎回 explorer からやり直す設計であり、厳密な「入力ハッシュで冪等性を保証する」機構は無い。ただし working tree が uncommitted な差分を保持したまま再実行されるため、「同じサブタスクを再実行すると、既にある差分の上に増分変更が乗る」形になり、Saga文脈の冪等性とは異なる意味論になる（悪い意味で「非冪等」になりうる：2回目の実行が1回目の差分を前提にしてしまう）。この点は deliberation で「サブタスク再実行時に前回差分を破棄するか継続するかを明示的にプロトコル化すべきか」を検討する価値がある |

---

## 5. Human-in-the-loop の集約とエスカレーション

### 一次情報から確認した事実

- LangGraph HITL: `interrupt()` でグラフ実行を特定ノードで一時停止し、状態は checkpointer で永続化される。人間の決定は **approve（そのまま実行）/ edit（引数修正して実行）/ reject（実行せずフィードバック返却）/ respond（人間の応答を直接ツール結果として返す）** の4種。複数の保留アクションがある場合は「decisions must be provided in the same order as the actions appear in the interrupt request」という**順序整合ルール**がある — [LangChain: Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- タイムアウト時の安全側デフォルト挙動については、参照した一次ドキュメントに明示的な記載が見つからなかった（**未確認**として明記。reject の説明が「人間が拒否する場合に使う」とあるのみで、無応答時の自動フォールバックの規定は確認できていない）

### epic への適用可能性

| パターン名 | 何を保証するか | epic への適用可能性 |
|---|---|---|
| interrupt-and-wait型 HITL（真のブロッキング一時停止＋明示的resume） | 人間が判断するまで実行を止め、決定後に厳密にその地点から再開する | **本環境では不可（現行設計の意図的トレードオフ）**。epic の L1（ネスト pir2 ランナー）はユーザーと対話できないため、LangGraph型の「その場で止めて人間の入力を待つ」は構造的に実現できない。epic は代わりに「保守的デフォルトを選んで進み、決定点を `deferred-decisions.md` に記録し、事後に L0 へ bubble-up する」**非ブロッキング委譲**方式を採用している。これは意図的な設計判断（サブエージェントはユーザー対話不可という Claude Code の制約から来る）であり、"劣化" ではなく "trade-off" として明示的にdeliberationに乗せる価値がある論点：「epic が canonical HITL に近づけるとしたら、plan-choice-gate 相当の分岐点で L1 ランナーが**完了させずに** L0 へ制御を戻すプロトコル（=`EXPLORATION_NEEDED` 相当の中断復帰方式をユーザー確認ゲートにも拡張する）を検討する余地があるか」 |
| 複数保留決定の順序整合ルール | 並列実行された複数エージェントからの決定要求を、要求順と対応させて取りこぼしなく集約する | **要適応**。epic の Phase 3「epic 本体はサブ pir2 完了ごとに `DEFERRED_USER_DECISIONS` を集約」は、並列 fan-out されたサブタスク群から複数の deferred decision が同時に上がってきた場合の**集約順序・競合時の扱い**を明記していない（例: T1 と T2 が並列実行され、両方が同じ共有インターフェースについて異なる保守的デフォルトを選んでいた場合の整合確認手順が無い）。LangGraph の「順序整合」の発想を借りて、`epic-runs.md` に Ti の起動順・完了順を記録し、Phase 3 集約時に「同一トピックに対する複数 deferred decision の矛盾検出」を明示的なチェック項目として加える余地がある |

---

## 6. 観測可能性（tracing/span）

### 一次情報から確認した事実

- OpenTelemetry GenAI Semantic Conventions: `create_agent` / `invoke_agent` / `invoke_workflow` / `execute_tool` の4種の span を Layer 2（Agent & Workflow Spans）として定義。最新は v1.41.1（2026年5月）で、GenAI 領域は**全体として "Development" ステータス**（正式な Stable 版のタイムラインは未公表、`OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` で最新実験的挙動にオプトイン）— [OpenTelemetry Blog: Inside the LLM Call](https://opentelemetry.io/blog/2026/genai-observability/)、[Greptime: OpenTelemetry GenAI Semantic Conventions](https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions)（後者はversion表を含む詳細な二次情報、確度は中程度として扱う）
- **重要な発見（本探索の主要成果）**: **Claude Code 自体がネイティブに OpenTelemetry を（ベータで）サポートしている**。`CLAUDE_CODE_ENABLE_TELEMETRY=1` に加え `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1` を設定すると、`claude_code.llm_request` span と `claude_code.tool` span の双方に **`agent_id` / `parent_agent_id` 属性**が付与され、サブエージェント（`Agent` ツール経由のネスト起動）が親子関係付きで個別に識別可能になる。`tool_parameters.Agent.subagent_type` フィールドで起動したサブエージェント種別も記録される。トレースエクスポーターは `OTEL_TRACES_EXPORTER=console,otlp,none` で選択可能 — [Claude Code Docs: Monitoring](https://code.claude.com/docs/en/monitoring-usage)

### epic への適用可能性

| パターン名 | 何を保証するか | epic への適用可能性 |
|---|---|---|
| OTel GenAI Semantic Conventions（invoke_agent/execute_toolのspan階層） | ベンダー中立な形式で agent 呼び出し階層をトレースバックエンドに送り、Datadog/Honeycomb/New Relic等で可視化できる | **そのまま適用可能（要オプトイン設定、ベータ機能）**。当初「Claude Code にネスト構造を計装する手段は無い」と仮定していたが、一次情報で誤りと判明した。Claude Code 自体が `agent_id`/`parent_agent_id` 付きの span を発行できるため、epic の L0→L1→L2 という3階層ネストは、この機能を有効化するだけで**実際のOTelトレースとして可視化可能**（`parent_agent_id` を辿ることで epic 本体 → ネスト pir2 ランナー → explorer/planner/implementer/reviewer/tester の親子関係が再構成できる）。これは epic 側のスキル定義を変更しなくても、**ユーザー環境変数設定のみで得られる観測可能性の強化**であり、6つの調査パターンの中で最も「そのまま適用可能」に近い |
| ファイルベース手動トレース（`epic-runs.md` 等） | 外部インフラ不要で、markdown ファイルとして手動運用できる最小限の観測可能性 | **既に採用済み**。OTel span 階層の「概念」（span名・親子関係・開始/終了時刻・入出力サイズ）を `epic-runs.md` の記法に転用する余地はあるが、これは OTel ネイティブ計装と役割が重複するため、OTel ベータを有効化する運用ならず者としての「二重管理」を避けるべき。OTel を使わない/使えない環境（オプトインしていない既定状態）向けの最低限のフォールバックとして現状のファイルベース記録を維持するのが妥当 |

---

## 全体まとめ表: パターン名 → 保証内容 → 適用可能性

| # | パターン名 | 出典 | 何を保証するか | epic適用可能性 |
|---|---|---|---|---|
| 1 | Temporal決定論的リプレイ | [docs.temporal.io](https://docs.temporal.io/workflow-execution) | クラッシュ後も「効果的に一度だけ」実行完了 | 本環境では不可 |
| 2 | Restateジャーナル+冪等キー | [docs.restate.dev](https://docs.restate.dev/concepts/durable_execution/) | 副作用ステップのrecord-and-skip再現、重複排除 | 本環境では不可（冪等性の発想のみ部分転用可） |
| 3 | LangGraph checkpointerスナップショット | [docs.langchain.com](https://docs.langchain.com/oss/python/langgraph/persistence) | thread_id単位の状態復元、resume/time-travel | 要適応（RUN_DIRファイル群を明文化されたresumeプロトコルに昇格） |
| 4 | Strict JSON Schema tool use | [platform.claude.com](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use) | 引数がスキーマに厳密準拠、境界での機械検証 | 本環境では不可（サブエージェント返り値には非適用） |
| 5 | リテラルキーワード契約（VERDICT等） | 内部SSOT観察＋Anthropic tool_result is_error | 自然文中の固定フィールドで機械的検出を可能にする | 既に部分採用・要拡張（必須見出し化） |
| 6 | Artifact system | [Anthropic multi-agent](https://www.anthropic.com/engineering/multi-agent-research-system) | 大出力のトークンオーバーヘッド削減・情報損失防止 | 既に採用済み |
| 7 | 三層検証（決定論+LLM判定+人間サンプリング） | [CogniSwitch](https://cogniswitch.ai/guides/llm-as-a-judge-vs-deterministic-verification) | 各層が異なる誤りを捕捉、コスト最小化 | 既に部分採用（L2）・Phase3統合確認は要適応 |
| 8 | Sagaの補償トランザクション | [microservices.io](https://microservices.io/patterns/data/saga.html) | 途中失敗時の意味的巻き戻し手順 | 要適応（working tree diff revertが自然な補償単位、ただしユーザーゲート必須） |
| 9 | LangGraph HITL（interrupt/resume, 決定4種） | [docs.langchain.com](https://docs.langchain.com/oss/python/langchain/human-in-the-loop) | ブロッキング一時停止+厳密な再開点 | 本環境では不可（意図的トレードオフ、非ブロッキング委譲を採用中） |
| 10 | 複数保留決定の順序整合ルール | 同上 | 並列決定要求の取りこぼし防止 | 要適応（DEFERRED_USER_DECISIONS集約時の矛盾検出手順が未定義） |
| 11 | OTel GenAI Semantic Conventions | [opentelemetry.io](https://opentelemetry.io/blog/2026/genai-observability/) | ベンダー中立なagent span階層の可視化 | そのまま適用可能（Claude Code自体がベータ対応、要オプトイン） |
| 12 | Claude Code ネイティブOTel（agent_id/parent_agent_id） | [code.claude.com](https://code.claude.com/docs/en/monitoring-usage) | L0/L1/L2の親子関係をトレースとして機械的に再構成 | そのまま適用可能（本探索の最重要発見） |

### 補足情報

- **視覚情報との整合チェック**: 本タスクにはユーザー提供のスクリーンショット等の視覚的一次情報は含まれていないため、当該チェックは非該当
- **「存在しない」型結論のチェック**: 「Claude Code に計装手段は無い」という初期仮説について、コードベース側の推測だけで結論せず `WebSearch` で改めて確認したところ誤りと判明した（ネイティブOTelベータが存在）。これは本探索プロトコル自身が定める「チェックリストを通さずに結論を出さない」の実例として機能した。検索した keyword: `Claude Code OpenTelemetry monitoring usage metrics documentation`
- **確度の階層**: 一次情報（公式ドキュメント）に基づく記述と、二次情報（ブログ・Medium記事）に基づく記述を各セクションで明示的に区別した。特に (a) Diagrid社ブログの「LangGraph批判」はベンダーバイアスありとして格下げ、(b) 「AI agentワークフローの冪等キー」に関する記述は2026年の実務者ブログ（AI Workflow Lab, Medium）に基づき一次情報ではないことを明記、(c) OTel GenAI semconvのバージョン表はGreptimeブログ（二次情報）由来であり公式リポジトリでは版数の直接確認ができなかった旨を明記した
- **L0/L1/L2 制約下での当たり**（以下は推測であることを明示。deepthink 側での検証が必要）:
  - 最も低コストで導入できそうなのは **#12（Claude Code ネイティブOTel）** — epic 側のスキル定義変更なしに、ユーザー環境変数設定だけで L0→L1→L2 の親子関係が可視化される可能性が高い。ただし「ベータ機能」であることのリスク（API安定性・課金・パフォーマンスオーバーヘッド）は未検証
  - 次に低コストなのは **#5（リテラルキーワード契約の必須見出し化）** — 既存の `VERDICT` 方式を `USER_DECISION_REQUIRED` / `EXPLORATION_NEEDED` / `DEFERRED_USER_DECISIONS` にも一律適用する程度の変更で、SKILL.md/epic-planner.md の記述追加のみで実現できる
  - **#3（resumeプロトコルの明文化）** と **#8（補償の明文化）** は設計判断（USER_DECISION_REQUIRED相当）を要する規模の変更であり、「epic は現状 exploratory 実験であり Evidence Summary が全項目0件」という前提を踏まえると、まず1〜2回の実 epic 実行で「本当に中断・部分失敗が起きるか」を観測してから設計に落とすほうが `experimental.md` の運用方針（観測→採用判断）と整合する
  - **#1・#2・#4・#9（Temporal/Restate/Strict tool use/LangGraph HITL の完全版）** は Claude Code の Agent ツールという実行基盤の構造的制約により本環境では実現不可と判断する。これらを目指す設計変更は提案しない

### 参照した外部ソース

| ソース種別 | URL | 確認した内容 |
|-----------|-----|------------|
| 公式doc (Temporal) | https://docs.temporal.io/workflow-execution | Durable Execution定義、Event History/Replay、決定論制約、Activity分離 |
| 公式doc (LangChain/LangGraph) | https://docs.langchain.com/oss/python/langgraph/persistence | Checkpointer、thread、super-step、StateSnapshot、resume/time-travel/HITLとの関係 |
| 公式doc (Restate) | https://docs.restate.dev/concepts/durable_execution/ | journal、replay、冪等キー、Virtual Object/Workflowの状態管理 |
| 公式ブログ (Anthropic) | https://www.anthropic.com/engineering/multi-agent-research-system | orchestrator-workerパターン、タスク仕様4要素、artifact system、チェックポイント併用のエラーハンドリング、トレーシング |
| 公式blog (microservices.io) | https://microservices.io/patterns/data/saga.html | 補償トランザクション、Orchestration/Choreography、自動ロールバック不在の課題 |
| ガイド記事 (CogniSwitch) | https://cogniswitch.ai/guides/llm-as-a-judge-vs-deterministic-verification | LLM-as-judgeの限界、決定論的検証の定義、三層構成 |
| 記事 (Braintrust) | https://www.braintrust.dev/articles/what-is-llm-as-a-judge | LLM-as-judge使い所とdeterministic evalsとの使い分け |
| 公式doc (LangChain) | https://docs.langchain.com/oss/python/langchain/human-in-the-loop | HumanInTheLoopMiddleware、approve/edit/reject/respond、interrupt/Command(resume=)、決定順序整合ルール |
| 公式blog (OpenTelemetry) | https://opentelemetry.io/blog/2026/genai-observability/ | GenAI semantic conventionsのスコープ、agent/chat/tool spanの親子関係 |
| 二次情報 (Greptime、確度中) | https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions | span 6層構造、v1.36〜v1.41のバージョン変遷表（公式リポジトリでは直接確認できず） |
| 公式doc (Claude Code) | https://code.claude.com/docs/en/monitoring-usage | OTelベータ、`claude_code.tool_result`/`claude_code.api_request`イベント構造、`agent_id`/`parent_agent_id`によるサブエージェント親子関係の計装 |
| 公式doc (Anthropic) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use | strict tool useのgrammar-constrained sampling、型安全保証 |
| 公式doc (Anthropic) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls | tool_result/is_errorの構造化エラー伝達、エラー種別（実行エラー/無効なtool名/サーバーツールエラー） |
| 公式doc (OpenAI) | https://developers.openai.com/api/docs/guides/structured-outputs | structured outputsの2形態、strict modeの要件（additionalProperties:false、全フィールドrequired） |
| 二次情報 (Diagrid、ベンダーバイアスあり・確度低) | https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows | LangGraph checkpointerとdurable executionの違い（規範的主張は割引評価） |
| 二次情報 (実務者ブログ、確度中) | https://aiworkflowlab.dev/article/ai-workflow-orchestration-in-production-building-durable-agent-pipelines-with-langgraph-and-temporal | AIワークフローにおける冪等キー・Saga補償の実務適用 |
| 二次情報 (Medium、確度中) | https://nittikkin.medium.com/agent-workflows-are-rediscovering-durable-execution-be110661ed8c | エージェントワークフローがdurable executionを再発見しているという論点 |

### 呼び出し元への依頼

- 本探索は read-only の外部一次情報収集であり、子 explorer のネスト起動は行っていない（探索範囲が「外部ドキュメント」中心で複数コードベース領域の並列調査ではなかったため不要と判断）
- **ライブラリ/インフラ選定の判断が必要な箇所**: Claude Code ネイティブ OTel ベータ（`CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`）を実際に有効化してエクスポート先（console/otlp/バックエンド製品）を選定する場合は、性能オーバーヘッド・データ保持ポリシー・課金影響の比較検討が必要になるため、採用を具体化するフェーズでは `tech-validator` エージェントへの委譲を推奨する（本探索はあくまで「存在確認」までに留めている）
- deepthink（thinker/hypothesizer/deliberator）に対して: 本レポートの「全体まとめ表」と「L0/L1/L2 制約下での当たり」セクションは推測を含むため、他の並列探索（前回の外部BP探索＝失敗モード編）の結果と突き合わせて、特に #8（補償）と #10（複数保留決定の順序整合）が実際に epic の失敗シナリオとして再現性があるかどうかを検証してから設計に落とすことを推奨する
