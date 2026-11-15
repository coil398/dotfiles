## 熟考レポート（ROUND 1 / 04）: W0+W1（6-3 決定論的完了検証）の採用可否・優先度設計

### レンズ
採用判断・優先度設計（rubric #4/#5/#6/#7 を主に埋める。#1/#2/#3 は採用判断に必要な範囲で参照）

---

### 思考の起点（前提の確認）

**context から確定的に言える事実（出典つき）**
- 行レベルの正確性は多重レビューで全 PASS（ドッグフーディング＋sonnet×3＋fable×2）。本レビューは「行が正しいか」でなく「正しいものを作ったか・出荷してよいか」（rubric 前提）。
- 6-3 が着地する先は **pir2/pir2codex の初回実装点（6-1）** = 通常 run のホットパス。適用は「初回実装点のみ・main スキップ」（context 詳細資料）。**executions 0 なのは epic 側であって、6-3 が乗る pir2/pir2codex は高頻度**。ここが採用判断の分水嶺。
- git-working-tree を oracle にすること自体は健全。穴は **staged 変更**と **case-insensitive FS の case-only rename** の2点に限定（exp-03 一次情報）。
- 発見済み偽陽性2件（staged／case-rename）は「再実行で直らない hard fail」経路（PHANTOM → 2回目 PHANTOM で reviewer 起動せずユーザーゲート、自動 restore なし）。
- 統治の非対称: `experimental.md` は epic/shards 等を `Status: Active` で追跡するが **6-3 のエントリは存在しない**（全文検索確認）。同日設計の epic は実験 track、6-3 は無条件本採用。
- 設計内非対称: 完成形設計で hook 側は log-only 段階導入（Stage A→B）、**git-diff 側（6-3）はいきなり blocking**。
- 事象X（resume 時 implementer 完全捏造→reviewer 全FAIL→19分迷走）は実インシデントで、その後半連鎖は 6-3 で断てる（exp-02 問い1=部分適合）。
- 外部整合: Anthropic の Outcome/State check パターンに整合。Unit42「skill の 80% が宣言と挙動不一致」が決定論ゲート一般の必要性を裏付け。落とし穴3つ（alert fatigue／eval saturation／Verification Theatre）が発見 FP と重なる。

**前提として置くもの（崩れると結論が変わる）**
- 「executions 0＝過剰投資」の議論対象は 6-3 の**核機構ではなく、6-3 が属する広義の検証パイプライン構想（L0 6手順・W2+・epic 側）**である、という切り分け。6-3 コアはホットパスに乗る＝高頻度側。← これが本レンズの核。
- must-fix は「レビューと推奨」の範囲内。実装は呼び出し元/implementer が行う（rubric out-of-scope: これ以上の実装変更）。したがって「修正してコミット」は**修正指示リスト**であってこの熟考内で実装はしない。

---

### 段階的推論（採用推奨の導出）

**段1: 採用の4択を粗く篩にかける。**
- 「保留／ロールバック」は妥当か → 事象X は実損（19分迷走）が観測済み、oracle は健全、外部ベストプラクティスに整合、行レベル PASS。ロールバックは**安価に塞げるエッジ（穴は2点に限定）と引き換えに実証済み価値を放棄**する。過剰反応。→ 棄却。
  - 自己点検（隠れ前提）: 「実証済み価値」は事象X 1件の観測に基づく。頻度は低い可能性。だが downside（捏造→全FAIL→迷走）の**深刻度**が高く、しかも oracle が安価。期待損失で正当化される。
- 「そのままコミット」は妥当か → 2件のホットパス FP（staged は unrecoverable）が未修整・未文書、かつ observe 層を回す harness（experiment track）が無い。**安価に塞げる既知欠陥を残したままホットパスに出荷**することになる。→ 棄却（後述 steelman で再検討）。
- 残るは「修正してコミット」。

