## 熟考レポート（ROUND 2 / 01）: W0+W1（6-3）の最終深レビュー ―― oracle 残存限界の完全境界づけ

### レンズ
**oracle 残存限界の完全境界づけ**（この推論の軸）。ROUND 1 結論「修正してコミット＋must-fix 3点」は据え置き、gate が rubric #1 を「部分」とした未境界づけ（submodule / 入れ子フェンス / 実在 gitignore / pre-existing-dirty・resume-stale）を方向つきで台帳化し、**新 must-fix 昇格の有無を裁定**するのが本ラウンドの唯一のタスク。

### 思考の起点（前提の確認）

- **context / exploration-01.md から確定的に言える事実（出典つき）**:
  - 実集合は `git diff --name-only --ignore-submodules=dirty`（unstaged）＋ `ls-files --others`（untracked）。**staged は対象外**（exp-01 L59, L84-86, L99-101）。
  - **submodule フィルタ（FIX-F 由来）**: `--ignore-submodules=dirty` は「submodule work tree 内部の非コミット変更を無視しつつ、pointer bump（親リポの記録コミット vs submodule HEAD の差）は親リポの1行として残す」。`=all` を選ぶと pointer bump まで消え正当申告が PHANTOM 化するため `dirty` を選択（exp-01 L81-83 のコメント逐語）。
  - **check-ignore 3分岐（3b, L134-159）**: exit 0=gitignore→untrackable / exit 1=非ignore→trackable / **exit 128（fatal, submodule 内パス）→untrackable**。
  - **test -f 実体確認（3c, L161-180）**: untrackable 申告は実ファイル存在を `test -f` で確認。存在すれば silent、非存在なら missing warn（**非ブロッキング**）。コメントに明記された残存限界: 「実在する gitignore 対象/リポ外ファイルへの虚偽申告（実体は在るが今回未変更）は test -f を通過し検出できない。設計 SSOT（Fable5 残存限界④⑥＝**fail-open な事故計器であり攻撃防御ではない**）と同型で受容する既知の限界」（L166-168 逐語）。
  - **submodule フィクスチャの実挙動（verify-deterministic-check.sh, L801-848）**: 親リポで pointer bump（unstaged）を作り、`mysub`（pointer）と `mysub/inner.md`（内部パス）を両方申告。**アサーション**: `mysub` → `claimed-trackable.list`（L845）、`mysub/inner.md` → `claimed-untrackable.list`（L846、「check-ignore exit 128 の3分岐判定」）、`phantom.list` は空（L847）、`claimed-untrackable-missing.list` は空（L848、mysub/inner.md は実在するため）。
  - **入れ子フェンスの既知限界（L117-123 逐語）**: フェンス除去は「行頭 ``` でトグル」の単純状態機械。4バッククォート内に3バッククォート ``` があるとトグル反転→decoy パス混入。「混入した decoy は git delta に無いため **PHANTOM 誤検知（偽陽性・fail-closed）** に倒れる」。同型限界が NO_OP 判定にも存在。
  - **verify script のフェンス parser は堅牢（L481-494, L538-555）**: commonmark 準拠で「trim 後に完全一致 ```bash / ``` の行のみ境界」。ランタイム抽出（reference の naive awk）とは**非対称**。
  - dotfiles は ai-* スキルが submodule 3本 live（LENS 指定）。本セッションは開始時に4ファイル既 `M`（context / position-1 L55）。
- **前提として置くもの（崩れると裁定が変わる）**:
  - 脅威モデル＝**accident, not adversary**（position-1 前提。実装 actor は「悪意の検出回避」でなく「実装したと誤認した善意の混乱」）。
  - 実集合 bash は逐語どおり動く（行レビュー PASS 済み）。フィクスチャのアサーションは実機で緑（exp-01 L856）。
  - must-fix の昇格基準＝ROUND 1 で staged FP に適用した3条件の連言: **(1) fail-closed（正常 run を誤ブロック）AND (2) common-path（単一の通常操作で発火）AND (3) clean fix が存在（偽陰性を生まず安価）**。
