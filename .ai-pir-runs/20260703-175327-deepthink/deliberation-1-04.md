## 熟考レポート（ROUND 1 / 04）: /epic＋ネスト多エージェント機構の信頼性改善点

### レンズ
既存SSOT整合＋優先度設計（この推論の軸）。各改善候補を pir2 references / deepthink hard-cap / CLAUDE.md 規定と照合し「準拠復元 / 逸脱是正 / 新規 / 継承」を判定し、pir2 に解法があるものは「epic が継承すれば済む」ことを明示。そのうえで全候補を優先度3層に割り付け、rubric #8 の設計根幹矛盾に SSOT の原文趣旨から答える。

---

### 思考の起点（前提の確認）

**context から確定的に言える事実（出典あり）**
- epic は experimental（executions 0）。前提は「過剰設計を避け、実験を回せる最小の堅牢性を優先」（context L10）。
- 事象X（フリーズ）root cause = CONFIRMED: resume 直後 implementer 完了報告の捏造 → 5 reviewer 全 FAIL → 19分迷走。parse-failure-continue-hook は整形式のため検知不能（context L8）。
- 事象Y（ゾンビ成功）= CONFIRMED: `status:completed` / `tool_uses:0` / 4.8秒。異常検知手順がどこにも無い（context L9）。
- epic が欠く仕組みの多くは pir2 references に実在（loop hard-cap / continuation-gate / next-steps-queue / handoff / サブ失敗回復）（context L29-32）。
- citation の穴: inline モード造語（L20）/ nested-explorer 誤記＋"運用実績あり"虚偽（L21）/ sanitized_cwd 未登録＋`cut -c1-32` 逸脱（L22-23）/ retrospector param 写像未定義＋PROJECT_MEMORY_DIR 欠落（L24）/ run-dir-base docs コピー無し（L25）/ fan-out-gate.md 転用不可（L26）。
- CLAUDE.md 規定（原文趣旨）: 制御フロー（起動・ループ管理・VERDICT集約・ユーザーゲート）をスキル本体に集約する根拠は **(i) ループカウンタの SSOT / (ii) サブはユーザー対話不可 / (iii) 観測可能性**。「サブからのネスト起動は read-only の探索（explorer）に限る」。一方 CLAUDE.md の epic 節自身が「3階層ネスト: epic本体 → ネスト pir2 ランナー → 各 pir2 配下の explorer/implementer/reviewer」を明記（＝L1→L2 の write ネストを epic 節が既に容認）。

**前提として置くもの（崩れると結論が変わる仮定）**
- epic の価値提案は「/pir2 を丸ごとネスト再利用する」点にある（L1 ランナーを消すと再利用性が失われる）。→ #8 の解消方針選択に効く。
- L1 ランナーが L0 へ構造化 return を返せる（Agent 戻り値でテレメトリを渡せる）。→ 観測性復元策の実現可能性の前提。
- 初回 epic の「題材」は運用者が選べる（線形/additive-only な題材を選定できる）。→ 一部の未対応（fan-in・破壊的変更）を「設計」でなく「初回題材の制約」で回避できるという前提。

---

### 段階的推論

#### Step 1: 全改善候補の SSOT 照合マスターマップ

各候補を「既存 SSOT との関係」で4分類する。**準拠復元**＝SSOT が既にあり epic がそれを外している/未継承（戻せば済む）。**逸脱是正**＝SSOT の明示規定に反する未文書化逸脱。**新規**＝SSOT に対応物が無い（epic or 共通機構で新設）。**継承**＝pir2/deepthink に解法が実在し epic は配線するだけ。