**段2: なぜ「修正してコミット」で、しかも must-fix は最小3点で足りるか。**
- staged FP: implementer は Claude 側で Bash フル権限を持つが git add 禁止が implementer.md に0件。**plan のリスク開示は Codex 側のみ根拠で Claude implementer 側は未検証**（exp-03）。頻度は低いが、発火すると「実行しても直らない hard fail」＝ホットパスで通常 run を殺す。修正は安価（実集合に staged を union する／または prose 1行）。→ **must-fix**。飛躍の点検: 「頻度低いなら受容では」への反論 = 深刻度（unrecoverable）× ホットパス（高頻度母集団）で、期待損失は無視できない。かつ修正費用がほぼ0。費用対効果で must-fix。
- experiment 登録: governance 非対称の是正であると同時に、**observe 層を実運用する唯一の harness**（rollback トリガ・観測窓が無ければ「commit 後に観測」はただの願望）。安価。→ **must-fix**。
- known-limitations 明記: case-rename・7-4/8-2 未配線・blocking 即時採用の根拠・再帰的信頼の錨。rubric #1 が要求する「残存限界が**正しく境界づけられ受容可能か**」を成立させる最小文書。安価。→ **must-fix**。
- それ以外（再帰的信頼のコア・複雑性・pipeline 1/6・blocking 非対称）は「観測」か「受容」に落とせる（後述の3層割付）。

**段3: 優先度設計としての追加提案（blast radius 最小化）。**
- 変更集合には W0（citation 衛生・epic sanitized_cwd 登録）と W1（6-3 一式）に加え、`.gitignore`/`CLAUDE.md`/`epic-planner.md`/`epic/` skill 等が混在（git status）。**W0 と W1 はリスク階層が違う**（W0 は低リスクの衛生系、W1 はホットパス改変）。
  - 推奨: **コミットを分割**し、W0 と低リスク文書を先行コミット、W1（6-3）を must-fix 適用後に別コミット。理由: W1 に FP 再発があった際、**W0 の citation/epic 修正を巻き込まず 6-3 だけを surgical に revert** できる。優先度設計＝可逆性の確保。
- blocking 即時採用の非対称（受容）を**可逆にする安全弁**: experiment エントリに「観測窓 N run で FP が閾値超なら hard-fail→warn に降格」の rollback トリガを明記。これで「hook は log-only なのに 6-3 は即 blocking」の非対称を、**監視付き・可逆な決定**へ変換する（accept を observe と接続）。

**段4: 明確な採用推奨（玉虫色にしない）。**
- **推奨 = 修正してコミット**。must-fix は最小3点（下記）。可能なら W0/W1 のコミット分割を併用。

**コミット前 must-fix（最小リスト）**
1. **staged FP を塞ぐ**（優先形＝堅牢）: `deterministic-completion-check.md` の実集合に `git -C … -c core.quotePath=false diff --cached --name-only` を pre/post 両方に union（コメント「staged は対象外」を撤回）。＋補助: implementer.md に「申告ファイルを自分で `git add` しない」1行。
   - **今セッションで実装ラウンドを再開したくない場合の floor**: prose 1行＋known-limitation 明記のみで着地し、staged 残存を台帳 R-staged に計上。ただし後述プロセス自己言及の理由から**堅牢形を推奨**。
2. **experimental.md に 6-3 を Active 実験登録**: 観測項目（FP 実発生・L0 が 6-3 bash を毎回実行したか）＋ rollback トリガ（FP 閾値超で hard-fail→warn 降格）＋観測窓を明記。
3. **known-limitations 追記**（`deterministic-completion-check.md`）: (a) case-rename FP（APFS）(b) 7-4/8-2/6.5-2(C)/refactor-gate 再実装 entry 無検証（INNER_LOOP_COUNT が部分安全網）(c) blocking 即時採用の根拠（oracle 成熟度差）(d) 再帰的信頼の錨（どこかで人間/決定論に接地する不可避境界）(e) L0 パイプライン 1/6（残り5手順は W2+）。

---

### 反証・対立仮説の検討（steelman）