- **前回の到達点とゲート指摘**: position-1 は #1 を「充足」自己申告したが、gate は submodule（High・needs-thinking）/ 入れ子フェンス（Medium）/ 実在 gitignore（Medium）が方向つき境界づけ未了で **部分** と裁定。「再探索・fixture 実証は不要、oracle レンズの延長のみ」と明示。pre-existing-dirty・resume-stale は position-1「未解決の対立1」で方向づけ済みだが台帳への3層割付が未確定。

---

### 段階的推論

#### 段1: submodule の方向を確定する（gate の High を潰す核心）

gate は「submodule 内ファイルが post に出ず PHANTOM＝fail-closed FP でありうる（trackable 扱いなら hard fail / untrackable 扱いなら fail-open silent）」と**方向を未決のまま**High とした。コードとフィクスチャがこの二分岐を**決定的に解く**。

- **submodule 内部パス（`mysub/inner.md` 等）の虚偽申告** ―― 機序を追う:
  1. CLAIMED に `mysub/inner.md`。3b の `git check-ignore -q -- mysub/inner.md` は submodule 内パスに対し **fatal exit 128** を返す（`fatal: pathspec is in submodule`）→ `*)` 分岐 → **untrackable**（フィクスチャ L846 が実機で確認）。
  2. PHANTOM 照合（step4）は `claimed-trackable` のみ対象。`mysub/inner.md` は untrackable なので **PHANTOM 照合に一切入らない** → hard fail に**ならない**。
  3. 3c: `test -f "$PROJECT_ROOT/mysub/inner.md"` → 実在すれば silent（missing warn すら出ない、L848）。
  - **結論**: submodule 内部パスの虚偽申告は **fail-open silent**。gate が疑った「trackable→fail-closed hard fail」分岐は **起きない**。check-ignore が 128 を安定して返す限り submodule 内パスは常に untrackable。**方向は fail-open で確定**。
  - **飛躍の自己点検**: 「check-ignore が本当に 128 を返すか」に依存。フィクスチャ L846 が live submodule（初期化済み）で実機確認済み。dotfiles の ai-* も初期化済み live なので同挙動。未初期化 submodule の稀有ケースでも gitlink が index に在れば git は「is in submodule」を返す想定。→ 依存は薄く、裁定は安定。

- **submodule pointer bump（`mysub`）の申告** ―― 機序:
  1. `mysub`（gitlink パス）は非 ignore の追跡対象 → check-ignore exit 1 → **trackable**（L845）。
  2. `--ignore-submodules=dirty` は pointer bump を post に**残す**（L82-83）→ 正当な pointer bump 申告は post に一致 → PASS（L847）。
  3. **虚偽の pointer bump 申告**（bump してないのに `mysub` を申告）→ trackable かつ post に無い → **PHANTOM hard fail**。ただしこれは**真陽性（正しい捏造検出）であって FP ではない**。
  - **結論**: pointer bump は **trackable で検証可能**。正当申告はPASS、虚偽申告は正しく hard fail。**FIX-F（`=all` でなく `=dirty`）は pointer bump の fail-closed FP を意図的に防いだ正しい修正**（`=all` なら正当な bump が PHANTOM 化していた）。

- **唯一の fail-closed submodule シナリオ = staged pointer bump**:
  - submodule 内で commit し親リポで `git add mysub` すると pointer bump が **staged** になり、unstaged `git diff` に出ない → 正当申告が PHANTOM 化 = fail-closed FP。
  - **これは submodule 固有の新カテゴリではなく staged FP（must-fix #1）の submodule 経由の顕現**。must-fix #1（実集合に `--cached` を union）は staged pointer bump も同時に塞ぐ（`git diff --cached --name-only` は staged gitlink 変更を出す）。→ **submodule から新 must-fix は生じない。#1 に相乗り**。

- **裁定（段1）**: submodule 残存限界＝**fail-open（内部パス虚偽申告）**。staged FP と**同クラスではない**（あちらは fail-closed hard fail、こちらは fail-open silent）。gate が懸念した「未台帳の fail-closed hard fail」は**実在しない**。→ submodule は **受容・文書化**（実在 gitignore と同クラス）。fail-closed 軸（staged pointer bump）は must-fix #1 に包含。**新 must-fix なし**。

#### 段2: 入れ子フェンスの方向（両向き）を確定する

