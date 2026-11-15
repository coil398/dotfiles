## position（ROUND 2）: W0+W1（6-3 決定論的完了検証）の最終深レビュー ―― コミット/採用可否と残存リスク

### 結論（現時点の最良の答え）

**修正してコミット**（そのままコミット ×・ロールバック ×）。ROUND 1 で 4レンズ（第一原理・反証・二次波及・採用判断）が独立にこの結論へ収束し、ROUND 2 は **結論・must-fix 3点・3層台帳を変えない**。ROUND 2 の唯一の追加は、gate が rubric #1 を「部分」とした未境界づけ（submodule / 入れ子フェンス / 実在 gitignore / pre-existing-dirty・resume-stale）を**方向つき（fail-open / fail-closed）で完全台帳化（R1〜R11）し、新 must-fix 昇格がゼロであることを連言基準で裁定**したこと。#1 は部分 → **充足**に上がる。

- **なぜロールバックでないか**（ROUND 1 据え置き）: 事象X（resume 時 L0 捏造→reviewer 全FAIL→19分迷走）は実損が観測済み、oracle（git working-tree 集合照合）は独立性・真正性の第一原理で健全、Anthropic の Outcome/State-check パターン・Unit42（skill の 80% が宣言と挙動不一致）に整合、行レビューは全 PASS。穴は既知＋新規に限定され、いずれも安価に塞げるか文書化で境界づけられる。**epic（executions 0）が廃止されても 6-3 は pir2/pir2codex ホットパスの硬化として単体で元が取れる**。
- **なぜそのままでないか**（ROUND 1 据え置き）: staged 変更 FP は「単一の無害コマンド（`git add`）で発火し、再実行で直らない hard fail」＝ホットパスで正当な run を殺す fail-closed の unrecoverable 地雷。実集合に staged を含めない前提が Claude implementer 側で一度も検証されていない（`implementer.md` に git add 禁止 0 件）。FP 率・「L0 が本当に 6-3 bash を毎回走らせるか」を測る観測 harness も皆無（experimental.md 未登録）。
- **ROUND 2 の確定（新規）**: gate が High（方向未決）とした submodule は、コード（check-ignore exit 128 → untrackable）＋実機フィクスチャ（L846/848）で **fail-open silent に方向確定**し、staged FP（fail-closed hard fail）とは**非同クラス**。gate が疑った「未台帳の fail-closed hard fail」は**実在しない**。submodule の唯一の fail-closed 軸（staged pointer bump）は must-fix #1（`--cached` union）に**無償で相乗り**。→ **新 must-fix はゼロ。must-fix 3点は完全据え置きで #1 台帳が閉じる**。

**コミット前 must-fix（ROUND 1 から不変・3点）**

1. **staged 変更 FP を堅牢に塞ぐ**: `deterministic-completion-check.md` の実集合に `git -C … -c core.quotePath=false diff --cached --name-only` を **pre.list と post.list の両方**に union（「staged は対象外」コメントを撤回）。健全性の根拠 = staged ⊆ 実際に変更されたファイル（未変更を stage しても index に何も足さない）なので、これは **PHANTOM を縮めるだけで偽陰性を生まない**。**pre 片側だけに足すと実行前から staged のファイルが delta（UNDECLARED=warn）に誤混入する ―― FIX-5/FIX-F の regression 再演になるため pre/post 両側必須**。補助として implementer.md に「申告ファイルを自分で `git add` しない」1行（prose は補助であって主ではない、理由は #7）。**ROUND 2 追記**: この修正は submodule staged pointer bump（R4）も同時に塞ぐ（`--cached` が staged gitlink 変更を出す）。#1 の射程は position-1 記載より広い。
2. **experimental.md に 6-3 を Active 実験登録**: 観測項目に **(a) FP 実発生率 (b) L0 が 6-3 bash を実際に実行したか（verify-*.list の生成有無）** を必須化。rollback トリガ「観測窓 N run で FP が閾値超なら **hard-fail→warn 降格**」を明記。これで「hook は log-only 段階導入なのに 6-3 は即 blocking」の設計内非対称を、監視付き・可逆な決定に変換し、同日 epic の統治（Active track）と対称化する。**ROUND 2 追記**: 観測窓は R7（resume-stale fail-closed FP）の計測窓を兼ねる ―― 噛めば W2 hook-floor を前倒しする。
3. **known-limitations 明記**（`deterministic-completion-check.md`）: ROUND 2 で確定した **oracle 残存限界・完全台帳（R1〜R11）を方向つきで転記**する。特に (a) fail-open 群（submodule 内部 R2・実在 gitignore R5・pre-existing-dirty R6・symlink R11）を「**git を oracle にした選択の定義的 domain 境界であって bug ではない**」という単一原理で束ねて明記（下記「主要な論拠」段6）、(b) fail-closed 群のうち must-fix でないもの（case-rename R9・net-zero R10・入れ子フェンス R8 主方向・resume-stale R7）を rare/recoverable の理由つきで明記、(c) must-fix #1 が staged pointer bump（R4）に相乗りで効く1行、(d) ランタイム awk と verify script パーサの非対称（R8）を commit 後 hardening 候補として注記、(e) 再帰的信頼の錨（runtime 錨は W2/W5 hook-floor）、(f) L0 検証パイプライン 1/6（残り5手順は W2+）。