**反論1: 「そのままコミット」で十分（staged FP は受容でよい）。**
steelman: implementer は運用上 stage しないのが常態。plan で Codex 側は既に検証済み。FP は理論上の穴で、事象X という実損を防ぐ価値の方が桁違いに大きい。安価だが不要な追加をせずに出荷し、FP が実際に出たら直せばよい（YAGNI）。
評価: 半分正しい。だが**「実行しても直らない hard fail」は fail-closed で通常 run を止める**——これは alert fatigue／Verification Theatre の逆で、むしろ「正当な run を殺す」最悪クラス。しかも修正費用がほぼ0。YAGNI は「安いのに既知の壊れ方を残す」ことを正当化しない（context: YAGNI は品質投資を否定しない）。→ **結論は耐える**が、「堅牢形が無理なら prose+doc floor で妥協可」に緩む余地は認める（must-fix #1 の floor 条項に反映済み）。

**反論2: ロールバックすべき（再帰的信頼が致命）。**
steelman: 6-3 は L0 が prose 通り bash を実際に呼ぶことに依存し、外部 hook の独立検証がない。事象X はまさに **L0 自身が resume 直後に捏造・迷走**した事象。捏造する L0 は 6-3 の bash も捏造/スキップしうる。ならば 6-3 は「最も守りたい状況で最も無力」＝ Verification Theatre であり、偽の安心を与える分だけ無いより悪い。
評価: この反論は本レビュー最強。だが結論を**ロールバックには倒さない**。理由: (a) 再帰的信頼はあらゆる検証チェーンが必ずどこかで接地する不可避境界（論点A の後半）で、6-3 固有の欠陥ではない。(b) 「theatre 化」は**部分的に機械で塞げる**——L0 パイプライン6手順のうち「hook floor」（Stop hook が RUN_DIR に `verify-*.list` の生成有無を検証）を W2 で入れれば、6-3 の実行そのものを runtime で機械照合できる。つまり再帰的信頼の残穴は「永久受容」ではなく「W2 の hook-floor で錨を下ろす観測課題」。(c) それまでは experiment 観測項目に「L0 が 6-3 bash を実行したか」を必ず入れることで theatre 化を early-warn する。→ **結論は修正（ロールバックでなく observe+W2 で錨）**。これは論点A と論点D（pipeline 1/6）を接続する本レンズ固有の寄与。

**反論3: executions 0 に 5 ラウンド＋verify＋6 フィクスチャは過剰投資。**
steelman: epic は 0 回しか動いていない試験機能。その周辺に self-verify スクリプト＋6 フィクスチャまで積むのは、動くかも分からない機能への過剰な堅牢化。YAGNI 違反。
評価: **対象の取り違え**として棄却。過剰投資の議論は「6-3 が epic（0回）機能だ」という前提に立つが、6-3 は **pir2/pir2codex のホットパス**に乗る（executions 多数側）。ホットパスの blocking ゲートで FP が出れば通常 run を殺すのだから、verify＋フィクスチャは**過剰どころか proportionate**。むしろ**フィクスチャは under-covering だった**——staged と case-rename の2 FP を6フィクスチャが取り逃した（本レビューで初検出）。→ 過剰投資論は 6-3 コアには当たらない。当たるのは後述「fix ループの浪費」。

**対立仮説: L0 パイプライン 1/6 は過小（under-engineering）。**
評価: これも**「不完全なビジョン」と「不完全なインクリメント」の混同**として退ける。良いインクリメントは1手順を完全にやる。W1 が git 集合照合1手順に絞ったのは plan 明示のスコープ境界で、残り5手順は W2+。「1/6 だから過小」は増分開発を否定する誤り。真の過小は**テストの FP カバレッジ**（staged/case-rename）だったが、それは今 pre-commit で塞げる。→ pipeline 1/6 は**妥当なスコープ境界**（受容）、under-engineering ではない。

---

### 二次・三次の含意と境界条件

**含意（推奨が正しいとき）**
- experiment 登録＋rollback トリガを入れることで、6-3 は「不可逆な本採用」から「監視付き・可逆な段階採用」へ変わる。これは同日 epic の統治と対称になり、governance 一貫性が回復。
- must-fix #1 を堅牢形（staged union）で入れると、oracle が working-tree 全状態（HEAD+staged+unstaged+untracked）を捉え、rubric #1 の「境界づけ」が2点→1点（case-rename のみ）に縮む。
- W0/W1 分割コミットは、W1 の revert 可能性を W0 から独立させ、blast radius を最小化。