- **主方向 = fail-closed（偽 PHANTOM）**: reference L117-123 逐語のとおり、トグル反転で decoy パスが CLAIMED 混入 → git delta に無い → PHANTOM 誤検知（hard fail）。安全側（run を殺すが捏造を通さない）。
- **副方向 = fail-open（取り落とし）**: トグル反転が**本物の**変更ファイル一覧行を「フェンス内」と誤認し除去する parity のとき、真の CLAIMED が欠落。この場合:
  - 欠落したのが**正当申告**なら → 当該ファイルは delta に残り UNDECLARED warn（非ブロッキング）に落ちる＝軽微 fail-open（実害は「申告として検証されない」だけ、warn で可視）。
  - 欠落したのが**捏造申告**なら → PHANTOM 検出を取り逃す＝真の fail-open。ただし捏造行が入れ子フェンスの後に位置する必要があり、二重に contrived。
- **頻度**: 極低。変更ファイル一覧セクション内に4バッククォート入れ子フェンス例示がある実装レポートは実務上ほぼ発生しない。
- **裁定（段2）**: 主方向 fail-closed（安全側）＋副方向 fail-open だがトリガが極稀。**common-path でない**ため must-fix 基準（連言）を満たさない。→ **受容・文書化**（IMPL 05 で reference に既記載、台帳にも方向つきで載せる）。
  - **利用可能だが必須でない hardening**: verify script は既に堅牢 commonmark parser（trim 完全一致）を持つ（L538-555）。これをランタイム CLAIMED 抽出の awk に移植すれば入れ子フェンス限界を消せる。ただし common-path でないので must-fix ではなく **commit 後の任意 hardening（nice-to-have）**。ランタイム抽出と検証 script のパーサ非対称は台帳に注記する。

#### 段3: 実在 gitignore への虚偽申告 ―― fail-open の正典

- **機序**: 実在するがこの run で未変更の gitignore 対象ファイルを申告 → 3b check-ignore exit 0 → untrackable → PHANTOM 対象外 → 3c test -f 実在 → silent PASS。
- **方向**: **fail-open（捏造見逃し）**。reference L166-168 が明示的に「受容する既知の限界・Fable5 残存限界④⑥ 同型」と自己申告済み。
- **裁定（段3）**: **受容・文書化**。must-fix でない理由は頻度でなく**原理**: git を oracle にする以上、gitignore 対象は「git が差分を出さない」ことがまさに ignore の定義。「この run で変わったか」を知る唯一の信号（git）が原理的に盲。→ **clean fix が存在しない（domain 境界であって bug でない）**。段5 で正当化を一般化する。

#### 段4: pre-existing-dirty（fail-open）と resume-stale（fail-closed）の割付

- **pre-existing-dirty への虚偽申告（fail-open）**:
  - 機序: pre-set 時点で既 dirty のファイル F を「変更した」と申告、実際は未編集。PHANTOM は post 基準 → F は post に在る（前から dirty）→ 非 PHANTOM。delta=post−pre は F を除外（両方に在る）→ UNDECLARED も無反応。**F は両検査に完全不可視**。
  - 頻度: **最も高い fail-open**。active dev セッション中の pir2（＝dotfiles の日常。本セッションも開始時4 M）では pre-existing dirty 集合が非空で、そのぶん見逃し面が開く。
  - clean fix: **存在しない**。検出には pre-set 時に全 dirty ファイルの**内容ハッシュ**を取り post で比較する必要があり、name-set 照合から content 照合への質的複雑化（major）。
  - 裁定: **受容・文書化（頻度警告つき）**。fail-open は must-fix 基準（fail-closed 要件）を満たさず、かつ clean fix なし。ただし**最頻の fail-open として台帳で目立たせる**。閾値: 脅威モデルが adversarial 化 or content-hashing が安価化したら**最初に再訪すべき**穴。