| ID | 改善候補 | SSOT 関係 | pir2 に解法? → 継承可否 | 機序(b)の要点 | コスト(c) |
|----|---------|-----------|------------------------|--------------|-----------|
| C1 | "inline モード/直接探索フォールバック"造語の是正 | **逸脱是正**（存在しない概念を参照） | pir2 に実在せず＝epic 固有の事実誤り。継承ではなく削除/実在概念へ差替 | 実行時に「fall back to inline」で未定義動作に落ちるのを防ぐ | doc 修正のみ（低） |
| C2 | `nested-explorer`→`pir2-explorer-nesting` 誤記是正 | **逸脱是正**（実験名誤記） | 既存実験 SSOT へ名寄せ | 観測ログの記録先実験を正す | doc 修正のみ（低） |
| C3 | "3階層で運用実績がある"→executions 0 明記 | **逸脱是正**（虚偽記述） | — | 運用者に「未実証」を正しく伝え初回判断を誤らせない | doc 修正のみ（低） |
| C4 | sanitized_cwd を consumer 表/verify script に登録＋`cut -c1-40` 統一 | **逸脱是正**（未文書化逸脱） | SSOT 実在・epic が10番目 consumer で未登録 | `-c1-32` は SSOT 逸脱で run dir が期待と別パスになりクロスツール前提が崩れる/将来 SSOT 正規表現変更を機械検証が見逃す | verify script SKILL_FILES + 表 + cut 1箇所（低） |
| C5 | retrospector に PROJECT_MEMORY_DIR 追加＋loop param 写像定義 | **逸脱是正＋新規写像** | retrospector-prompt.md 実在。epic はループ非保持で INNER/OUTER/REPLAN の写像未定義 | Phase 3 が起動失敗 or 無意味な param で走るのを防ぐ | 最小(PROJECT_MEMORY_DIR＋N/A 明示)は低 / 全写像設計は中 |
| C6 | 最終成果物を docs/&lt;kind&gt;/ に git 追跡コピー | **逸脱**（run-dir-base 未実装） | SSOT 実在。継承で足りる | 成果物が gitignore の .ai-pir-runs のみに残るのを是正 | 中（初回実験では必須でない） |
| C7 | 並列 fan-out 宣言テンプレの参照先を pir2 SKILL.md 7-2A に修正 | **新規用途＋部分再利用** | 宣言テンプレ本体は 7-2A に実在。fan-out-gate.md は reviewer5観点専用で転用不可 | 並列起動宣言が reviewer 専用形で malform するのを防ぐ | 中（初回に並列ステップがある場合のみ効く） |
| L1 | ループ hard-cap/収束条件 | **継承（pattern 準拠）** | deepthink hard-cap / pir2 max3 が SSOT。epic は DAG なので per-unit retry と全体 replan の2軸に写像が要る | 無限リトライ/文脈枯渇を止める | 上限値の較正は要観測（配線は低） |
| L2 | resume/中断復帰 | **継承（準拠）だが並列で衝突** | continuation-gate/next-steps-queue/handoff が実在 | 長時間フローの API 中断からの再開 | 中〜高（初回単発実行では不要な可能性） |
| L3 | handoff を run-dir スコープ化 | **逸脱是正**（並列衝突） | handoff.md はプロジェクト単一ファイル設計。run-dir-base の per-run 隔離を handoff に適用 | 並列ネスト pir2 の handoff.md 競合書込を防ぐ | 中（handoff/resume を使う場合のみ顕在） |
| L4 | サブエージェント失敗回復パス | **継承（準拠）** | pir2/pir2async が保持 | サブ FAIL 時のリカバリ | 中 |
| R1 | 捏造検知（事象X）＝claimed 変更 vs 実ファイル差分の突合 | **新規（共通機構）** | parse-failure-continue-hook は整形式を検知不可。継承では埋まらない | resume 直後の完了報告捏造を L0 が突合検知 | 中（hook or 検証ゲート新設） |
| R2 | ゾンビ成功検知（事象Y）＝tool_uses:0/極端に短い completed の異常判定 | **新規（共通機構）** | 手順がどこにも無い | サブの実質無作業 completed を検知 | 中（explorer.md/agent-delegation.md に手順追記＋L0 チェック） |
| R3 | 並列 fan-out の watchdog/直列化（#44783 デッドロック緩和） | **新規（epic 並列固有）** | — | 並列サブの Bash ハングが親を完全デッドロックさせるのを timeout で緩和 | 中（初回は並列度を絞る/直列化で代替可） |
| R4 | HITL タイムアウト時ブロック（安全側） | **新規（escalation SSOT と整合）** | DEFERRED_USER_DECISIONS は escalation 構造として整合。timeout-block 相当のみ欠落 | ゲート無応答時に危険側に進まない | 低〜中 |
| O1 | epic-runs.md に Phase/timestamp 追加 | **新規（観測可能性）** | — | フリーズ時「どこで止まったか」を特定可能に | 低 |
| O2 | 共有ステート競合のランタイム検知 | **新規** | — | epic-planner の静的直列化の検知漏れに実行時セーフティネット | 中〜高 |
| G1 | L1 境界での構造化テレメトリ return（Phase/loop count/VERDICT/tool_uses） | **準拠復元**（CLAUDE.md 観測性根拠(iii) の回復） | — | L0 が L1 の内部進捗を観測・突合できる基盤。#8 観測性・R1/R2 検知入力・C5 retro param の**共通入力**になる | 低〜中（return フォーマット規定） |
| G2 | DAG fan-in（合流）対応 | **新規** | — | 合流ノードの入力集約 | 中〜高（初回は線形題材で回避可） |
| G3 | 破壊的変更の事前ゲート化 | **継承（準拠）** | pir2 の USER_DECISION_REQUIRED ゲートが実在 | 事後承認で破壊が先行するのを防ぐ | 低（or additive-only 題材制約で代替） |
| G4 | subtask 数の上限 | **継承（deepthink hard-cap 準拠）** | deepthink のハードキャップが SSOT | runaway fan-out/組合せ爆発を止める | 低 |

