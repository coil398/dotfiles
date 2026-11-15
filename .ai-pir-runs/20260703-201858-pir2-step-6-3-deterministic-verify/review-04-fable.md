VERDICT: PASS

### 担当 role
comprehensive（Fable5 最終確認再レビュー。review-03-fable.md の High 3件 + should-fix の修正確認と新規リグレッション監視）

### レビュー方針
implementation-03/04 の全修正を実物 Read + 実機検証で確認した。verify スクリプト 2 本は呼び出し元の実行結果を鵜呑みにせず自分で再実行し一致を確認。submodule まわり（FIX-F）は scratch repo（親リポ + 実 submodule）を作り、**reference から実際に抽出した bash ブロック**で end-to-end 実行して挙動を確定させた（フィクスチャ: scratchpad/dcc-final-04）。

---

### 判断根拠（確認した事実）

#### H1（core.quotePath）— 解消を確認
- pre-set（reference 56-57行）・post-set（71-72行）の diff / ls-files 計 4 呼び出し全てに `-c core.quotePath=false` が付与されている。理由コメントも併記。
- 非ASCII フィクスチャ（`日本語ファイル.txt` を untracked で申告）を私自身の `verify-deterministic-check.sh` 再実行で確認: claimed-trackable に生 UTF-8 で入り、phantom 空。**実機で偽陽性解消を確認**。

#### H2（CLAIMED 抽出のフェンス誤認識・範囲再開）— 解消を確認
- 抽出が「フェンス除去 awk（`/^```/{c=!c;next} !c`）→ セクション打ち切り awk（`/^### 変更ファイル一覧/{f=1;next} (/^## /||/^### /){if(f)exit} f`）」の 2 段に置換（91-92行）。
- 論理確認: (a) `exit` により最初のセクション終端で awk 全体が終了するため、レポート後方の見出し再出現による**範囲再開は構造的に不可能**。(b) フェンス内引用は前段で除去されるため汚染不可能。(c) EOF 終端（変更ファイル一覧が最終セクション）も f=1 のまま出力継続で正しい。
- フェンス内 decoy フィクスチャ（`decoy/fake/path.txt` をフェンス内例示に含む）を再実行で確認: claimed に decoy 混入なし・phantom 空。NO_OP 判定（block-3）も同じ 2 段前処理＋`### 注意点・未解決事項` セクション限定＋行頭アンカー（179-181行）に統一されている。

#### H3（CLAIMED 累積の撤回）— 解消を確認
- CLAIMED は `for f in "$RUN_DIR"/implementation-${IMPL_INDEX}*.md` の**現ラウンド単一 glob のみ**（89行）。PRE との和集合ループは存在しない（grep で不在確認）。
- `PRE_IMPL_INDEX` は pre.list のファイル名参照（51行・76-78行・失敗パス手順2の 224行「PRE_IMPL_INDEX は変更しない」）**専用に温存**。post/delta/CLAIMED は現行 `IMPL_INDEX`。
- 失敗パスの再実行プロンプト（221行）に「**訂正後の完全な変更ファイル一覧を再宣言すること**」が required として明記され、申告訂正の救済経路が構造的に成立する。関連 4 箇所（抽出コメント 82-86行・失敗パス 221/224行・verify テンプレート 200行）の記述が全て整合。
- 副作用確認: 再宣言漏れは UNDECLARED warn（非ブロッキング）に落ちる設計で、設計 SSOT の非対称検証（hard fail は PHANTOM のみ）と整合。旧・累積方式の導入理由（前ラウンド正当申告の誤検知防止）は再宣言指示で代替されており、退行なし。

#### should-fix 4件
- **pre.list 存在ガード**: 手順0（66-68行）に fail-loud の ERROR（stderr）＋ 150行の blockquote に運用指示（「PHANTOM 照合のみでの縮退運転はしない」）。ワークフローを止めない非ブロッキング設計は implementation-03 自己検証(f) の実機確認どおり。
- **NO_OP grep**: 無アンカー `grep -q` → フェンス除去＋セクション限定＋`^[[:space:]]*(-[[:space:]]*)?`?NO_OP_JUSTIFIED:`?`（181行）。番号リスト（`4. NO_OP_JUSTIFIED: 該当なし` — implementation-03.md 自身に実例あり）を**意図的に除外**した判断は fail-closed 方向で安全。implementer.md:107 の規定フォーマット（素の `NO_OP_JUSTIFIED:` / 箇条書き `-`）と一致することを実物 Read で照合。
- **submodule**: 部分的（下記 Medium 参照）。
- **pir2codex 6-1b/6-1c**: 「統合確認の**後**に 6-3 を全 shard/unit 申告の和集合へ 1 回だけ」が SKILL.md（6-1b/6-1c 両方）と reference「適用タイミング」節の双方に明記。位置が「統合後 1 回」に確定したことで review-03 M-4 の「直列途中 PHANTOM」問題は発生し得なくなった（質問自体が解消）。6-2 の dangling reference も「適用タイミング」節（実在）への参照に修正済み。