- **resume 中の外部 git 変化（fail-closed・事象X 同クラス）**:
  - 機序: pre.list 記録後〜post-set 前に中断→resume 間に user が commit/stash → working tree clean → claimed 全件が偽 PHANTOM。
  - 頻度: 低（resume ＋ pre/post 窓での外部 git 操作の交差が必要）。
  - **recoverability**: fail-closed だが失敗パスは「レポート再注入→再実行→2回目 PHANTOM でユーザーゲート」であり、staged FP のような「再実行で直らない unrecoverable」ではなく**ユーザーゲートで脱出可能**。
  - 裁定: fail-closed だが **common-path でない ＆ ユーザーゲートで回復可能** → must-fix 基準の (2) を満たさない。→ **commit 後観測**（experimental.md の観測窓で resume-stale FP を計測。噛むなら W2 hook-floor を前倒し）。

#### 段5: fail-open 群を「受容」にする正当化の一般化（task 必須項目）

3つの fail-open（実在 gitignore・submodule 内部・pre-existing-dirty）を横断する**単一の原理**で受容を根拠づける:

> **git を oracle に選んだ以上、git の視野の外にある領域の虚偽申告は原理的に検出不能。** git の domain は「追跡ファイルの working-tree 状態（unstaged、＋#1 で staged）」。構造的に3領域が親リポ git の視野外に置かれる ――
> ① gitignore 対象（git が差分を出さない＝ignore の定義そのもの）
> ② submodule 内部（親が sub-repo に委譲。`--ignore-submodules=dirty` が oracle に「中を見るな」と明示指定）
> ③ 既 dirty ファイルの内容同一性（name-set 粒度では「再申告された既存 dirty」と「新規編集」を区別不能）

これらは**bug でも未修正ギャップでもなく、「git を oracle にする」という選択の定義的境界**。3c の `test -f` は best-effort の可視化層（out-of-domain 領域への「実在しないファイル」申告を warn で拾う）だが、「この run で変わったか」は verify できない ―― その唯一の信号（git）が設計上盲だから。これは設計 SSOT の残存限界④⑥（**fail-open な事故計器であり攻撃防御ではない**）と**厳密に同型**。

受容の**境界条件**（ここが崩れると受容が無効化）: 脅威モデル＝**accident, not adversary**。善意で混乱した implementer が「gitignore/submodule/既 dirty ファイルを変えた」と誤認するとき、その捏造が**out-of-domain 領域に完全に収まる**確率は accident モデル下では低い偶然（設計された回避ではない）。adversarial モデル（out-of-domain パスだけを狙って申告し検出回避）では**全 fail-open が同時に開く**が、それは受容済み脅威モデルの**外**（position-1 前提「N3 decoy-edit は scope 外」）。→ 脅威モデルが adversarial 化したら fail-open 群を content-hashing / hook-floor で塞ぐ W2+ 課題として文書化する。

---

### 反証・対立仮説の検討

- **最強の反論①「submodule は dotfiles で 3本 live・common だから staged と同じく must-fix にすべき」**:
  steelman: dotfiles は ai-* を submodule で持ち、pir2 が submodule 内を触る現実的シナリオがある。staged を「fail-closed かつ common」で must-fix にしたなら submodule も対称に扱え。
  → 反論への応答（なお結論が耐える）: **方向が違う**。コード＋フィクスチャ（L846: `mysub/inner.md`→untrackable）が証明するとおり submodule 内部は **fail-open silent** であって staged の **fail-closed hard fail** ではない。must-fix 基準の第一条件（fail-closed）を満たさない。唯一の fail-closed 軸（staged pointer bump）は既に #1 に包含。加えて頻度も過大評価: submodule 内編集は通常 **PROJECT_ROOT=submodule 自身**で pir2 を回す（その場合 submodule が top-level repo になり全て trackable で正常）。fail-open が噛むのは「PROJECT_ROOT=親 dotfiles かつ submodule 内パスを申告」という**狭い交差**のみ → common-path でもない。→ **must-fix 昇格は不当。受容・文書化が正しい**。gate の High は「方向未確定」ゆえの保守的 flag であり、方向を確定すれば fail-open に解決し High → 受容に落ちる。

