## 熟考レポート（ROUND 1 / 02）: W0+W1（6-3 決定論的完了検証）の採用可否

### レンズ
反証・レッドチーム（この推論の軸）。「コミットしてよい」「コミットすべきでない」を両方 steelman し、衝突させて残るものを取り出す。

### 思考の起点（前提の確認）
- context から確定的に言える事実:
  - 6-3 の oracle は「CLAIMED（implementer 報告の `変更ファイル一覧`）」対「ACTUAL（`git diff --name-only` unstaged ＋ `ls-files --others` untracked）」の集合照合。`claimed-trackable − post` が非空なら **PHANTOM = hard fail**（出典: context L40-54）。
  - 事象X の捏造は「**L0（メイン Claude）自身が resume 直後に捏造・迷走**、tool 呼び出しが transcript に存在しない完全捏造」（出典: context L8）。
  - 偽陽性2件を実機発見: (1) `git add` 済み（staged）は unstaged にも untracked にも現れず PHANTOM hard fail、`implementer.md` に git add 禁止 **0件**、plan のリスク開示は Codex 側のみ・**Claude implementer 側は未検証**（出典: context L13）。(2) case-only rename（macOS APFS 既定）は git シグナル空 → PHANTOM（出典: context L14）。
  - `experimental.md` は epic 等を `Status: Active` で追跡するが **6-3 に該当エントリ無し**（全文検索確認、出典 L15）。完成形設計では hook 側は log-only 段階導入なのに **6-3 は即 blocking**（設計内の一貫性欠如、L16）。
  - Fable5 の L0 検証パイプライン6手順中、6-3 は **git 集合照合 1 手順のみ**。W2 は情報源・スコープ粒度が異なり **コード単純再利用不可・技術のみ再利用**（出典 L9）。
- 前提として置くもの: 行レベルの正確性は多重レビュー PASS 済み（rubric 前提 L9）。本レビューは「正しく作ったか・出荷してよいか」を問う。FP=偽陽性は「正常 run をブロック」＝fail-closed（安全側）であり「捏造を通す」偽陰性ではない、という方向性は据える。

### 段階的推論

#### 攻撃(a): Verification Theatre ―― 6-3 は守ろうとした失敗を防がない
- (a)対象主張: 「6-3 は事象X（捏造→reviewer 全FAIL→19分迷走）に対処する」。
- (b)攻撃の機序: 事象X の捏造者は **L0 自身**。6-3 は L0 が prose 指示どおり bash を実際に走らせることに依存し、**外部 hook の独立検証がない**（context L8「再帰的信頼の盲点」）。L0 が捏造状態なら「6-3 を走らせた・PASS した」も同様に捏造でき、あるいは単にスキップできる。よって 6-3 が捕まえるのは **implementer サブエージェントの捏造**であり、実際に失敗した **L0 自身の捏造**ではない。守ろうとした当の失敗モードを防がない ＝ 検証の体裁だけ（Unit42 の Verification Theatre）。
  - 自己点検（この飛躍は正当か）: 「同一 actor が実行する検証は当該 actor の捏造を捕まえられない」は 6-3 固有の欠陥ではなく、**あらゆる in-context チェック（reviewer verdict を L0 が読む行為すら）に共通する普遍property**。ここが攻撃の過大化ポイント。
- (c)それでも残る価値/反論:
  1. **implementer 捏造は独立した実在の攻撃面**。Unit42「agent-skill の 80% が宣言と挙動不一致」はサブエージェント/skill の話であり、implementer 捏造を捕まえる価値は L0 捏造と無関係に立つ。
  2. **「報告内容の捏造」と「bash 実行の捏造」は難度が違う**。6-3 を実行すれば RUN_DIR に `delta.list`/`phantom.list` の構造化 artifact が残る。L0 が助けを得られないのは「6-3 出力ごと偽造/スキップ」する場合のみで、それは事象X（捏造 claim を無批判に生成/受容）より**厳密に難しい捏造**。床は上がる（無限には上がらないが）。
  3. **錨の議論**: どこかで人間/決定論に錨を下ろすしかない（論点A）。6-3 は錨を「implementer の prose を信じる」から「git 状態を、L0 が bash で仲介して信じる」へ移す。L0 が汚染されれば全て汚染される ―― これは 6-3 に固有でない。
- 中間結論: 攻撃(a)は**主張の正当化を格下げする**が、**コミットをブロックしない**。ただし context が「両 deepthink レポート未記載の新規論点」と明記する通り、設計は「事象X を直す」と**過大広告**していた。実態は「事象X の**兄弟**（implementer 捏造クラス）を直し、L0 自己捏造は対象外」。→ **主張の訂正（must-correct-the-claim）**であって code defect ではない。