> ℹ️ **車輪の再発明を避ける（本レンズの核）**: L1/L2/L4/G3/G4 は pir2/deepthink に解法が実在する。epic の正しい改善は「新設計」でなく「既存 SSOT を継承・配線する」こと。ただし L2/L3 は naive 継承だと handoff の project 単一ファイル設計が並列ネストで衝突するため、run-dir-base の per-run 隔離を重ねる適応が要る（＝継承にも適応コストがある）。

#### Step 2: 高レバレッジ収束点 — G1（L1 テレメトリ return）が3つを同時に満たす

**推論**: 事象X（捏造検知 R1）・事象Y（ゾンビ検知 R2）・#8 観測性・C5 retro param（epic は loop 非保持で何を渡すか未定義）は、一見バラバラだが**すべて「L0 が L1 の内部状態を境界で受け取れない」ことに起因**する。1つの機構＝**L1 が構造化テレメトリ（各 unit の Phase 到達・INNER/OUTER/REPLAN カウント・VERDICT・claimed 変更ファイル一覧・tool_uses）を return する規定**を置けば、
- R1: L0 が「claimed 変更ファイル」を実 diff と突合 → 捏造検知
- R2: L0 が tool_uses:0/極短 completed を異常判定 → ゾンビ検知
- #8: L0 が loop count/Phase を観測 → CLAUDE.md 根拠(iii)観測性を境界で回復
- C5: 集約した INNER/OUTER/REPLAN を retrospector にそのまま渡す → SSOT param を epic モードで満たす

自己点検（飛躍はないか）: 前提は「L1 が return にこれを載せられる」こと。Agent 戻り値は自由記述テキストなので技術的には可能。ただし「L1 が正直に自己申告する」保証は無い（捏造は自己申告レイヤで起きる）。よって R1 だけは self-report では不十分で、**L0 側の独立検証（git diff 突合）が必須**。この点は G1 単独では埋まらず R1 の L0 突合を別途要する。→ G1 は「観測の配管」、R1 の突合は「配管上の検証」で分離。

#### Step 3: rubric #8 への正面回答（L1 制御責務 vs CLAUDE.md 規定）

**規定の原文趣旨の分解**: CLAUDE.md が制御をスキル本体に集約する根拠は3つ ―― (i) ループカウンタ SSOT、(ii) サブはユーザー対話不可、(iii) 観測可能性。禁止の主対象は文面上「planner 等の**専門サブ**が制御を兼務すること（役割兼務／role-conflation）」。

