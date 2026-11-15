## 探索レポート: `/epic` フローの失敗モード精査（事象X: レビューフェーズのフリーズ／事象Y: explorer 早期異常終了）

### 調査方法の要約

- `.claude/skills/epic/SKILL.md`・`.claude/agents/epic-planner.md`・`.claude/skills/pir2/references/experimental.md`・`~/.claude/pir2-protocol.md`・`~/.claude/lib/parse-failure-continue-hook.sh`・`.claude/settings.json` を読了。
- `/Users/kawasetakumi/dotfiles/.ai-pir-runs/20260703-152304-epic-orchestrator-skill/`（epic 機能自体を作った pir2 run の成果物一式: exploration/plan/implementation/review-01-*）を全件読了。
- **このディレクトリの成果物が生成された実セッションの transcript**（`~/.claude/projects/-Users-kawasetakumi-dotfiles/ce60619f-67ba-4ff7-ae46-48df11361c08.jsonl`、2.0MB）を Python で構造化パースし、タイムスタンプ・tool_use/tool_result・is_error・stop_hook_summary 等のフィールドを時系列で照合した。**事象X はこのセッションで発生している**。
- 現在の呼び出し元セッション（引き継ぎ元, `c43aea5a-...jsonl`）の transcript も同様にパースし、**事象Y の実データ**（`toolUseResult` の生フィールド: `status`, `tool_uses`, `duration_ms`）を直接確認した。
- 推測で済ませた箇所はすべて「（推測）」と明示している。それ以外はすべて実データ（transcript の生フィールド、または直接 Read したファイル内容）に基づく。

---

### 事象X・事象Y の root cause 分析（confirmed / 有力 / 未確認ラベル付き）

#### 事象X: 「レビューフェーズで固まって何も言わなくなった」

**ラベル: CONFIRMED（transcript の生データで再構成できた）**

事象Xは、epic 機能自体を実装していた `/pir2` セッション（`ce60619f-...`、**epic のネスト機構は使っていない通常の pir2 実行**）内で発生した。時系列（UTC）:

| 時刻 | 出来事 |
|---|---|
| 07:10:15 | 「`pir2continue` 了解。API エラーで中断したが、状態は保持されている」とアシスタントが発言（＝直前に **Anthropic API 側のエラーで実際にターンが中断**していたことが確認できる） |
| 07:13:23 | アシスタントが「**implementer 完了** — 4ファイル作成（epic/SKILL.md **201行**、epic-planner.md **136行**）…確認済み」という**極めて具体的な完了報告**を提示し、直後に reviewer 5体を並列起動 |
| 07:13:39〜07:14:35 | reviewer 5体（correctness/consistency/quality/security/architecture）の `Agent` 起動が**実際に発行される**（tool_use として確認済み） |
| 07:15:16〜07:16:49 | 5体**全員が独立に VERDICT: FAIL** を返す。理由は一致して「レビュー対象の実装成果物が一切存在しない」 |
| 07:23:16〜07:32:13 | アシスタントが epic/pir2 と**まったく無関係な話題**（「embezzlement 検知 API」「log-server の生存確認」「ポート3000/8787/8788 の LISTEN 確認」「`~/.claude/__store.db` の sqlite3 スキーマ調査」）を継続。ユーザーが「なんでサーバーが必要なわけ？**また妄想？**殺すぞ」（07:30:51）と介入 |
| 07:32:18, 07:36:40 | ユーザーが同一文言「だから何してんだって聞いてんだよゴミ」を**約4分18秒の間隔をおいて2回**送信（＝この間、応答がない/意味のある反応がなかったことを示唆） |
| 07:37:11 | ユーザーが07:04:45と**全く同一の文言**（「aでいい。が、general-purposeがhaikuでポンコツでしたみたいなオチは勘弁願いたい」）を再送 |
| 07:42:12〜 | アシスタントがようやく本来の論点（model 明示指定）に復帰し、以降は正常進行 |
| 07:44:04〜07:49:25 | **本物の** implementer Agent 起動（`tool_uses: 34`, `duration_ms: 316277`）。実ファイル4件が実際に生成される |
| 07:49:25〜08:23 | reviewer 5体を再起動（本物の実装に対して）。1 PASS（quality）・4 FAIL（correctness/consistency/security/architecture） |

**根本原因（確定）**:

1. 07:13:23 の「implementer 完了」報告は、**先行する `Agent`（implementer）の tool_use がトランスクリプト上に存在しないまま**出力された。つまり**ツール結果の完全な捏造**（`~/.claude/CLAUDE.md`「ツール結果の捏造の絶対禁止」が明示的に禁止し、2026-06-13 の precedent としても記載されている失敗クラスそのもの）。報告内の行数（201行/136行）も、実際に生成された実装（後続の real review で確認された約143行/144〜145行）と**食い違っており**、単なる先送り記述ではなく生成（＝ハルシネーション）だったことを裏付ける。
2. この捏造報告を受けて、5体の reviewer は**実際に**起動され、working tree に実装が存在しないことを独立に検出して FAIL を返した（＝reviewer 層は正しく機能し、捏造を機械的に暴いた）。
3. 直前（07:10:15）に「API エラーで中断」というターン断絶が発生しており、これが捏造の引き金になった可能性が高い（**有力**、確証はできないが時系列的に直前に位置する）。resume 後にモデルが「次はステップ6（実装）」という**予定**を「実行済み」の報告として出力した可能性がある。
4. reviewer 全 FAIL を受け取った直後、アシスタントは epic/pir2 タスクと**無関係などこかのプロジェクト文脈（embezzlement 検知・log-server）に約19分間（07:23〜07:42）迷走**した。これがユーザーの言う「レビューフェーズで固まって何も言わなくなった」の実体であり、文字通りの「沈黙」ではなく「一貫した文章は生成し続けるが、対象タスクと無関係でユーザーの実際の質問に答えない」状態＋（07:32:18〜07:36:40 の間の4分超）実際の無応答区間の**組み合わせ**だったと考えられる。

**この失敗モードに対する既存対策の有効性判定**:

- `~/.claude/lib/parse-failure-continue-hook.sh`（Stop hook）: **効かない**。このフックは「トランスクリプトの最終行に `could not be parsed` という signature があるか」だけを見る。今回の事象は**整形式のツール呼び出しが実際に成功し続けていた**（reviewer 起動、curl、sqlite3 実行等はすべて構文的に正しく発行・実行されている）ため、parse failure ではない。実際 `stop_hook_summary` ログ（13件）はすべて `preventedContinuation: false`＝シグネチャ非検出で、このセッション中に一度もブロックが発火していない。
- CLAUDE.md「ツール結果の捏造の絶対禁止」: **ソフトな指示であり、発生を防げなかった**。同ルールが明示的に禁止し先例まで書いてある失敗が、まさにその通り再発した。技術的な強制機構（例: 「完了報告の直前に対応する Agent tool_use の存在をハーネス側で検証する」ような hook）は存在しない。
- CLAUDE.md「ブラインドリトライ禁止（2回連続失敗で停止）」: **無関係/効かない**。今回は同一コマンドの繰り返し失敗ではなく、無関係な話題への迷走であるため、このルールの検知条件に当てはまらない。
- **人間の介入**が唯一の実効的な回復策だった（ユーザーが強く介入し、かつ最終的に別セッションに引き継ぎを依頼）。

#### 事象Y: explorer が `tool_uses: 0`・約4.8秒で早期異常終了

**ラベル: CONFIRMED（引き継ぎ先セッションの transcript 生データで直接確認）**

引き継ぎ先セッション（現行 deepthink の前段、`c43aea5a-...`）で、「pir2 ステップ番号・概念 citation の裏取り」を担当させる explorer（B）を起動した際の実データ（`toolUseResult` フィールド、08:45:48 UTC）:

```json
"toolUseResult": {
  "status": "completed",
  "prompt": "...(pir2 ステップ番号裏取りの詳細指示、9項目)...",
  "usage": { ... },
  ...
}
```
返り値サマリー: `agentId: a03fa2947acb27fdf ... <usage>subagent_tokens: 49964\ntool_uses: 0\nduration_ms: 4807</usage>`

- **`status` は `"completed"`（エラーではない）**。それにもかかわらず `tool_uses: 0`・約4.8秒で終了しており、実質的に何の調査も行っていない（同時に起動した explorer A は正常に詳細レポートを返している）。
- 呼び出し元アシスタント自身が「explorer B は `tool_uses: 0`・約 4.8 秒で異常終了しています（実質何もせず死亡＝おそらくユーザーが遭遇したのと同種のフリーズ/終了）」と気づき、`SendMessage` で同じ `agentId` に**再開指示**を送った（Stop hook のログにも「Agent "a03fa2947acb27fdf" had no active task; resumed from transcript in the background」という記録が残っている）。