**境界（結論が崩れる条件）**
- **FP 実発生頻度が想定を超える**なら（未測定・context 空白）、修正してコミットの前提（安価に塞げるエッジ）が崩れ、「hard-fail→warn 降格」を前倒し発動すべき。→ だから rollback トリガ必須。
- **L0 が 6-3 bash を体系的に走らせない**ことが観測されたら（再帰的信頼が実挙動で破綻）、6-3 は theatre 化し、hook-floor（W2）を**前倒し**しない限り価値が空洞化。→ 観測項目に「実行有無」を必ず入れる前提。
- staged 堅牢形が予期せぬ副作用（例: pir2 開始前に別目的で stage 済みのファイルが pre/post 両方に入り delta から落ちる）を持つ場合。分析上は pre/post 対称で問題ないが、堅牢形採用時は**フィクスチャ1本追加で検証**すべき（自己言及: フィクスチャ不足が今回の FP を見逃した）。

---

### 全懸念の3層割付（must-fix / commit後に観測 / 受容）

| 懸念 | 層 | 割付根拠（executions 0＝epic 前提に紐づけ） |
|---|---|---|
| **staged FP**（論点C） | **must-fix** | 6-3 はホットパス（executions 多数側、epic の 0 回とは別母集団）。unrecoverable hard fail が通常 run を殺す。修正費用ほぼ0＝費用対効果で塞ぐ一択 |
| **無条件採用＝experiment 未登録**（論点B） | **must-fix** | 同日 epic は Active track。6-3 は FP 確信度が executions 0 相当（実 run 未蓄積）にもかかわらず本採用は非対称。observe 層の harness として登録が前提 |
| **境界の未文書**（case-rename・7-4/8-2・blocking根拠・再帰信頼の錨） | **must-fix** | rubric #1「残存限界が正しく境界づけられ受容可能か」の成立条件。安価。文書化しない受容は「気づかず飲む」＝受容と言えない |
| **case-rename FP** | **観測**（文書化後） | 頻度極低（case-only rename は稀）。documented なら発火時に手当てで足りる。ホットパスだが母集団内での発生率が staged より低い |
| **再帰的信頼の runtime 実挙動**（論点A・実行有無） | **観測** | 「L0 が 6-3 bash を毎回実行するか」は未観測（context 空白）。experiment 観測項目に必須。theatre 化の early-warn。将来 hook-floor（W2）で機械錨 |
| **FP 実発生頻度・通常 run 完走率影響** | **観測** | 実 run 未蓄積で未測定（context 空白）。experiment 観測窓で計測し rollback トリガに接続 |
| **複雑性 2.4〜5倍・verify 手動実行依存** | **観測** | 保守コストは累積で顕在化する類。CI/hook 未配線は W2+ 課題。当面は observe |
| **L0 パイプライン 1/6**（論点D 過小方向・問い2） | **受容**（スコープ境界） | 増分の1手順完遂は正当。残り5手順は plan 明示の W2+。うち hook-floor は再帰信頼の錨として優先度上げて観測課題に接続 |
| **7-4/8-2/6.5-2(C)/refactor-gate 再実装 entry 無検証**（決定1 の穴・問い3） | **受容**（文書化） | plan に follow-up 記録・意図的限定。INNER_LOOP_COUNT が部分安全網。真のギャップでなくスコープ境界 |
| **設計内 blocking 非対称**（hook log-only vs 6-3 即 blocking） | **受容**（可逆化して） | oracle 成熟度差で正当化（git working-tree は成熟、hook oracle は新規でノイジー）。ただし rollback トリガ（hard→warn 降格）で可逆にすることが受容の条件 |
| **再帰的信頼のコア**（不可避な信頼境界） | **受容** | あらゆる検証チェーンが接地する不可避境界。6-3 固有欠陥でない。錨を文書化して飲む |

---

### 過剰/過小の裁定（rubric #5）

**裁定: 機構コアは過剰でも過小でもなく proportionate。浪費は「人間主導 fix ループ（FIX-5/FIX-F）」に集中。テストは FP エッジで under-covering だった（今塞げる）。**