**epic の実態との照合**:
- (ii) サブは対話不可 → epic は DEFERRED_USER_DECISIONS で L0 に bubble-up。**この点は SSOT 準拠**（違反していない）。
- (i) ループ SSOT → 各ネスト pir2 は自スコープに隔離された loop を持ち、L0 は関知しない。スコープ内では L1 が SSOT。**per-scope では衝突なし**だが、L0 が loop を観測できない＝(iii)と地続きで劣化。
- (iii) 観測可能性 → epic-runs.md に Phase/timestamp が無く（O1）、L1 は black box。**事象X はこの劣化の実証**（フリーズ箇所を特定できず19分迷走）。**epic は(iii)を実務上侵害している**。
- さらに「ネスト起動は read-only explorer に限る」条項 vs epic 節の「L1→L2 で implementer/reviewer を write ネスト容認」→ **CLAUDE.md 内部に条項間テンション**が既に存在する。

**判定（明示的判断）: 部分正当化＋条件付き。**
1. **正当化できる部分**: L1 は「専門サブが制御を兼務する role-conflation」ではなく「自スコープを丸ごと統率する**再帰オーケストレーション**（ネスト /pir2 インスタンス）」。人間が sub-shell で /pir2 を回すのと同型で、規定の主対象（役割兼務）とは別カテゴリ。かつ CLAUDE.md epic 節が既に3階層を明示容認しているため、**アーキテクチャそのものは原理的に正当化可能**。
2. **正当化が成立する条件（＝今直す必須）**: ただし正当化は根拠(i)(iii)を境界で保全して初めて有効。**G1（L1→L0 テレメトリ return）＋O1（Phase/timestamp）＋R3（L0 watchdog）** が無い現状は「逸脱」ではなく「経験的に破綻済み」（事象X が証拠）。よって #8 は「思想として正当化、ただし境界観測性の実装を前提条件として付す」。
3. **SSOT ドリフト対策**: 再帰オーケストレーションと role-conflation を区別する **carve-out を CLAUDE.md に明記**する（epic 節は3階層を容認するが、一般 PIR² 規則の「read-only explorer のみ」条項との関係を1文で調停）。CLAUDE.md には既に「外部事実変化に追従する CORE 事実訂正はロールバック対象外」の前例があり、この carve-out も同型の意図的例外として retrospector にロールバックさせない。

**代替（純粋解消案）も明示**: L1 ランナーを廃し、L0（epic 本体）が各 pir2 フェーズ（explorer→planner→implementer→reviewer）を直接オーケストレーションする再設計。(i)(iii)を完全に満たすが、**epic の価値提案（/pir2 丸ごと再利用）を壊し、L0 の文脈が unit数×各 pir2 全フェーズで爆発する**（トレードオフ: 観測性を得て文脈効率とコード再利用を失う）。experimental 段階では「価値提案を壊す全面再設計」より「境界観測性を足す最小適応」が合理的 → **推奨は Option B（条件付き正当化）**。

#### Step 4: 優先度3層への割付（experimental=executions 0 に紐づけ）

割付原理: 初回1回を「安全に回し・正しく観測・正しく解釈できる」ために不可欠なものだけを【今直す必須】に置く。値・形状が実観測なしに決められないものは【観測に回す】。production 級堅牢化・到達しない領域は【見送り】。

**【今直す必須】＝1回目を安全に回し観測可能にする最小集合**

