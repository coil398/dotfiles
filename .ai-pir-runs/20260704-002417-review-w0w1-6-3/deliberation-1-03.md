## 熟考レポート（ROUND 1 / 03）: W0+W1（6-3 決定論的完了検証）の採用可否 ― 二次波及・境界条件レンズ

### レンズ
**二次波及・境界条件**（この推論の軸）。「捏造していない大多数の run に 6-3 が何をするか」「どの境界で honest run が誤爆/素通りするか」「無条件本採用の非対称が将来どこへ波及するか」「(A) 最小スコープの境界に何が漏れるか」を、事故方向（fail-closed=偽 PHANTOM / fail-open=見逃し）つきで追う。

---

### 思考の起点（前提の確認）

**context から確定的に言える事実（出典つき）**
- 6-3 は pre-set（implementer 起動**前**）と post-set/照合（完了**後**）に**時間分割**された2段トランザクション（exp-01 §pre-set/post-set, ref 全文 L72–192）。
- PHANTOM 判定は `claimed-trackable - post`、UNDECLARED は `delta - claimed`。**PHANTOM は delta でなく post を使う**（ref L182–191, 判定表 L200–201）。
- staged 変更は実集合に含めない（`diff`=unstaged＋`ls-files --others`=untracked のみ。ref L59, L84–86）。exp-03 が staged / case-only-rename の偽陽性2件を実機発見（context L13–14）。
- 非対称: PHANTOM のみ hard fail、UNDECLARED は warn 非ブロッキング（context L208, 判定表）。
- `experimental.md` に 6-3 エントリは**不在**（全文検索確認）。同日 epic は Active 実験（context L15）。
- FP 実発生頻度・L0 が毎回 bash を正しく走らせるかは**未測定**（context L33–34）。
- 環境は macOS/APFS（env=darwin）＝case-insensitive FS が既定。**本セッションの git status 開始時点で `experimental.md` 等が既に `M`（pre-existing dirty）**。

**前提として置くもの（崩れると結論が変わる）**
- 実 run 母数は個人ワークフロー規模（epic executions=0、pir2 は散発）＝アラート学習に必要な反復頻度は低い。この前提が崩れて（epic が多数のネスト pir2 を駆動する等で）run 母数が跳ねると、後述のアラート疲労閾値が実際に噛む。
- INNER_LOOP_COUNT（reviewer FAIL ループ上限3）は SKILL の記述どおり 7-4 でも機能する。

---

### 段階的推論

#### 段①: 「毎回の負担」の実体はレイテンシでなく手順分割による L0 脱落面
- **飛躍の点検**: 「毎回 bash を走らせる負担」を計算コストと読むと誤る。bash 自体（`diff --name-only`/`ls-files`/`sort`/`comm`/`awk`）は sub-second。`check-ignore` は claimed 1件ごとに git サブプロセスだが、通常 2–10 件で <1s、大量 codegen（200件）でも数秒。→ **レイテンシは実質ゼロコスト（赤ニシン）**。
- **真のコストは手順分割**: pre-set は 6-1（implementer 起動前）、post-set は 6-3（完了後）で、間に subagent 1体分の実行（数分）が挟まる。L0 は「pre-set を記録した」という状態を跨いで保持せねばならない。pre-set 記録を L0 が飛ばすと、post-set の手順0が `ERROR: pre-set 未記録` を出し、設計は **「6-1 に戻り pre-set 再記録 → implementer を再実行」** を指示（ref L94–96, L194）。
- **二次効果（重要）**: 捏造していない honest run で、L0 が単に bookkeeping 1手順を忘れただけで **implementer フル再実行** が強制される。しかも「L0 が prose 指示の手順を飛ばす」ことは、まさに事象X が実証した L0 の不信頼そのもの。**6-3 は、L0 が不信頼だと示された当のこと（手順を確実に実行）に、6-3 自身の前提（pre-set 記録）を依存させている**。分割トランザクションは L0 脱落の露出面を2倍にする（論点A を境界側から補強）。

