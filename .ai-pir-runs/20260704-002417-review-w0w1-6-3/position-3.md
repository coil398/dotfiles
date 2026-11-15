# position（ROUND 3 / fable-solo 決定版）: W0+W1（6-3 決定論的完了検証）の最終深レビュー ―― コミット/採用可否と残存リスク

### レンズ
第一原理・機序 / 反証・レッドチーム / 二次波及・境界条件 / 採用判断・優先度設計 / oracle 残存限界 ―― の5レンズを1体で内省的に通した Fable5 単独の決定版。opus-panel（position-2 まで）を下地として Read 済みだが、各裁定は逐語コード（exploration-01.md 995行）から独立に再導出した。

---

## 結論（採用勧告・1つに確定）

**修正してコミット**。（そのままコミット ×・保留 ×・ロールバック ×。確信度: 高）

opus-panel の position-2 と**独立に同一の勧告に到達**した。ただし追認一色ではない ―― 本 position は position-2 に対し **訂正2件**（過大主張の修正）、**台帳2行の追加**（R12/R13）、**must-fix #1 の完了定義の強化**（フィクスチャ内包）を加える。差分明細は末尾。

- **なぜロールバックでないか**（独立再導出・高確信）: 事象X（resume 時捏造→reviewer 全FAIL→19分迷走）は実損が観測済み。oracle（git working-tree 集合照合）は検証の第一原理 ―― 主張 P と独立観測 O の突き合わせで、O を「編集という物理作用の副産物（dirty 状態）」に置いたことで独立性・真正性を満たす ―― に照らして健全。Anthropic Outcome/State-check・Unit42 に整合し、行レビューは全 PASS。穴は既知＋新規に境界づけられ、fail-closed 側の common-path 穴は1点（staged）で安価に塞げる。**6-3 は epic（executions 0）ではなく pir2/pir2codex の初回実装点＝ホットパスに乗るため、epic が廃止されても単体で元が取れる**。
- **なぜそのままコミットでないか**（独立再導出・高確信）: staged FP（R1）は「単一の無害コマンド `git add` で発火し、**再実行で直らない** fail-closed hard fail」＝ホットパスで正当な run を殺す unrecoverable 地雷。「implementer は stage しない」前提は `implementer.md` に禁止 0 件・Claude 側未検証の**願望**であり、この未検証仮定が行レビュー4ラウンドを生き延びた事実自体が prose-confidence の限界を示す。加えて観測 harness ゼロ（experimental.md 未登録）は 6-3 を実運用上 **unfalsifiable** にする ―― 有害でも検知する材料が集まらない。
- **なぜ保留でないか**（fable 追加の明示棄却）: 保留で得られる追加情報が存在しない。最大の未知（FP 実頻度・L0 が 6-3 bash を毎回走らせるか）は**実 run の蓄積でしか測れず**、保留は「観測もされない状態」を延長するだけ。must-fix は小さく、待つ利益がコストを上回る局面がない。

**併用推奨（継承）**: W0（citation 衛生・epic sanitized_cwd 登録）と W1（6-3 一式）は**分割コミット**（W1 に FP 再発時、6-3 だけを surgical に revert できる blast radius 最小化）。コミット時は `git add` をファイル個別指定し、本タスク無関係の残差分（`.claude/agents/epic-planner.md` / `.claude/skills/epic/` / `.gitignore` / `CLAUDE.md` / `.claude/settings.json` 等、exploration-01 冒頭で無関係と確認済み）を**巻き込まない**。`sanitized-cwd.md` / `verify-sanitized-cwd.sh` の epic 登録行は W0 側。

---

## コミット前 must-fix（3点・件数据え置き / 内容を2点強化）

opus の3点リストを**過不足の裁定として「件数は据え置き」**とする（増やさない・減らさない）。ただし #1 の完了定義と #3 の記載項目を強化する。

### must-fix #1: staged FP を堅牢に塞ぐ（＋同一コミットにフィクスチャを内包）

`deterministic-completion-check.md` の実集合に `git -C … -c core.quotePath=false diff --cached --name-only` を **pre.list / post.list の両側に union**（「staged は対象外」コメント撤回）。pre 片側だけだと実行前から staged のファイルが delta（UNDECLARED warn）に誤混入する ―― FIX-5/FIX-F regression の再演になるため両側必須（継承・正当）。この修正は submodule staged pointer bump（R4）も無償で塞ぐ（継承・正当）。