- **最強の反論②「pre-existing-dirty は dotfiles で最頻の fail-open。高頻度の fail-open は must-fix にすべきでは」**:
  steelman: active dev で常に dirty がある dotfiles では pre-existing-dirty 見逃し面が毎 run 開く。頻度が高いなら塞ぐべき。
  → 応答: **頻度は fail-open を must-fix に変えない**。must-fix 基準は「fail-closed unrecoverable（正当 run を殺す）」に特化した基準。fail-open は**正当 run を一度も殺さない**（捏造を silent に通すだけ）。accident モデル下で「誤認捏造が pre-existing-dirty 集合に完全に当たる」確率は低い。かつ clean fix が無い（content-hashing への質的複雑化）。→ **受容だが最頻 fail-open として台帳で明示**し、adversarial 化 or content-hashing 安価化を再訪トリガに置く。結論（新 must-fix なし）は耐える。

- **対立仮説「入れ子フェンスは fail-open にも倒れうるから must-fix」**:
  → 棄却: 主方向は fail-closed（安全側）。fail-open 副方向はトリガが二重に contrived（入れ子フェンス例示＋捏造行がその後）で common-path から程遠い。堅牢 parser は既に verify script に在り移植は任意 hardening。→ 受容・文書化＋任意 hardening。

### 二次・三次の含意と境界条件

- **含意1（must-fix リストの安定）**: 4残存カテゴリの方向を確定した結果、**新 must-fix はゼロ**。ROUND 1 の must-fix 3点（staged 堅牢修正・experimental 登録・known-limitations）は完全に据え置きで足りる。gate の #1 部分判定は「境界づけ欠落」であって「結論の不成立」ではなかった、という gate 自身の自己申告（gate L7）と整合。
- **含意2（must-fix #1 の射程拡大）**: staged FP 修正（`--cached` union）が **staged pointer bump（submodule 経由の唯一の fail-closed 穴）も無償で塞ぐ**。#1 の価値は position-1 記載より広い。known-limitations にこの相乗り効果を1行足すと台帳が閉じる。
- **含意3（parser 非対称の技術的負債）**: 検証 script は堅牢 commonmark、ランタイム抽出は naive toggle。片方だけ堅牢という非対称は「検証は通るがランタイムで穴」を生む構造。commit 後 hardening 候補として台帳に記録。
- **境界条件（受容が無効化する条件）**:
  - 脅威モデルが **accident → adversary** に遷移: 全 fail-open（①②③）が同時に開く。受容の前提が崩れる → W2 で content-hashing / hook-floor 必須化。
  - **content-hashing が安価に**: pre-existing-dirty（最頻 fail-open）の clean fix が出現 → 受容から must-fix/観測に格上げ検討。
  - **run 母数が跳ねる**（epic が多数ネスト pir2 を駆動）: resume-stale の fail-closed FP 絶対数が増え commit 後観測の閾値が噛む → hook-floor 前倒し。

---

### oracle 残存限界・完全台帳（(a)機序 (b)方向 (c)頻度 (d)3層割付 (e)理由）

