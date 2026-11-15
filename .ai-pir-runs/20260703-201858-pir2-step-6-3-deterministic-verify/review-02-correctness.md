VERDICT: PASS

### 担当 role
correctness

### 判断根拠

- **バグ・正確性（前回 High/Medium の解消確認）**:
  `.claude/skills/pir2/references/deterministic-completion-check.md` を全文 Read し、前回 FAIL の2指摘それぞれについて実機シミュレーション（scratch git repo を作成し、実際に pre-set/post-set/CLAIMED 抽出/3b/3c/PHANTOM/UNDECLARED の bash を逐語実行）で検証した。

  1. **FIX-1（3b tilde 対応）**: `case "$p" in /*|"~"|"~"/*) ...` を実際に `~`, `~/foo/bar.md`, `~/`, `/abs/path`, `relative/path` の5パターンで実行し、前者4つが `UNTRACKABLE` に、`relative/path` のみ通過することを確認した（`bash -c` での直接実行、結果は本文参照）。前回 High で指摘された「`~/...` 記法が `/*` にマッチせず claimed-trackable に混入 → PHANTOM 誤検知」という具体的な再現手順は、修正後は `~/.claude/projects/foo/memory/pir_implementer_log.md` が正しく `claimed-untrackable.list` に分類されることをエンドツーエンドの scratch-repo シミュレーションで確認し、解消を確認した。

  2. **FIX-5（PRE_IMPL_INDEX 導入・CLAIMED 累積）**: 前回 architecture reviewer が High として指摘した「pre.list と post.list が同一 `${IMPL_INDEX}` 変数でファイル名を組み立てるため、リトライ後に pre.list が存在しない/誤って新規スナップショットを取り直す」という潜在バグと、前回 correctness reviewer が Medium として指摘した「CLAIMED 抽出が新ラウンドのみに限定され、旧ラウンドの正当な申告が UNDECLARED 誤検知される」という2点を、2ラウンドの PHANTOM retry を模したシナリオ（round1: `a.txt` を変更したと申告したが実際は `b.txt` のみ変更 → PHANTOM 検出 → round2: `IMPL_INDEX` を 01→02 にインクリメントし `a.txt` を実際に変更、`implementation-02.md` には round2 分の `a.txt` のみ申告）で実際に bash を実行し検証した。結果: `PRE_IMPL_INDEX=01`（据え置き）・`IMPL_INDEX=02` の下で `delta.list` が `a.txt,b.txt`（round1+round2の実変更を正しく累積）、`claimed.list` も `a.txt,b.txt`（`for idx in "$PRE_IMPL_INDEX" "$IMPL_INDEX"` ループにより round1 の `implementation-01.md` と round2 の `implementation-02.md` 両方の申告を累積・`sort -u` で重複排除）となり、`phantom.list` / `undeclared.list` ともに空（正しく PASS 判定）であることを確認した。旧実装なら round1 の `b.txt` 申告が round2 の CLAIMED に含まれず UNDECLARED 誤検知が発生していたはずだが、その退行が解消されていることを実行結果で確認した。

  3. **`comm` の集合前提・claimed-trackable/claimed の使い分け**: `sort -u` を経た入力に対する `comm -13`（delta = post − pre）・`comm -23`（phantom = claimed-trackable − post、undeclared = delta − claimed）が全シミュレーションで意図通りの集合演算結果を返すことを確認した。PHANTOM 判定行は `claimed-trackable`（3b フィルタ後）を、UNDECLARED 判定行は（フィルタ前の）`claimed` を使うという非対称設計は、doc 内の脚注（132行目）が説明する理由（delta は git 追跡可能なファイルしか含み得ないため UNDECLARED 側はフィルタ不要）と実際の動作が一致することを確認した。

  以上により、前回 FAIL の根拠となった2件（tilde 未対応・CLAIMED 再集計不整合）はいずれも実機検証込みで解消を確認した。

