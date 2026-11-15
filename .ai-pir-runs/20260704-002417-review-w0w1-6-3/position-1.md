## position（ROUND 1）: W0+W1（6-3 決定論的完了検証）の最終深レビュー ―― コミット/採用可否と残存リスク

### 結論（現時点の最良の答え）

**修正してコミット**（そのままコミット ×・ロールバック ×）。4レンズ（第一原理・反証・二次波及・採用判断）が独立にこの結論へ収束した。

- **なぜロールバックでないか**: 事象X（resume 時 L0 捏造→reviewer 全FAIL→19分迷走）は実損が観測済み、oracle（git working-tree 集合照合）は独立性・真正性の第一原理で健全、Anthropic の Outcome/State-check パターン・Unit42（skill の 80% が宣言と挙動不一致）に整合、行レビューは全 PASS。穴は既知2点＋新規4点に限定され、いずれも安価に塞げるか文書化で境界づけられる。ロールバックは実証済み価値を過剰反応で放棄する。**epic（executions 0）が廃止されても 6-3 は pir2/pir2codex ホットパスの硬化として単体で元が取れる**（回収可能性が最も強い真）。
- **なぜそのままでないか**: staged 変更 FP は「単一の無害コマンド（`git add`）で発火し、再実行で直らない hard fail」＝ホットパスで正当な run を殺す fail-closed の unrecoverable 地雷。しかも実集合に staged を含めない前提が Claude implementer 側で一度も検証されていない（`implementer.md` に git add 禁止 0 件）。かつ FP 率・「L0 が本当に 6-3 bash を毎回走らせるか」を測る観測 harness が皆無（experimental.md 未登録）で、6-3 は実運用上 unfalsifiable。既知・安価・共通経路の欠陥を無修正でホットパスに出荷するのが最も擁護困難。

**コミット前 must-fix（最小リスト・下記「未解決の対立」で robust/floor の緊張を明示）**

1. **staged 変更 FP を堅牢に塞ぐ**: `deterministic-completion-check.md` の実集合に `git -C … -c core.quotePath=false diff --cached --name-only` を **pre.list と post.list の両方**に union（「staged は対象外」コメントを撤回）。健全性の根拠 = staged ⊆ 実際に変更されたファイル（未変更を stage しても index に何も足さない）なので、これは **PHANTOM を縮めるだけで偽陰性を生まない**。**pre 片側だけに足すと実行前から staged のファイルが delta（UNDECLARED=warn）に誤混入する ―― FIX-5/FIX-F の regression 再演になるため pre/post 両側必須**。補助として implementer.md に「申告ファイルを自分で `git add` しない」1行（prose は補助であって主ではない、理由は #7）。
2. **experimental.md に 6-3 を Active 実験登録**: 観測項目に **(a) FP 実発生率 (b) L0 が 6-3 bash を実際に実行したか（verify-*.list の生成有無）** を必須化。rollback トリガ「観測窓 N run で FP が閾値超なら **hard-fail→warn 降格**」を明記。これで「hook は log-only 段階導入なのに 6-3 は即 blocking」の設計内非対称を、監視付き・可逆な決定に変換し、同日 epic の統治（Active track）と対称化する。
3. **known-limitations 明記**（`deterministic-completion-check.md`）: (a) case-only rename FP（APFS）(b) 7-4/8-2/6.5-2(C)/refactor-gate 再実装 entry 無検証（INNER_LOOP_COUNT が部分安全網）(c) blocking 即時採用の根拠（git working-tree は成熟 oracle、hook oracle は新規でノイジー）(d) 再帰的信頼の錨（どこかで人間/決定論に接地する不可避境界。runtime 錨は W2/W5 hook-floor）(e) L0 検証パイプライン 1/6（残り5手順は W2+）**＋ (f) 二次波及レンズが新規導出した2穴**（pre-existing-dirty への虚偽申告＝fail-open / resume 中の外部 git 変化＝fail-closed、下記「未解決の対立」参照）。

**併用推奨**: W0（citation 衛生・epic の sanitized_cwd 登録）と W1（6-3 一式）は**リスク階層が違う**（W0=低リスク衛生系、W1=ホットパス改変）ため**分割コミット**。W1 に FP 再発時、W0 を巻き込まず 6-3 だけを surgical に revert できる（blast radius 最小化）。

---

### 主要な論拠