**併用推奨**（ROUND 1 据え置き）: W0（citation 衛生・epic の sanitized_cwd 登録）と W1（6-3 一式）は**リスク階層が違う**ため**分割コミット**。W1 に FP 再発時、W0 を巻き込まず 6-3 だけを surgical に revert できる（blast radius 最小化）。

---

### 主要な論拠

（段1〜6。段1〜5 は ROUND 1 据え置き、段6 は ROUND 2 が新規追加した fail-open 受容の一般化原則。）

- **段1: oracle は第一原理的に健全**: 検証は「主張 P」と「独立観測 O」の突き合わせで、意味を持つ必要条件は独立性（O が P の生成主体と別チャネル）と真正性。6-3 は O を **git delta（編集という物理作用の副産物）** に置いた。dirty 状態は「編集した言明」でなく「編集作用の副産物」で、L2 は自己申告で作れない。事象X で reviewer が空振りしたのは入力が L2 の自己申告で独立性を欠いたから ―― 6-3 はその独立性を回復する (D-01 第一原理レンズ)。
- **段2: 6-3 は事象X の「兄弟」を直す（過大広告の訂正が要る）**: 事象X の捏造主体は **L0 自身**。6-3 は「L2 の捏造」装置で、対処対象インシデントの捏造主体を構造上カバーできない。ただし事象X の L0 は「嘘つき」でなく「実装したと**誤認**した者」で、**誤認者は検証を避けない**。よって L0 が手順どおり 6-3 を実行すれば自分の誤認（delta 空・CLAIMED 非空 → PHANTOM）を暴かれる。**錨は「L0 の実行意志」という単一点に集約**される。これは「completion verifier」でなく「**phantom-claim floor（浅い単一次元の床）**」と再ラベルすべき ―― 6 次元中 file-set 存在 1 次元しか見ず substance を検証しないので、完全捏造（tool 呼び出しが transcript に不在＝事象X の署名）は捕捉するが部分/実質捏造は捕捉しない、という**正しい境界** (D-02攻撃d)。
- **段3: staged FP の判定は頻度に非依存でロバスト**: 単一共通コマンドでの hard fail ＋ 既知の安価健全修正あり ＝ 頻度が高かろうが低かろうが無修正出荷は不可。L0 が「これは staged だ」と自己診断して `git restore --staged` するのは、失敗パスが「報告再注入＋implementer 再実行」であること、無断 restore がユーザー CLAUDE.md の**明示禁止**行為であることの二重で塞がれ、ユーザーゲート行き (D-02攻撃b)。
- **段4: コストの主成分はレイテンシでなく手順分割による L0 脱落面**: bash は sub-second（赤ニシン）。真のコストは pre-set（6-1）と post-set（6-3）が subagent 1体分（数分）を挟んで時間分割され、L0 が pre-set 記録を跨いで保持せねばならない点。**honest run で L0 が bookkeeping 1手順を忘れただけで implementer フル再実行が強制される** (D-03段①)。
- **段5: プロセス自己言及が堅牢形を要求**: FIX-5（累積）・FIX-F（submodule）という人間主導の修正指示自体が regression を作り、後段レビューと verify スクリプトが捕捉した。prose 指示駆動の修正は可謬 ―― これは 6-3 が守る失敗モード（prose 通り動いたつもりで outcome が誤り）と**同型**。ゆえに **prose に依存する塞ぎ方（git add 禁止1行）より、コードに接地した塞ぎ方（実集合に staged を union）を優先**すべき (D-04 #7)。
- **段6【ROUND 2 新規】: fail-open 受容は「git-oracle の定義的 domain 境界」で一般化される**: 3つの fail-open（実在 gitignore R5・submodule 内部 R2・pre-existing-dirty R6、加えて symlink R11）は**単一原理**で受容が根拠づく ―― **git を oracle に選んだ以上、git の視野の外にある領域への虚偽申告は原理的に検出不能**。git の domain は「追跡ファイルの working-tree 状態（unstaged、＋#1 で staged）」で、構造的に3領域が親リポ git の視野外に置かれる: ① gitignore 対象（git が差分を出さない＝ignore の定義そのもの）／② submodule 内部（親が sub-repo に委譲。`--ignore-submodules=dirty` が oracle に「中を見るな」と明示指定）／③ 既 dirty ファイルの内容同一性（name-set 粒度では「再申告された既存 dirty」と「新規編集」を区別不能）。これらは **bug でも未修正ギャップでもなく、「git を oracle にする」選択の定義的境界**で、設計 SSOT の残存限界④⑥（**fail-open な事故計器であり攻撃防御ではない**、reference L166-168 逐語）と厳密に同型。3c の `test -f` は best-effort の可視化層（out-of-domain への「実在しないファイル」申告を warn で拾う）だが「この run で変わったか」は原理的に verify できない ―― その唯一の信号（git）が設計上盲だから。**受容の境界条件＝脅威モデル accident-not-adversary**: 善意で混乱した implementer の捏造が out-of-domain 領域に完全に収まる確率は accident モデル下では低い偶然（設計された回避でない）。adversarial モデル（out-of-domain パスだけ狙って申告し検出回避）では**全 fail-open が同時に開く**が、それは受容済み脅威モデルの**外**（position-1 前提「N3 decoy-edit は scope 外」）(D-2-01 段5)。

---

### 統合の過程（採否）

**採用した論点（骨格）**（ROUND 1 据え置き）
- 「修正してコミット」= 4レンズ共通の結論を単一勧告に。回収可能性（epic 廃止でも元が取れる）を最強の真として据えた (D-02/D-04)。
- must-fix 3点（staged 堅牢修正・experiment 登録＋rollback トリガ・known-limitations）＝ D-04 の最小リストを骨格に、staged 修正の健全性証明（pre/post 両側 union で偽陰性を生まない）を実装細部として結合。
- oracle 健全性の第一原理（独立性・真正性）と「phantom floor」再ラベル (D-01/D-02) を oracle 判定の中核に。
- 3層割付（must-fix / 観測 / 受容）は D-04 の台帳を土台に、ROUND 2 (D-2-01) の11穴完全台帳で置換・拡張。

**退けた/留保した論点**（ROUND 1 据え置き＋ROUND 2 追加）
- 「そのままコミット」（YAGNI で staged FP を受容）: 「実行しても直らない fail-closed hard fail」は最悪クラスで修正費用がほぼ 0 → 棄却 (D-04反論1)。
- 「ロールバック（再帰的信頼が致命）」: 再帰的信頼は全検証チェーンが接地する不可避境界で 6-3 固有欠陥でない → observe+W2 で錨、に修正 (D-01段3 / D-04反論2)。
- 「6-3 不要、reviewer に『git diff を取れ』を一行足せば同じ」: reviewer も自己申告主体で git diff 結果を捏造しうる → 棄却 (D-01対立仮説)。
- 「executions 0 に 5 ラウンド＋verify＋6 フィクスチャは過剰投資」: 6-3 は epic（0回）でなく pir2/pir2codex ホットパス（多数側）に乗る → proportionate、フィクスチャはむしろ staged/case-rename を取り逃した under-covering → 棄却 (D-04反論3)。
- 「pipeline 1/6 は過小（under-engineering）」: 1/6 は意図したスコープ境界 → 「妥当なスコープ境界」に判定 (D-04対立仮説)。
- **【ROUND 2】「submodule は dotfiles で 3本 live・common だから staged と同じく must-fix にすべき」**: 方向が違う。コード＋フィクスチャ (L846: `mysub/inner.md`→untrackable) が証明するとおり submodule 内部は **fail-open silent** であって staged の fail-closed hard fail ではない。must-fix 基準の第一条件（fail-closed）を満たさない。頻度も過大評価 ―― submodule 内編集は通常 PROJECT_ROOT=submodule 自身で回す（その場合 submodule が top-level repo になり全て trackable で正常）ため、fail-open が噛むのは「PROJECT_ROOT=親 dotfiles かつ submodule 内パス申告」の狭い交差のみ → **受容・文書化が正しい**。gate の High は方向未確定ゆえの保守的 flag で、方向を確定すれば fail-open に解決し High → 受容に落ちる (D-2-01反論①)。
- **【ROUND 2】「pre-existing-dirty は dotfiles で最頻の fail-open だから must-fix にすべき」**: 頻度は fail-open を must-fix に変えない。must-fix 基準は「fail-closed unrecoverable（正当 run を殺す）」に特化しており、fail-open は**正当 run を一度も殺さない**（捏造を silent に通すだけ）。かつ clean fix が無い（content-hashing への質的複雑化）→ **受容だが最頻 fail-open として台帳で明示**し、adversarial 化 or content-hashing 安価化を再訪トリガに置く (D-2-01反論②)。
- **【ROUND 2】「入れ子フェンスは fail-open にも倒れうるから must-fix」**: 主方向は fail-closed（安全側）。fail-open 副方向はトリガが二重に contrived（入れ子フェンス例示＋捏造行がその後）で common-path から程遠い → 受容・文書化＋任意 hardening (D-2-01対立仮説)。

**前回（ROUND 1）からの変化**
- **上積み（撤回はゼロ）**: ROUND 1 の結論・must-fix 3点・W0/W1 分割コミット・受容台帳は**すべて据え置き**。ROUND 2 が足したのは (1) gate 名指しの未境界づけ4カテゴリ（submodule / 入れ子フェンス / 実在 gitignore / pre-existing-dirty・resume-stale）を**方向つきで確定**し11穴の完全台帳（R1〜R11）に整理、(2) fail-open 受容の**一般化原則**（git-oracle domain 境界、段6）、(3) **新 must-fix 昇格ゼロ**を連言基準で機械的に裁定、(4) must-fix #1 の**射程拡大**（staged pointer bump R4 に無償相乗り）。
- **判定の更新**: rubric #1 を **部分 → 充足**（境界づけが完成したため）。他6基準はカバレッジ変化なし（ROUND 1 で既に充足）。
- **未解決の対立の縮約**: ROUND 1「未解決の対立1（fail-open vs fail-closed の重大度差）」の**方向・3層割付は ROUND 2 で確定**（残るのは頻度パラメータの未測定のみ ―― 裁定は頻度非依存で耐えるため「確度向上タスク」に格下げ）。対立2（robust vs floor）・対立3（再帰的信頼の runtime 挙動）は未決のまま残す。

---

### 未解決の対立（潰さない）

1. **【ROUND 2 で方向確定・頻度のみ未測定に縮約】fail-open な穴 vs fail-closed な穴**: ROUND 1 で二次波及レンズが導出した2穴（pre-existing-dirty・resume-stale）を含む全残存限界の**方向と3層割付は ROUND 2 (D-2-01) で確定**した（下記完全台帳 R1〜R11）。fail-open 群（R2/R5/R6/R11）は「git-oracle domain 境界」で一律受容、fail-closed 群のうち must-fix でないもの（R7/R8/R9/R10）は rare/recoverable で観測 or 受容。**残る未決は頻度パラメータのみ**: R6 pre-existing-dirty が「最頻 fail-open」という順位は active dev の dirty 集合サイズ・accident 捏造が dirty 集合に当たる base rate に依存し**未測定**、R2 submodule fail-open の頻度「低」は「submodule 編集は PROJECT_ROOT=submodule で回す」運用推定に依存し**未実証**。**ただし方向＝fail-open・受容の裁定は頻度に非依存で耐える**。**決着に要るもの**: scratch repo で「pre-existing-dirty ファイルへの虚偽申告（fail-open）」「resume 中の外部 git 変化（fail-closed）」の2フィクスチャを verify-deterministic-check.sh に追加 → 理論を実証に昇格。ただし gate がこれを「次ラウンドで潰さなくてよい確度向上タスク」に分類済みで、**境界づけ・3層割付・新 must-fix ゼロの裁定はコード＋実機フィクスチャ（submodule L846/848）で既に確定**（実装は本レビューのスコープ外）。

2. **staged 修正の robust（コード） vs floor（prose+doc）**（ROUND 1 据え置き）: must-fix #1 を堅牢形（実集合に `--cached` union）で入れると**今セッションで実装ラウンドが再開する**。D-04 は「着地を優先し実装を再開したくない場合の floor」として prose 1行＋known-limitation 明記で妥協し staged 残存を台帳に計上する逃げ道を用意。しかし #7 自己言及は「prose-confidence こそ FIX-5/FIX-F で破れた」ため堅牢形を第一推奨とする。**条件つき結論**: 原則は堅牢形（コード接地）。実装ラウンド再開を避けたい呼び出し元/ユーザーの時間選好が優先される場合のみ floor に緩め、その場合 staged を残存限界として明示的に飲む。**決着に要るもの**: 呼び出し元/ユーザーの時間選好の確認、および堅牢形採用時は「pir2 開始前に無関係ファイルが stage 済み」フィクスチャ1本で副作用（pre/post 対称性）を検証。**ROUND 2 補強**: 堅牢形は submodule staged pointer bump（R4）も無償で塞ぐため、floor に緩めると R4 も同時に残存する（台帳 R1＋R4 が連動）。

3. **再帰的信頼（論点A）の位置づけ ―― 収束済みだが残存リスクは開示**（ROUND 1 据え置き）: 「6-3 が自分自身の実行を自分で検証することは論理的に不可能」（同一主体 L0 が検証と実行を兼ねると独立性が破れる自己言及パラドクス）。4レンズは「達成不可能を 6-3 に求めるのは筋違い ＝ スコープ外として正当」で収束。錨は「L0 の bash 実行意志」単一点に集約 → 次の投資最適点は W2/W5 の hook-floor（Stop hook が verify-*.list の生成有無を runtime 照合＝外部化）。**未決部分**: L0 が 6-3 bash を体系的に走らせるかは未観測で、これが破綻すれば theatre 化。experiment 観測項目「実行有無」で early-warn し、破綻観測時は hook-floor（W2）を前倒しする、という条件つき対処に留まる。

---

### oracle 残存限界・完全台帳（R1〜R11・方向つき／3層割付）【ROUND 2 で完成】

| # | 残存限界 | (a)機序 | (b)方向 | (c)頻度 | (d)割付 | (e)理由 |
|---|---|---|---|---|---|---|
| R1 | staged 変更（一般） | `git add` で unstaged diff から消失→正当申告が PHANTOM 化・再実行で直らない | **fail-closed**（unrecoverable） | 中（単一コマンド `git add`） | **must-fix #1**（ROUND1 既定） | fail-closed AND common AND clean fix（`--cached` を pre/post 両側 union、staged⊆実変更ゆえ偽陰性なし）＝3条件連言を満たす唯一の穴 |
| R2 | **submodule 内部パス虚偽申告** | check-ignore exit128→untrackable→PHANTOM 対象外／test-f 実在→silent（fixture L846/848 で実証） | **fail-open** silent | 低（PROJECT_ROOT=親 かつ submodule 内パス申告の狭い交差） | **受容・文書化** | 内部は git-parent の domain 外（`--ignore-submodules=dirty` が明示除外）。gate 懸念の fail-closed hard fail は check-ignore128 が untrackable に落とすため**起きない**。実在 gitignore と同クラス |
| R3 | submodule pointer bump（正当/虚偽） | trackable（check-ignore exit1）／`=dirty` が post に残す | 正当→PASS・虚偽→**正しく hard fail（真陽性）** | 低 | **受容**（設計どおり健全） | FIX-F（`=all`でなく`=dirty`）が pointer bump の fail-closed FP を意図的に予防済み。FP でも穴でもない |
| R4 | submodule staged pointer bump | 親で `git add mysub`→staged→unstaged diff に不出 | **fail-closed** | 低 | **must-fix #1 に包含** | 独立カテゴリでなく staged FP の submodule 顕現。`--cached` union が同時に塞ぐ（新 must-fix 不要） |
| R5 | **実在 gitignore への虚偽申告** | check-ignore exit0→untrackable→PHANTOM 対象外／test-f 実在→silent（L166-168） | **fail-open** silent | 低〜中（bookkeeping 系申告時） | **受容・文書化** | git は ignore 対象の差分を原理的に出さない＝oracle domain 外。clean fix 不在（bug でなく境界）。SSOT 残存限界④⑥ 同型 |
| R6 | **pre-existing-dirty への虚偽申告** | 既 dirty F を申告・未編集→post に在り非 PHANTOM／delta 除外で UNDECLARED も無反応→両検査不可視 | **fail-open** silent | **最高**（active dev の既 dirty 集合。本セッションも開始時4 M） | **受容・文書化（頻度警告つき）** | name-set 粒度では「再申告された既存 dirty」と「新規編集」を区別不能＝git domain 外の内容同一性。clean fix は content-hashing で質的複雑化。**adversarial 化 or hashing 安価化時に最初に再訪** |
| R7 | resume 中の外部 git 変化 | pre.list 後〜post 前に中断→resume 間に user commit/stash→tree clean→claimed 全件が偽 PHANTOM | **fail-closed** | 低（resume×外部 git 操作の交差） | **commit 後観測**（must-fix #2 の観測窓） | fail-closed だが common でなく、失敗パスがユーザーゲートで**回復可能**（unrecoverable でない）。observe 窓で FP 計測、噛めば W2 hook-floor 前倒し |
| R8 | 入れ子フェンス（decoy 混入） | naive toggle awk のトグル反転で decoy が CLAIMED 混入→git delta に無く PHANTOM（L117-123） | **主 fail-closed（偽 PHANTOM）**／副 fail-open（真行取り落とし） | 極低（変更一覧内の4バッククォート入れ子例示） | **受容・文書化（＋任意 hardening）** | 主方向は安全側。副方向はトリガ二重 contrived で common でない。堅牢 parser は verify script に既存（L538-555）→ランタイム awk への移植は任意 hardening（parser 非対称を注記） |
| R9 | case-only rename（APFS） | 大文字小文字のみ rename は git シグナル空→正当変更が PHANTOM | **fail-closed** FP | 低（macOS FS 依存の稀操作） | **受容・文書化** | common でなく（rename の稀 subset）clean fix が非自明。ROUND1 台帳既載 |
| R10 | net-zero 編集 | 編集して元に戻す等 delta 空→NO_OP 宣言なしで PHANTOM | **fail-closed** FP | 極低 | **受容・文書化** | ROUND1 台帳既載。NO_OP 免除で回避可 |
| R11 | symlink 経由パス | symlink 先の実体が git 追跡外だと申告が延べ検証不能 | **fail-open** | 極低 | **受容・文書化** | git domain 外の同クラス。ROUND1 台帳既載 |

**中央裁定**: 新たに must-fix へ昇格すべき残存限界は **ゼロ**。must-fix 基準（fail-closed AND common-path AND clean-fix 連言）を満たすのは R1（staged 一般）のみで、これは ROUND1 で既に must-fix #1 化済み。gate が High とした submodule（R2）は check-ignore128→untrackable により **fail-open で確定**（staged と非同クラス）、fail-closed 軸（R4 staged pointer bump）は #1 に相乗りで無償閉塞。他は fail-open（受容）か、fail-closed でも rare/recoverable（観測 or 受容）。→ **ROUND1 の must-fix 3点は完全据え置きで #1 台帳が閉じる**。

---

### rubric カバレッジ（自己申告）

| # | rubric 基準 | 充足 / 部分 / 未達 | 根拠（position のどこが答えているか） |
|---|---|---|---|
| 1 | oracle の健全性を系統的に判定（fail-open/closed 方向つき、残存限界の境界づけと受容可能性） | **充足**（ROUND 2 で部分→充足） | 独立性・真正性の第一原理で健全性を根拠づけ (D-01)。「phantom floor」再ラベルで捕捉/非捕捉境界を明示 (D-02)。**ROUND 2 で gate 名指しの未境界づけ4カテゴリを全て方向つき台帳化**（R2 submodule=fail-open silent 確定・R5 gitignore=fail-open・R8 入れ子フェンス=主 fail-closed／副 fail-open・R6 pre-existing-dirty=fail-open 最頻・R7 resume-stale=fail-closed 回復可能）。fail-open 群を「git-oracle の定義的 domain 境界」で一般化受容（段6）。**新 must-fix ゼロを連言基準で裁定**、3層割付を11穴で完備。残る不確実性は頻度パラメータ（R6 最頻・R2 低）の未測定のみで、方向・受容の裁定は頻度非依存 |
| 2 | 設計適合（root cause 対処）を機序で判定＋W1 移行パス整合 | 充足（ROUND 1 据え置き） | 6-3 は事象X の「兄弟」（implementer 捏造）を直し L0 自己捏造は対象外＝過大広告の訂正が要る、を機序分解 (D-01段4/D-02攻撃a)。錨が「L0 実行意志」単一点に集約。resume 経路が真のギャップ。W1→W2 はコード非再利用だが技術（git 集合演算）＋共通プロトコル doc が転移＝debt でない |
| 3 | 全通常 run への挙動影響を具体列挙し釣り合いを判定 | 充足（ROUND 1 据え置き） | ホットパス（初回実装点）が採用判断の分水嶺 (D-04)。コスト主成分＝手順分割の L0 脱落面（レイテンシは赤ニシン、D-03段①）。FP 集合の additive 性・毎 run の L0 bash 負担・alert fatigue（標的が稀ゆえ低 FP でも PPV が割れる）。未測定 FP に blocking は不釣り合い → log-only/warn 先行を rollback トリガで担保 |
| 4 | 完成度・残ギャップを網羅（真のギャップ/スコープ境界の判定） | 充足（ROUND 1 据え置き） | 7-4/8-2/6.5-2(C)/refactor-gate 無検証＝スコープ境界（INNER_LOOP が部分安全網、穴は correctness でなく cost、D-03段⑤）。pipeline 1/6＝妥当なスコープ境界（過小でない、D-04）。verify 未配線・複雑性 2.4〜5倍＝観測課題。pir2async/.codex overlay/W2+ は plan 明示の follow-up |
| 5 | 過剰/過小の判定（experimental 前提、最有力反論を steelman） | 充足（ROUND 1 据え置き） | 3方向 steelman を裁定 (D-04)。機構コア＝proportionate（epic 0回でなくホットパスに乗るため verify+フィクスチャは釣り合う）。真の過剰＝プロセス（FIX-5/FIX-F の人間 fix ループ往復が自己誘発 regression）。真の過小＝フィクスチャの FP カバレッジ（staged/case-rename 取り逃し） |
| 6 | 採用/コミット推奨を明示＋受容する残存リスク列挙 | 充足（ROUND 2 で補強） | 「修正してコミット」を単一勧告として提示。must-fix 最小3点＋W0/W1 分割コミット＋rollback トリガ。**ROUND 2 で受容残存リスク台帳を R1〜R11 で完全化** ―― ユーザーが自環境（submodule live）で飲む fail-open を明示列挙し、「ユーザーが live な残存リスクを知らされずコミット」懸念を解消 |
| 7 | プロセス自己言及の考察 | 充足（ROUND 2 で補強） | FIX-5/FIX-F regression 捕捉 → fix ループ可謬（6-3 が守る失敗モードと同型）→ **prose 修正より code 接地修正を優先**（must-fix #1 が堅牢形を第一推奨にした根拠、D-04）。**ROUND 2 追記**: FIX-F（`--ignore-submodules=dirty`）は pointer bump の fail-closed FP を意図的に予防した「正しい人間 fix」でもあり (R3)、fix ループが regression だけでなく正しい防御も生む両面性を確認。機械検証の dev-time 成功は runtime 再帰信頼を保証しない（過度一般化しない） |

---

### 確信度・前提・残課題

- **全体の確信度: 中〜高**（ROUND 2 で #1 部分が高確信に上振れ） — 「修正してコミット」の骨格・oracle 健全性の第一原理切り分け・staged must-fix の頻度非依存ロバスト性・fix ループ可謬→堅牢形優先・pipeline 1/6=スコープ境界は**高確信**。**ROUND 2 で新規高確信化**: submodule の方向確定（fail-open silent）はコメント・コード・**実機フィクスチャ L846/848 の3点で裏取り済み**で gate の二分岐（trackable/untrackable）を決定的に解いた。新 must-fix ゼロは連言基準の機械的適用で、fail-open を must-fix にしない論理（fail-open は正当 run を殺さない）は堅牢。fail-open 受容の一般化は SSOT 残存限界④⑥ の逐語引用に接地。中に留まる部分: (a) FP 実頻度（R6 最頻・R2 低の順位）は未測定（裁定は頻度非依存で耐えるが実害推定は将来条件つき）、(b) alert fatigue が「噛むか」は実 run 母数・真捏造 base rate 未測定に依存、(c) resume 経路が真のギャップという判定は該当手順（RESUME_MODE × 6-3 checkbox 相互作用）の逐語未確認。

- **依存している前提（崩れると結論が変わる）**:
  - 現在の失敗モードは「LLM の善意の混乱（resume 時の認識論的真空）」であり「敵対的な検出回避」ではない（脅威モデル＝**accident, not adversary**）。adversarial に変わると全 fail-open（R2/R5/R6/R11）が同時に開き受容前提が崩れる（→ W2 で content-hashing / hook-floor 必須化）。
  - 実集合の bash は逐語どおり動く（行レビュー PASS 済み・submodule フィクスチャ実機緑という rubric 前提）。
  - 実 run 母数は個人ワークフロー規模で低反復。epic が多数のネスト pir2 を駆動して run 母数が跳ねると alert fatigue 閾値が噛み、R7 resume-stale の fail-closed FP 絶対数も増える。
  - clean tree で走る前提。active dev セッション中（pre-existing dirty 集合が非空）ほど R6 fail-open 面が開く。

- **残る不確実性 / 未解決の対立**:
  - FP 実発生頻度・通常 run 完走率への影響（未測定、context §空白）。特に Claude implementer の staging 実挙動は未検証。
  - L0 が 6-3 bash を毎回正直に実行するか（再帰的信頼の実挙動、未観測）。theatre 化の実害はここで確定する。
  - 上記「未解決の対立」3件（fail-open/closed の頻度パラメータ・robust vs floor・再帰的信頼の runtime 挙動）。

- **受容する残存リスク（コミットでユーザーが飲むもの・R1〜R11 台帳に完全化）**:
  - 【must-fix で閉じる】R1 staged（一般）＋ R4 staged pointer bump（#1 の `--cached` union に相乗り）。
  - 【観測へ】R7 resume-stale FP（experiment 観測窓→噛めば W2 hook-floor 前倒し）／再帰的信頼の runtime 実挙動（experiment 観測項目「実行有無」）／FP 実頻度・完走率影響（rollback トリガ）／複雑性 2.4〜5倍・verify 手動実行依存（CI/hook 未配線は W2+）。
  - 【受容・文書化】R2 submodule 内部（fail-open silent）／R5 実在 gitignore（fail-open）／R6 pre-existing-dirty（fail-open 最頻・頻度警告つき）／R11 symlink（fail-open）＝すべて git-oracle domain 境界。R3 submodule pointer bump（設計どおり健全）／R8 入れ子フェンス（主 fail-closed 安全側＋任意 hardening）／R9 case-rename／R10 net-zero＝fail-closed だが rare。L0 パイプライン 1/6（スコープ境界、hook-floor は錨として観測課題に接続）／7-4/8-2/6.5-2(C)/refactor-gate 再実装 entry 無検証（INNER_LOOP が部分安全網）／設計内 blocking 非対称（oracle 成熟度差で正当化、rollback トリガで可逆化が受容条件）／再帰的信頼のコア（不可避な信頼境界）。

- **追加探索が要る論点（deliberator 集約・実装は本レビューのスコープ外・gate が「確度向上のみ・必須でない」と分類済み）**:
  - **フィクスチャ2本追加で新規2穴を実証**: 「pre-existing-dirty ファイルへの虚偽申告（fail-open・R6）」「resume 中の外部 git 変化（fail-closed・R7）」を verify-deterministic-check.sh に追加 → 理論を実証に昇格（境界づけ・3層割付・新 must-fix ゼロの裁定は既に確定済みのため、これは確度向上）。
  - **staged 堅牢形の副作用検証**: 「pir2 開始前に無関係ファイルが stage 済み」フィクスチャ1本で pre/post 対称性を検証（未解決の対立2の決着材料）。
  - **resume 経路の pir2 SKILL.md 逐語確認**: RESUME_MODE と 6-3 checkbox の相互作用を Read し「resume 時 6-3 が強制再実行されるか」を確定（rubric #2 の中確信度判定を高/低に振る）。
