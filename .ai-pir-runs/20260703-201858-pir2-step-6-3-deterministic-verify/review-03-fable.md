VERDICT: FAIL

### 担当 role
comprehensive（correctness / consistency / architecture / quality / security / reference-fidelity を1体で通す独立ホリスティックレビュー。Fable 5）

### レビュー方針
sonnet 3観点×2ラウンド（全 PASS）が確認済みの論点（PRE_IMPL_INDEX 分離・pir2codex 順序修正・3b/3c フィルタ・旧表現置換・checkbox 配線）は再検証のみ行い、焼き直しはしない。本レビューの新規指摘はすべて **scratch repo / 実データでの実機再現** を伴う。検証フィクスチャ: `/private/tmp/claude-501/.../scratchpad/dcc-1783084677/`。

---

### 判断根拠（確認した事実）

- **既 PASS 論点の再確認**: `PRE_IMPL_INDEX` の pre-set 据え置き（reference 40-47行・60-62行）、CLAIMED の 2 ラウンド累積（67-75行）、pir2codex「Write → 検証 → threadId」の順序厳守（SKILL.md 174-181行）、3b の `case "$p" in /*|~*)`（84行、bash 3.2 実機で `~/foo` `~user/foo` `~` `/abs` すべて untrackable 判定・`rel/x` のみ通過を確認）、3c の `$PROJECT_ROOT` アンカー（107行）を実物確認。round-2 レビューの解消確認はすべて事実と一致。
- **集合演算の意味論**: phantom = claimed-trackable − post（delta でなく post を使う）は SSOT §1-3-2 の `CLAIMED ⊆ post` と一致し、「既 dirty ファイルへの虚偽申告は検出不能」（SSOT 残存限界④）とも整合。UNDECLARED = delta − claimed（フィルタ前 claimed で良い理由の脚注 134行）も論理的に正当（delta は in-repo 非 ignore しか含み得ない）。空白入りパスは git 出力で quote されず問題なし（実機確認）。削除ファイルは `git diff --name-only` に現れ post に入るため申告と整合する。
- **フェイルセーフの向き**: git コマンド失敗→post 空→全 claimed が phantom（fail-closed）。claimed 抽出失敗＋delta 空→row 2 PHANTOM（fail-closed）。fail-open に倒れるのは「NO_OP grep の無アンカー」（M1）と「pre.list 不在時に UNDECLARED 層のみ silent 無効化」（L3）の 2 点に限られることを分岐網羅で確認。
- **本 run のドッグフード実データ**: verify-01-claimed.list（8件・untrackable 2件分離）と delta（6件）の照合は正しい。verify-02 は claimed 4 / delta 0 / phantom 0 — review-fix ラウンドでは対象が既に dirty のため delta が空になり検証力が post 照合のみに縮退することを実データで確認（L5）。

---

### 問題一覧

#### High（3件 — いずれも実機再現済み・過去2ラウンドの未検出領域）

- **High** `deterministic-completion-check.md:42-44,53-55` — **`core.quotePath` 未制御により、非 ASCII ファイル名で PHANTOM 偽陽性 hard fail が確定的に発生する**。git のデフォルト（quotePath=true。本マシンも global/repo とも未設定＝有効を確認済み）では `git diff --name-only` / `git ls-files --others` が非 ASCII パスを `"\346\227\245..."`（八進エスケープ＋二重引用符）で出力する。scratch repo で実証: `日本語ファイル.md` の変更が post.list に `"\346\227\245\346\234\254\350\252\236..."` として入る一方、CLAIMED には implementer が UTF-8 生文字列で申告するため、`comm` のパス文字列一致が絶対に成立せず **必ず PHANTOM（hard fail）→ 再実行1回浪費 → ユーザーゲート**に落ちる。本 reference はグローバル SSOT であり日本語ファイル名を持つプロジェクト（記事・ドキュメント系）で常時発火する。「偽陽性で実験を殺さない」という本設計の中核原則（136行）に自ら反する。
  → 修正: 4 箇所の git 呼び出し全てに `-c core.quotePath=false` を付与する（`git -C "$PROJECT_ROOT" -c core.quotePath=false diff --name-only` / 同 `ls-files --others --exclude-standard`。pre-set・post-set の両方）。

