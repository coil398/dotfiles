VERDICT: FAIL

### 担当 role
correctness

### 判断根拠

- **バグ・正確性**:
  新規 reference `.claude/skills/pir2/references/deterministic-completion-check.md` の集合照合 bash を逐行検証した。`sort -u` による正規化・`comm -13`（delta = post - pre）・`comm -23`（PHANTOM = claimed-trackable - post、UNDECLARED = delta - claimed）の各集合演算は集合論的に正しい（`comm` の入力は全経路で `sort -u` 済み）。CLAIMED 抽出の `sed -n '/^### 変更ファイル一覧/,/^### /p'` は GNU/BSD sed の標準挙動（終了アドレスの照合は開始行の**次の行**から始まる）により、見出し自身が終了パターンにもマッチする構造でも即座に打ち切られず正しく次セクション境界まで抽出することを確認した。`grep -E '^- *`'` → `sed -E 's/^- *`([^`]+)`.*/\1/'` によるパス抽出も、backtick で囲まれた最初のペアのみを非貪欲的に取り出す設計で、概要文中に追加の backtick が含まれても誤動作しない。

  しかし、ステップ 3b「git-trackability フィルタ」（ドッグフーディングで追加された偽陽性修正本体）に**実装漏れ**を発見した。詳細は「問題一覧」参照（tilde パス未対応）。この 3b はまさに今回のドッグフーディングで見つかった偽陽性を修正するために追加された箇所であり、その同じ箇所に新たな見落としがあるのは看過できない。

  加えて、失敗パス（PHANTOM 再実行）における CLAIMED 再集計のロジックにも部分的な不整合を検出した（「問題一覧」参照）。

- **パフォーマンス**:
  全処理は `git diff --name-only` / `git ls-files --others --exclude-standard` / `sort -u` / `comm` / `sed` / `grep` の単純な O(ファイル数) 処理であり、想定される PIR² の変更ファイル数（数十件オーダー）に対して性能上の懸念はない。`git check-ignore` をパスごとに `while read` ループで1回ずつ呼ぶ（3b）のは N 回の子プロセス起動になるが、想定 CLAIMED 件数が数〜数十件程度である PIR² のスコープでは許容範囲。

- **リグレッション**:
  pir2codex 側の既存 6-1「wrapper 返り後の処理」bullet 1・bullet 3 の書き換えを確認した。旧実装は `git diff --stat HEAD` / `git diff --name-only HEAD`（**staged+unstaged・HEAD 基準**）で実体検証していたが、新実装は共通 reference の `git diff --name-only`（unstaged のみ）+ `git ls-files --others --exclude-standard`（untracked）に統一される。plan.md 内で明示的にこの実集合定義変更を「意図的」と申告しており（注意点・リスク欄）、リグレッションではなく設計変更として妥当。実際に `grep -n 'git diff --name-only HEAD'` 相当で旧記述が残っていないことも implementation-01.md の自己検証記録で確認済み（本 reviewer でも `git diff` で該当箇所を直接確認し、旧 bullet がプロトコル参照に完全置換されていることを確認した）。既存の 6-2 inner-loop（review-fix ループ側の git diff 検証）は明示的に無変更（プランの決定1範囲を厳守）であることも diff で確認した。既存の implementer.md「diff-to-plan 照合（必須）」（`git diff --name-only HEAD` ベースのスコープ逸脱検知、既存の別ロジック）とは実集合定義（HEAD 基準 vs pre-set 基準）が異なる二重体系になるが、両者は目的が異なる別レイヤー（スコープ逸脱検知 vs 捏造検知）であり共存に矛盾はない。

### 問題一覧

- High `.claude/skills/pir2/references/deterministic-completion-check.md:23,75-84` — ステップ 3b「git-trackability フィルタ」の絶対パス判定 `case "$p" in /*) ... ;; esac` が **tilde 展開前のパス（`~/...`）を捕捉できない**。同じ段落で「検証不能」の例として明示的に挙げている `~/.claude/projects/.../memory/*` という記法（tilde 形式）自体が、実装されたケースパターンの対象外になっている。実機検証済み:
  ```bash
  $ bash -c 'p="~/.claude/projects/foo/memory/bar.md"; case "$p" in /*) echo matched;; *) echo "not matched";; esac'
  not matched
  $ git check-ignore -q -- "~/.claude/projects/foo/memory/bar.md"; echo $?
  1   # 「無視されていない」= trackable 扱いに分類される
  ```
  つまり CLAIMED に tilde 形式（例: `` `~/.claude/projects/-Users-kawasetakumi-dotfiles/memory/pir_implementer_log.md` ``）で申告された場合、`/*` にマッチせず `git check-ignore` にも掛からないため `claimed-trackable.list` に混入し、post.list には絶対に現れない（実在しない相対パスのため）ので `comm -23 claimed-trackable post` で **PHANTOM_CLAIM として誤検知（hard fail）**される。これはまさに今回のドッグフーディングで発見・修正したはずの偽陽性バグ（リポ外ファイルの誤検知）が、tilde 記法という別の入り口から再発する経路である。
  今回の実データ（implementation-01.md）ではメモリログパスが `$HOME` 展開済みの絶対パス（`/Users/kawasetakumi/.claude/projects/...`）で記載されていたため 3b は正しく機能したが、これは `PROJECT_MEMORY_DIR="${HOME}/.claude/projects/${sanitized_cwd}/memory"`（pir2 SKILL.md 25行目）という **このプロジェクト内の特定変数だけ** が `$HOME` 展開されている偶然の産物であり、一般則ではない。tilde 記法（`~/...`）はこのリポジトリの CLAUDE.md・agents・SKILL.md 全体で最も頻出するパス表記慣習であり、他プロジェクトで pir2/pir2codex を使う際に実装 actor がリポジトリ外ファイル（ユーザーのホーム直下の設定ファイル等）を tilde 記法で申告するのは十分に起こり得る。
  → 修正案: `case "$p" in /*|~*) ...` のように tilde もパターンに追加するか、ループ冒頭で `p="${p/#\~/$HOME}"`（bash パラメータ展開によるチルダ正規化）を実行してから `/*` 判定に通す。