- **新規リグレッション確認**: `.claude/skills/pir2codex/SKILL.md` の diff（FIX-2/FIX-3: 「wrapper 返り後の処理」の手順順序を「レポートWrite→検証→threadId保持」に組み替え）を確認した。旧実装は「1. git diff 検証 → 2. threadId 保持 → 3. レポート Write」の順で、CLAIMED の情報源（`implementation-*.md` の `### 変更ファイル一覧`）が検証実行時点でまだ存在しないため CLAIMED が常に空になる欠陥があったが、新実装は Write を検証より先に移動しており、この欠陥は解消されている。6-2（inner-loop 再実装）が「6-3 は初回実装（6-1）のみ適用するスコープで、6-2 では対象外（git diff による軽量自己チェックのみ）」という設計を明記しており、これは前回レビュー時点で既に確立していた設計（本ラウンドで変更されていない既存スコープ）と整合する。`.claude/skills/pir2/SKILL.md` の diff（6-3 手順の新設・pre-set 記録位置の起動宣言文より前への移動・`#### 完了後` の `### 完了後` への統合）および `next-steps-queue.md` の diff（6-3 checkbox 文言追記）も確認したが、いずれも architecture/consistency 指摘への対応であり、correctness の観点で退行を生む変更は見当たらない。`bash -n` で全3つの bash ブロックの構文チェックを実行し、いずれも構文エラーなしを確認した。

- **パフォーマンス**: 前回から変更なし。`git check-ignore` を1件ずつ `while read` ループで呼ぶ設計（3b）に加え、3c で `test -f` を1件ずつ実行する処理が追加されたが、想定 CLAIMED 件数（数〜数十件オーダー）に対しては無視できるオーバーヘッド。

### 問題一覧

- Medium `.claude/skills/pir2/references/deterministic-completion-check.md:83-84`（3b） — tilde 記法のうち **`~user/...`（他ユーザーのホームディレクトリ展開）形式が untrackable 判定の対象外**のまま残っている。実機確認済み:
  ```bash
  $ bash -c 'case "~user/foo.md" in /*|"~"|"~"/*) echo untrackable;; *) echo "trackable-candidate";; esac'
  trackable-candidate
  $ git check-ignore -q -- "~user/foo.md"; echo $?
  1   # 「無視されていない」= trackable 扱いに分類される
  ```
  この形式が `claimed-trackable.list` に混入した場合、post.list には絶対に現れない（実在しない相対パスのため）ので PHANTOM 誤検知（hard fail）を再発する経路が理論上残る。ただし、この doc 自身が「git 検証不能な申告」の対象として明記しているのは常に `~/...`（カレントユーザーのホーム相対）のみであり（23行目、`~user` への言及はどこにもない）、PIR² の実行文脈（実装 actor が自分自身のメモリ/ログパスを申告する場面のみ）で他ユーザーのホームディレクトリを参照する事態は現実的にほぼ起こり得ないため、前回 High 指摘（`~/...` という文書内で明記された想定ケース自体が対象外だった問題）とは性質が異なる（ドキュメントが明示的にカバーを謳っていない拡張ケース）。とはいえ将来 pir2/pir2codex が他ユーザー環境や共有ワークスペースで再利用される可能性を考えると、`case` パターンを `/*|~|~/*|~[a-zA-Z0-9_]*)` のように拡張するか、`case "$p" in ~*)` （tilde 全般を1パターンで捕捉、ただし unquoted だと tilde 展開に巻き込まれるため `"~"*` のようにクォート）にしておくと堅牢性が上がる。→ 修正案（任意対応）: `case "$p" in /*|"~"*) ...` へ変更（`"~"*` は先頭が文字通り `~` である任意の文字列にマッチし、bash の tilde 展開の影響を受けない）。