> ⚠️ **訂正1（opus の過大主張の修正）**: position-2 の健全性証明「staged ⊆ 実際に変更されたファイルなので **偽陰性を生まない**」は**厳密には偽**。この証明は「implementer が変更したファイル」と「誰かが stage したファイル」を混同している。run 開始前からユーザーが stage していたファイル F への虚偽申告は、修正前なら F ∉ post → PHANTOM（偶発的な真陽性）だったが、修正後は F ∈ post（--cached 経由）→ **silent PASS（新規の偽陰性）**になる。正確な正当化は「**#1 は fail-closed FP（common・unrecoverable）を fail-open FN（rare・pre-existing-staged 集合限定）に転換する修正**」であり、その FN は R6（pre-existing-dirty）と**同型・同一の受容根拠**（git-oracle domain 境界＋accident 脅威モデル）に合流する。結論（#1 実施）は不変だが、known-limitations にはこの副作用を明記する（#3 (g)）。

**完了定義（DoD）の強化 ―― フィクスチャ2本を同一コミットに内包する**:
1. 「implementer が自分の変更を stage して申告」→ PHANTOM にならず PASS すること
2. 「pir2 開始前に無関係ファイルが stage 済み」→ delta に誤混入しない（pre/post 対称性）こと

> ❌ gate-1 はフィクスチャ追加を「確度向上タスク（必須でない）」に分類したが、あの分類は**既存の穴を文書化するための実証**に対するもの。must-fix #1 は**検証 bash そのものを変更する**ため事情が異なる ―― un-fixtured な fix こそが FIX-5/FIX-F で regression を生んだ当のパターンであり、rubric #7 の教訓（prose-confidence でなくコード接地検証）を #1 自身に適用しないのは自己矛盾になる。既存6フィクスチャは `--cached` 挙動を1本もカバーしないため、フィクスチャなしの #1 は「検証されない修正」として出荷される。→ **フィクスチャは #1 の DoD の一部**（第4の must-fix ではない）。

補助として `implementer.md` に「申告ファイルを自分で `git add` しない」1行（prose は補助・主はコード接地。継承）。

### must-fix #2: experimental.md に 6-3 を Active 実験登録＋rollback トリガ

観測項目: **(a) FP 実発生率 (b) L0 が 6-3 bash を実際に実行したか（verify-*.list の生成有無） (c) 【fable 追加】PHANTOM 発火時の原因分類**（真捏造 / staged 系 / 申告規律 R13 / resume-stale R7 / その他）。rollback トリガ「観測窓 N run で FP 閾値超なら hard-fail→warn 降格」明記（継承）。観測窓は R7・R12 の計測窓を兼ねる。

> ⚠️ **訂正2（opus の過大主張の修正・観測項目 (b) の格上げ）**: position-2 段2 の「事象X の L0 は嘘つきでなく**誤認者**で、誤認者は検証を避けない」という動機論は**過大**。事象X の署名は「tool 呼び出しの prose 幻覚（実際には発行せず、結果テキストだけ生成）」であり、この失敗モードは **6-3 の bash 自体にも同型に適用される** ―― 誤認 L0 は「6-3 を走らせた・PASS だった」を同じ機序で幻覚しうる。頼れるのは動機でなく機序: 「6-3 導入後は、幻覚実行をすると **RUN_DIR に verify-*.list が物理的に存在しない**という、事後に決定論検証可能な痕跡が初めて残る」。つまり 6-3 が L0 自己捏造に対して与えるのは防止でなく**可監査性**であり、その可監査性を実際に監査するのが観測項目 (b)。→ (b) は nice-to-have でなく **load-bearing**（これが無いと再帰的信頼の受容根拠が崩れる）。W2 hook-floor はこの監査の機械化。

### must-fix #3: known-limitations 明記（`deterministic-completion-check.md`）

完全台帳 R1〜R13（下記）を方向つきで転記。opus の (a)〜(f)（fail-open 群の単一原理束ね / fail-closed rare 群の理由 / #1 の R4 相乗り / parser 非対称 / 再帰的信頼の錨 / pipeline 1/6）に加え、fable 追加3点:
- **(g)** #1 の副作用: pre-existing-**staged** への虚偽申告が新規 fail-open として R6 に合流する（意図的トレードオフ・fail-closed FP の fail-open 転換）。
- **(h)** submodule 方向確定（R2 = fail-open）は `check-ignore` の **exit 128 という観測挙動に接地**しており、文書化された契約ではない。git 将来版で exit 1（trackable）に変われば方向が fail-closed hard fail に反転する ―― verify スクリプトのフィクスチャ L846 が回帰検知の砦であることを注記。
- **(i)** フィクスチャ盲点の**系統性**: 既存6本はすべて「機構が宣伝する挙動の確認型」（PHANTOM/UNDECLARED/NO_OP/非ASCII/フェンス/submodule）で、「環境が clean-tree 前提とズレる干渉型」（staged / case-rename / pre-existing-dirty / resume-stale）を**ゼロカバー**。今後 verify スクリプトを拡張する際は「設計の機能リスト」でなく「clean-tree 前提の破れ方の列挙」からフィクスチャを起こすこと（検証設計の教訓として記録）。