#### 攻撃(b): staged 変更 FP ―― 通常運用で踏む地雷
- (a)対象主張: 「発見済み穴は実運用頻度が極めて低く fail-closed（安全側）だから受容可能」。
- (b)攻撃の機序: `git add` 済みファイルは unstaged/untracked のどちらにも現れず、claimed-trackable が dirty でない ＝ **PHANTOM hard fail**。しかも:
  - `implementer.md` に git add 禁止 **0件**、Claude implementer は**フル Bash 権限**。
  - plan のリスク開示は **Codex 側のみ**、**Claude 側は一度も検証されていない**（context L13）。
  - 失敗は **hard fail で再実行では直らない**（implementer を再実行しても staged は解けない → 2回目 PHANTOM → ユーザーゲート）。**正常に完了した実装が誤ってブロックされる**。
  - トリガーは「`git add` という**単一の無害コマンド**」。しかもこのリポの CLAUDE.md は agent に `git diff --cached` での確認を促す文脈があり、staging する経路は非ゼロ。
  - 自己点検（自分の最強主張を叩く）: L0 が PHANTOM を見て「これは staged だ」と自己診断し `git restore --staged` で解けば回避可能では？ → だが (i) 6-3 の失敗パスは「報告再注入＋implementer 再実行」であって「unstage して再チェック」ではなく（context L54）、(ii) 無断 `git restore --staged` はまさにユーザー CLAUDE.md が**明示禁止**する行為。よって L0 は「偽 PHANTOM」と「禁じられた git 状態変更」に挟まれ**ユーザーゲート行き**。severity は高いまま。
- (c)それでも残る価値/反論:
  1. **fail-closed は本当に安全側**。失敗は「正当な run をブロック」（FP）であって「捏造を通す」（FN）ではない。人間ゲートに縮退し、捏造は漏れない。「安全側」主張自体は正しい。
  2. **修正は安価かつ健全**。post.list の union に `git diff --name-only --cached` を足す（**pre.list にも同時に足す**）。staged ⊆ 実際に変更されたファイル（未変更ファイルを stage しても index に何も足さない）だから、これは **PHANTOM を縮めるだけで偽陰性を生まない**。健全性が証明できる修正。1行級。
     - 自己点検（修正が新バグを生まないか＝rubric #7 の自己適用）: post だけに `--cached` を足し pre に足さないと、実行前から staged だったファイルが delta（UNDECLARED=warn）に誤混入する。**pre/post 両方に足す**必要。これを外すと「修正が regression を作る」（FIX-5/FIX-F の再演）。fix-then-commit はこの実装細部を外してはならない。
  3. **case-rename は本当に受容可能残存**: トリガー（case-only rename ＋ claim）が exotic かつ fail-closed。staged との非対称を明確化すべき。
- 中間結論: **「低頻度・受容可能」は case-rename には成立、staged には不成立**。staged は (i) 共通トリガー（単一 `git add`）、(ii) 既定 actor（フル bash・禁止0の Claude implementer）、(iii) hard fail・再実行復旧なし、(iv) 「低頻度」が Claude 側**未検証の仮定**（結論の先取り）、(v) exp-03 が**既に発見済み・健全な1行修正あり**。→ **既知・安価・共通経路の地雷を無修正出荷は最も擁護困難**。

#### 攻撃(c): experimental 統治の非対称
- (a)対象主張: 「6-3 を無条件本採用（experimental.md 未登録）してよい」。
- (b)攻撃の機序: 同一人物が同日、epic（新規オーケストレーション層）は `Status: Active` で観測、6-3（executions 0・FP 頻度未測定・**全 run 必須 blocking ゲート**）は無登録で本採用。しかも**完成形設計自身が hook 側は log-only 段階導入を規定**するのに、6-3 は即 blocking（context L16）。**維持者自身の設計哲学（log-only-first）を 6-3 が破る**。
- (c)それでも残る価値/反論:
  1. **6-3 は epic と種類が違う**（機能でなく既存高頻度 workflow 内の安全チェック）。安全チェックは実験扱いになじまない ―― だが逆に、**毎 run 発火し hard fail しうる**チェックこそ canary/log-only を先行すべき。攻撃を**強める**。
  2. **fail-closed でユーザーゲート縮退**なので「無統治だが安全なゲート」は「無統治の新機能」より低リスク。維持者が「観測されたインシデントへの標的修正だから実験 track 不要」と判断するのは**合理的**。ただしその判断は**明示すべき**で、記載漏れによる暗黙採用は不可。