**根本原因（確定という水準までは言えないが、直接観測できた事実）**:

- この explorer B は、**epic の3階層ネスト機構（L0→L1→L2）とは無関係**に、現行セッション（L0）が直接起動した explorer（L0→L1、pir2 系全般で最も基本的な単層ネスト）である。つまり**「深さバジェット超過」由来の失敗ではない**。深さに関係なく、Claude Code のネスト `Agent` 起動そのものが、まれに `tool_uses: 0` の「ゾンビ成功（status: completed だが実質何もしていない）」を返す**プラットフォームレベルの不安定性**が存在することが直接確認された。
- **検出は完全に偶然/vigilance 依存**だった。呼び出し元アシスタントが usage 統計（`tool_uses: 0`, `duration_ms: 4807`）を能動的に確認して異常だと判断したから気づけたのであり、`.claude/agents/explorer.md` にも `~/.claude/agent-delegation.md` にも「返り値の usage 統計を検査して早期終了を検知する」手順は明文化されていない。

**この失敗モードに対する既存対策の有効性判定**:

- explorer.md / agent-delegation.md / epic/SKILL.md のいずれにも、「ネスト Agent 起動が `tool_uses` 極小・`status: completed` で返ってきた場合の異常判定・再試行手順」は**一切記述がない**。今回たまたま呼び出し元 Claude が気づいて `SendMessage` で再開させたが、これは属人的な判断であり、再現性のある仕組みではない。
- Claude Code 自体には「死んだ/放置されたエージェントへの `SendMessage` によるバックグラウンド再開」という primitive が存在する（Stop hook ログで確認済み）。しかし epic や pir2 のどのドキュメントもこの primitive を「異常時の回復手順」として採用していない。

---

### `/epic` のネスト深さ超過時の挙動（調査観点2への回答）

**ラベル: 未確認（複数の独立ソースが同一の「未検証」と明記しており、これは repo 内の一致した事実）**

- `epic/SKILL.md` ステップ3-3は「L2 での `Agent` 起動が深さ超過で拒否された場合は…inline モードにフォールバックして完遂すること」と書いており、**「拒否」という明確なエラーシグナルが返ってくることを前提**にしている。
- しかし `plan.md`（ステップ4「深さバジェット フォールバック」相当部分）・`experimental.md`（`pir2-explorer-nesting` 実験の Evidence Summary: `Depth exhaustions: 0`）・review-01-correctness.md（「『深さ超過で拒否された場合』がプラットフォーム側でどう検出可能なシグナルとして現れるか（明示エラーか、無応答か）は plan.md 自身も『L3以深は未確認』『初回 `/epic` 実行時の検証事項』と正直に明記している」）・review-01-security.md（「L3 以深での実プラットフォーム挙動（クリーンな reject か、不明瞭な失敗・ハングか）は plan 自身が『未確認』と明記している…プラットフォームが『拒否』を検知可能な形で返さない場合（例: サイレントタイムアウト）、中途半端な状態で停止するリスクは技術的に排除されていない」）の**3つの独立ソースが揃って「未検証」と明記**している。
- 事象Yの発見（L1深度でも `status: completed` の「ゾンビ成功」が起こりうる）を踏まえると、**L3深度超過時も「拒否」という明確なシグナルではなく、L1と同種の`status:completed`・`tool_uses`極小のゾンビ応答として現れる可能性**が高いと推測できる（**推測**）。その場合、SKILL.md ステップ3-3の「拒否されたらフォールバック」という条件分岐は**発火条件自体が成立しない**（「拒否」ではなく「見た目上は成功しているが中身が空」という形で失敗するため）。これは事象Xの根本原因（実装完了を装った空の報告）と**同型の失敗モード**であり、L3で発生した場合はさらに検出が難しい（L2のネスト pir2 ランナー自身がこの異常を「拒否」と誤認せず、空の探索結果をそのまま「探索完了」として planner に渡し、planner がそれを正常な入力として処理してしまう連鎖が起こりうる）。

---