---

## 主要な論拠（段1〜7。継承分は圧縮、訂正・新規は明示）

- **段1（継承・第一原理）**: 検証の必要条件は独立性と真正性。6-3 は独立観測 O を git delta（編集作用の副産物）に置き、L2 が自己申告で偽造できないチャネルを確立した。事象X で reviewer が空振りしたのは入力が L2 自己申告で独立性を欠いたから。oracle の選択自体は健全。
- **段2'（訂正・再帰的信頼の裁定）**: 「6-3 の実行を誰が検証するか」は**スコープ外として正当・設計欠陥ではない**（全検証チェーンはどこかで接地する。同一主体が実行と検証を兼ねると独立性が破れる自己言及構造は 6-3 固有でない）。ただし受容は**無条件でない**: 「誤認者は検証を避けない」という動機的保証には依拠しない（訂正2）。受容の実質的根拠は (i) 幻覚実行が verify-*.list 不在という機械検出可能な痕跡を残すこと、(ii) その痕跡を観測項目 (b) が監査し、(iii) W2/W5 hook-floor が監査を runtime 機械化するという**3段の可監査性チェーン**。この意味で 6-3 は「completion verifier」でなく「**phantom-claim floor**」（6次元中 file-set 存在の1次元のみ・substance 非検証）であり、この再ラベルの known-limitations 明記（#3 (e)）が過大広告を正す。
- **段3（継承＋訂正1）**: staged FP の must-fix 判定は頻度に非依存でロバスト（単一共通コマンド × unrecoverable hard fail × 安価な修正の連言）。ただし修正の健全性証明は「偽陰性ゼロ」でなく「偽陰性の増分が pre-existing-staged 集合に限定され R6 と同型受容」に修正する。
- **段4（継承＋新規 R12）**: 通常 run へのコスト主成分はレイテンシ（sub-second・赤ニシン）でなく、pre-set（6-1）と post-set（6-3）が subagent 実行を挟んで時間分割されることによる **L0 脱落面**。脱落時の設計は「縮退運転なし・6-1 に戻り implementer 全再実行」（reference 手順0＋blockquote 逐語）。PHANTOM 照合だけなら post 単独で計算可能なのに縮退を禁じたのは fail-loud の意図的選択で正当だが、**honest run が L0 の bookkeeping 1手順の失念で implementer フル再実行を強制される**コストは台帳に載るべき（R12・opus 台帳に欠落）。観測窓で pre-set 記録漏れの実発生を計測し、頻発するなら「PHANTOM-only 縮退モード＋UNDECLARED 判定不能 warn」か pre-set 記録の hook 化を W2 候補とする。
- **段5（継承・プロセス自己言及）**: FIX-5/FIX-F という人間主導 fix 指示自体が regression を作り、後段レビューと verify スクリプト（機械検証）が捕捉した。prose 指示駆動の修正は可謬 ―― 6-3 が守る失敗モード（prose 通り動いたつもりで outcome が誤り）と同型。ゆえに prose の塞ぎ方（git add 禁止1行）よりコード接地（--cached union）を優先し、**さらに同じ教訓を #1 自身に適用してフィクスチャを DoD に内包する**（must-fix #1 強化の根拠）。
- **段6（継承・fail-open 受容の一般原理）**: fail-open 群（R2 submodule 内部・R5 実在 gitignore・R6 pre-existing-dirty・R11 symlink、＋#1 適用後の pre-existing-staged）は単一原理で受容される ―― **git を oracle に選んだ以上、git の視野の外（ignore 対象 / submodule 内部 / 既 dirty・既 staged の内容同一性）への虚偽申告は原理的に検出不能**。bug でも未修正ギャップでもなく oracle 選択の定義的 domain 境界。受容の境界条件は脅威モデル = accident, not adversary。adversarial 化すると全 fail-open が同時に開き、content-hashing / hook-floor が W2+ で必須化する。
- **段7（新規・申告規律の税 R13）**: PHANTOM 発火の一部は捏造でも環境干渉でもなく「**申告フォーマットの逸脱**」を検知する ―― ディレクトリ申告（`src/foo/`）・glob（`src/*.ts`）・typo パスは trackable 扱いで post に一致せず PHANTOM に落ちる。ただし staged FP と決定的に違い、失敗パスの再実行プロンプト「**申告を実体に一致させよ**」が明示するとおり**再実行1回の申告訂正で in-band 回復する**（unrecoverable でない）。これは欠陥というより「申告規律の強制」という副次機能だが、**FP 統計上は PHANTOM に計上される**ため、観測項目 (c) の原因分類で真捏造と区別して記録しないと rollback トリガの閾値判定が汚染される（must-fix #2 に (c) を足した根拠）。稀な亜種（埋め込み plain git repo のネスト）も同クラスに footnote。