| # | 残存限界 | (a)機序 | (b)方向 | (c)頻度 | (d)割付 | (e)理由 |
|---|---|---|---|---|---|---|
| R1 | staged 変更（一般） | `git add` で unstaged diff から消失→正当申告が PHANTOM 化・再実行で直らない | **fail-closed**（unrecoverable） | 中（単一コマンド `git add`） | **must-fix**（#1・ROUND1 既定） | fail-closed AND common AND clean fix（`--cached` を pre/post 両側 union、staged⊆実変更ゆえ偽陰性なし）＝3条件連言を満たす唯一の穴 |
| R2 | **submodule 内部パス虚偽申告** | check-ignore exit128→untrackable→PHANTOM対象外／test-f 実在→silent（fixture L846/848 で実証） | **fail-open** silent | 低（PROJECT_ROOT=親 かつ submodule 内パス申告の狭い交差） | **受容・文書化** | 内部は git-parent の domain 外（`--ignore-submodules=dirty` が明示除外）。gate 懸念の fail-closed hard fail は check-ignore128 が untrackable に落とすため**起きない**。実在 gitignore と同クラス |
| R3 | submodule pointer bump（正当/虚偽） | trackable（check-ignore exit1）／`=dirty` が post に残す | 正当→PASS・虚偽→**正しく hard fail（真陽性）** | 低 | **受容**（設計どおり健全） | FIX-F（`=all`でなく`=dirty`）が pointer bump の fail-closed FP を意図的に予防済み。FP でも穴でもない |
| R4 | submodule staged pointer bump | 親で `git add mysub`→staged→unstaged diff に不出 | **fail-closed** | 低 | **must-fix #1 に包含** | 独立カテゴリでなく staged FP の submodule 顕現。`--cached` union が同時に塞ぐ（新 must-fix 不要） |
| R5 | **実在 gitignore への虚偽申告** | check-ignore exit0→untrackable→PHANTOM対象外／test-f 実在→silent（L166-168） | **fail-open** silent | 低〜中（bookkeeping 系申告時） | **受容・文書化** | git は ignore 対象の差分を原理的に出さない＝oracle domain 外。clean fix 不在（bug でなく境界）。SSOT 残存限界④⑥ 同型 |
| R6 | **pre-existing-dirty への虚偽申告** | 既 dirty F を申告・未編集→post に在り非PHANTOM／delta 除外で UNDECLARED も無反応→両検査不可視 | **fail-open** silent | **最高**（active dev の既 dirty 集合。本セッションも開始時4 M） | **受容・文書化（頻度警告つき）** | name-set 粒度では「再申告された既存 dirty」と「新規編集」を区別不能＝git domain 外の内容同一性。clean fix は content-hashing で質的複雑化。**adversarial 化 or hashing 安価化時に最初に再訪** |
| R7 | resume 中の外部 git 変化 | pre.list 後〜post 前に中断→resume 間に user commit/stash→tree clean→claimed 全件が偽 PHANTOM | **fail-closed** | 低（resume×外部 git 操作の交差） | **commit 後観測** | fail-closed だが common でなく、失敗パスがユーザーゲートで**回復可能**（unrecoverable でない）。observe 窓で FP 計測、噛めば W2 hook-floor 前倒し |
| R8 | 入れ子フェンス（decoy 混入） | naive toggle awk のトグル反転で decoy が CLAIMED 混入→git delta に無く PHANTOM（L117-123） | **主 fail-closed（偽 PHANTOM）**／副 fail-open（真行取り落とし） | 極低（変更一覧内の4バッククォート入れ子例示） | **受容・文書化（＋任意 hardening）** | 主方向は安全側。副方向はトリガ二重 contrived で common でない。堅牢 parser は verify script に既存（L538-555）→ランタイム awk への移植は任意 hardening（parser 非対称を注記） |
| R9 | case-only rename（APFS） | 大文字小文字のみ rename は git シグナル空→正当変更が PHANTOM | **fail-closed** FP | 低（macOS FS 依存の稀操作） | **受容・文書化** | common でなく（rename の稀 subset）clean fix が非自明。ROUND1 台帳既載 |
| R10 | net-zero 編集 | 編集して元に戻す等 delta 空→NO_OP 宣言なしで PHANTOM | **fail-closed** FP | 極低 | **受容・文書化** | ROUND1 台帳既載。NO_OP 免除で回避可 |
| R11 | symlink 経由パス | symlink 先の実体が git 追跡外だと申告が延べ検証不能 | **fail-open** | 極低 | **受容・文書化** | git domain 外の同クラス。ROUND1 台帳既載 |

**中央裁定（task 必須）**: 新たに must-fix へ昇格すべき残存限界は **ゼロ**。理由 ―― must-fix 基準（fail-closed AND common-path AND clean-fix 連言）を満たすのは R1（staged 一般）のみで、これは ROUND1 で既に must-fix #1 化済み。gate が High とした submodule（R2）は check-ignore128→untrackable により **fail-open** で確定（staged と非同クラス）、fail-closed 軸（R4 staged pointer bump）は #1 に相乗りで無償閉塞。他は fail-open（受容）か、fail-closed でも rare/recoverable（観測）。→ **ROUND1 の must-fix 3点は完全据え置きで #1 台帳が閉じる**。

---

### rubric への寄与（現時点）