#### 段②: honest run が hard fail する境界の全列挙（事故方向つき）
context の2件に加え、bash ロジックから新規に3件を導出する。

| # | 境界（honest なのに） | 機序 | 事故方向 | 再実行で直るか | 頻度（推論） |
|---|---|---|---|---|---|
| 1 | **staged 変更** | `git add` 済み→`diff`(unstaged)にも`ls-files --others`にも出ず post に不在→`claimed-trackable - post`=PHANTOM | fail-closed（偽 PHANTOM） | 直らない→user gate | 低（implementer.md に git add 禁止0件だが実務では稀）|
| 2 | **case-only rename**（APFS） | 大小のみ rename は git の全シグナル空→post 不在→PHANTOM | fail-closed | 直らない→user gate | 稀（だが環境が APFS 既定）|
| 3 | **net-zero 編集（HEAD へ revert）** [新規] | claimed ファイルを編集した結果 HEAD と一致→`git diff` 空→post 不在→PHANTOM | fail-closed | 直りにくい | 稀 |
| 4 | **symlink パス形の不一致** [新規] | dotfiles の `~/.claude`→`.claude` symlink 等で、implementer が `~/...` 形で申告→3b が untrackable 分類→**PHANTOM 免除だが検証もされない** | fail-open（見逃し側に倒れる）| ― | dotfiles 自己改変 run で常態 |
| 5 | **resume 中の外部 git 状態変化** [新規・最重要] | pre.list 記録後〜post-set 前に中断→resume 間に user が commit/stash→working tree clean→post 空→claimed 全件が PHANTOM | fail-closed | 直りにくい→user gate | resume run で顕在 |

- **段①との接続**: #5 は **事象X と同一クラス（resume）** で発火する。6-3 は「resume 時の捏造→迷走」を断つために作られたのに、6-3 自身の baseline 健全性が最も脆いのが resume。pre.list は「pre〜post 間の working tree 変化は implementer だけが起こす」と暗黙前提する。resume を跨いだ commit/stash/checkout はこの前提を破り偽 PHANTOM を製造する。ただし**方向は fail-closed（偽警報）で degrade は graceful**（見逃しではない）。

#### 段③: post-vs-delta の選択が生む fail-open ―「pre-existing dirty への虚偽申告」[新規・rubric#1 直撃]
- PHANTOM が delta でなく **post** を使うのは「起動時点で既に dirty なファイルを implementer が更に編集しても偽 PHANTOM にしない」ため（context L89, 設計意図として正当）。
- だがその裏コスト: **pre-set 時点で既に dirty だったファイル F を implementer が「変更した」と申告し、実際は一切触っていない場合**を追う:
  - pre.list ∋ F（既 M）。implementer は F を申告のみ・未編集。
  - post.list ∋ F（pre-existing dirt が残存）。
  - PHANTOM = `claimed-trackable - post` = {F} − {F,…} = **空 → PASS（fail-open=捏造見逃し）**。
  - delta = `post - pre` は F を除外→ UNDECLARED も F に無反応。**F は両検査に完全不可視**。
- **二次波及**: これは staged FP（fail-closed）の**鏡像 FN（fail-open）**で、両方とも post-vs-delta 選択に由来する双子。しかも **本セッションは開始時に4ファイルが既 `M`**（git status）。「クリーンツリーで走る」メンタルモデルと違い、**活発な dev セッション中の run では、pre-existing dirty 集合のぶんだけ捏造見逃し面が開く**。6-3 の実運用カバレッジは "clean tree" 想定より狭い。設計の「fail-open な事故計器」宣言と整合はするが、**残存限界として明示されていない**（ref の残存限界は git 検証不能・submodule・入れ子フェンスに集中し、pre-existing-dirty FN は未記載）。