---

## oracle 残存限界・完全台帳（R1〜R13・方向つき / 3層割付）【fable 完成版】

R1〜R11 は position-2 / D-2-01 の台帳を検証のうえ**追認**（各行の機序・方向を exploration-01 の逐語 bash から独立に再トレースし、反例を発見しなかった）。R6 に注記拡張、R12/R13 を新規追加。

| # | 残存限界 | (a) 機序 | (b) 方向 | (c) 頻度 | (d) 割付 | (e) 理由・注記 |
|---|---|---|---|---|---|---|
| R1 | staged 変更（一般） | `git add` で unstaged diff から消失 → 正当申告が PHANTOM 化・再実行で直らない | **fail-closed**（unrecoverable） | 中 | **must-fix #1** | fail-closed AND common AND clean-fix の3条件連言を満たす唯一の穴。DoD にフィクスチャ2本内包 |
| R2 | submodule 内部パス虚偽申告 | check-ignore exit 128 → untrackable → PHANTOM 対象外 / test -f 実在 → silent（fixture L846/848 実証） | **fail-open** silent | 低（PROJECT_ROOT=親 × 内部パス申告の狭い交差） | **受容・文書化** | git-parent の domain 外。gate 懸念の fail-closed 分岐は起きない。**(h) exit 128 は観測挙動接地・版依存を注記** |
| R3 | submodule pointer bump | trackable / `=dirty` が post に残す | 正当→PASS・虚偽→**正しく hard fail（真陽性）** | 低 | **受容**（設計どおり健全） | FIX-F が `=all` の fail-closed FP を意図的に予防。穴でない |
| R4 | submodule staged pointer bump | 親で `git add mysub` → unstaged diff に不出 | **fail-closed** | 低 | **must-fix #1 に包含** | staged FP の submodule 顕現。`--cached` union が同時閉塞 |
| R5 | 実在 gitignore への虚偽申告 | check-ignore exit 0 → untrackable / test -f 実在 → silent（L166-168 自己申告済み） | **fail-open** silent | 低〜中 | **受容・文書化** | ignore の定義そのもの＝oracle domain 外。clean fix 不在 |
| R6 | pre-existing-dirty への虚偽申告 | 既 dirty F を申告・未編集 → post に在り非 PHANTOM / delta 除外で UNDECLARED も無反応 → 両検査不可視 | **fail-open** silent | **最高**（active dev の既 dirty 集合） | **受容・文書化（頻度警告つき）** | name-set 粒度の原理的盲点。**注記拡張: #1 適用後は pre-existing-staged も本行に合流（(g)）**。adversarial 化 or content-hashing 安価化で最初に再訪 |
| R7 | resume 中の外部 git 変化 | pre.list 後〜post 前の中断中に user commit/stash → tree clean → claimed 全件が偽 PHANTOM | **fail-closed** | 低 | **commit 後観測**（#2 の窓） | rare かつユーザーゲートで回復可能。噛めば W2 hook-floor 前倒し |
| R8 | 入れ子フェンス（decoy 混入） | naive toggle awk の parity 反転で decoy が CLAIMED 混入 → PHANTOM（L117-123） | **主 fail-closed** / 副 fail-open | 極低 | **受容・文書化＋任意 hardening** | 主方向は安全側。堅牢 parser は verify script に既存（L538-555）→ ランタイム移植は任意。parser 非対称を注記 |
| R9 | case-only rename（APFS） | 大小のみ rename は git シグナル空 → PHANTOM | **fail-closed** | 低（稀操作 × FS 依存） | **受容・文書化** | rare・clean fix 非自明 |
| R10 | net-zero 編集 | 編集して元に戻す → delta 空 → NO_OP 宣言なしで PHANTOM | **fail-closed** | 極低 | **受容・文書化** | NO_OP 免除で回避可 |
| R11 | symlink 経由パス | symlink 先実体が git 追跡外 → 検証不能 | **fail-open** | 極低 | **受容・文書化** | git domain 外の同クラス |
| **R12**【新規】 | pre-set 記録漏れ | L0 が 6-1 の pre-set を失念 → 手順0 ERROR → 縮退運転なしで **implementer 全再実行**を強制（reference 逐語） | **fail-closed 系**（honest run コスト。hard fail でなく回復可能・正当性無傷） | 低〜中（L0 の prose 遵守率に依存・未測定） | **commit 後観測**（#2 の窓で発生数を計測） | fail-loud の意図的設計で correctness は守られるが、コストが台帳外だと「honest run の主要停止要因」が観測から漏れる。頻発時の hardening 候補: PHANTOM-only 縮退モード or pre-set の hook 化（W2） |
| **R13**【新規】 | 申告粒度の不一致（ディレクトリ / glob / typo 申告） | `src/foo/` 等は trackable 扱いだが post のファイル単位エントリと不一致 → PHANTOM | **fail-closed** | 中（申告規律に依存） | **受容**（in-band 回復・申告規律強制の副次機能） | staged と違い**再実行1回の申告訂正で回復**（unrecoverable でない）。ただし FP 統計を汚染するため観測項目 (c) で真捏造と区別記録。稀な亜種: 埋め込み plain git repo のネストパス申告も同クラス |