#### 適用タイミング節（新設）
- 決定1=(A)（初回実装点のみ・7-4/8-2 対象外）と一致。user-decisions.md の決定 1〜3 と全て整合。本 run の verify-02 拡大適用を「正式仕様外」と明文化しており、review-03 の verify-02 まわりの指摘（L）にも実質回答している。

#### IMPL-04（L-1/L-2/L-4・M-4・sanitized_cwd 登録）
- L-1: verify-{IMPL_INDEX}.md テンプレート（199-203行）に PRE_IMPL_INDEX / CLAIMED 情報源 / PHANTOM_RETRY_COUNT / untrackable 件数 / untrackable-missing 件数を追加。判定表・失敗パスと記載項目が整合。
- L-2: 3b の `/*|"~"*)` クォート統一（106行）。case パターンではチルダ展開は元々起きないため機能等価＝安全な表記改善。
- L-3: 正当な no-op（指摘対象コメントが FIX-C で既に消滅）。grep で「1回/2回」系コメントの不在を私も確認。
- L-4: pir2/SKILL.md の pre-set 記録指示が pir2codex と対称の独立 h4 見出しに昇格（diff で確認）。
- M-4 `verify-deterministic-check.sh`: **私自身の再実行で 3 ブロック構文 OK + 5 フィクスチャ全一致（exit 0）**。健全性確認: (a) フィクスチャは**本物の reference から trim 完全一致方式で抽出したブロックを実行**しており、ロジックの複製ではなく SSOT 自体を検証している。(b) 埋め込み ``` （`awk '/^```/...'` 行）を閉じフェンスと誤認しない抽出方式で、implementation-04 は素朴抽出への一時差し替えによる mutation test（false NG の実出現確認）まで実施。(c) 後始末は `trap cleanup EXIT` + `find -mindepth 1 -delete` + `rmdir` で **`rm -rf` 不使用**。(d) scratch repo に `core.hooksPath /dev/null` を設定しグローバル pre-commit dispatcher（gitleaks）を回避。(e) bash 3.2 互換（空配列参照は `${#arr[@]}==0` ガード後にのみ `"${arr[@]}"` 展開・mapfile 不使用）。(f) ブロック数 ≠3 時はフィクスチャを WARN スキップ（構文チェック結果は有効のまま）で前提脆弱性を明示。
- sanitized_cwd epic 登録: verify-sanitized-cwd.sh の SKILL_FILES に epic/SKILL.md 追加＋sanitized-cwd.md の 9→10 同期（冒頭・consumer 表・ファイル一覧・手順・出力例の全箇所）。**私の再実行で 10 ファイル OK**。値の出現箇所単位の同期漏れなし。

#### 新規リグレッション監視（重点）
- H3 変更（現ラウンドのみ CLAIMED）: 前ラウンド正当申告の再宣言漏れ → UNDECLARED warn 止まり（fail-open 方向だが warn で可視化・設計 SSOT の受容済み非対称と同型）。退行なし。
- FIX-F（`--ignore-submodules=all`）: **1 件の部分リグレッションを実機で検出**（下記 Medium M-A の (2)）。それ以外の通常ファイル系の挙動はフィクスチャ 5 種で不変を確認。
- スコープ: IMPL-03 の変更は宣言どおり 2 ファイル、IMPL-04 は宣言どおり（+gitignored handoff・memory ログ）。作業ツリーの他の diff（implementer.md / delegation.md / next-steps-queue.md / pir2 SKILL 手前半 等）は本 run の先行ラウンド（implementation-01/02 で申告済み）、experimental.md / CLAUDE.md / .gitignore / epic 系はセッション開始時点で既存の並行作業由来（gitStatus スナップショットと一致）。IMPL-03/04 によるスコープ逸脱なし。

---

### 問題一覧

#### Medium（1件）

- **Medium** `deterministic-completion-check.md:33,55-56,71` — **FIX-F（submodule 対応）が不完全で、doc の記述が実挙動と乖離している**。scratch repo（親リポ+実 submodule）で reference から抽出した実ブロックを end-to-end 実行して確認した事実:
  1. **submodule 内パス申告（`mysub/inner.md`）は PHANTOM hard fail のまま**。`git check-ignore -q -- mysub/inner.md` は exit 128（`fatal: Pathspec 'mysub/inner.md' is in submodule 'mysub'`）を返し、3b の `if` では偽 → **else 分岐で claimed-trackable に分類**される。post は `--ignore-submodules=all` で空 → phantom 入り。33行の「サブモジュール内ファイルの編集タスクは本ゲートでは検証不能扱いとなる」は、本 doc 自身の用語定義（検証不能 = PHANTOM 判定対象外の untrackable バケット）と照らすと**実挙動と矛盾する誤記述**（実際は hard fail）。
  2. **pointer bump 申告の新規リグレッション**: submodule のコミット参照だけを進めたケース（`git diff --name-only` は本来 `mysub` を 1 行出す = 親リポで正当に追跡可能な変更）が `--ignore-submodules=all` で post から消え、`mysub` と申告すると **PHANTOM hard fail**（FIX-F 前は post に `mysub` が出て PASS だった）。
  - 帰結はいずれも fail-loud（再実行 1 回浪費 → ユーザーゲート、選択肢 (B) で回復可能）で発火条件も稀（submodule 編集/bump タスク × 申告）のため Medium に留める（review-03 で同系を Medium 判定した較正とも整合）。ただし dotfiles には submodule が 3 つ実在（ai-design-system / ai-diary / ai-ltm）し発火し得る。
  - → 修正案（2 点セット・数行）: (a) pre-set / post-set の diff を `--ignore-submodules=all` → **`--ignore-submodules=dirty`** に変更（内容 dirty は除外したまま pointer bump を post に復元）。(b) 3b で check-ignore の終了コードを取り、**0（ignored）または 2 以上（fatal = submodule 内等）を untrackable に振り分ける**（例: `git -C "$PROJECT_ROOT" check-ignore -q -- "$p" 2>/dev/null; rc=$?; if [ "$rc" -ne 1 ]; then untrackable; else trackable; fi`）。これで 33 行の「検証不能扱い」が実挙動として真になり、3c の `test -f` 可視化にも乗る。

#### Low（5件）

- **Low** `deterministic-completion-check.md:132` — 3c の `~*)` が unquoted のまま（L-2 のクォート統一は 3b のみ）。case パターンではチルダ展開されず機能差ゼロだが、同一ファイル内で `"~"*`（3b）と `~*`（3c）の表記が混在。
- **Low** `deterministic-completion-check.md:68,150` — 手順0 の ERROR 文（「原因を確認せよ」）と blockquote（「6-1 の pre-set 記録手順に戻ってやり直す」）の指示粒度に差があり、「やり直す」の具体アクション（pre-set 再記録＋実装 actor 再実行、の両方が必要）が一読で確定しない。1 句補うと親切。
- **Low** `deterministic-completion-check.md:91` — フェンス除去 awk は 4-backtick 入れ子フェンス（```` で開き内部に ``` を含む例示）で内容が漏れ得る。漏れが CLAIMED を汚染するのは「変更ファイル一覧セクション内に入れ子フェンスがある」場合のみで現実性は極めて低く、方向も fail-closed（偽 PHANTOM）。記録のみ。
- **Low** `verify-deterministic-check.sh` — 実行ビットなし（`verify-sanitized-cwd.sh` は 755）。用法は `bash <path>` 直呼びのため機能差なしだが、同種スクリプトとの表記ゆれ。
- **Low** `verify-deterministic-check.sh` — フィクスチャに submodule シナリオがない。上記 Medium M-A を修正した際は「submodule 内申告 → untrackable」「pointer bump 申告 → PASS」の 2 assert を追加すると回帰防止になる。

---

### 良好点

- H1/H2/H3 の修正がすべて「reference 内の実ブロックを抽出して実行する」機械検証（M-4 スクリプト）で担保され、私の独立再実行でも全一致した。修正 → 検証機構の同時新設 → mutation test（素朴抽出への差し替えで false NG の実出現を確認してから戻す）という進め方は、この run 自体が作っている「申告と実体の突合」思想の模範的な自己適用。
- FIX-E で呼び出し元指示（番号リスト対応許容）より絞る判断をし、その根拠（`4. NO_OP_JUSTIFIED: 該当なし` という否定の慣習表現を宣言と誤認する fail-open 穴の実機発見）を implementation-03 に明記した。指示の字義より安全性の実データを優先し、かつ逸脱を隠さず申告する運用は正しい。
- H3 の修正で「PHANTOM 照合は現ラウンドのみ・UNDECLARED は再宣言指示でカバー」という分離が、bash・コメント・失敗パス・verify テンプレートの 4 箇所で一貫して書かれており、将来の再破壊耐性がある。

### 次のアクション

なし（PASS）。Medium M-A（submodule: `dirty` 化 + 3b の exit 128 振り分け）と Low 2 件（3c クォート・フィクスチャ追加）は数行の follow-up として次 run または refactor 適用ゲートで対応するのが妥当。
