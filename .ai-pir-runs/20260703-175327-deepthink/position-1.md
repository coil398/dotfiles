## position（ROUND 1）: /epic＋そのネスト多エージェント機構全般の信頼性改善点の抽出・優先度づけ

### 結論（現時点の最良の答え）

epic の信頼性改善は「**本番堅牢化(robustification)**」の問題ではなく「**計器(instrumentation)を今入れる**」問題として framing する。4体が独立に収束した中核命題は4つ:

1. **今回観測された失敗2件（事象X=捏造フリーズ / 事象Y=ゾンビ成功）は、epic のネスト機構（DAG / fan-out / 深さバジェット / L1 ランナー）を1つも通っていない。** X は epic を書いていた通常 pir2 セッションの resume 直後、Y は深さバジェット無関係の L0→L1 直接 explorer。∴ epic 固有機能（DAG fan-in / handoff 競合 / 深さバジェット / サブタスク上限）を**どれだけ直しても今回の失敗は再現的には防げない**。
2. **要るのは計器であって堅牢化ではない。** 両者は別カテゴリ。今入れるのは決定論的な測定装置（観測性・境界検証）で、重い本番堅牢化（resume 完全版 / fan-in merge / worktree 分離 / timeout harness）は初回実行の観測データが出るまで回す。
3. **instrumentation ≠ robustification のカテゴリ区別が、最有力反論「試験実装に堅牢化は過剰、まず0回を1回動かせ」への応答の核。** 堅牢化は見送るが計器は今入れる。計器がないと1回目の失敗すら診断不能（事象X が「フリーズ箇所を特定できず19分迷走・学び0」を実証済み）。
4. **L1 ランナーに制御責務を持たせる設計は、CLAUDE.md が禁じる role-conflation（専門サブの制御兼務）とは別カテゴリ＝「再帰オーケストレーション」であり、境界観測性の実装を前提条件に付せば条件付きで正当化可。**

そのうえで最高レバレッジは epic 固有でなく**共通層（pir2-protocol.md / 共有 references）**に「L0 が L1/サブの内部状態を境界で受け取り、self-report でなく決定論で外形照合する」**二層機構**（テレメトリ return ＋ 独立 git/floor 検証）を置くこと。これ＋観測性（epic-runs.md への Phase/timestamp）＋最小安全弁（hard-cap 配線・fan-out 直列化・破壊的事前ゲート・citation 是正・初回題材制約）を【今直す必須】に、重い堅牢化を【観測に回す】に割り付ける。設計根幹 #8 は試験段階 **Option B（条件付き正当化）**、恒久採用判断時に **Option A（L0 直接統率）へ再評価** という時間軸付きで残す。

---

### 主要な論拠

- **今回失敗は epic 機構外**という事実からの直撃 (D-02 反証レンズ)。context の CONFIRMED 2件が epic ネストを通っていない以上、「epic 堅牢化＝今回失敗対策」は成立しない。ここから「机上で数えた失敗モード（DAG合流・handoff競合・深さバジェット等）は rubric #3 に寄与しない」を導ける。
- **委譲型オーケストレータ＝信頼できない語り手を含む分散システム**であり、完了報告は claim であって ground truth ではない (D-01 第一原理)。事象X は「resume 状態欠如(I5)が残した認識論的真空をモデルが穴埋め(I1破綻)→ implementer claim と reviewer verdict の矛盾に解決経路なし(I2)→ 迷走」の3段連鎖。`parse-failure-continue-hook` は「整形式だが偽」を検知できず貫通。
- **計器 vs 堅牢化のカテゴリ錯誤** (D-02, D-04)。「まず1回動かせ」を**成立させる前提条件**が観測性・境界検証であり、これらは贅肉でなく実験の測定系。
- **G1 テレメトリ return が事象X検知(R1)・事象Y検知(R2)・#8観測性・retrospector param(C5) の共通入力**になる収束 (D-04 SSOT整合)。バラバラに見えた4問題は全て「L0 が L1 の内部状態を境界で受け取れない」に起因。
- **ただし self-report だけでは捏造は捕まらない**。テレメトリ(G1)は自己申告レイヤで、捏造はまさにそこで起きる。∴ **L0 側の独立外形検証（git diff 突合・役割別 tool_use floor）が別立てで必須** (D-01 IMP-1, D-02 決定論hook, D-03 事後ゾンビ検知, D-04 R1/R3 が全員一致)。「テレメトリ＝正常時の観測配管、独立検証＝異常時の外形検知」の二層。
- **#44783 デッドロックは親プロセスの内側から検知不能**（L0 watchdog 自身が同じ親でブロックされる）(D-03 境界条件)。∴ 防御は事前（並列幅を下げる/直列化）か事外（人間/外部プロセス監視）に限られ、試験段階では直列化が platform-safe。