- **過剰でない**: 6-3 コアはホットパスの blocking ゲート。ホットパスで FP が通常 run を殺す以上、verify スクリプト＋フィクスチャは投資として釣り合う。「executions 0 にやり過ぎ」は epic を対象に取った誤爆で、6-3 コアには当たらない。
- **過小でない（pipeline 1/6）**: 1手順完遂は増分開発の正しい姿。1/6 は「不完全なインクリメント」でなく「意図したスコープ境界」。過小と呼ぶのはビジョンの未完成をインクリメントの欠損と混同している。
- **真に過剰だったもの**: FIX-5 累積・FIX-F submodule の**人間 fix ループの往復**が regression を生み後段レビューが捕捉した。5 実装ラウンドの一部は自己誘発 regression の手戻りで、機構の内在的複雑性ではない。**過剰は機構でなくプロセス**。
- **真に過小だったもの**: 6 フィクスチャが staged/case-rename の2 FP を取り逃した＝**テストの FP カバレッジが過小**。ただしこれは本レビューが pre-commit で検出済みで、フィクスチャ追加で回収可能。

要約すると「機構本体は妥当、行レビューの往復に費やされた分が過剰、フィクスチャの FP カバレッジが過小」——タスクが提示した第三の裁定に最も近い。

---

### プロセス自己言及の考察（rubric #7）

**観察された事実**: FIX-5（累積）・FIX-F（submodule）という**人間主導の修正指示自体が regression を作り**、それを (a) 後段の多エージェントレビューと (b) verify スクリプトの6フィクスチャ（機械検証）が捕捉した。

**含意1（fix ループの信頼性）**: prose 指示駆動の修正は**可謬**であることが実証された。これは 6-3 が守ろうとしている失敗モード——「prose 通り動いたつもりで outcome が誤り」——と**同型**。つまり本開発プロセス自身が「prose-confidence は当てにならない」というテーゼの生きた証拠を提供した。

**含意2（採用判断への直接反映）**: fix ループが可謬なら、**prose に依存する修正（implementer.md の git add 禁止1行）より、コードに接地した修正（実集合に staged を union）を優先すべき**。理由は循環的だが正しい——prose 遵守こそが FIX-5/FIX-F で破れたのだから、prose を信頼する塞ぎ方は同じ穴を踏む。これが must-fix #1 で堅牢形を第一推奨にした根拠。

**含意3（機械検証の価値の正の証拠）**: verify スクリプトが**自分の開発バグ（FIX 由来 regression）を捕まえた**事実は、6-3 の価値命題「決定論検証は prose レビューが見逃すものを捕まえる」を dev-time で実証。これは 6-3 を採用する側の追い風。

**含意4（ただし dev-time の成功は runtime 信頼に移らない）**: verify が捕まえたのは 6-3 **実装のバグ**（dev-time、人間がスクリプトを走らせた）。production の 6-3 は **L0 が bash を実際に走らせること**に依存（runtime、未観測）。dev-time の機械検証成功は runtime の再帰的信頼を保証しない（論点A）。→ 「機械検証は効く」を「だから runtime も安心」に**過度一般化しない**。runtime の機械錨は W2 の hook-floor を待つ。

**メタ結論**: 「行レビュー全 PASus」という prose-confidence は、FIX-5/FIX-F が示す通り**それ自体では出荷許可の十分条件にならない**。だからこそ本熟考（設計・システミック層）が必要で、かつ採用は「本採用」でなく「experiment 観測付き」が規律ある選択。プロセスの可謬性が、そのまま「監視付き段階採用」を支持する。

---

### rubric への寄与（現時点）