- Medium `.claude/skills/pir2/references/deterministic-completion-check.md:147-151` — PHANTOM 検出時の再実行（失敗パス 2.）で「`IMPL_INDEX` をインクリメントし... pre-set は据え置き（同じ基準で再照合）」と明記されているが、CLAIMED 抽出の bash（47-67行目）は `"$RUN_DIR"/implementation-${IMPL_INDEX}*.md` という **インクリメント後の新しい `IMPL_INDEX` だけ**をグロブする設計になっている。実装 actor（implementer / Codex）はサブエージェントとして fresh に再起動されるため、再実行後の新しい `implementation-{new_IMPL_INDEX}.md` は通常「今回の呼び出しで対応した内容」のみを申告し、直前ラウンドの `implementation-{old_IMPL_INDEX}.md` に記載された正当な申告（PHANTOM ではなく実際に変更されたファイル）を再掲しない。
  一方 pre-set は据え置き（最初のラウンド開始前のスナップショット）のままなので、post-set / delta は **両ラウンドの変更を累積**して含む。結果、旧ラウンドで正当に申告・実施された変更が新ラウンドの CLAIMED には含まれず、`comm -23 delta claimed` で **UNDECLARED_CHANGE（warn）として誤って計上**される。UNDECLARED は非ブロッキングのため PASS/FAIL の判定自体を誤らせるものではないが、「同じ基準で再照合する」という設計意図（累積的な申告と実変更を正しく突き合わせる）に対して、実際の CLAIMED 集計ロジックが新ラウンド分のみに限定されており、記録上の不整合（誤解を招く warn ノイズ）を生む。
  → 修正案: 再実行後の CLAIMED 抽出は `implementation-${ORIGINAL_IMPL_INDEX}*.md` から `implementation-${new_IMPL_INDEX}*.md` までの**全ラウンドの和集合**を対象にする（グロブを `implementation-{0${IMPL_INDEX_original}..${IMPL_INDEX}}*.md` 相当に拡張する、または pre-set 同様に「今回の PHANTOM 検証セッションで使う IMPL_INDEX の配列」を保持して for ループで回す）。

### 良好点
- `comm` / `sed` の集合演算・範囲抽出ロジックそのものは正確で、`sort -u` による前処理も一貫している。ドッグフーディングで発見した「リポ外・gitignore 対象は検証不能」という着眼点自体は妥当で、hard fail を偽陽性から守る設計思想（非対称検証: PHANTOM のみ hard fail、UNDECLARED は warn）は一貫して実装されている。
- pir2codex 側の実集合定義変更（HEAD 基準 → pre-set 基準の unstaged+untracked）は plan.md に明示的なリスク開示があり、既存の `git diff --name-only HEAD` 記述が dead code として残っていないことも確認できた（置換漏れなし）。

### 次のアクション
implementer に以下を差し戻す:
1. `.claude/skills/pir2/references/deterministic-completion-check.md` のステップ 3b（71-84行目付近）の `case "$p" in /*) ... ;; esac` に tilde パス（`~/...`）も untrackable 判定されるよう修正する（`case` パターンへの `~*` 追加、または `$HOME` へのチルダ正規化を先に実施）。あわせて、同段落の説明文（23行目付近）が示す「絶対パス」という表現が tilde 記法の例と技術的に矛盾しないよう、「tilde 記法および `$PROJECT_ROOT` 配下でない絶対パス」等に文言も整合させる。
2. 失敗パス（145-151行目付近）の CLAIMED 再集計ロジックを、再実行後も**元の IMPL_INDEX から現在の IMPL_INDEX までの全ラウンドの申告を累積**する形に修正する（もしくは「新ラウンドの CLAIMED は前ラウンドの CLAIMED との和集合として扱う」旨を明記し、bash スニペットもそれに合わせて拡張する）。
両修正後、`bash -n` での構文チェックに加えて、上記の実機検証コマンド（tilde パスでの `case` マッチ結果、`git check-ignore` の挙動）を使い、修正後のロジックが tilde パスも正しく untrackable 判定することを確認すること。