#### 段④: アラート疲労の閾値 ― base rate との相対で見る
- 機序: honest run で PHANTOM が誤爆（段②の #1/#2/#3/#5）→ user が調べ「staged/case-rename/何もない」と分かる → 「PHANTOM=本物」の事前確率が減衰 → k 回後に (B)「承知で reviewer へ」を**無調査で常用** → ゲートは Verification Theatre 化（本物の捏造も (B) 素通り）。
- **閾値は PPV = p_fab / (p_fab + p_fp)**。事象X が示すとおり真捏造 p_fab は**極めて低い**（特定の resume+圧力条件でのみ発火、run の 1% 未満オーダー）。段②の FP は絶対値は低いが、**検出対象がそれ以上に稀**なため、低 FP でも PPV を割る。0.1% base rate の事象を検出するなら FP<0.1% が要る ― staged/case-rename/pre-existing 未閉塞では届かない。**「稀な FP」が危険なのは、標的がもっと稀だから**。
- **現設計の防御と限界**: 非対称（PHANTOM のみ hard fail・UNDECLARED は warn）は**優れたアラート疲労緩和**。頻出事象（formatter/codegen 副産物）を warn 側に隔離し hard fail チャネルの PPV を保つ。だが**この非対称は PHANTOM チャネル自身の FP は守らない**。段②の hard-fail FP はまさに PHANTOM チャネルに着弾する。→ 疲労リスクは未閉塞 FP 集合に集中する。

#### 段⑤: (A) 最小スコープの境界 ― 圧力の高い点を外している
- (A) は初回実装点（6-1）のみ。7-4（reviewer FAIL 後再実装）・8-2（tester FAIL 後）は無検証（context L10, ref L48–49）。
- **境界の逆説**: 捏造の生成機序は「詰まった時に進捗を見せる圧力」で、これは**再実装点（FAIL を告げられ「直せ」と言われる）で最も強い**。6-3 は**圧力最小の点（初回）をカバーし、圧力最大の点（再実装）を外す**。事象X の実インシデントは初回点（新規ファイル作成）で起きたので (A) は観測事例を捕捉するが、捏造の生成的高リスク文脈は外す。
- **INNER_LOOP がどこまで代替網か（定量）**: 7-4 で implementer が捏造 fix→reviewer 再起動（5体・高コスト）→ 偽 fix なので再 FAIL → INNER_LOOP 消費 → 3回で user gate。**INNER_LOOP は最終的に捏造を止めるが、6-3 が回避したかった当のコスト（reviewer 5体 × 最大3ループ）を払ってから**。失われる価値=「早期・安価検知」で、7-4 捏造では最大3ラウンド分の reviewer 起動が無駄になる。**つまり (A) の穴は「捏造が見逃される」ではなく「安価にでなく高価に検知される」**。

---

### 反証・対立仮説の検討

**最強の反論①: 「アラート疲労は低 run 母数では発火しない。閾値論は構造的に正しくても実際には噛まない」**
- steelman: 疲労は**反復量**で (B)-反射を条件づける。個人ワークフローで週数回の pir2 なら 3% FP でも数週に1回＝毎回 fresh に調査される。PPV が低くても**絶対警報頻度が低いので疲労は潜在に留まる**。
- 判定: **正しい。ただし条件つき**。疲労は現母数では顕在化しにくい。しかし (1) fail-closed 偽警報は「調査コスト＋再実行」を毎回課す（疲労以前に直接コスト）、(2) run 母数が epic 採用でスケールした瞬間に潜在リスクが噛む。**結論修正**: 「must-fix」の緊急度は**期待 run 母数に連動**し、それは epic 採用（実験・0回）に連動する ⇒ staged 閉塞の緊急度は**絶対でなく将来条件つき**。今は「煩わしいが生存可能」、スケール時に「ゲート生存性クリティカル」に昇格する。