**中央裁定（追認・独立再導出）**: 新規2行（R12/R13）を加えても **must-fix への新昇格はゼロ**。must-fix 基準（fail-closed AND common-path AND clean-fix AND unrecoverable の連言）を満たすのは R1 のみ ―― R12 は correctness 無傷・回復可能・fail-loud の意図的設計、R13 は in-band 回復可能で「直らない hard fail」でない。fail-open 群は正当 run を一度も殺さないため頻度に関わらず must-fix 対象外（頻度は受容の警告レベルにのみ効く）。→ **must-fix 3点は件数据え置きで台帳が閉じる**。

---

## 再帰的信頼（6-3 の実行を誰が検証するか）の裁定 ―― 確定

**スコープ外として正当・設計欠陥ではない**（確信度: 高）。ただし**条件つき受容**であり、無条件の受容ではない。

- 正当である理由: 同一主体 L0 が検証と実行を兼ねると独立性が破れる ―― これは 6-3 固有の欠陥でなく、あらゆる検証チェーンが持つ接地点の問題。6-3 に「自分自身の実行の検証」を要求するのは論理的に達成不可能なものの要求。
- **ただし opus の「誤認者は検証を避けない」には依拠しない**（訂正2）: 事象X の署名（tool 呼び出しの prose 幻覚）は 6-3 の bash にも同型適用され、誤認 L0 は 6-3 の実行と PASS を同じ機序で幻覚しうる。受容の実質的根拠は動機でなく**可監査性の3段チェーン**: ① 幻覚実行は verify-*.list の物理不在という決定論検出可能な痕跡を残す → ② 観測項目 (b) がそれを監査する（**load-bearing**） → ③ W2/W5 hook-floor が監査を runtime 機械化する。①だけでは「誰も見ない痕跡」で theatre 化するため、**②が must-fix #2 に入っていることが受容の成立条件**。②で破綻（L0 が体系的に 6-3 を走らせない）が観測されたら hook-floor を前倒しする。
- 過大広告の訂正: 6-3 は「事象X を直す」のでなく「事象X の**兄弟**（L2 捏造、および L0 が誠実実行した場合の L0 誤認）を直し、L0 自己捏造には可監査性を与える」。この再ラベル（phantom-claim floor）を known-limitations に明記する（#3）。

---

## 過剰/過小の裁定（rubric #5）＋プロセス自己言及（rubric #7）

**裁定（追認＋深化）**: 機構コアは proportionate・浪費はプロセスに集中・検証は FP カバレッジが過小。