| rubric 基準 | 寄与/未達 | 根拠 |
|---|---|---|
| #1 oracle 健全性（残存限界を fail-open/closed 方向つきで境界づけ・受容可能性） | **寄与（完成）** | gate 名指しの未境界づけ4カテゴリを全て方向つき台帳化（R2 submodule=fail-open 確定・R5 gitignore=fail-open・R8 入れ子フェンス=主fail-closed・R6/R7 pre-existing-dirty/resume-stale）。fail-open 群の受容を「git-oracle の定義的 domain 境界」で一般化（段5）。新 must-fix ゼロを連言基準で裁定。3層割付を11穴で完備 |
| #6 採用/コミット推奨・受容残存リスク列挙 | 寄与 | 受容残存リスク台帳を R1-R11 で完全化。ユーザーが自環境（submodule live）で飲む fail-open を明示的に列挙 → gate の「ユーザーが live な残存リスクを知らされずコミット」懸念を解消 |
| #7 プロセス自己言及 | 部分（補強） | FIX-F（`--ignore-submodules=dirty`）が pointer bump の fail-closed FP を意図的に予防した「正しい人間 fix」だったことを R3 で機序確認 ―― fix ループが regression だけでなく正しい防御も生んだ両面性を補強 |

（#2〜#5 は gate が既に充足判定。本ラウンドは #1 完成に限定し据え置き。）

### 事実と推測の仕分け

- **事実（exploration-01.md / context に出典あり）**: `--ignore-submodules=dirty` の pointer bump 保持挙動とコメント意図（L81-83）。check-ignore 3分岐（L134-159）。test -f 実体確認と残存限界コメント（L161-180）。submodule フィクスチャのアサーション結果 ―― `mysub`→trackable / `mysub/inner.md`→untrackable / phantom 空 / missing 空（L845-848）。入れ子フェンス方向＝fail-closed の reference 記載（L117-123）。verify script の堅牢 parser（L538-555）。SSOT 残存限界④⑥＝fail-open 事故計器の引用（L166-168）。本セッション開始時4 M（position-1 L55）。
- **推論（deliberator の解釈）**: 「submodule 内部虚偽申告は check-ignore128 により **fail-open で確定、staged と非同クラス**」（機序＋フィクスチャからの演繹）。「staged pointer bump は must-fix #1 に無償相乗り」（`--cached` が staged gitlink を出す推論）。「3 fail-open は単一原理＝git-oracle domain 境界で受容」（一般化）。「新 must-fix ゼロ」（連言基準の適用）。「pre-existing-dirty が最頻 fail-open」（active dev の dirty 集合からの推論、未測定）。「submodule fail-open は PROJECT_ROOT=親×内部パス申告の狭い交差ゆえ低頻度」（運用パターンの推論、未測定）。

### 現時点の確信度と残る不確実性

- **確信度: 高** ―― submodule の方向確定（fail-open）はコメント・コード・**実機フィクスチャ L846/848 の3点で裏取り済み**で、gate の二分岐（trackable/untrackable）を決定的に解いた。新 must-fix ゼロの裁定は連言基準の機械的適用で、fail-open を must-fix にしない論理（fail-open は正当 run を殺さない）は堅牢。fail-open 受容の一般化（git domain 境界）は SSOT 残存限界④⑥ の逐語引用に接地。
- **残る不確実性（結論非依存の頻度パラメータ）**:
  - R6 pre-existing-dirty が「最頻」という順位は active dev の dirty 集合サイズに依存し**未測定**（accident 捏造が dirty 集合に当たる base rate も未測定）。ただし fail-open→受容の裁定自体は頻度に非依存で耐える。
  - R2 submodule fail-open の頻度「低」は「submodule 編集は PROJECT_ROOT=submodule で回す」という運用推定に依存し未実証。だが方向＝fail-open の裁定は頻度と独立。
  - これらは gate が「次ラウンドで潰さなくてよい確度向上タスク」に分類した fixture 実証（pre-existing-dirty FN / resume-stale FP）で理論→実証に昇格する。**本ラウンドの境界づけ（方向・割付）は fixture 未了でも成立**。

### 追加探索が必要な論点
- なし（gate 指示どおり oracle レンズの延長のみで完結。再探索・fixture 追跡は不要と gate が明示。fixture 2本の実証は「受容/観測の理論→実証」への確度向上であり、境界づけ・3層割付・新 must-fix ゼロの裁定はコード＋実機フィクスチャで既に確定している）。