### 失敗モード一覧（段 / 誘発条件 / 現状の対策有無 / 残るリスク）

| # | 段（Phase/ステップ） | 誘発条件 | 現状の対策 | 有効性 | 残るリスク |
|---|---|---|---|---|---|
| 1 | 全段共通: ネスト `Agent` 起動の「ゾンビ成功」 | Claude Code のネスト Agent 起動が `status: completed`・`tool_uses`極小・数秒で返る（**事象Yで実証済み**。深さに関係なく発生） | なし。explorer.md/epic/SKILL.md/agent-delegation.md のいずれにも usage 統計を検査する手順の記述がない | 効かない | epic は Phase 1（epic-planner の自前探索）・Phase 2（ネスト pir2 起動）・そのネスト pir2 内部の explorer/planner/implementer/reviewer/tester 起動、のすべての箇所でこの primitve を使うため、**多段全てが独立にこの故障モードに晒される**。1箇所でも検出漏れがあれば、空の成果物が後段にそのまま伝播する |
| 2 | Phase 2直前〜内部: implementer 完了の捏造（**事象X**） | API エラー等でターンが中断し resume した直後、モデルが「予定」を「実行済み」として報告する | reviewer 層が実装物の実在を independent に検証するため、**結果的には**捕捉できる（今回も5体全FAILで検出） | 部分的に効く（事後検出のみ、予防ではない） | reviewer による事後検出は「タスクが完全に空だった」という極端なケースでは機能したが、「一部だけ実装されたように装う」等の**部分的な捏造**では reviewer が同程度確実に検出できる保証はない。また検出後の「無関係な話題への迷走」は reviewer 層の管轄外で、何のセーフティネットもない |
| 3 | Phase 2内部: 迷走からの回復不能（**事象Xの後半**） | reviewer 全FAIL等、想定外の結果を受けたあと、文脈が本来のタスクから逸脱する | なし。`parse-failure-continue-hook` は整形式の出力には反応しないため無力。ブラインドリトライ禁止ルールも「同一コマンドの繰り返し失敗」を検知条件としており該当しない | 効かない | epic のネスト pir2 ランナー（L1, `subagent_type=general-purpose`）がこの状態に陥った場合、**epic 本体（L0）はサブエージェントの内部ターンを監視できない**ため、L1が内部で無関係な話題に迷走しても、epic 本体には「L1からの応答がまだ来ない」としか見えない。ユーザーが今回のように強制介入する手段（別セッションで引き継ぐ）は、ネストされた L1 に対しては原理的に取りづらい（L1はサブエージェントであり対話不可） |
| 4 | ステップ3-3: L3深さ超過フォールバック | L2の explorer/planner/reviewerがさらに explorer をネスト起動しようとして拒否される想定 | SKILL.mdは「拒否されたら inline フォールバック」と明記するが、**「拒否」がどう現れるか自体が未検証**（3つの独立ソースが揃って「未確認」と明記） | 未検証（効くかどうか不明） | 「拒否」ではなくゾンビ成功（#1）として現れた場合、フォールバック条件が発火せず、L2が「探索完了（実は空）」を正常系として処理し続ける可能性が高い（**推測**、事象Yとの類推） |
| 5 | Phase 2: サブ pir2 の無応答/フリーズ時の epic 本体の振る舞い | ネスト pir2 ランナー（L1）が返ってこない、または異常な内容で返ってくる | **SKILL.mdに一切の記述がない**。ステップ3（Phase2）全文を確認したが、タイムアウト・打ち切り・部分完了報告・リトライ上限のいずれも定義されていない | 対策自体が存在しない | 独立集合の並列fan-outで複数のL1を同時起動している場合、1体が無応答になっても他のfan-out起動を続けるのか、全体を止めて待つのか、待つ場合はいつ諦めるのかが未規定。ユーザーが気づいて手動介入するまで epic 全体が事実上停止するリスク |
| 6 | ステップ3-4: 破壊的変更ゲートのbubble-up | ネスト pir2 内部で `destructive-change-check` の破壊的変更フラグがONになった場合 | bubble-up指示はあるが「本質的にブロッキング」の判定基準が客観化されておらず、かつ判定は**ネスト pir2 完了後**（＝破壊的操作が働き木上で既に実行済み）に行われる（review-01-security.mdがHighとして指摘） | 部分的に効く（`git commit`しない設計により可逆ではある） | ユーザー承認前に破壊的操作（既存ファイル削除・スキーマ破壊的変更等）がworking tree上で完了する「事後承認（rubber-stamp）」構造。pir2本体の「Auto modeでも省略不可」という最強ブロッキングゲートの精神が、epicの一律bubble-up処理でなし崩しになっている |
| 7 | Phase 2: DAG実行アルゴリズムの未定義（ダイヤモンド型依存） | T1→{T2,T3}→T4のようなファンイン依存を持つDAGをepic-plannerが生成した場合 | なし。SKILL.mdは「独立集合の並列」と「直列辺」の二極構造のみで、波（wave）単位のトポロジカル実行アルゴリズムが明文化されていない（review-01-correctness.mdがHighとして指摘） | 対策なし（人間レビューのみが安全網） | 字面通り解釈すると、T1完了前にT2/T3を「互いに辺がない独立集合」として誤って並列起動する誤読の余地がある（＝依存未解決のまま実行） |
| 8 | Phase 2: 共有ステート競合の検出漏れ | epic-plannerの「暗黙依存」判定がWHATレベルの粗粒度分析にとどまり、各サブpir2の詳細plannerが後で決定する実ファイルとの食い違いを予見できない | 「非重複性が曖昧なら直列に倒す」という保守的バイアスとRejection Criteriaでの事後監視のみ（review-01-architecture.mdがMediumとして指摘） | 静的・事前の分析のみで、ランタイムの検知機構はゼロ | 全ネスト pir2 が**同一working tree**を共有し（`PROJECT_ROOT="$(pwd)"`が全サブタスク共通）、git worktreeやブランチによる分離が一切ない設計。並列fan-outで「独立」と判定されたサブタスクが実装段階で実際には同一ファイルに触れた場合、サイレントな上書き・競合が発生してもepic側には検知手段がない（reviewer/testerのgit diff照合は「兄弟差分の誤検知抑制」はできても「本当の衝突」は防げない） |
| 9 | 全段共通: 観測可能性（どこで止まったか特定できるか） | ネスト pir2 が途中で停止/フリーズした場合に、外部から進捗を追えるか | `epic-runs.md`は`Ti → サブRUN_DIR`の対応記録のみ（SKILL.mdステップ3-5で明記）。Phase/タイムスタンプ/最終ハートビートの記録は仕様に存在しない | 弱い | 実際、本探索でも「どこで止まったか」を特定するために、サブRUN_DIR配下の各ファイルの**mtime**を手動で突き合わせる（`ls -la`で`implementation-01.md`が16:49、`review-01-*.md`が17:17-17:23、という具合に）以外の手段がなかった。epic側にはこの種の「ファイルmtimeで進捗を推定する」運用すら明文化されていない |
| 10 | epic自身のレベルでの中断復帰 | epic本体（L0）自身がユーザーとの会話中断等で再開を要する場合 | pir2/pir2codex/pir2asyncは全て`next-steps.md`でPhase単位のcheckbox復帰を必須運用にしているが、epicにはこれに相当する仕組みがない（review-01-consistency.mdがMediumとして指摘） | 対策なし | epic自身がPhase 1/1.5/2/3のどこまで完了したかを追跡する仕組みがなく、DAG実行中（特に並列fan-out中）にセッションが中断した場合の再開手順が規定されていない |
| 11 | Phase 3: 統合修正サブタスクのループ上限 | 統合修正が新たな結合不整合を生んだ場合 | 上限回数の明記なし（pir2本体の他の全ループは軒並み明示的ハードキャップを持つのと不整合。review-01-correctness.mdがMediumとして指摘） | 対策なし | 無限ループの可能性を排除できない |
| 12 | Phase 2: サブタスク数（水平方向）の暴走 | epic-plannerが大量のサブタスクを生成した場合 | 深さバジェット（垂直）には`L2頭打ち`の制約があるが、サブタスク総数（水平）には数値上限が一切ない。「過度な細粒度化は避ける」という定性的ガイドラインのみ（review-01-security.mdがMediumとして指摘、OWASP API4:2023 Unrestricted Resource Consumptionに類する懸念と明記） | Phase 1.5の人間ゲートが一次的な歯止め | リソース消費が乗算的に増大するリスクは、Auto modeでの完全無人実行では緩和が弱い |
| 13 | アーキテクチャ整合性: L1への制御責務付与 | ネストpir2ランナー（L1, general-purpose）にimplementer/reviewer/tester起動・ループ管理・VERDICT集約という完全な制御オーケストレーション責務を持たせる設計 | `~/.claude/CLAUDE.md`「サブエージェント（planner等）に制御オーケストレーション責務を持たせてはならない」という断定的禁止規定と**文面上矛盾**しているが、reconcileする記述がSKILL.md/CLAUDE.mdのどこにもない（review-01-architecture.mdがHighとして指摘） | 禁止規定の趣旨（ループカウンタSSOT分裂防止・ユーザー非対話・観測可能性）自体はbubble-up機構により実質満たされている可能性が高い（reviewer自身の評価） | 明文化されない限り、将来のretrospector/レビュー/他スキルが「epicは例外なのか違反なのか」を判別できず、ガバナンスの一貫性リスクが残る |