- **「executions 0 にやり過ぎ」は対象の取り違えとして棄却**（追認・高確信）: 6-3 は epic（0回）でなく pir2/pir2codex の初回実装点＝ホットパスに乗る。ホットパスの blocking ゲートに verify スクリプト＋フィクスチャは釣り合う投資。
- **pipeline 1/6 は過小でなくスコープ境界**（追認）: 良いインクリメントは1手順を完全にやる。残り5手順（契約見出し grep・ARTIFACTS・hook floor・STATUS 不変条件・台帳）は plan 明示の W2+。W2 とのコード非再利用は debt でなく技術（git 集合演算）＋共通プロトコル doc の転移。
- **真の過剰 = 人間 fix ループの往復**（追認）: FIX-5（累積）→ regression、FIX-F（submodule）→ 正しい防御と regression の両面。5実装ラウンドの一部は自己誘発 regression の手戻り。
- **真の過小 = フィクスチャの FP カバレッジ、しかも盲点は系統的**（深化・fable 追加）: 6本すべてが「機構の宣伝挙動の確認型」で、「clean-tree 前提の破れ方」（staged / case-rename / pre-existing-dirty / resume-stale）を1本もカバーしない。盲点が偶発でなく**フィクスチャの導出方法（設計の機能リストから起こした）に由来する系統的なもの**である点が教訓 ―― 今後は「前提の破れ方の列挙」から起こす（#3 (i) に記録）。
- **プロセス自己言及のメタ結論**: (1) prose 指示駆動の fix は可謬（FIX-5/FIX-F 実証）→ コード接地修正を優先（#1 堅牢形）＋ **fix 自身にフィクスチャを付ける**（#1 DoD 内包）。(2) verify スクリプトが自分の開発バグを dev-time で捕捉した事実は 6-3 の価値命題の正の実例だが、dev-time の機械検証成功は runtime の再帰的信頼を保証しない（過度一般化しない）。(3) 「行レビュー全 PASS」の prose-confidence は出荷十分条件でない ―― staged という未検証仮定が4ラウンド生き延び、実機プロービング（exp-03）が発見した。発話でなく状態を突くことの優位の、本開発内での再演。(4) 【fable 追加】本ラウンド自体の含意: opus-panel と独立の fable 単独パスが同一勧告に到達しつつ過大主張2件を検出したことは、「同一材料への独立検証者の付加価値は結論の変更でなく**正当化の修正**に現れる」ことの実例 ―― 6-3 の設計思想（独立チャネルの検証）とプロセスが自己整合。

---

## 受容する残存リスク台帳（コミットでユーザーが飲むもの・3層）

- **【must-fix で閉じる】** R1 staged（一般）＋ R4 staged pointer bump（#1 の `--cached` union・フィクスチャ2本つき）。
- **【観測へ（must-fix #2 の窓）】** R7 resume-stale FP ／ **R12 pre-set 記録漏れの発生数**（新規）／ L0 の 6-3 実行有無 = verify-*.list 生成監査（**load-bearing**）／ FP 実発生率と**原因分類 (c)**（R13 申告規律起因を真捏造と区別）→ rollback トリガ（hard-fail→warn 降格）に接続 ／ 複雑性 2.4〜5倍・verify 手動実行依存（CI/hook 配線は W2+）。
- **【受容・文書化】** R2 submodule 内部（fail-open・exit 128 版依存注記つき）／ R5 実在 gitignore（fail-open）／ R6 pre-existing-dirty（fail-open 最頻・**#1 適用後は pre-existing-staged も合流**）／ R11 symlink（fail-open）＝ git-oracle domain 境界の単一原理で受容（脅威モデル accident 前提。adversarial 化で W2 content-hashing / hook-floor 必須化）。R3 pointer bump（設計どおり健全）／ R8 入れ子フェンス（主 fail-closed・任意 hardening・parser 非対称注記）／ R9 case-rename ／ R10 net-zero ／ **R13 申告粒度**（in-band 回復・規律強制の副次機能）＝ fail-closed だが rare または回復可能。L0 パイプライン 1/6（スコープ境界）／ 7-4/8-2/6.5-2(C)/refactor-gate 再実装 entry 無検証（INNER_LOOP が部分安全網・穴は correctness でなく cost）／ 設計内 blocking 非対称（oracle 成熟度差＋rollback トリガによる可逆化が受容条件）／ 再帰的信頼のコア（可監査性3段チェーンを条件に受容）／ 6-3 は substance 非検証の phantom-claim floor（部分/実質捏造は reviewer 層の責務）。

---

## 反証・対立仮説の検討（fable 独立分）