- **High** `deterministic-completion-check.md:67-75` — **CLAIMED 抽出 sed の「範囲再開」とコードフェンス非認識により、レポート内の引用テンプレートが CLAIMED を汚染し PHANTOM 偽陽性を起こす**。`sed -n '/^### 変更ファイル一覧/,/^### /p'` は範囲終了後も開始パターンを再照合するため、レポート後方のコードフェンス内に `### 変更ファイル一覧` の引用（例示・テンプレート断片）があると第2の範囲が開き、フェンス内の `` - `example/fake-path.md` `` 行が実申告として抽出される。フィクスチャで実証: 実申告 `real/file.md` に加え、フェンス内例示の `example/fake-path.md` が抽出された。汚染エントリは post に存在しないため **PHANTOM hard fail**。この失敗クラスは「pir2 のスキル文書・テンプレート自体を編集するメタタスク」（本 run がまさにそれ。dotfiles での pir2 の主用途）で発火確率が高く、再実行レポートが再び同じ引用を含めば決定論的にユーザーゲートまで直行する。
  → 修正: 抽出を (a) フェンス除去の前段フィルタ（`awk '/^```/{c=!c;next} !c'`）を通し、(b) 最初のセクションで打ち切る awk（`awk '/^### 変更ファイル一覧/{f=1;next} /^### /{if(f)exit} f'`）に置き換える。両対応で範囲再開・フェンス内引用の双方を遮断できる。

- **High** `deterministic-completion-check.md:179-182` — **PHANTOM 再実行時の CLAIMED 累積（PRE+現行の和集合）が、再実行指示文が提示する救済経路「または申告を実体に一致させよ」を構造的に達成不能にする**。retry プロンプト（179行）は「実際に編集せよ／申告を実体に一致させよ」の 2 択を提示するが、CLAIMED は `implementation-{PRE_IMPL_INDEX}*.md` と `implementation-{IMPL_INDEX}*.md` の**和集合**（67-75行）のため、round-1 の誤申告（phantom エントリ）は round-2 レポートでどう訂正しても和集合に残存し続ける。したがって「申告訂正」経路を選んだ再実行は**必ず 2 回目 PHANTOM → ユーザーゲート**になる（唯一の回避は前ラウンドのレポート実物を書き換えることだが、それは申告記録の改変であり未指示・監査痕跡的にも不適）。round-2 correctness レビューのシミュレーションは「実際に編集する」分岐のみ検証しており、この分岐は未検証。誤申告が typo 起因（`foo.ts` と書いたが実体は `foo.tsx`）の場合、正当な修正手段が存在しない。
  → 修正: 再実行レポートに「**訂正後の完全な変更ファイル一覧**を再宣言する」ことを required にし、**PHANTOM 照合は最新ラウンドのレポートのみ**・**UNDECLARED 照合は累積（現行どおり）**と照合対象を分離する。これで「前ラウンドの正当申告の UNDECLARED 誤検知防止」（累積の導入理由）と「申告訂正の救済」が両立する。

#### Medium（5件）