| rubric 基準 | 寄与/未達 | 根拠 |
|---|---|---|
| #1 oracle 健全性・境界づけ | 部分 | 採用視点から「境界の未文書」を must-fix 化し、staged 堅牢形で穴を2→1点に縮める提案。健全性の系統判定本体は他レンズ（機序）に委ねる |
| #2 設計適合（root cause） | 部分 | 再帰的信頼を「W2 hook-floor で錨を下ろす観測課題」に再定位（論点A×D 接続）。機序の逐一判定は他レンズ |
| #3 全通常 run 影響 | 部分 | ホットパスである点を採用判断の分水嶺として明示。FP の fail-closed 深刻度をコスト計上。実頻度は観測課題（未達部分は explorer 蓄積待ち） |
| #4 完成度・残ギャップ | 寄与 | 7-4/8-2・pipeline 1/6・複雑性・verify 未配線を「真のギャップ/スコープ境界」に判定して3層割付 |
| #5 過剰/過小判定 | 寄与 | 3方向 steelman（過剰投資/過小 pipeline/fix ループ浪費）を裁定。機構=proportionate、過剰=プロセス、過小=フィクスチャ FP カバレッジ |
| #6 採用/コミット推奨 | 寄与 | 明確に「修正してコミット」＋最小 must-fix 3点＋分割コミット＋残存リスク台帳 |
| #7 プロセス自己言及 | 寄与 | fix ループ可謬→堅牢形優先／機械検証 dev-time 成功→runtime に移らない／prose-confidence は出荷十分条件でない、を導出 |

---

### 事実と推測の仕分け

- **事実（context に出典あり）**: 行レベル全 PASS／6-3 はホットパス（初回実装点）適用／穴は staged・case-rename の2点／両 FP は unrecoverable hard fail 経路／experimental.md に 6-3 エントリ無し／hook は log-only・6-3 は blocking／事象X は実インシデント／Anthropic・Unit42・落とし穴3つ／FP 頻度と L0 実行有無は未測定。
- **推論（deliberator の解釈）**: 「executions 0 過剰投資論は epic を対象に取った誤爆で 6-3 コアには当たらない」／「pipeline 1/6 は過小でなくスコープ境界」／「fix ループ可謬性ゆえ prose 修正より堅牢修正を優先」／「再帰的信頼の残穴は W2 hook-floor で部分的に錨を下ろせる（論点A×D 接続）」／「W0/W1 分割コミットで blast radius 最小化」／「rollback トリガで blocking 非対称を可逆化」／「must-fix は最小3点で足りる」。これらは私の優先度設計上の判断であり、context の断定ではない。

---

### 現時点の確信度と残る不確実性

- **確信度: 中〜高**。
  - 高い部分: 「ロールバックは過剰・そのままコミットも既知欠陥残し」→「修正してコミット」の骨格、および fix ループ可謬性からの堅牢形優先、pipeline 1/6=スコープ境界の裁定。これらは context の事実から論理的に導ける。
  - 中の部分: must-fix を「最小3点」に絞れるかは、FP 実頻度が未測定（context 空白）である以上、観測で覆る余地。頻度が高ければ #1 の floor（prose+doc）では不足し堅牢形が必須化する。
- **残る不確実性**:
  1. staged 堅牢形（`git diff --cached` union）の副作用が本当に無いか（pre 段階で別目的 stage 済みファイルの扱い）。分析上は pre/post 対称で問題ないが、フィクスチャ検証が要る。
  2. 「修正してコミット」の must-fix #1 を堅牢形にすると実装ラウンドが再開する。今セッションで着地させたい要求と、堅牢形推奨のトレードオフは呼び出し元/ユーザーの時間選好に依存（floor 条項で逃げ道は用意済み）。

---

### 追加探索が必要な論点（オーケストレーターが判断する材料）

- **staged 堅牢形の副作用検証**: `git diff --cached --name-only` を実集合に union した際、pir2 開始前 stage 済みファイルが delta から落ちるケースの網羅。→ 何を確かめれば埋まる: フィクスチャ「pir2 開始前に無関係ファイルが stage 済み」を1本足して verify スクリプトを回す（explorer/tester 領域）。本熟考は実装しない。
- **FP 実発生頻度**: 通常 run の完走率低下は実 run 蓄積が無く未測定（context 空白）。→ experiment 観測窓で N run 計測してからでないと「最小 must-fix で足りる」の確度が上がらない。
- **L0 の 6-3 bash 実行有無（再帰的信頼の実挙動）**: 未観測。→ experiment に「verify-*.list の生成有無」をログ化し、theatre 化を early-warn する観測項目を置けば埋まる。W2 hook-floor 実装の優先度判断材料にもなる。