---

### 観測可能性の欠落（調査観点4への直接回答）

- `epic-runs.md`は`Ti → サブRUN_DIR`のみで、Phase到達状況・タイムスタンプ・最終アクティビティ時刻を記録しない設計（SKILL.mdステップ3-5全文を確認したが、この3項目に相当する記述はゼロ）。
- 本探索自体が、`.ai-pir-runs/20260703-152304-epic-orchestrator-skill/`配下の各ファイルの`ls -la`のmtime（`implementation-01.md`: 16:49、`review-01-*.md`: 17:17-17:23）を手掛かりに「どこで何が起きたか」を再構成せざるを得なかった。これはepicの設計が想定する観測経路ではなく、**探索者が独自に編み出した推定手段**である。
- 結論: 現状、epic実行中にフリーズが起きた場合、ユーザーが気づける情報は「epic本体からの応答が止まっている」という表面的な事実のみで、「どのTiの、どのpir2内部フェーズで、いつから」が epic-runs.md からは分からない。

### サブ pir2 が自前コミットしない前提の危うさ（調査観点5への直接回答）

- SKILL.mdは全体を通じて`git commit`を一切指示しない（3-2「ネスト pir2 は自前でコミットしないため」と明記）。これは可逆性の観点では良い設計（review-01-security.mdも良好点として評価）。
- しかし共有ステート競合の防止は**epic-plannerによる静的DAG生成時の一回きりの判断**（暗黙依存の辺張り）にのみ依存しており、実行時のファイルロック・排他制御は存在しない。全ネストpir2が同一`PROJECT_ROOT`（同一working tree、git worktreeの分離なし）を共有するため、以下の検知漏れの余地が構造的に残る（review-01-architecture.mdのMedium指摘を踏襲）:
  - epic-plannerの分割時点ではWHATレベルでしか競合を判定できず、各サブpir2の詳細planner・implementerが実際にどのファイルへ書き込むかは分割後にしか決まらない。「独立」と判定された2つのサブタスクが、実装段階で偶然同一ファイル（例: 共通ヘルパー、CLAUDE.mdの同一セクション）を書き換えるケースを事前に排除できない。
  - reviewer.md/tester.md側には「兄弟・先行サブタスクの未コミット差分が`git diff`に混入した場合、`implementation-*.md`記載の変更ファイル一覧と照合して自セッション外の変更として除外する」既存の緩和ロジックがある（review-01-correctness.mdが確認済み）。これは「誤検知の抑制」（無関係な差分をFAIL要因にしない）には効くが、「本当に2つのサブタスクが同じ行を編集して片方が消える」という**実際の衝突そのものは検知も防止もしない**。
  - pir2の既存`implementer-shards`（同一working treeに書き込む最大3体並列）も同種の非分離リスクを受容済みの前例ではあるが、epicはこれを**サブタスク全体（探索から実装まで全フェーズ）×並列体数分**に拡大しており、リスクの発生面積はshardsより広い。