- Medium `.claude/skills/pir2/references/deterministic-completion-check.md:100-107`（3c） — 「git 検証不能な申告の実体確認」の existence チェックが、**gitignore 対象の相対パス（例: `.ai-pir-runs/xxx/handoff.md`）に対して `$PROJECT_ROOT` アンカリングを行わず、シェルのカレントディレクトリ依存で `[ -f "$p" ]` を実行**している。同 doc の他の全 git 操作（pre-set/post-set/3b の `check-ignore`）は一貫して `git -C "$PROJECT_ROOT"` で明示的にディレクトリを固定しているのに対し、3c の `case` 分岐は `"~"` / `"~"/*` の2パターンのみ `$HOME` 展開しており、残る `*)` フォールバックが「絶対パス（アンカリング不要）」と「gitignore 対象の相対パス（`$PROJECT_ROOT` 基準でアンカリングが必要）」を区別せず同一に扱っている。scratch repo での実機シミュレーションで再現を確認した:
  ```
  # $PROJECT_ROOT=/private/tmp/.../verify-sim/repo に実在する
  # .ai-pir-runs/somebogus/handoff.md を claimed-untrackable と申告
  # → 3c 実行時のシェル cwd が $PROJECT_ROOT と異なると missing 誤判定される
  ==  claimed-untrackable ==
  .ai-pir-runs/somebogus/handoff.md
  ~/.claude/projects/foo/memory/pir_implementer_log.md
  == claimed-untrackable-missing ==
  .ai-pir-runs/somebogus/handoff.md   # 実際には存在するのに missing 判定（cwd 依存のバグ）
  ~/.claude/projects/foo/memory/pir_implementer_log.md
  ```
  この doc 自身が「git 検証不能な申告」の headline 例として挙げている `.ai-pir-runs/` 配下の handoff.md（23行目）がまさにこのバグの対象になる。実行時のシェル cwd が `$PROJECT_ROOT` と一致していれば問題は顕在化しないが（pir2 は `PROJECT_ROOT="$(pwd)"` で起動時の cwd を固定するため実運用上は一致するケースが多いと推測される）、同 doc の他の箇所が一貫して `-C` でこの前提に依存しない設計をしているのと矛盾する。影響は `claimed-untrackable-missing.list`（warn 専用・hard fail 対象外）に限定されるため PASS/FAIL 判定自体は誤らせないが、FIX-4 の目的（「silent な抜け穴にしない」可視化）が cwd 依存で不正確な警告を出しうる点は見過ごせない。→ 修正案: `*)` フォールバックを `case "$p" in /*) expanded="$p" ;; *) expanded="${PROJECT_ROOT}/${p}" ;; esac` のようにネストし、絶対パスと相対パス（gitignore 対象）を明示的に分岐させる。

### 良好点
- FIX-1（tilde 対応）・FIX-5（PRE_IMPL_INDEX 累積）ともに、前回指摘の再現手順をそのまま scratch git repo でトレースし直し、修正後は期待通りの分類・集合演算結果になることを実行結果で確認できた。特に FIX-5 は「pre-set 据え置き・CLAIMED 累積・delta 累積」という3点が絡む複雑なロジックだが、2ラウンドのシミュレーションで phantom/undeclared がともに正しく空になることを確認でき、設計意図どおりに機能している。
- pir2codex 側の手順順序組み替え（FIX-2）は「情報源が存在してから検証する」という当たり前だが見落としやすい因果順序の修正であり、`git diff で実体検証` という旧表現の残存（FIX-3）も整合的に一掃されていることを確認した。

### 担当外で気づいた点（参考）
- `.claude/skills/pir2/references/deterministic-completion-check.md:65-66` — CLAIMED 抽出のコメントに「通常（再実行なし）は PRE_IMPL_INDEX == IMPL_INDEX で同じファイルを1回読むだけ」とあるが、実際の `for idx in "$PRE_IMPL_INDEX" "$IMPL_INDEX"` は両者が同値でも2回ループして同一ファイルを2回読む（`sort -u` で重複排除されるため結果は同じだが、コメントの記述がやや不正確）。動作に影響しない誤記レベルの指摘のため quality/consistency 観点判断に譲る。

### 次のアクション
なし（VERDICT: PASS）。任意対応として、上記2件の Medium（`~user` tilde 形式の網羅性・3c の `$PROJECT_ROOT` アンカリング）は次回の軽微な改善時にまとめて解消することを推奨する。