| ID | 理由（experimental 位置づけへの紐付け） |
|----|------|
| G1 | 境界テレメトリ。これが無いと L1 は black box で、事象X 型のフリーズを**観測できない＝1回目から学びが0**。#8 の正当化前提でもある。最高レバレッジ（R1/R2/C5 の共通入力） |
| O1 | Phase/timestamp。「どこで止まったか」を特定できないと 19分迷走が再演し、初回の失敗すら診断不能 |
| R1 | 捏造検知（L0 の git diff 突合）。事象X の直接原因。検知が無いと「実装が存在しないのに完了」を掴めず全 reviewer FAIL 連鎖 |
| R2 | ゾンビ成功検知。事象Y の直接原因。cheap（異常閾値チェック）で初回の無作業 completed を掴む |
| C1/C3 | 造語是正・"運用実績あり"→executions0 明記。**運用者の初回解釈を毒する**虚偽/未定義参照。doc 修正のみで高誤導リスクを消す |
| C4 | sanitized_cwd の `cut -c1-40` 統一。`-c1-32` は run dir を期待と別パスにし、クロスツール前提を初回から壊す |
| C5(最小) | retrospector に PROJECT_MEMORY_DIR 追加＋loop param を明示 N/A。Phase 3 起動失敗を防ぐ最小限 |
| R3 | 並列 fan-out に watchdog/timeout（#44783）。**初回は並列度を1〜2 に絞る or 直列化**で代替可。並列題材なら必須 |
| G3/G4 | 破壊的変更の事前ゲート（or additive-only 題材制約）＋subtask 上限。pir2/deepthink から**継承するだけ**で cheap。runaway と不可逆破壊を防ぐ安全弁 |
| C2 | nested-explorer 誤記是正。観測ログの記録先実験を正す（cheap） |

**【観測に回す】＝1回動かしてから値/形状を決めるべきもの**

| ID | 理由 |
|----|------|
| L1 | ループ hard-cap の**上限値**は epic の分割安定性・スループットを1回観測しないと較正できない。配線パターンは継承済みだが値は要実測 |
| C5(全写像) | retro param の epic モード全設計は「epic が実際にどんな loop 集合を持つか」を観測後に確定 |
| G2 | DAG fan-in。初回は線形/tree 題材で**回避**し、合流の実頻度を見てから実装判断 |
| R4 | HITL timeout-block の閾値は実ゲート頻度を観測後 |
| O2 | 共有ステート競合ランタイム検知。epic-planner 静的直列化の検知漏れ実頻度を観測後に投資判断 |
| L4 | サブ失敗回復パス。初回の失敗モード分布を見てから継承範囲を決める |

**【試験段階として許容・見送り】＝experimental には過剰 or 未到達**

| ID | 理由 |
|----|------|
| L2 | resume/中断復帰。初回は単発実行で観測する想定 → production 級堅牢化。ただし**トリガ条件**（初回フローが API 中断を跨ぐ長さになる）を満たしたら観測層へ繰上げ |
| L3 | handoff の run-dir スコープ化。resume/handoff を初回で行使しない限り顕在化しない（L2 と連動） |
| C6 | docs/ git 追跡コピー。experimental 成果物は .ai-pir-runs 隔離で足りる。nice-to-have |
| — | L3+ 深さ挙動・OpenTelemetry span 等。epic は L0-L2 で未到達 / 二次ソースのみ |

---

### 反証・対立仮説の検討

**最も強い反論（rubric #6 の steelman）: 「試験実装に堅牢化は過剰。まず executions 0 を 1 回動かせ。観測性も捏造検知も production の贅肉だ」**

steelman: MAST 論文が言うのは「失敗の 41.8% は設計問題」であって「設計を先に全部固めろ」ではない。experimental の目的はまさに未知の失敗モードを**実地で発見**すること。先回りで堅牢化すると、起きもしない失敗に投資し、実際の失敗モードを塞いで観測機会を潰す。resume/fan-in/durable execution を今作るのは典型的過剰設計。

応答: この反論は**大半について正しく、私はそれを受け入れて【見送り】層に置いた**（resume/L3/fan-in/O2/docs コピー）。しかし反論は【今直す必須】層に対しては**カテゴリ錯誤**を犯している ―― そこにあるのは「堅牢化（robustness）」ではなく「**測定装置（observability/measurement correctness）**」である。executions 0 の唯一の狙いは run 1 から学ぶこと。ところが事象X は「フリーズ箇所を特定できず19分迷走・手動復帰」で**学び 0** を実証した。black box を1回走らせても、観測できない失敗は診断できず、次の設計判断に使えない。さらに C3 の "運用実績あり" 虚偽は運用者の初回解釈そのものを毒する。つまり「まず1回動かせ」を**成立させる前提条件**が G1/O1/R1/R2/citation 是正であって、これらは贅肉でなく実験の測定系。加えて【今直す必須】の多くは新設計でなく **pir2/deepthink からの継承＋doc 修正**（G3/G4 は継承、C1-C4 は doc）で、コストは実験速度をほぼ削らない。よってトップ推奨（測定系だけ先に入れて即回す）は反論に耐える。