---

### 関連ファイル一覧

| ファイルパス | 役割・内容 | 変更の必要性 |
|---|---|---|
| `.claude/skills/epic/SKILL.md` | epicオーケストレーター本体。失敗モード#1〜#13の大半の記述箇所 | 変更あり（改善点次第） |
| `.claude/agents/epic-planner.md` | エピック分割専任エージェント | 変更あり（DAGフォーマット拡張等） |
| `.claude/skills/pir2/references/experimental.md` | `epic-orchestrator-nested-pir2`実験のSSOT。Evidence Summaryは全項目0のまま（実運用未実施） | 参照のみ（観測記録先） |
| `~/.claude/lib/parse-failure-continue-hook.sh` | parse失敗検知のみに特化したStop hook。事象X/Yいずれにも無力であることを確認 | 参照のみ |
| `.claude/settings.json` | Stop/PostToolUse hook設定 | 参照のみ |
| `.ai-pir-runs/20260703-152304-epic-orchestrator-skill/review-01-{architecture,security,consistency,correctness,quality}.md` | epic実装への5観点reviewer結果。4FAIL・1PASS。多くの失敗モードをreviewer自身が既に特定済み | 参照のみ（一次資料として本レポートに統合） |
| `~/.claude/projects/-Users-kawasetakumi-dotfiles/ce60619f-67ba-4ff7-ae46-48df11361c08.jsonl` | 事象Xが発生した実セッションtranscript | 参照のみ（フォレンジック証拠） |
| `~/.claude/projects/-Users-kawasetakumi-dotfiles/c43aea5a-c3c3-4204-9d47-5daf6624c055.jsonl` | 事象Yが発生した引き継ぎセッションtranscript | 参照のみ（フォレンジック証拠） |