- **「blocking でなく log-only/warn 先行にすべき（hook 側 Stage A→B と対称に）」**: steelman ―― FP 未測定の必須ゲートを blocking で出荷するのは自らの設計哲学（段階導入）に反する。→ **棄却（条件つき）**: (i) 6-3 が防ぐ当のコスト（捏造の上に reviewer 5体を積む・19分迷走）は warn では防げない（記録されるだけ）。(ii) must-fix #1 適用後、既知の common-path fail-closed は閉じ、残る fail-closed は rare（R7/R9/R10）か in-band 回復可能（R13）か correctness 無傷（R12）。(iii) 失敗パスに (B) エスケープとユーザーゲートがあり、rollback トリガで warn 降格が可逆に用意される。blocking 維持＋監視付き可逆が正しい。確信度: 中〜高（FP 実頻度未測定のため観測窓が保険）。
- **「R12/R13 も must-fix にすべき（増員方向）」**: → 棄却。R12 は correctness 無傷・fail-loud の意図的設計で、頻度未測定のまま縮退モードを足すのは複雑性の先払い。R13 は設計どおりの in-band 回復であり、修正でなく観測（原因分類）が正しい手当て。
- **「#2 experimental 登録は官僚主義・6-3 は既存ハードルールの機構化で実験でない（減員方向）」**: → 棄却。filing の名前が実験かチューニングかは本質でなく、**観測 harness の有無**が本質。登録なしでは verify-*.md が gitignored RUN_DIR に散逸し集約されず、6-3 は unfalsifiable になる。retrospector が毎回 experimental.md を評価する既存ループに乗せるのが最安の harness。
- **「opus と同一勧告なのは anchoring（下地に引きずられた）では」**: 自己点検 ―― 独立性の証拠は (1) 台帳2行（R12/R13）の新規発見、(2) opus の健全性証明の反例（pre-existing-staged FN）の検出、(3) 「誤認者は検証を避けない」の機序的棄却、(4) gate のフィクスチャ分類への異議（#1 DoD 内包）。結論の一致は、同一の逐語コードと機序が同じ方向を指すためであり、正当化の経路は有意に異なる。

---

## rubric カバレッジ（7基準・自己申告）

| # | rubric 基準 | 判定 | 根拠（本 position のどこが答えるか） |
|---|---|---|---|
| 1 | oracle 健全性（方向つき境界づけ・受容可能性） | **充足** | 第一原理（独立性・真正性）で健全と判定（段1）。残存限界を R1〜R13 の完全台帳で方向つき（fail-open/closed）・頻度・3層割付つきで境界づけ。gate 名指しの submodule（R2 fail-open 確定・版依存注記）/ 入れ子フェンス（R8 主 fail-closed）/ 実在 gitignore（R5 fail-open）/ pre-existing-dirty（R6 最頻 fail-open）/ resume-stale（R7 fail-closed 回復可能）を全収録。fail-open 受容を git-oracle domain 境界の単一原理で一般化（段6）。#1 の FN 副作用（(g)）まで含め台帳が閉じる |
| 2 | 設計適合（root cause 機序）＋W1 移行パス整合 | **充足** | 6-3 は事象X の「兄弟」を直し、L0 自己捏造には可監査性（防止でなく）を与えると機序分解（段2'）。錨は動機論でなく可監査性3段チェーンに置き直し。resume 経路（RESUME_MODE × API 中断の層違い）は残ギャップとして #2 観測＋独立 checkbox が既存の最大手当て。W1→W2 はコード非再利用・技術＋プロトコル doc 転移で debt でない |
| 3 | 全通常 run への挙動影響・釣り合い | **充足** | コスト主成分 = 手順分割の L0 脱落面（R12 として台帳化・レイテンシは赤ニシン）。FP 集合の additive 性・PPV（標的が稀ゆえ低 FP でも割れる）・R13 申告規律税を具体列挙。must-fix #1＋観測窓＋rollback トリガで釣り合うと判定（blocking 維持の条件つき裁定） |
| 4 | 完成度・残ギャップの網羅 | **充足** | 7-4/8-2/6.5-2(C)/refactor-gate 無検証 = スコープ境界（穴は correctness でなく cost・INNER_LOOP が部分安全網）。pipeline 1/6 = 妥当な境界。verify 未配線・複雑性 = 観測。pir2async / .codex overlay / W2+ = plan 明示 follow-up |
| 5 | 過剰/過小（steelman つき） | **充足** | 「0回機能にやり過ぎ」を steelman → 対象取り違えで棄却（ホットパス）。逆方向「1/6 過小」も棄却。真の過剰 = fix ループ往復、真の過小 = フィクスチャ FP カバレッジ（盲点の系統性まで特定） |
| 6 | 採用/コミット推奨＋受容残存リスク | **充足** | 「修正してコミット」を単一勧告で確定（そのまま×・保留×・ロールバック× の棄却理由つき）。must-fix 3点（件数据え置き・内容強化）＋W0/W1 分割コミット＋コミット衛生。受容残存リスクを3層台帳で完全列挙 |
| 7 | プロセス自己言及 | **充足** | fix ループ可謬 → コード接地優先 → **fix 自身へのフィクスチャ内包**まで教訓を貫徹。dev-time 成功 ≠ runtime 信頼。prose-confidence は出荷十分条件でない。独立検証者の付加価値は正当化の修正に現れる（本ラウンド自体が実例） |