**対立仮説: 「#8 は正当化でなく解消（L1 廃止・L0 直接統率）すべき。境界テレメトリで観測性を『取り繕う』のは、CLAUDE.md がまさに禁じた『サブに制御を持たせる』の潜脱だ」**

これが正しいとしたら: L1 が return するテレメトリは**自己申告**であり、L1 がハング/捏造した瞬間にテレメトリ自体が届かない or 嘘になる。観測性の根拠(iii)は「制御を持つ本体が同一 context で観測する」ことで担保されていたのであって、black box の事後 return では担保されない。事象X はまさに「サブの自己申告を信じた」失敗。

棄却/修正: 部分的に妥当で、私の R1（L0 の独立 git diff 突合）と R3（watchdog）はこの批判への応答として**自己申告に依存しない外形検証**を別立てしている（Step 2 の自己点検で既に「G1 単独では R1 を埋められない」と留保済み）。つまりテレメトリ（G1）＝正常時の観測配管、突合＋watchdog（R1/R3）＝異常時の外形検知、の二層。ただしこの対立仮説は「Option A（L0 直接統率）の方が構造的に堅い」ことを正しく突いており、**私の推奨は『experimental 段階では Option B、恒久採用判断時に Option A へ寄せるか再評価』という時間軸付き**に修正すべき。完全な棄却はできない ―― これは #8 の残る不確実性。

---

### 二次・三次の含意と境界条件

**含意**
- G1（テレメトリ return）を「Agent 戻り値の構造化スキーマ」として一度定義すると、epic だけでなく **pir2async のチーム集約・将来のネスト系全般で再利用可能な共通 SSOT** になる。改善が epic 局所に留まらず共通機構に還元される（context L8 の「pir2/共通機構への波及可」と整合）。
- 「初回題材を線形・additive-only に制約する」という運用的回避（G2/G3 を設計でなく題材選定で回避）は、**設計改善を観測データが出るまで遅延させつつ安全に1回回す**という experimental に最適な手。SSOT を増やさず experimental を進める。

**境界（結論が崩れる条件）**
- 前提「L1 が return にテレメトリを載せられる」が崩れる（プラットフォームが構造化 return を切り詰める/L1 がハングして return 自体が来ない）と、G1 の観測性は届かず R3 watchdog だけが最後の砦になる。→ R3 の優先度は G1 に連動して上がる。
- 前提「初回題材を運用者が選べる」が崩れる（epic を任意タスクに即適用する運用）と、G2 fan-in・G3 破壊的変更を題材制約で回避できず、これらが【観測】→【今直す】へ繰上がる。
- #8 の正当化は「再帰オーケストレーション ≠ role-conflation」という解釈に依存。もし CLAUDE.md 改訂で「ネストされた本体も本体の制御を L0 が保持せよ」と明確化されたら、Option B は逸脱に転落し Option A（再設計）が強制される。

---

### rubric への寄与（現時点）