- **oracle は第一原理的に健全**: 検証は「主張 P」と「独立観測 O」の突き合わせで、意味を持つ必要条件は独立性（O が P の生成主体と別チャネル）と真正性。6-3 は O を **git delta（編集という物理作用の副産物）** に置いた。dirty 状態は「編集した言明」でなく「編集作用の副産物」で、L2 は自己申告で作れない。事象X で reviewer が空振りしたのは入力が L2 の自己申告で独立性を欠いたから ―― 6-3 はその独立性を回復する (D-01 第一原理レンズ)。
- **6-3 は事象X の「兄弟」を直す（過大広告の訂正が要る）**: 事象X の捏造主体は **L0 自身**。6-3 は「L2 の捏造」装置で、対処対象インシデントの捏造主体を構造上カバーできない。ただし事象X の L0 は「嘘つき」でなく「実装したと**誤認**した者」で、**誤認者は検証を避けない**（隠す動機がない）。よって L0 が手順どおり 6-3 を実行すれば自分の誤認（delta 空・CLAIMED 非空 → PHANTOM）を暴かれる。**錨は「L0 の実行意志」という単一点に集約**され、この一点が守られれば L2 捏造も L0 の (b)(c) 型混乱捏造も両方カバーする。守られなければ全部素通り (D-01段4 / D-02攻撃a)。これは「completion verifier」でなく「**phantom-claim floor（浅い単一次元の床）**」と再ラベルすべき ―― 6 次元中 file-set 存在 1 次元しか見ず substance を検証しないので、完全捏造（tool 呼び出しが transcript に不在＝事象X の署名）は捕捉するが部分/実質捏造は捕捉しない、という**正しい境界** (D-02攻撃d)。
- **staged FP の判定は頻度に非依存でロバスト**: 単一共通コマンドでの hard fail ＋ 既知の安価健全修正あり ＝ 頻度が高かろうが低かろうが無修正出荷は不可。L0 が「これは staged だ」と自己診断して `git restore --staged` するのは、失敗パスが「報告再注入＋implementer 再実行」であること、無断 restore がユーザー CLAUDE.md の**明示禁止**行為であることの二重で塞がれ、L0 は「偽 PHANTOM」と「禁じられた git 変更」に挟まれユーザーゲート行き (D-02攻撃b)。
- **コストの主成分はレイテンシでなく手順分割による L0 脱落面**: bash は sub-second（赤ニシン）。真のコストは pre-set（6-1）と post-set（6-3）が subagent 1体分（数分）を挟んで時間分割され、L0 が pre-set 記録を跨いで保持せねばならない点。**honest run で L0 が bookkeeping 1手順を忘れただけで implementer フル再実行が強制される**。そして「L0 が手順を飛ばす」ことこそ事象X が実証した不信頼で、6-3 は自身の前提（pre-set 記録）をその不信頼に依存させている (D-03段①)。
- **experiment 登録は governance 是正であると同時に観測 harness そのもの**: verify-*.md は毎 run 書かれる（材料は存在）が RUN_DIR は gitignore・ephemeral で集約されない。observe 層を回す唯一の harness が experiment 登録＋rollback トリガで、これが無ければ「commit 後に観測」はただの願望。無条件本採用＋観測 hook ゼロだけが将来の是正を封じる (D-02攻撃c / D-03反論②)。
- **プロセス自己言及が堅牢形を要求**: FIX-5（累積）・FIX-F（submodule）という人間主導の修正指示自体が regression を作り、後段レビューと verify スクリプトが捕捉した。prose 指示駆動の修正は可謬 ―― これは 6-3 が守る失敗モード（prose 通り動いたつもりで outcome が誤り）と**同型**。ゆえに **prose に依存する塞ぎ方（git add 禁止1行）より、コードに接地した塞ぎ方（実集合に staged を union）を優先**すべき。prose 遵守こそが FIX で破れたのだから、prose を信頼する修正は同じ穴を踏む (D-04 #7)。

---

### 統合の過程（採否）

**採用した論点（骨格）**
- 「修正してコミット」= 4レンズ共通の結論を単一勧告に。回収可能性（epic 廃止でも元が取れる）を最強の真として据えた (D-02/D-04)。
- must-fix 3点（staged 堅牢修正・experiment 登録＋rollback トリガ・known-limitations）＝ D-04 の最小リストを骨格に、D-01/D-02 の staged 修正の健全性証明（pre/post 両側 union で偽陰性を生まない）を実装細部として結合。
- oracle 健全性の第一原理（独立性・真正性）と「phantom floor」再ラベル（D-01/D-02）を oracle 判定の中核に。
- コスト主成分＝手順分割の L0 脱落面という D-03 の赤ニシン指摘を #3 の中心に据えた。
- 3層割付（must-fix / 観測 / 受容）は D-04 の台帳を土台に、D-03 の新規2穴を追加割付。
- W0/W1 分割コミット（D-04）を blast radius 最小化策として採用。

**退けた/留保した論点**
- 「そのままコミット」（YAGNI で staged FP を受容）: 半分正しいが、「実行しても直らない fail-closed hard fail」は最悪クラスで、修正費用がほぼ 0。YAGNI は「安いのに既知の壊れ方を残す」ことを正当化しない → 棄却 (D-04反論1)。
- 「ロールバック（再帰的信頼が致命）」: 本レビュー最強の反論だが、再帰的信頼は全検証チェーンが接地する不可避境界で 6-3 固有欠陥でない。theatre 化は部分的に機械で塞げる（W2 hook-floor で 6-3 実行を runtime 照合）→ ロールバックでなく observe+W2 で錨、に修正 (D-01段3 / D-04反論2)。
- 「6-3 不要、reviewer に『git diff を取れ』を一行足せば同じ」: reviewer も自己申告主体で git diff 結果を捏造しうる。決定論層を LLM 層の前に置くことに独立価値 → 棄却 (D-01対立仮説)。
- 「executions 0 に 5 ラウンド＋verify＋6 フィクスチャは過剰投資」: 対象の取り違え。6-3 は epic（0回）でなく pir2/pir2codex ホットパス（多数側）に乗る。過剰でなく proportionate、むしろフィクスチャは staged/case-rename を取り逃した under-covering → 棄却 (D-04反論3)。
- 「pipeline 1/6 は過小（under-engineering）」: 良い増分は1手順を完全にやる。1/6 は意図したスコープ境界で、ビジョンの未完成をインクリメントの欠損と混同 → 「妥当なスコープ境界」に判定 (D-04対立仮説)。

（本 ROUND は初回統合のため「前回からの変化」なし。）

---

### 未解決の対立（潰さない）

1. **【新規・レンズ間で重大度が割れる】fail-open な穴 vs fail-closed な穴**: 二次波及レンズ (D-03) が bash ロジックから新規に導出した2穴は、他3レンズが扱った fail-closed FP とは**重大度の種類が違う**。
   - **pre-existing-dirty への虚偽申告（fail-open＝捏造見逃し）**: pre-set 時点で既に dirty なファイル F を implementer が「変更した」と申告し実際は未編集の場合、PHANTOM は post を使うため `{F}−{F,…}=空 → PASS`、delta も F を除外し UNDECLARED も無反応。**F は両検査に完全不可視**。しかも本セッションは開始時に4ファイルが既 `M` で、active dev セッション中の pir2（＝この dotfiles リポの日常）では pre-existing dirty のぶんだけ捏造見逃し面が開く。**方向が fail-open（守るべき捏造を見逃す）なので silent ―― 名指ししないと誰も気づけない**。これは staged FP の鏡像 FN で、両方 post-vs-delta 選択に由来する双子。
   - **resume 中の外部 git 状態変化（fail-closed・事象X と同クラス）**: pre.list 記録後〜post-set 前に中断→resume 間に user が commit/stash→working tree clean→claimed 全件が偽 PHANTOM。6-3 は「resume 時の迷走」を断つために作られたのに、baseline 健全性が最も脆いのが resume。
   - **対立の所在**: D-03 は両者を「残存限界として明示すべき（＝文書化で足りる）」と判定するが、これは**単一レンズの新規導出で他レンズの反証を経ていない**。fail-open は「6-3 が守るべき当のもの（捏造）を見逃す」ため質的に fail-closed より悪い一方、実害（意図的捏造が pre-existing-dirty 集合に当たる確率）は低い。**決着に要るもの**: scratch repo で「pre-set 時に F を dirty 化 → implementer が F を申告のみ・未編集」「pre-set→中断→間に commit→resume→post-set」の2フィクスチャを verify-deterministic-check.sh に追加し、fail-open/fail-closed を実証すれば「理論」から「実証済み残存限界」に昇格し、must-fix か documented-accept かが確定する（実行は本レビューのスコープ外＝レビューと推奨まで）。

2. **staged 修正の robust（コード） vs floor（prose+doc）**: must-fix #1 を堅牢形（実集合に `--cached` union）で入れると**今セッションで実装ラウンドが再開する**。D-04 は「着地を優先し実装を再開したくない場合の floor」として prose 1行＋known-limitation 明記で妥協し staged 残存を台帳 R-staged に計上する逃げ道を用意。しかし D-02/D-04 の #7 自己言及は「prose-confidence こそ FIX-5/FIX-F で破れた」ため堅牢形を第一推奨とする。**条件つき結論**: 原則は堅牢形（コード接地）。実装ラウンド再開を避けたい呼び出し元/ユーザーの時間選好が優先される場合のみ floor に緩め、その場合 staged を残存限界として明示的に飲む。**決着に要るもの**: 呼び出し元/ユーザーの時間選好の確認、および堅牢形採用時は「pir2 開始前に無関係ファイルが stage 済み」フィクスチャ1本で副作用（pre/post 対称性）を検証。

3. **再帰的信頼（論点A）の位置づけ ―― 収束済みだが残存リスクは開示**: 「6-3 が自分自身の実行を自分で検証することは論理的に不可能」（同一主体 L0 が検証と実行を兼ねると独立性が破れる自己言及パラドクス）。4レンズは「達成不可能を 6-3 に求めるのは筋違い ＝ スコープ外として正当」で収束。ただし**残存リスクとして開示**し、錨は「L0 の bash 実行意志」単一点に集約 → 次の投資最適点は明白（W2/W5 の hook-floor で Stop hook が verify-*.list の生成有無を runtime 照合＝外部化）。**未決部分**: L0 が 6-3 bash を体系的に走らせるかは未観測で、これが破綻すれば theatre 化。experiment 観測項目「実行有無」で early-warn し、破綻観測時は hook-floor（W2）を前倒しする、という条件つき対処に留まる。

---

### rubric カバレッジ（自己申告）

| # | rubric 基準 | 充足 / 部分 / 未達 | 根拠（position のどこが答えているか） |
|---|---|---|---|
| 1 | oracle の健全性を系統的に判定（fail-open/closed 方向つき、残存限界の境界づけと受容可能性） | 充足 | 独立性・真正性の第一原理で健全性を根拠づけ (D-01)。「phantom floor」再ラベルで捕捉/非捕捉境界を明示 (D-02)。残存穴を方向つきで境界づけ ―― fail-closed: staged（must-fix）・case-rename（受容+文書）・net-zero（文書）・resume-stale（文書+観測）／fail-open: pre-existing-dirty（未解決対立）・symlink パス（文書）。ただし新規4穴は単一レンズ導出・FP 実頻度未測定（未解決の対立1・確信度参照） |
| 2 | 設計適合（root cause 対処）を機序で判定＋W1 移行パス整合 | 充足 | 6-3 は事象X の「兄弟」（implementer 捏造）を直し L0 自己捏造は対象外＝過大広告の訂正が要る、を機序分解 (D-01段4/D-02攻撃a)。錨が「L0 実行意志」単一点に集約。resume 経路が真のギャップ。W1→W2 はコード非再利用だが技術（git 集合演算）＋共通プロトコル doc が転移＝debt でない |
| 3 | 全通常 run への挙動影響を具体列挙し釣り合いを判定 | 充足 | ホットパス（初回実装点）が採用判断の分水嶺 (D-04)。コスト主成分＝手順分割の L0 脱落面（レイテンシは赤ニシン、D-03段①）。FP 集合の additive 性・毎 run の L0 bash 負担・alert fatigue（PPV=p_fab/(p_fab+p_fp)、標的が稀ゆえ低 FP でも割れる）。未測定 FP に blocking は不釣り合い → log-only/warn 先行を rollback トリガで担保 |
| 4 | 完成度・残ギャップを網羅（真のギャップ/スコープ境界の判定） | 充足 | 7-4/8-2/6.5-2(C)/refactor-gate 無検証＝スコープ境界（INNER_LOOP が部分安全網、穴は correctness でなく cost＝「安価にでなく高価に検知」D-03段⑤）。pipeline 1/6＝妥当なスコープ境界（過小でない、D-04）。verify 未配線・複雑性 2.4〜5倍＝観測課題。pir2async/.codex overlay/W2+ は plan 明示の follow-up |
| 5 | 過剰/過小の判定（experimental 前提、最有力反論を steelman） | 充足 | 3方向 steelman を裁定 (D-04)。機構コア＝proportionate（epic 0回でなくホットパスに乗るため verify+フィクスチャは釣り合う）。真の過剰＝プロセス（FIX-5/FIX-F の人間 fix ループ往復が自己誘発 regression）。真の過小＝フィクスチャの FP カバレッジ（staged/case-rename 取り逃し、今 pre-commit で塞げる） |
| 6 | 採用/コミット推奨を明示＋受容する残存リスク列挙 | 充足 | 「修正してコミット」を単一勧告として提示。must-fix 最小3点＋W0/W1 分割コミット＋rollback トリガ。受容する残存リスク＝3層割付台帳（下記「確信度・前提」に集約）に列挙 |
| 7 | プロセス自己言及の考察 | 充足 | FIX-5/FIX-F regression 捕捉 → fix ループ可謬（6-3 が守る失敗モードと同型）→ **prose 修正より code 接地修正を優先**（must-fix #1 が堅牢形を第一推奨にした根拠、D-04）。機械検証の dev-time 成功は runtime 再帰信頼を保証しない（過度一般化しない）。「行レビュー全 PASS」という prose-confidence は出荷十分条件でない → 監視付き段階採用を支持 |

---

### 確信度・前提・残課題

- **全体の確信度: 中〜高** — 「修正してコミット」の骨格・oracle 健全性の第一原理切り分け・staged must-fix の頻度非依存ロバスト性・fix ループ可謬→堅牢形優先・pipeline 1/6=スコープ境界は、context の事実と確立した第一原理（独立性条件・trust anchor・自己言及パラドクス）から直接導け**高確信**。中に留まる部分: (a) 新規4穴（特に pre-existing-dirty FN・resume-stale FP）は単一レンズの bash ロジック導出でフィクスチャ実証がまだ、(b) alert fatigue が「噛むか」は実 run 母数・真捏造 base rate 未測定に依存し将来条件つき、(c) resume 経路が真のギャップという判定は該当手順（RESUME_MODE × 6-3 checkbox 相互作用）の逐語未確認。

- **依存している前提（崩れると結論が変わる）**:
  - 現在の失敗モードは「LLM の善意の混乱（resume 時の認識論的真空）」であり「敵対的な検出回避」ではない（脅威モデル＝accident, not adversary）。adversarial に変わると N3（decoy edit＝痕跡だけ作る）で無力化。
  - 実集合の bash は逐語どおり動く（行レビュー PASS 済みという rubric 前提）。
  - 実 run 母数は個人ワークフロー規模で低反復。epic が多数のネスト pir2 を駆動して run 母数が跳ねると alert fatigue 閾値が実際に噛み、staged 閉塞の緊急度が「煩わしいが生存可能」→「ゲート生存性クリティカル」に昇格。
  - clean tree で走る前提。active dev セッション中（pre-existing dirty 集合が非空）ほど fail-open 面が開く。

- **残る不確実性 / 未解決の対立**:
  - FP 実発生頻度・通常 run 完走率への影響（未測定、context §空白）。特に Claude implementer の staging 実挙動は未検証。
  - L0 が 6-3 bash を毎回正直に実行するか（再帰的信頼の実挙動、未観測）。theatre 化の実害はここで確定する。
  - 上記「未解決の対立」3件（fail-open/closed の重大度差、robust vs floor、再帰的信頼の runtime 挙動）。

- **受容する残存リスク（コミットでユーザーが飲むもの・3層割付台帳）**:
  - 【観測へ】case-rename FP（文書化後）／再帰的信頼の runtime 実挙動（experiment 観測項目「実行有無」）／FP 実頻度・完走率影響（experiment 観測窓→rollback トリガ）／複雑性 2.4〜5倍・verify 手動実行依存（CI/hook 未配線は W2+）。
  - 【受容】L0 パイプライン 1/6（スコープ境界、うち hook-floor は錨として観測課題に接続）／7-4/8-2/6.5-2(C)/refactor-gate 再実装 entry 無検証（INNER_LOOP が部分安全網）／設計内 blocking 非対称（oracle 成熟度差で正当化、ただし rollback トリガで可逆化が受容条件）／再帰的信頼のコア（不可避な信頼境界）。

- **追加探索が要る論点（deliberator 集約・実装は本レビューのスコープ外）**:
  - **フィクスチャ2本追加で新規2穴を実証**: 「pre-existing-dirty ファイルへの虚偽申告（fail-open）」「resume 中の外部 git 変化（fail-closed）」を verify-deterministic-check.sh に追加 → must-fix か documented-accept かを確定（未解決の対立1の決着材料）。
  - **staged 堅牢形の副作用検証**: 「pir2 開始前に無関係ファイルが stage 済み」フィクスチャ1本で pre/post 対称性を検証（未解決の対立2の決着材料）。
  - **resume 経路の pir2 SKILL.md 逐語確認**: RESUME_MODE と 6-3 checkbox の相互作用を Read し「resume 時 6-3 が強制再実行されるか」を確定（rubric #2 の中確信度判定を高/低に振る）。