- 中間結論: hard blocker ではないが **統治 must-address**。(b) の staged FP が未測定であることが、log-only 先行の論拠を**実質的に強める**。→ **(b)+(c) は結合する**: 未測定 FP を持つ必須 blocking ゲートは log-only/warn で観測窓を先に置くべき。

#### 攻撃(d): 6手順中1手順の「中途半端な計器」
- (a)対象主張: 「W1 は W2+ の土台になる」。
- (b)攻撃の機序: Fable5 6手順中 6-3 は git 集合照合 1 手順のみ。W2 は情報源・粒度が異なり**コード単純再利用不可**（context L9）。今の複雑性（5 実装ラウンド・verify スクリプト・6 フィクスチャ）は W2 が作り直す点解であり負債。
- (c)それでも残る価値/反論:
  1. **6-3 は W2 の足場でなく、観測された pir2 インシデントへの自立した修正**。事象X は初回実装点で発生＝6-3 のスコープ内（context L10, 問い3）。W2 が来ようが来まいが pir2 硬化として**単体で元が取れる**（rubric「epic 廃止でも回収可能」＝真）。「1/6」批判は「6-3 の正当化が W2 足場依存である場合のみ」刺さるが、依存していない。
  2. **コード非再利用は debt でない**。技術（git 集合演算・phantom/undeclared 分類・フェンス除去抽出）と**共有プロトコル doc（pir2+pir2codex が既に共通化）**が転移する。再利用ストーリーは「0」より良い。
  3. **ただし real residual**: 6-3 は 6 次元中 1 次元（file-set 存在）しか見ず、**substance を検証しない**。implementer が claimed ファイルを `echo >> file` で trivially 触れば 6-3 は通るが実質何もしていない ―― brittle grading / eval saturation。6-3 の oracle は**浅い**: 「ファイルが触られたか」であって「claimed の変更がなされたか」ではない。これは**必要条件であって十分条件でない完了チェック**。事象X の署名（tool 呼び出しが transcript に不在＝**完全**捏造）は捕まえるが、**部分/実質捏造**は捕まえない ―― という**正しい境界**。
- 中間結論: blocker としては**失敗**（価値は自己完結）。だが**framing を格下げ**: 6-3 は「completion verifier」でなく「**phantom-claim floor（浅い単一次元の床）**」。そう文書化する限り 1/6 は妥当なスコープ境界。複雑性は「blocking ゲートなら 6 フィクスチャは正当」で、(c) の log-only を採るなら「観測にやや先行するが浪費ではない（昇格時に有効）」。

### 反証・対立仮説の検討
- **最も強い反論（コミット反対側の核）**: 「単一攻撃でなく **(b)+(c) の結合**こそ最強のコミット反対だ ―― 既知・共通経路・未修正の FP を持ち、実 run 観測ゼロで、維持者自身の哲学が log-only-first を説く、必須・blocking・hard-fail ゲートは blocking のまま出荷すべきでない」。
  - steelman した上で: 正しい。ただしこれは「そのままコミット反対」であって「機構ロールバック」ではない。結論は**「修正して＋log-only で」コミット**へ収束する。攻撃は出荷形態を変えるが機構を否定しない。
- **対立仮説（コミット即可）**: 「行レベル全 PASS・Anthropic 整合・Unit42 裏付け・fail-closed・epic 廃止でも回収可能」。
  - 正しい部分（~70%）: 機構は健全・有用・自立・外部整合、行仕事はクリーン。「epic 廃止でも回収可能」は攻撃(d)を blocker から外す**最強の真**。
  - 誤り: (1) staged FP を「受容可能残存」扱いするが、既知・共通経路・未修正・1行修正ありの地雷（攻撃b）。(2) 統治/log-only 非対称を過小評価（攻撃c）。(3) Unit42 を**片面引用**している ―― 同一出典が alert-fatigue/Verification Theatre を警告し、攻撃(a)(b)を**支持**する。純粋な援護として引くのは選択的。

### 二次・三次の含意と境界条件
- 含意1（alert fatigue の連鎖）: staged FP が最初に発火した瞬間、正当な実装が誤ブロックされ、L0/ユーザーはゲートを信頼しなくなる ―― Unit42 が名指しした失敗モードそのもの。**未修正出荷は 6-3 の信頼を自壊させうる**。
- 含意2（rubric #7 の自己適用）: FIX-5/FIX-F が regression を作り後段レビューで捕捉された事実は**両刃**。人間主導 fix ループは可謬 → 機械ゲート一般を支持。だが 6-3 自身も同じ可謬ループで作られ、「implementer は stage しない」という**未検証の人間仮定が4ラウンドのレビューを生き延びた**（staged FP は**その生きた実例**）。→ 即 blocking 採用でなく canary（log-only）が思慮的、という**観測フェーズ支持の証拠**。
- 境界（機構が正しく効く条件）: 通常編集・削除・mode 変更・非ステージ rename では実機正常（context L23）。破れる条件は staged と case-insensitive FS の2点に限定。加えて「L0 が 6-3 を毎回正直に実行する」ことに全体が依存（未観測、context L34）。