---

## 事実と推論の仕分け

- **事実（exploration-01.md / context に出典）**: 実集合の定義と staged 対象外（L59, L84-86）／check-ignore 3分岐と exit 128（L134-159）／test -f と残存限界の自己申告（L161-180）／pre-set 未記録時の全再実行指示と縮退禁止（L94-96, L194）／失敗パスの「申告を実体に一致させよ」逐語（L265）／入れ子フェンス限界の方向（L117-123）／verify script の堅牢 parser（L538-555）と6フィクスチャ構成（L677-857）／submodule フィクスチャのアサーション（L845-848）／experimental.md に 6-3 エントリ不在・staged/case-rename の実機発見・事象X の捏造主体 = L0（context）／本セッション開始時の既 dirty（exploration 冒頭 git status）。
- **推論（fable の解釈）**: 「#1 が pre-existing-staged FN を開く」（集合演算からの演繹・高確信）／「誤認 L0 は 6-3 実行も幻覚しうる」（事象X の署名からの類推・機序は確実、実頻度は未観測）／R12・R13 の頻度推定（未測定）／「フィクスチャ盲点は導出方法由来で系統的」（構成の観察からの帰納）／「blocking 維持が正しい」（条件つき判断）／「保留に情報利得なし」（観測手段の所在からの演繹）。

---

## 確信度と残る不確実性

- **全体確信度: 高**（勧告・must-fix 件数・台帳の方向づけ・再帰的信頼の裁定）。**中**にとどまる部分: (a) FP 実頻度と R12/R13 の実発生率（未測定 ―― ただし全裁定は頻度非依存に組んである）、(b) L0 の 6-3 実行遵守率（未観測 ―― 観測項目 (b) が受容条件）、(c) blocking 維持（rare-FP 前提が観測で覆れば rollback トリガで warn 降格）、(d) resume 経路の逐語未確認（RESUME_MODE × 6-3 checkbox 相互作用 ―― 結論非依存の確度向上タスク）。
- **依存する前提（崩れると結論が変わる）**: 脅威モデル = accident, not adversary（adversarial 化で fail-open 群が同時に開く）／実集合 bash とフィクスチャは逐語どおり動く（行レビュー PASS・実機緑の rubric 前提）／run 母数は個人ワークフロー規模（epic スケールで alert fatigue 閾値と R7/R12 絶対数が変わる）／check-ignore exit 128 の挙動が現行 git で安定（版依存は (h) で文書化）。
- **コミット後の確度向上タスク（must-fix でない）**: pre-existing-dirty FN / resume-stale FP のフィクスチャ実証（理論→実証昇格）／resume 経路の逐語確認／R12・R13 の実発生率計測（観測窓）。

---

## opus-panel（position-2）との差分明細

| 種別 | 内容 | 帰結 |
|---|---|---|
| **追認** | 勧告「修正してコミット」／must-fix 3点の骨格／R1〜R11 の方向・割付／新 must-fix 昇格ゼロの連言裁定／W0/W1 分割コミット／fail-open 受容の単一原理（段6）／phantom-claim floor 再ラベル | 独立再導出で一致。確信度が上がる |
| **訂正1** | #1 の健全性証明「偽陰性を生まない」は偽 ―― pre-existing-staged への虚偽申告という新 FN を開く（R6 同型・受容可） | #1 は実施のまま、正当化を「fail-closed FP の fail-open 転換」に修正し #3 (g) に明記 |
| **訂正2** | 「誤認者は検証を避けない」（段2）は過大 ―― 事象X の署名（prose 幻覚）は 6-3 の bash にも同型適用される | 受容根拠を可監査性3段チェーンに置換。観測項目 (b) を load-bearing に格上げ |
| **深化1** | 台帳に R12（pre-set 漏れ→縮退なし全再実行）・R13（申告粒度の税・in-band 回復）を追加 | honest-run コストの主要因が台帳・観測窓に載る。観測項目 (c)（原因分類）を #2 に追加 |
| **深化2** | must-fix #1 の DoD にフィクスチャ2本を内包（gate の「確度向上」分類はコード変更を伴う fix には不適用） | FIX-5/FIX-F の教訓を #1 自身に適用。un-fixtured fix の regression 再演を予防 |
| **深化3** | フィクスチャ盲点の系統性（機構確認型 vs 環境干渉型）／check-ignore exit 128 の版依存注記 | #3 known-limitations (h)(i) に追加。将来の verify 拡張とgit 更新時の回帰検知の指針 |