| rubric 基準 | 寄与/未達 | 根拠 |
|---|---|---|
| #4（既存 SSOT 整合・準拠/逸脱明示） | **寄与（強）** | Step1 マスターマップで全21候補を準拠復元/逸脱是正/新規/継承に分類し、逸脱に理由を付した。本レンズの主担当 |
| #5（優先度づけ・experimental 紐付け） | **寄与（強）** | Step4 で3層に割付、各層を executions 0 の「測定系 vs 較正待ち vs 過剰」に紐付け |
| #8（L1 制御責務の矛盾） | **寄与（強）** | Step3 で CLAUDE.md 3根拠を分解し、部分正当化＋条件付き＋carve-out＋代替 Option A を明示判断 |
| #2（改善5件以上・a/b/c） | **部分** | 21件を SSOT 関係＋機序(b)＋コスト(c)付きで表化。解決する問題(a)は各行に含むが、機序の深掘りは機序レンズ担当と分業 |
| #6（steelman＋応答） | **寄与** | 「まず1回動かせ」を steelman し、測定系 vs 堅牢化のカテゴリ錯誤で応答。対立仮説（Option A 潜脱論）も steelman |
| #7（トレードオフ具体） | **部分** | Option A の文脈爆発 vs 観測性、handoff naive 継承の並列衝突、ユーザーゲート集約 vs 並列スループット劣化を具体で提示 |
| #1/#3（各段の機序・root cause） | **参照のみ** | 事象X/Y の root cause は context 既出を前提に使用。機序の一次分解は他レンズ主担当 |

---

### 事実と推測の仕分け

**事実（context に出典あり）**
- 事象X/Y の root cause、parse-failure-continue-hook の整形式検知不能、pir2 references に該当機構が実在、citation の各穴（造語/誤記/虚偽/cut逸脱/param未定義/docs無し/fan-out-gate転用不可）、CLAUDE.md epic 節が3階層を容認、#44783、AWS の timeout-block 定石。

**推論（deliberator の解釈）**
- 各候補の「準拠復元/逸脱是正/新規/継承」への分類（SSOT 原文の照合に基づく私の判定）。
- G1 テレメトリが R1/R2/C5/#8 の共通入力になるという収束の指摘。
- #8 を「role-conflation ≠ 再帰オーケストレーション」で部分正当化する解釈（CLAUDE.md の禁止主対象の読み）。
- 3層への割付と「測定系 vs 堅牢化」のカテゴリ区分。
- 「初回題材を線形/additive-only に制約して fan-in/破壊的変更を設計でなく運用で回避」という手。
- Option B 推奨に「恒久採用時は Option A へ再評価」の時間軸を付す修正。

---

### 現時点の確信度と残る不確実性

- **確信度: 中〜高**。
  - 高い部分: citation 是正（C1-C4）の SSOT 逸脱判定と【今直す必須】割付（doc/verify の突き合わせで機械的に確定でき、コストも低い）。継承項目（L1/L4/G3/G4）が pir2/deepthink に実在する点。G1 が複数問題の共通入力になる収束。
  - 中程度の部分: #8 の「部分正当化」。role-conflation と再帰オーケストレーションの区別は CLAUDE.md 原文の**解釈**であり、原文が明示的にこの区別を書いているわけではない。運用者/synthesizer が「解消（Option A）を採るべき」と判断する余地は残る。
- **残る不確実性**:
  - L1 ランナーが本当に SKILL.md 全文を自律解釈してオーケストレーションできるか未実証（context L49）。できないなら #8 は「正当化以前に機能しない」→ Option A 強制。
  - テレメトリ return がプラットフォームで切り詰められないか（G1 実現可能性）。
  - 初回題材の shape（線形か fan-in を含むか）が未定 → G2/G3 の層が動く。

---

### 追加探索が必要な論点

- **L1 ランナーの自律オーケストレーション実証**: ネスト /pir2 ランナー（general-purpose, model=opus 前提）が SKILL.md 全文を解釈してループ管理まで自律実行できるか。これが否なら #8 は Option A 強制になり優先度地図が変わる。**確かめ方**: 最小1 unit の epic を dry-run し、L1 の return に Phase 到達・loop count が載るか観測（＝G1 の実現可能性検証を兼ねる）。
- **Agent 戻り値の構造化許容量**: L1→L0 の return がプラットフォームで truncate されないか。**確かめ方**: 実測 return の長さ上限を1回のネスト実行で確認。
- **初回 epic 題材の shape**: 線形 chain か fan-in を含むか。**確かめ方**: 運用者に初回題材候補を1つ挙げてもらい DAG を epic-planner に描かせて fan-in ノードの有無を確認（G2/G3 の層確定に必要）。