- **Medium** `deterministic-completion-check.md:143`（NO_OP 免除） — `grep -q 'NO_OP_JUSTIFIED'` が行頭・コロン・セクションのいずれにもアンカーされておらず、**本文中の言及・フェンス内の引用だけで免除が誤発動する（fail-open 方向で本ゲート唯一の緩み）**。実データ: 本 run の implementation-01.md には仕様言及として `NO_OP_JUSTIFIED` が 4 回出現しており（宣言ではない）、もし claimed/delta が空だったら免除が誤発動していた。本 reference を編集するメタタスクでは言及の混入が常態。宣言フォーマットは `NO_OP_JUSTIFIED: <理由>`（implementer.md:107）と定義済み。 → `grep -qE '^\s*(-\s*)?NO_OP_JUSTIFIED:'` のように行頭＋コロンでアンカーする（フェンス内引用は完全には防げないが実質リスクを大幅に削れる）。
- **Medium** `deterministic-completion-check.md:22,53-55` — **サブモジュール内ファイルの編集は親リポの post に「サブモジュールパス 1 行」としてしか現れない**（scratch repo で実証: `mysub/inner.md` を編集 → post は `mysub`）。implementer が `mysub/inner.md` と申告すると文字列不一致で PHANTOM 偽陽性 hard fail。dotfiles には submodule が 3 つ（ai-design-system / ai-diary / ai-ltm）実在し、これらのスキルを編集するタスクで発火し得る。 → 「検証の情報源」節にサブモジュールの扱いを明記する（最小対応: 申告パスがサブモジュール配下なら submodule ルートに丸めて照合、または「サブモジュール内編集タスクは 3b 相当の検証不能扱い」と明文化）。
- **Medium** `deterministic-completion-check.md:126-131`（reference-fidelity・設計 SSOT との未申告の意味論乖離） — SSOT §1-3-2 は「**CLAIMED_FILES=none かつ編集想定タスク → PHANTOM 扱い**（NO_OP_JUSTIFIED 宣言時は免除）」を delta の状態に**無条件**で規定するが、reference の判定表は「claimed 空かつ **delta も空**のときのみ PHANTOM。claimed 空かつ delta 非空は warn（row 4）」に緩和している。この緩和は plan 付録A の段階で導入され、3b/3c（verify-01.md に意図的逸脱として申し送り済み）と異なり**どこにも逸脱として記録されていない**。緩和自体は「抽出失敗・報告書式ドリフトを hard fail にしない」合理性があるが、epic W2 が SSOT §1-3 を逐語実装すると両ゲートの判定が食い違う。 → reference に「SSOT §1-3-2 からの意図的緩和である」旨と理由を 1 行明記する（または SSOT 側に追記）。
- **Medium** `.claude/skills/pir2codex/SKILL.md:186-198`（6-1b/6-1c） — shards / sequential での 6-3 の実行位置が未規定。6-1a（182行）だけが「Write → 検証 → threadId」を明示し、6-1b/6-1c は統合確認までしか書いていないため、(a) 6-3 を「各 wrapper 返り毎」に行うのか「全 shard/unit 完了＋統合確認後に 1 回」なのかが読み手依存、(b) 直列途中で PHANTOM が出た場合の unit 再実行のスコープ・`IMPL_INDEX` インクリメント後の unit レポート命名（`implementation-02-unit-03.md`?）が未定義。CLAIMED 和集合（glob `implementation-{idx}*.md`）と pre-set 単一記録自体は両モードで数学的に整合することは確認済みで、欠けているのは手順の規定のみ。 → 6-1b/6-1c の末尾に「統合確認の後に 6-3 を 1 回実施」を明記し、直列途中 PHANTOM の再実行単位を規定する。
- **Medium**（プロセス・round-1 指摘の未解消残） — `.claude/agents/implementer.md` の NO_OP 追記（107行）に対する `.codex/agents/implementer.toml` の再生成が依然未実施（サブエージェント Edit では PostToolUse hook 不発。round-1 architecture が担当外指摘済みだが最終ラウンド時点でも `git status` に toml の差分なし）。Codex CLI / OpenCode 経由の implementer には NO_OP_JUSTIFIED ガイダンスが伝播せず、正当な no-op が PHANTOM 誤判定される片系統が残る。 → コミット前にスキル本体が `bash etc/sync-codex.sh`（必要なら `sync-opencode.sh`）を実行する。

#### Low（5件）