**最強の反論②: 「6-3 は既存ハードルール（CLAUDE.md 捏造禁止）の機械化であって新規実験ではない。experimental.md 追跡は novel 機構（shards/epic）用で、6-3 の価値は自明。だから本採用でよい」**
- steelman: 追跡すべきは「これは役に立つか？」が未証の機構。6-3 の価値（捏造の上にレビューを積まない）は疑問の余地なし。問うべきは「FP 税はいくらか」＝運用チューニング問題で、実験生存性問題ではない。→ 本採用＋チューニング backlog が正しい filing。
- 判定: **framing としては妥当だが、行き着く先は同じ安価アクション**。価値が自明でも **FP コストは未測定**（context L33）。無条件本採用で experimental エントリ無し＝**observability hook が皆無**なら、6-3 が実は net-harmful でも「FP が honest run を止める頻度 > 捏造を捕まえる頻度」を**後から測る材料が集まらない**。verify-{IMPL_INDEX}.md は毎 run 書かれる（材料は存在）が RUN_DIR は gitignored・ephemeral で**集約されない**。→ 追跡を「実験」と呼ぶか「チューニング backlog」と呼ぶかは filing の違いで、**実質要件は同一: コストを観測可能にする hook を1つ置く**。純・二次波及の判定: **無条件本採用＋観測 hook ゼロ**という現在の選択だけが将来の是正を封じる。

**対立仮説: 「段③の pre-existing-dirty FN は理論的なだけで実害は無い（implementer が既 dirty ファイルを申告のみ・未編集で出す状況は非現実的）」**
- 検討: 部分的に棄却。plan/reference は必ずしも clean tree を保証しない。本セッション自体が4ファイル既 `M` で走っている。activeな dev セッション中の pir2（＝この dotfiles リポの日常）では pre-existing dirty が常態で、FN 面は非ゼロ。ただし「申告のみ・未編集」の意図的捏造がその集合に**当たる**確率は低い ⇒ **実害は小さいが、残存限界として明示すべき（fail-open 方向なので silent。名指ししないと誰も気づけない）**。

---

### 二次・三次の含意と境界条件

**含意（採用した場合に派生する帰結）**
- 6-3 の「毎回コスト」の主成分は**手順分割による L0 脱落面**（レイテンシではない）。honest run の停止要因は FP よりむしろ「L0 が pre-set を忘れる→implementer 再実行」でありうる。
- FP 集合（段②）は additive に全 run へ乗る。個々は低頻度でも、**検出対象（真捏造）がさらに稀**なため PPV を構造的に押し下げる。
- 観測 hook ゼロの本採用は 6-3 を**実運用上 unfalsifiable** にする（有害でも検知不能）。

**境界（結論が成り立たなくなる条件）**
- run 母数が epic 経由でスケール ⇒ アラート疲労が潜在から顕在へ。staged 閉塞の緊急度が跳ねる。
- clean tree で走る run（pre-existing dirty 集合=空）⇒ 段③ FN 面は閉じ、6-3 のカバレッジは "clean tree" 想定どおりになる。逆に active dev セッション中の run ほど FN 面が開く。
- resume を跨ぐ外部 git 変化が無い ⇒ 段② #5 は発火しない。resume 頻度が高いワークフローほど #5 の偽警報が増える。

---

### rubric への寄与（現時点）

| rubric 基準 | 寄与/未達 | 根拠（このレンズのどこが効くか） |
|---|---|---|
| #1 oracle 健全性（fail-open/closed 方向つき） | **寄与（強）** | context の FP2件に加え、**pre-existing-dirty FN（fail-open, 段③）**・**resume-stale-baseline FP（fail-closed, 段②#5）**・net-zero編集・symlinkパスを新規に境界づけ。post-vs-delta 選択が FP/FN の双子を生む構造を明示 |
| #2 設計適合（root cause） | 寄与（中） | pre-set/post-set 分割が「L0 の不信頼」に 6-3 自身の前提を依存させる再帰結合（論点A を境界側から補強）。(A) が圧力最小点をカバーし最大点を外す逆説 |
| #3 全通常 run への挙動影響 | **寄与（強・主担当）** | コストの主成分は手順分割による L0 脱落面（レイテンシは赤ニシン）。honest run 停止要因＝FP＋pre-set 忘れ再実行。FP 集合の全列挙と additive 性 |
| #4 完成度・残ギャップ（(A) 7-4/8-2） | **寄与（強）** | INNER_LOOP は 7-4 捏造を**安価にでなく高価に**検知（reviewer 5体×最大3）。穴は correctness でなく cost ⇒ (A) は「妥当な境界」＋「圧力-コスト反転」の1行注記つき |
| #5 過剰/過小（experimental 前提） | 寄与（弱〜中） | 低 run 母数では堅牢化（6フィクスチャ）は FP-閉塞ギャップ（staged 未閉塞）に対し過剰に見える一方、観測 hook ゼロは過小。緊張は run 母数に連動 |
| #6 採用/コミット推奨 | 寄与（中） | 採用条件を供給: (a) staged 閉塞（implementer.md に git add 禁止1行）、(b) 観測 hook 1つ、(c) pre-existing-dirty FN と resume-stale を残存限界に明記 |
| #7 プロセス自己言及 | 寄与（弱） | 「ゲートが distrust する当の L0 信頼に、ゲート自身が pre-set で依存する」再帰は、人間主導 fix ループの信頼性論と同型 |