---

### 統合の過程（採否）

**採用した論点（骨格）**
- D-02 の切り分け「今回失敗は epic 機構を通っていない」を最上位 framing に（結論の起点）。
- D-02/D-04 の「instrumentation ≠ robustification」を steelman 応答の骨格に。
- D-04 の SSOT マスターマップ＋3層割付を改善リストの構造骨格に。
- D-01 の invariant フレーム(I1〜I9)を機序の基礎に、D-04 G1＋D-01 IMP-1 の統合を高レバレッジ収束点に。
- D-03 の境界条件/トレードオフ(T1〜T4・#44783 検知不能・役割別 floor)をトレードオフ節に。

**退けた/留保した論点**
- **行数照合による捏造検知**(D-02 #2 が攻撃): 複数ファイル/要約/diff 報告で偽陽性量産 → 退け、**claimed ファイル集合 vs 実 git diff --name-only の集合照合＋証拠有無**に転化（偽陽性が原理的に出ない非対称化）。
- **文章手順でのゾンビ/捏造検知**(D-02 攻撃): 捏造中の親 LLM に検知させるのは自己参照でゾンビ化下に入る（parse-failure-hook すり抜けが先例）→ 退け、**決定論 hook / L0 外形照合**に統一。
- **捏造検知→自動リトライ**: CLAUDE.md「ブラインドリトライ禁止（2回で止める）」と衝突 → 「再実行1回まで＋no-op justified トークン」に制限。
- **D-03 の「矛盾解消(L1薄化)は他改善の前提条件＝先に L0 に寄せよ」**: Option A 寄りの強い主張だが、検証(R1/R3)を L0 に置けば「L1 の不信頼性継承」は回避できる(D-04) → 「前提条件」までは採らず**対立として保持**（未解決の対立#1）。
- **timeout ウォッチドッグ機構**(D-02: 本環境では LLM に自分をタイムアウトさせる決定論的時計が無く実装困難)→ 機構は見送り、**破壊的事前ゲート/題材制約**に置換。D-04/D-01 の「AWS timeout-block 定石」は破壊的操作の事前 bubble-up 部分のみ採用。
- **retrospector param 全写像の発明**: 無理な写像(=1 等)は retrospector 汎化を誤らせる新失敗(D-02) → 最小(PROJECT_MEMORY_DIR＋N/A 明示)を今、全写像 or 「Phase 3 で縮約 param/起動しない」は観測後。

（ラウンド1のため前回 position なし）

---

### 未解決の対立（潰さない）

**対立#1（設計根幹・#8）: L1 制御責務を「解消」するか「条件付き正当化」するか**
- **Option A（L0 直接統率＝純粋解消）**: L1 ランナーを廃し L0 が各 pir2 フェーズを直接駆動。CLAUDE.md 根拠(i)ループ counter SSOT・(iii)観測可能性を完全に満たす。第一原理では「本物の invariant を曲げず、深ネスト前提の方を疑うべき」(D-01)。D-03 も「後続の全信頼性改善を脆弱な L1 に置くと不信頼性を継承する」から解消を他改善の前提条件と位置づけ（A寄り）。**犠牲**: epic の価値提案「/pir2 を丸ごとネスト再利用」を壊し、L0 context が unit数×各pir2全フェーズで爆発。
- **Option B（L1 維持＋テレメトリで観測性補償＝条件付き正当化）**: L1 は「再帰オーケストレーション（sub-shell で /pir2 を回すのと同型）」で role-conflation とは別カテゴリ。CLAUDE.md epic 節が既に3階層を明示容認。experimental 段階は価値提案を壊す全面再設計より境界観測性(G1/O1/R1)を足す最小適応が合理的(D-04, D-02 条件付き正当化)。**犠牲**: L1 の自律性が未検証の信頼境界（L1 のループ状態報告が実体と乖離＝I1 再帰リスク）。
- **決着に要るもの**: L1 ランナーが本当に SKILL.md 全文を自律解釈してループ管理までオーケストレーションできるかの**実証**（context 空白・executions 0）。→ **統合推奨は「試験段階は Option B＋境界観測性を前提条件、恒久採用判断時に Option A へ寄せるか再評価」の時間軸付き。** ただし「そもそも先に L0 に寄せてから回すべき（A先行）」の立場(D-03)は棄却しきれず残す。

**対立#2: 並列 fan-out を試験段階で「既定 OFF（完全直列）」にするか「並列度≤2-3 の opt-in」で看板機能を維持するか**
- **既定 OFF 寄り**(D-03 最強): #44783 は親内から検知不能・上流で直らない。2並列でも1本ハングで詰む。∴ fan-out 既定 OFF（直列）が platform-safe な唯一解。並列性（epic の看板機能）を犠牲に安全を取る＝回避でなく前提受容。
- **並列度≤2-3 opt-in 寄り**(D-01 IMP-5 / D-04 R3): 初回は並列度1〜2 に絞る/直列化で代替可、並列題材なら watchdog 必須。看板機能を最小限検証しつつ露出を抑える。
- **共通合意**: 試験段階で「完全並列 fan-out をそのまま回す」は全員却下。争点は程度（完全 OFF か ≤2-3 か）。**決着に要るもの**: 初回題材が並列を含むか＋#44783 の Closed 後に workaround/フラグが出ていないか（要 Issue 追跡）。

**対立#3: 捏造裏取りを L0 集約すると context 爆発する（summary-up vs evidence-up）**
- **証拠アップ**: L0 に生証拠を集約すれば捏造を堅牢に捕捉するが、3層ネストで implementer の生 git-diff を2層バブルアップ → context が diff 規模×層数で膨張、深く大 diff で破綻(D-03 T1)。かつ L0 は L2 のファイル操作を直接見られず L1 のサマリしか持たない(D-03 段4)。
- **サマリアップ**: context 固定小だが事象X 型捏造を素通し。
- **部分的解消の見込み**: 決定論的 git 突合は**生 diff 本文を context に載せる必要がない**（L1 が claimed ファイル集合＝軽量リストを return、L0 が実 `git diff --name-only` と集合照合、O(1)、モデル判断ゼロ）(D-01 IMP-1)。これで T1 の緊張は「浅く小 diff」では回避可。**残る未解決**: ネスト層をまたぐ（L2 の操作を L0 が直接観測できない）ケースで、どの層が git 突合を担うか。境界は「ネスト深さ×diff 規模」。→ 各 pir2 が自分の implementer を発生源で git 突合（安いが担い手が脆弱 L1）vs L0 集約（堅牢だが context 膨張）のトレードオフが残る。

**対立#4（軽微）: resume/台帳の程度と timeout-block の実装可能性**
- 台帳 write: D-01 は「事象X の上流(I5)対策として今入れる」、D-04 は「初回単発なら不要、L2/L3 は見送り＋トリガ条件付き繰上げ」。→ 統合: **最小 per-node 台帳 write（O1 観測性と二重に効く）は今、full resume 機構は見送り**で吸収。
- timeout-block: D-04/D-01 は AWS 定石として整合、D-02 は本環境で実装困難。→ 統合: 破壊的操作の事前ゲート部分のみ今、決定論的 timeout ウォッチドッグ自体は見送り。

---

### 改善点 統合マスターリスト（rubric #2/#4/#5）

各 master 改善は4体が別名で呼んだ同一改善を名寄せ・重複排除した。(a)解決する問題 /(b)修正機序 /(c)トレードオフ /(d)SSOT関係 /(e)優先度3層。

| ID | 改善（名寄せ元） | (a) 解決する問題 | (b) 修正機序 | (c) トレードオフ | (d) SSOT 関係 | (e) 優先度 |
|----|---|---|---|---|---|---|
| **M1** | L1 境界テレメトリ return（D-04 G1 / D-01 IMP-6補償観測） | L0 が L1/サブの内部状態を境界で受け取れず black box → 事象X型フリーズを観測不能 | L1 が構造化テレメトリ（Phase到達・INNER/OUTER/REPLAN・VERDICT・claimed変更ファイル一覧・tool_uses）を return する規定。R1/R2/#8/C5 の共通入力 | self-report ゆえ正直さ保証なし（捏造は自己申告レイヤで起きる）→ M2 の独立検証必須。プラットフォームが return を切り詰めるリスク | **準拠復元**（CLAUDE.md 観測性根拠(iii)の境界回復） | **今直す必須** |
| **M2** | L0 決定論的境界検証: git 突合＋役割別 tool_use floor（D-01 IMP-1 / D-02 #1,#2 / D-03 事後ゾンビ・裏取り / D-04 R1,R2） | 事象X（捏造）＋事象Y（ゾンビ成功）。self-report を事実扱いすると捏造素通し | implementer 完了主張後、L0 が `git diff --name-only` 実集合と claimed 集合を照合（不一致/空→再実行1回、reviewer 起動せず）。サブ完了メタデータ(status/tool_uses/duration)を役割別 floor（explorer≥1 Read / implementer≥1 Edit / tester≥1 実行 / 推論系は0正常）と突合 | git 1本≈0コスト。**行数照合は退け集合照合/証拠有無に転化（偽陽性が原理的に出ない）**。正当 no-op は「no-op justified」トークンで回避。自動リトライ→「再実行1回まで」でブラインドリトライ禁止と非衝突。floor テーブルは SSOT 1枚増 | **新規（共通機構 pir2-protocol.md 本籍）**。pir2「reviewer が ground truth 照合」を前倒し・決定論化 | **今直す必須**（※hook 裏取り前提） |
| **M3** | epic-runs.md に Phase遷移＋timestamp＋現DAGノード（D-01 IMP-4 / D-04 O1 / D-03 per-nodeチェックポイント） | フリーズ位置を特定不能 → 19分迷走が再演、初回失敗すら診断不能＝学び0 | Phase遷移+timestamp+現ノード＋各エージェント境界で enter/exit ログ | 自明なログ、ほぼ無コスト | **新規（観測可能性）**。research/deepthink RUN_DIR 構造化ログに整合 | **今直す必須** |
| **M4** | ループ/サブタスク数 hard-cap（D-01 IMP-3 / D-02 #7 / D-04 L1配線+G4） | 無界ループ/サブタスク数 → スラッシング・組合せ爆発 | epic-planner がサブタスク数上限、Phase2 がネスト pir2 リトライ総数上限（per-unit retry と全体 replan の2軸）、DAG 全終端で停止。counter は L0 | 配線は低コスト。**上限「値」は0回実行で根拠なし＝要較正**。#44783 対策と紐づけない（上限≠デッドロック対策） | **継承**（deepthink hard-cap / pir2 max3）。epic だけ欠落 | 配線=**今** / 値較正=観測 |
| **M5** | 並列 fan-out の #44783 緩和（D-01 IMP-5 / D-02 #5 / D-03 fan-out OFF / D-04 R3） | 並列 Bash ハングが親を完全デッドロック（上流で直らない・親内から検知不能） | 試験段階は fan-out 既定 OFF or 明示 opt-in＋幅上限。並列サブに Bash を持たせない設計制約 | 並列スループット（看板機能）を犠牲。直列化で wall-clock max(T_i)→ΣT_i（例5分×3→5分→15分） | **新規（epic 並列固有）**。pir2async fan-out 慣習と接続 | 直列 stopgap=**今**【対立#2】/ watchdog機構=観測 |
| **M6** | L1 制御責務 vs CLAUDE.md 規定の解消/正当化（D-01 IMP-6 / D-02 #11 / D-03 対立仮説 / D-04 Step3） | L1 制御責務が CLAUDE.md 矛盾・loop counter SSOT/観測性破壊・捏造面増幅 | 【対立#1】Option A（L0直接統率）or Option B（L1維持＋テレメトリ条件付き正当化＋carve-out を CLAUDE.md に明記） | A=価値提案破壊＋L0 context 爆発 / B=未検証信頼境界 | **CLAUDE.md 規定に直接対峙**。逸脱は experimental.md 文書化、carve-out は意図的例外として retro ロールバック対象外 | **今判断必須**（設計根幹）【対立#1】 |
| **M7** | 破壊的変更の事前ゲート＋HITL timeout-block（D-01 IMP-7 / D-04 G3,R4） | 破壊的変更ゲートが事後承認化。ゲート無応答時に危険側へ進む | 破壊的操作は L0/ユーザーへ事前承認 bubble-up。ゲート timeout はブロック（自動続行しない） | 同期停止点で autonomy 減。additive-only 題材制約で代替可。**決定論的 timeout ウォッチドッグは本環境で実装困難(D-02)→見送り** | 破壊的事前ゲート=**継承**（pir2 USER_DECISION_REQUIRED）/ timeout-block=**新規**（AWS 定石・DEFERRED_USER_DECISIONS と整合） | 事前ゲート(or題材制約)=**今** / timeout閾値=観測 |
| **M8** | citation/SSOT 是正 C1-C7（D-01 IMP-8 / D-02 #10 / D-04 C1-C7） | 造語/誤記/虚偽が運用者の初回解釈を毒す・run dir が別パス・retrospector 起動失敗 | C1 inline造語是正 / C2 nested-explorer→pir2-explorer-nesting / C3 "運用実績あり"→executions0明記 / C4 sanitized_cwd登録＋cut -c1-40統一 / C5 PROJECT_MEMORY_DIR＋loop param / C6 docsコピー / C7 fan-out宣言テンプレ参照先 | 大半 doc/SSOT 低コスト。**「事象X/Y と無関係＝衛生」と明示して優先度混同を回避(D-02)**。retrospector 全写像は設計要 | **逸脱是正**(C1-C4)/ 継承 or 新規(C5-C7) | C1-C4・C5最小=**今**（衛生）/ C5全写像・C6・C7=観測or題材依存 |
| **M9** | resume/中断復帰（台帳永続化）（D-01 IMP-2 / D-02 #3 / D-03 checkpoint / D-04 L2,L3） | resume 時の認識論的真空→捏造（事象X の上流）。長時間フローの API 中断再開 | 各 unit 完了後に台帳追記（id/status/artifact path/git SHA）。resume 時は記憶再構成でなく git log＋台帳で照合復元。handoff.md は run-dir スコープ化（並列競合回避） | 台帳 write は安価。full 再構成は重い。handoff naive 継承は project 単一ファイルで並列衝突 | **継承**（continuation-gate/next-steps-queue/handoff）だが並列で run-dir 隔離の適応要 | 最小台帳write（M3と統合）=**今寄り**【対立#4】/ full resume=見送り（トリガ条件で繰上げ） |
| **M10** | DAG fan-in（合流）対応（D-02 #6 / D-03 tree-only / D-04 G2） | epic に fan-in 機構ゼロ（reviewer 既指摘）。合流ノードで衝突 | 試験段階は epic-planner をツリー型 DAG に制約 or 線形題材で回避。merge 実装は観測後 | 表現力を犠牲に機構コスト回避。逸脱時は明示 USER_DECISION | **新規**。初回は線形/tree 題材で回避可 | 題材制約=**今**（設計でなく運用回避）/ merge実装=観測 |
| **M11** | 共有ステート競合の保守直列化＋ランタイム検知（D-03 段7,シナリオ4 / D-04 O2） | 静的依存判定が共有書き込み（config/barrel/生成物）取りこぼし → lost update/merge conflict | 疑わしきは直列化（epic-planner が書込集合の重なり可能性を保守判定）。将来: worktree 分離＋ランタイム検知 | 並列度を犠牲に安全。ランタイム検知/worktree 分離は中〜高コスト | **新規**（epic-planner 静的直列化の補強） | 保守直列化=**今**（M5同方向）/ ランタイム検知・worktree=観測or見送り |
| **M12** | サブエージェント失敗回復パス（D-02暗黙 / D-03 シナリオ3 / D-04 L4） | サブ pir2 が部分完了で死→ DAG に半完成ノード、L0 が状態を持たない | per-node チェックポイント＋「reviewed 未達なら done 扱いしない」不変条件（M3/M9 と同一状態機構） | 状態機構コスト。初回の失敗モード分布を見てから継承範囲決定 | **継承**（pir2/pir2async 保持） | done判定の不変条件=**今寄り**/ full recovery=観測 |

**優先度3層サマリ（experimental=executions 0 に紐付け）**
- **【今直す必須】＝1回目を安全に回し・正しく観測・解釈できる最小集合（＝計器）**: M1, M2, M3, M4(配線), M5(直列stopgap), M6(判断), M7(事前ゲート/題材制約), M8(C1-C4/C5最小), M9(最小台帳), M10(題材制約), M11(保守直列化), M12(done不変条件)
- **【観測に回す】＝1回動かして値/形状を決める**: M4(上限値較正), M5(watchdog機構), M7(timeout閾値), M8(C5全写像), M10(fan-in merge), M11(ランタイム検知), M12(full recovery)
- **【試験段階として許容・見送り】**: M9(full resume/handoff スコープ化＝トリガ条件付き繰上げ), M8(C6 docsコピー), M11(worktree 分離), M7(決定論timeout ウォッチドッグ＝本環境実装困難), L3+ 深さ挙動・OpenTelemetry span（未到達/二次ソースのみ）

---

### 各 Phase / ネスト機構が壊れる機序（rubric #1）

| 段 | 破る不変条件(I) | 機序（どこで・なぜ・どう壊れるか） |
|---|---|---|
| **Phase 1（epic-planner 分割→DAG）** | I8, I6 | 「2サブタスクが同一ファイルに触るか」は実行せずに静的判定不能（一般に決定不能）→ 独立誤分類で並列 fan-out 競合(M11)。サブタスク数上限欠如で fan-out 無界(M4)。DAG ファンイン未対応で合流点未定義(M10)。※Phase 1.5 の実内容は D-01 が context 要約から推測（実 SKILL.md 未読）— 追加探索候補 |
| **Phase 1.5（分割確認ゲート）** | I9 | 唯一の同期ゲートで下流ユーザー判断は bubble-up するが、タイムアウト時安全側ブロック既定なし。破壊的変更が事後承認化(M7) |
| **Phase 2（DAG実行/ネスト pir2 起動）** | I7,I5,I6,I3,I4 | L1 ランナーが制御責務を持ち L0 がループ内部を観測不能(M6/M1)。複数ターン長時間フローなのに resume 状態外部化ゼロ＝事象X の構造的温床(M9)。ループ上限/全体リトライ概念なし(M4)。並列 fan-out の Bash ハングで #44783 デッドロック(M5)。サブ失敗回復パスなしで liveness が全サブ成功に依存(M12) |
| **Phase 3（retrospector 統合/永続化）** | I4,I5 | epic-runs.md に Phase/timestamp なくフリーズ位置特定不能(M3)。retrospector-prompt.md 必須 param（INNER/OUTER/REPLAN_COUNT）は単一 pir2 ループ前提、epic はループ非保持→写像未定義で起動失敗 or pattern registry 汚染(M8 C5)。docs/ コピー先欠落で人間可読成果物が gitignore に消える(M8 C6) |
| **citation/SSOT 層** | I5（参照整合） | 「inline フォールバック」は非在概念→深さバジェット超過時の挙動が未定義(landmine)。sanitized_cwd 未登録・`cut -c1-32`（SSOT は -c1-40）逸脱→ run-dir パスが静かに乖離しツール/オーケストレータが別 dir を見て observability と再構成が壊れる(M8 C1/C4) |

---

### rubric カバレッジ（自己申告）

| # | rubric 基準 | 充足/部分/未達 | 根拠（position のどこが答えているか） |
|---|---|---|---|
| 1 | フロー端から端まで分解、各段の失敗モードを**機序つき**で列挙 | **充足** | 「各 Phase が壊れる機序」表で Phase 1/1.5/2/3＋citation 層を各機序つき。※Phase 1.5 は実 SKILL.md 未読の推測ベース（追加探索に明記） |
| 2 | 改善点**5件以上**に (a)問題 (b)機序 (c)トレードオフ | **充足** | 統合マスターリスト M1-M12（12件）が各 a/b/c 明記 |
| 3 | 実観測失敗の**root cause**＋**ネスト全般の信頼性**改善 最低1つ | **充足** | 事象X=I5→I1→I2 連鎖（resume 真空穴埋め）/ 事象Y=ゾンビ成功、を root cause 言語化。信頼性改善 M2（捏造/ゾンビ検知）M5（親デッドロック）M1/M3（観測性）が対応。「今回失敗は epic 機構外」の切り分けも提供 |
| 4 | 既存 SSOT 照合、**整合/逸脱**明示・逸脱に理由 | **充足** | 各 master に (d) SSOT 関係（準拠復元/逸脱是正/新規/継承）。C1-C4 逸脱是正の理由付き |
| 5 | **優先度づけ**＋experimental 位置づけに紐づく判断根拠 | **充足** | 各 master に (e) 3層＋優先度サマリ。「計器 vs 較正待ち vs 過剰」で executions 0 に紐付け |
| 6 | トップ推奨への**最有力反論を steelman＋応答** | **充足** | 「試験実装に堅牢化は過剰、まず0回を1回動かせ」を steelman、instrumentation ≠ robustification のカテゴリ錯誤で応答。#8 の Option A 潜脱論も対立#1で steelman |
| 7 | 主要トレードオフが**具体**で最低2つ | **充足** | summary-up vs evidence-up（context膨張）/ 深さ vs 並列 vs デッドロック面 / ユーザーゲート集約 vs ゲート地獄 N×M / 静的直列化 vs 実行時検知 / 並列 max→Σ / 堅牢化が実験を食う自己矛盾 / (1-p)^N 完走確率劣化 |
| 8 | reviewer 既指摘の**設計根幹矛盾**（L1 制御責務 vs CLAUDE.md）に解消 or 正当化 | **充足** | M6＋対立#1 で Option A（純粋解消）/ Option B（条件付き正当化＋carve-out）を両論、CLAUDE.md 3根拠(i/ii/iii)を分解し「再帰オーケストレーション ≠ role-conflation」で部分正当化＋時間軸付き再評価を明示判断 |

> ℹ️ 8基準すべて **充足** と自己申告するが、根拠の**確度**は一様でない。#3/#8 は n=1・executions 0 に依存し「網羅性」でなく「機序の妥当性＋優先順位づけ」で充足を主張している点を gate は確認されたい。

---

### 確信度・前提・残課題

- **全体の確信度: 中〜高**
  - **高**: 「今回失敗は epic 機構を通っていない→epic 固有堅牢化は今回失敗を防がない」（context CONFIRMED 直結）。「self-report でなく決定論外形検証が要る／文章検知はゾンビ化下に入る」（parse-failure-hook 先例つき）。「#44783 は親内から検知不能→直列化が唯一解」。citation 是正(C1-C4)の SSOT 逸脱判定。継承項目(M4/M9/M12/M7事前ゲート)が pir2/deepthink に実在。
  - **中**: 「捏造＝resume 状態真空の穴埋め」因果（n=1・完全棄却不能。ただし M2 はこの因果に非依存で有効）。#8 の Option A/B 選択（L1 自律性が未実証）。(1-p)^N・N×M ゲート数・context 増加率など**数量は全て例示**（executions 0 で未実測）。
  - **低**: 失敗モードの網羅性（Epic 実行 0 回・epic 固有の未観測モードがありうる）。

- **依存している前提（崩れると結論が変わる）**
  1. サブの完了報告は claim であって ground truth ではない（この認識論的前提が崩れると全機構が無意味）。
  2. L1 が構造化テレメトリを return でき、プラットフォームが切り詰めない（崩れると M1 の観測性が届かず R3 watchdog が最後の砦）。
  3. SubagentStop/Stop hook で Agent メタデータ(tool_uses/status/duration)が決定論取得可能（崩れると M2 が文章手順に退化＝価値急落）。
  4. 初回題材を運用者が選べる（線形/additive-only）。崩れると M10 fan-in・M7 破壊的変更が題材制約で回避できず【観測】→【今】へ繰上げ。
  5. 事象X/Y が代表的失敗モード（n=1 サンプル、優先順位づけの確度 > 網羅の確度）。

- **残る不確実性 / 未解決の対立**
  - 対立#1（#8 Option A vs B）: L1 自律オーケストレーションの実証待ち。
  - 対立#2（fan-out 既定 OFF vs ≤2-3 opt-in）。
  - 対立#3（捏造裏取りの層配置＝summary-up vs evidence-up の残存トレードオフ）。
  - 対立#4（軽微・resume 程度／timeout-block 実装可能性）。
  - **事象X が epic の L1 ネスト pir2 内でも再発するか**は熟考では埋まらず、epic を1回動かした実行観測でしか埋まらない（steelman の核「epic を触っても直らない」が epic 内でも成り立つかの境界）。再発が確認されれば M2/M9 は epic 本体の必須要件に格上げ。

- **追加探索が要る論点（deliberator 集約・熟考では埋まらないもの含む）**
  1. **SubagentStop/Stop hook が Agent メタデータを決定論取得できるか**（M2 の優先度確定に直結・技術裏取り）。取得可→M2「今」確定、不可→文章手順に退化。
  2. **L1 ランナーの自律オーケストレーション実証**（#8 Option A/B の決着）。最小1 unit の epic dry-run で L1 return に Phase/loop count が載るか観測＝M1 実現可能性検証を兼ねる。
  3. **pir2 単発の実 duration 分布(P50/P99)**（timeout 誤殺境界の実閾値・過去 `.ai-pir-runs/` 集計で埋まる）。
  4. **#44783 の現在ステータス**（Closed 後の workaround/フラグ有無→fan-out 既定 OFF か opt-in 緩和かの判断材料）。
  5. **初回 epic 題材の shape**（線形か fan-in を含むか→M10/M7 の層確定）。
  6. **epic を1回完走させた実行トレース**（因果検証・L0 context 膨張率・epic 固有失敗モードの実測。※本熟考の結論は現材料で成立、確度向上のための任意探索）。
  7. **Phase 1.5 の実 SKILL.md 記述と epic-planner 静的依存判定アルゴリズム**（rubric #1 の Phase 1.5 分解を推測から実読へ精緻化）。