- **Low** `deterministic-completion-check.md:27-32,73-74` — パス正規化の残り穴: `./` プレフィックス・末尾 `/`（ディレクトリ申告）・1 行複数バッククォート（2 個目以降のパスは黙って捨てられる）はいずれも未正規化で、偽 PHANTOM / 申告漏れの小穴。rename の old path は仕様上必ず UNDECLARED warn ノイズになる（許容内だが正規化仕様に注記すると親切）。
- **Low** `deterministic-completion-check.md:124-136` — 判定表の適用（各 list の空/非空判断と verdict 合成）は LLM がファイルを読んで行う設計のまま。SSOT §0「LLM 判断は検証経路に挟まない」の完全化には、判定行まで bash 化（`[ -s phantom.list ] && echo PHANTOM_CLAIM` 等の verdict 出力スニペット）が半歩残っている。
- **Low** `deterministic-completion-check.md:60-62` — `verify-${PRE_IMPL_INDEX}-pre.list` 不在時（resume 端・記録漏れ・本機能導入前の run の再開）に `comm` がエラーし delta.list が空生成 → UNDECLARED 層のみ silent 無効化される。`[ -f ...pre.list ] || { echo "pre-set 不在"; }` の存在ガード 1 行が安い保険。
- **Low**（プロセス） — `verify-02.md` が存在しない（verify-02-*.list のみ）。round-2 は review-fix（7-4）で 6-3 のスコープ外だからドッグフード任意実行自体は正当だが、list だけ残しレポート未作成は中途半端で、外部参照（本レビュー依頼文含む）が実在ファイルとして誤参照している。作るか消すか、いずれかに揃えるとよい。
- **Low**（将来 follow-up への申し送り） — verify-02 実データ（claimed 4 / delta 0）が示すとおり、**再実装ラウンドでは対象ファイルが既に dirty のため delta が空になり、検証力が post 照合（＝既 dirty への虚偽申告を検出できない SSOT 残存限界④そのもの）に縮退する**。6-3 を 7-4/8-2 へ拡張する follow-up の際は、この縮退を設計前提として明記すべき。

---

### 良好点

- 非対称検証（hard fail は PHANTOM のみ・UNDECLARED は warn）の設計哲学が bash・判定表・失敗パス・ユーザーゲートまで一貫している。fail-open に倒れる分岐が M1/L3 の 2 点まで絞り込まれていること自体は、この種のプロトコル文書として高い完成度。
- `PRE_IMPL_INDEX` の導入と「pre 側だけ固定・post/delta/CLAIMED は現行 index」という分離は、既存の名目変数パターン（INNER_LOOP_COUNT 等）に忠実で、round-1 の High を正しく閉じている。
- ドッグフーディング（本 run 自身への 6-3 適用）で 3b の必要性を実地発見し、逸脱を verify-01.md に申し送りした運用は、この検証機構の目的（申告と実体の突合）を自己適用した好例。
- pir2codex の順序制約に「なぜこの順序でなければならないか」の理由文が付されており（「先に検証すると CLAIMED が常に空になり誤判定する」）、将来の再破壊への耐性がある。

### 次のアクション（implementer への差し戻し）

1. **H1**: reference の 4 つの git 呼び出し（pre-set / post-set の diff / ls-files）に `-c core.quotePath=false` を追加。
2. **H2**: CLAIMED 抽出をフェンス除去＋初回セクション打ち切りの awk 方式に置換（修正後、本レビューのフィクスチャ相当＝「フェンス内にテンプレート引用を含むレポート」で `real/file.md` のみ抽出されることを実機確認）。
3. **H3**: 失敗パスの再実行仕様を「再実行レポートは訂正後の完全な変更ファイル一覧を再宣言する。PHANTOM 照合は最新ラウンドのみ・UNDECLARED 照合は累積」に改訂し、bash（ステップ 3/4）をそれに合わせて分離。
4. M1（NO_OP grep の行頭コロンアンカー）・M3（SSOT 乖離の明記 1 行）は H 修正と同時対応を推奨。M2/M4 は文書追記のみで閉じられる。M5 は implementer ではなくスキル本体が `bash etc/sync-codex.sh` を実行。
5. 修正後の再レビューは H1/H2 の実機再現フィクスチャ（scratchpad/dcc-1783084677 の手順）で回帰確認すること。