---

### 事実と推測の仕分け

**事実（context / exp-01 に出典あり）**
- staged/case-rename FP は exp-03 実機発見（context L13–14）。PHANTOM は post を使う（ref L182–191）。staged 非対象・既 dirty は pre.list に入り delta から除外（ref L59, context L89）。experimental.md に 6-3 不在（context L15）。FP 頻度・L0 実挙動は未測定（context L33–34）。本セッション開始時4ファイル既 `M`（exp-01 冒頭 git status）。

**推論（deliberator の解釈）**
- pre-existing-dirty への虚偽申告は fail-open で両検査不可視（段③、bash ロジックからの導出）。resume 中の外部 git 変化が偽 PHANTOM を製造（段②#5）。コスト主成分は手順分割の L0 脱落面（レイテンシではない）。PPV は真捏造 base rate が稀なため低 FP でも割れる。アラート疲労は run 母数に連動し現母数では潜在。INNER_LOOP は 7-4 捏造を高価に検知＝(A) の穴は cost であり correctness ではない。観測 hook ゼロの本採用は 6-3 を unfalsifiable にする。

---

### 現時点の確信度と残る不確実性
- **確信度: 中〜高**。境界の機序（段②③の FP/FN、pre-set 分割、INNER_LOOP のコスト置換）は bash ロジックから直接トレースでき**高確信**。アラート疲労閾値と「無条件採用の波及」は**構造的に妥当だが、実 run 母数・真 base rate 未測定のため中確信**（噛むかどうかが将来条件に依存）。
- **残る不確実性**:
  - 段②の各 FP と段③の FN の**実発生頻度**（未測定、context L33 と同じ空白）。
  - L0 が pre-set/post-set を毎回正しく走らせるか（未観測、context L34）。これが低いと「毎回コスト」の主成分は FP でなく pre-set 忘れ再実行になる。
  - symlink パス（段②#4）で dotfiles 自己改変 run が実際どちらの path 形で申告されるか（`~/...` なら fail-open、リポ相対なら phantom-checkable）は run 依存で未確定。

---

### 追加探索が必要な論点（該当分のみ）
- **pre-existing-dirty FN の再現確認**: scratch repo で「pre-set 時に F を dirty にし、implementer が F を申告のみ・未編集」を verify-deterministic-check.sh のフィクスチャに1本追加して PASS（=見逃し）を実証できるか。確かめれば段③が「理論」から「実証済み残存限界」に昇格し rubric#1 が固まる。→ 本熟考は実装変更 out of scope のため提案に留める（gate/synthesizer が must-fix 判断の材料に）。
- **resume-stale-baseline（段②#5）**: 「pre-set 記録→中断→間に commit→resume→post-set」を1本フィクスチャ化すれば偽 PHANTOM を実証可能。事象X と同一クラスなので優先度は高い。
- どちらも「何を確かめれば埋まるか」は明確（フィクスチャ2本）だが、実行は本レビューのスコープ外（レビューと推奨まで）。