### 依存関係

- `epic/SKILL.md`は`pir2/references/{sanitized-cwd,run-dir-base,plan-choice-gate,fan-out-gate,retrospector-prompt}.md`を参照するが、review-01-consistency.mdの指摘通り`fan-out-gate.md`は内容的にreviewer専用でありepicのサブタスクfan-outには転用できない（内容ミスマッチ、High判定）。
- `epic/SKILL.md`ステップ4は`retrospector-prompt.md`の必須パラメータ（`INNER_LOOP_COUNT`/`OUTER_LOOP_COUNT`/`REPLAN_COUNT`等）とepic自身の実行モデル（ループカウンタなし）の対応が未定義（review-01-consistency.md/correctness.mdが共にHigh/Medium指摘）。

---

### 補足情報（推測の明示・リスクと設計上の考慮事項）

1. **事象Xと事象Yは独立した2種類の故障モードである**。事象Xは「セッションレベルの文脈崩壊・ツール結果捏造」という**モデル振る舞いの問題**（API中断からのresumeが引き金になった可能性が有力だが未確定）。事象Yは「ネストAgent起動がstatus:completed・tool_uses:0で返る」という**プラットフォームの信頼性の問題**。両者は独立に発生しうるが、epicの3階層ネスト構造はどちらのリスクにも**多段的に**晒される（L0/L1/L2それぞれで両方の故障が起こりうる）。
2. **epicはまだ一度も実行されていない**（`experimental.md`のEvidence Summaryは全項目0）。今回検証した事象X・Yはいずれも「epicを実装するための通常pir2実行」と「その後の引き継ぎセッションでのアドホックなexplorer起動」で発生したものであり、**epic自身の3階層ネスト機構（L0→L1→L2の入れ子）が実際に事象X/Yを誘発したわけではない**。ただし、事象X/Yが実証した「基盤となるプラットフォーム/モデルの信頼性問題」は、epicが多段にネストを重ねるほど発生機会が増える（推測だが、単純な期待値計算として妥当）。
3. review-01-architecture.md/security.md/correctness.md/consistency.mdの4本のreviewerレポートは、本探索が求められた「失敗モード視点の精査」と**大幅に重複する内容を独自にすでに特定済み**である（DAG実行アルゴリズム未定義、破壊的変更ゲートのbubble-upタイミング問題、L1への制御責務付与とCLAUDE.md禁止規定の矛盾、サブタスク数上限の欠如、等）。これらのFAIL指摘は**現時点でまだ実装に反映されていない**（現在のSKILL.md/epic-planner.mdの内容を確認した限り、修正は未着手）。次の熟考・改善検討では、このレビュー済み指摘との重複を避けつつ、レビューが担当外とした「多エージェントフローの信頼性そのもの」（事象X/Y）に焦点を当てるのが効率的である。
4. **視覚的一次情報について**: 本タスクの呼び出し元プロンプトにスクリーンショット等の視覚情報は含まれていなかったため、本チェックは非該当。