### rubric への寄与（現時点）
| # | rubric 基準 | 寄与/未達 | 根拠 |
|---|---|---|---|
| 1 | oracle の健全性 | 寄与 | 6-3=「phantom-claim floor（必要十分でない床）」と境界づけ。完全捏造（事象X 署名＝tool 不在）は捕捉、実質/部分捏造は非捕捉。FP 方向=fail-closed（捏造は通さない）。残存穴を staged（共通・must-fix）/case-rename（exotic・受容）に分離 |
| 2 | 設計適合（root cause） | 寄与 | 攻撃(a): 6-3 は事象X の**兄弟**（implementer 捏造）を直し L0 自己捏造は対象外＝過大広告。W1→W2 のコード非再利用は debt でなく技術+プロトコル転移 |
| 3 | 全通常 run 影響 | 寄与 | 攻撃(b): staged FP が具体的共通経路コスト。毎 run の L0 bash 負担・alert fatigue リスク。blocking のままでは未測定 FP に対しコスト不釣り合い → log-only 先行を支持 |
| 4 | 完成度・残ギャップ | 部分 | 攻撃(d): 1/6 は「phantom floor」と文書化すれば妥当なスコープ境界。真のギャップは「completion verifier」との過大広告 |
| 5 | 過剰/過小（experimental） | 寄与 | 攻撃(c)+(d): 「0回機能にやり過ぎ」を steelman → blocking ゲートなら 6 フィクスチャは正当（反論成立）が、executions 0 に対し観測先行（反論の一部を承認）。epic との統治非対称は実在 |
| 6 | 採用/コミット推奨 | 寄与 | **修正してコミット**（そのまま×・ロールバック×）。下記 |
| 7 | プロセス自己言及 | 寄与 | FIX-5/F の regression 捕捉は機械ゲート一般を支持しつつ、6-3 自身の未検証仮定（no-stage）が4ラウンド生存 → canary 支持 |

### 事実と推測の仕分け
- 事実（context に出典あり）: staged/case-rename の FP 機序と未検証（L13-14）、事象X の捏造者=L0（L8）、experimental.md に 6-3 無登録（L15）、設計の blocking/log-only 非対称（L16）、6手順中1手順・コード非再利用（L9）、fail-closed 方向（L22-23）、FP 頻度未測定（L33-34）。
- 推論（deliberator の解釈）: staged FP を **must-fix-before-commit** と格付けする判定。`--cached` を pre/post 両方に足す修正の健全性（staged ⊆ modified なので偽陰性を生まない）。(b)+(c) 結合が最強のコミット反対で、結論は「修正+log-only でコミット」に収束するという構図。6-3 を「phantom floor であって completion verifier でない」と再ラベルする境界づけ。攻撃(a)を「主張訂正」、(d)を「非 blocker」と格付けする判断。

### 現時点の確信度と残る不確実性
- 確信度: **中〜高**。機構事実は context で確立。最強攻撃(b)は**頻度に依存しない**ロバスト性を持つ（単一共通コマンドでの hard fail ＋ 既知の安価健全修正 ＝ 頻度が高かろうが低かろうが無修正出荷は不可）。ゆえに「修正してコミット」の骨格は堅い。
- 残る不確実性:
  - 実 FP 発生頻度が未測定（context L33）。staged を「共通トリガー」と評したが、pir2 実運用で implementer が実際に `git add` する率は実 run 蓄積がないと確定不能。ただし判定は頻度に非依存に組んだ。
  - L0 が 6-3 を毎回正直に実行するか（再帰的信頼の実挙動）は未観測（L34）。攻撃(a)の残存限界の実害はここで確定する。

### 追加探索が必要な論点（該当する場合のみ）
- **`--cached` 修正の pre.list 整合性**: 提案する修正が pre/post 両方に `git diff --name-only --cached` を足す必要がある点は、`deterministic-completion-check.md` の pre.list 生成箇所の逐語（exploration-01.md）を確認して整合を取るべき。何を確かめれば埋まるか＝pre.list を「6-1 実行前の baseline」としてどう生成しているか（--cached 未包含か）を逐語確認。
- **失敗パスの unstage 有無**: context L54 の失敗パスに「staged を検出して unstage を試みる」分岐が本当に無いか、reference bash 全文で確認すれば攻撃(b)の severity（hard fail か detour か）が確定する。
