# 探索レポート: W1（6-3 決定論的完了検証）実装の最終状態・逐語収録

> 本レポートは deliberator が元ファイルを開かずに設計判断できるよう、対象ファイルの**現時点の実ファイル内容をそのまま**収録したものである。要約・言い換えは行っていない。各コードブロックは `Read` で取得した実データをそのまま転記している。
>
> 対象リポジトリ: `/Users/kawasetakumi/dotfiles`（git working tree、未コミット）。`git status --short` で該当ファイルはすべて `M`（変更）または `??`（新規）であることを確認済み:
>
> ```
>  M .claude/agents/implementer.md
>  M .claude/skills/pir2/SKILL.md
>  M .claude/skills/pir2/references/experimental.md
>  M .claude/skills/pir2/references/implementation-delegation.md
>  M .claude/skills/pir2/references/next-steps-queue.md
>  M .claude/skills/pir2/references/sanitized-cwd.md
>  M .claude/skills/pir2/references/verify-sanitized-cwd.sh
>  M .claude/skills/pir2codex/SKILL.md
> ?? .claude/skills/pir2/references/deterministic-completion-check.md
> ?? .claude/skills/pir2/references/verify-deterministic-check.sh
> ```
>
> （`.claude/agents/epic-planner.md` / `.claude/skills/epic/` / `.gitignore` / `CLAUDE.md` / `.claude/settings.json` / `.claude/skills/deepthink/SKILL.md` の変更は本タスク＝6-3 決定論的完了検証機能とは無関係な別セッションの残差分であり、本レポートの収録対象外とした）

---

## 1. `.claude/skills/pir2/references/deterministic-completion-check.md`（全文・280行）

```markdown
# 決定論的完了検証（共通プロトコル: pir2 6-3 / pir2codex 6-1）

PIR² 系スキルの実装完了検証。実装 actor（Claude implementer / Codex）の **自己申告した変更ファイル集合** と **実 git の変更集合** を純 bash で集合照合し、捏造（PHANTOM_CLAIM）と未申告変更（UNDECLARED_CHANGE）を決定論検出する機械ゲート。

- **/pir2**: ステップ「6-3: 決定論的完了検証」として、implementer 完了報告の直後・reviewer 起動（ステップ7）より前にスキル本体が実施する。
- **/pir2codex**: ステップ 6-1「wrapper 返り後のスキル本体の処理」の実体検証としてスキル本体が実施する（Codex は自己申告しうるため）。

CLAUDE.md「ツール結果の捏造の絶対禁止」の機構化。既存の shard/sequential 統合確認（`implementation-delegation.md`「shard 統合確認」「unit 統合確認」）は shard/unit 境界の LLM 層レビューだが、本ゲートはその **デフォルト actor（pir2 の implementer-subagent）および Codex actor（pir2codex）への一般化**であり、claim-vs-diff の集合一致という決定論層を担う。両者は別レイヤーで補完し合う（新規発明ではなく既存先例の一般化）。

> 🔧 機械検証: `bash ~/.claude/skills/pir2/references/verify-deterministic-check.sh`（本ファイル内の全 ```bash ブロックを抽出して構文検証し、mktemp -d の scratch git repo で PHANTOM / UNDECLARED / NO_OP / 非ASCIIファイル名 / フェンス内例示 / サブモジュールの6シナリオを実行して期待判定と一致するかを確認する。この bash を編集したら実行すること）

## 適用対象 actor

- **適用する（/pir2）**: `implementer-subagent` / `implementer-shards` / `implementer-sequential`（いずれもサブエージェントが `implementation-{IMPL_INDEX}*.md` に自己申告を書く＝telephone-game 境界がある）
- **適用する（/pir2codex）**: `codex-single` / `codex-shards` / `codex-sequential`（Codex が自己申告し、スキル本体が implementation-*.md に正規化 Write する）。pir2codex には `main` actor が存在しないため常時適用。
- **スキップする**: `/pir2` の `IMPLEMENTATION_ACTOR=main`（スキル本体が直接編集。自己申告境界が存在しないため照合対象がない）

## 適用タイミング

決定論的完了検証は **初回実装点（/pir2 6-1・/pir2codex 6-1a/6-1b/6-1c）のみ**に適用する（決定1=(A) の最小スコープ）。

- **/pir2 ステップ7-4（reviewer FAIL 後の再実装）**: 本ゲートを再適用しない。再実装完了後は直接 reviewer を再起動する（7-4 手順に 6-3 再適用の明記がないのは意図的な字義であり、記載漏れではない）。
- **/pir2codex ステップ6-2（Codex inner-loop 再実装）**: 同上。既存記述どおり本ゲートの対象外。
- **/pir2codex 6-1b（codex-shards）/ 6-1c（codex-sequential）**: 初回実装点に含まれるため適用する。全 shard/unit の完了・統合確認（delegation.md「shard 統合確認」「unit 統合確認」）の**後**に、全 shard/unit の申告（`implementation-{IMPL_INDEX}-*.md` または `implementation-{IMPL_INDEX}-unit-*.md` の和集合）を対象として本ゲートを **1 回だけ**実施する（shard/unit ごとに個別実施しない）。
- **本 run（W1 実装 run）で行った `verify-02` の適用**: 上記スコープが明文化される前に実施したドッグフーディングによる拡大適用であり、正式仕様の一部ではない。以後の inner-loop 再実装ではこの節に従い適用しない。

## 検証の情報源

- **申告集合 CLAIMED**: `{RUN_DIR}/implementation-{IMPL_INDEX}*.md` の `### 変更ファイル一覧` セクションの各 `` - `path` `` 行
  - subagent / codex-single: `implementation-{IMPL_INDEX}.md`
  - shards: `implementation-{IMPL_INDEX}-*.md`（全 shard の和集合）
  - sequential: `implementation-{IMPL_INDEX}-unit-*.md`（全 unit の和集合）
- **実集合**: 作業ツリーの dirty 集合 = `git diff --name-only --ignore-submodules=dirty`（unstaged 変更。サブモジュール work tree 内部の非コミット変更は無視するが、サブモジュールのコミットポインタ変更（pointer bump）は親リポ側で「サブモジュールパス 1 行」として検出される）＋ `git ls-files --others --exclude-standard`（untracked）。staged 集合は対象外（implementer / Codex はステージング操作をしない前提。設計 SSOT §1-3-2 準拠）。サブモジュール**内部のファイル単位**の申告（例: `mysub/inner.md`）は 3b の `check-ignore` が exit 128（`fatal: pathspec is in submodule`）を返すため git 追跡可能性を判定できず、検証不能（untrackable）扱いとなる（後述「git 検証不能な申告の扱い」を参照）。一方、サブモジュールのポインタ変更そのもの（例: `mysub`）は git 追跡可能な通常の申告として扱う。
- **git 検証不能な申告の扱い（重要・偽陽性防止）**: CLAIMED のうち **リポジトリ外**（`$PROJECT_ROOT` 配下でない絶対パス、または `~/...` のようなチルダ記法。例: `~/.claude/projects/.../memory/*` のメモリログ）または **gitignore 対象**（例: `.ai-pir-runs/` 配下の handoff.md 等）のパスは、実集合（git delta）に原理的に現れないため **PHANTOM 判定の対象外**とする（git で dirty かを検証できない＝「捏造」ではなく「検証不能」）。実装 actor はこれら bookkeeping ファイルを `### 変更ファイル一覧` に載せることがあり、載っていても hard fail にしてはならない。PHANTOM 照合は **git 追跡可能な申告集合（`claimed-trackable`）** に対してのみ行う。ただし「検証不能」を無条件の抜け穴にはしない。「git 検証不能な申告の実体確認」で `test -f` により実ファイルの存在を確認し、存在しない申告は warn として可視化する（後述）。

### Codex 報告の正規化（/pir2codex のみ）

Codex は「変更ファイル一覧」を **markdown 構造未指定の free-form** で報告する。スキル本体は implementation-*.md を Write する際、Codex 報告から各パスを抽出し以下で正規化して `` - `<リポ相対パス>` — <概要> `` 行として `### 変更ファイル一覧` に書き出す（これにより下記の抽出 bash が /pir2 と同一に機能する）:

- git status 風プレフィックス（`M ` / `A ` / `D ` / `?? ` / `R old -> new` 等）を除去する。rename（`R old -> new`）は **new path** を採用する。
- 先頭の箇条書き記号（`- ` / `* ` / `1. `）・囲みバッククォート・引用符を除去する。
- 絶対パスは `$PROJECT_ROOT/` を剥がしてリポ相対にする。
- 1 行 1 パス・重複除去する。概要が取れない場合は `— (Codex 報告より)` 等のプレースホルダで可（照合はパスのみ使う）。
- Codex が「編集不要（no-op）」と報告した場合は `### 変更ファイル一覧` を「なし」とし、`### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記する。

## pre-set 記録（実装 actor 起動の直前に実行）

実装 actor（implementer / Codex wrapper）を起動する **前** に、基準スナップショットを記録する（/pir2 の `IMPLEMENTATION_ACTOR=main` のときは記録しない。/pir2codex は常時記録）:

```bash
PRE_IMPL_INDEX="$IMPL_INDEX"   # pre-set 記録時点の IMPL_INDEX を固定保持。PHANTOM 再実行で IMPL_INDEX が
                                # インクリメントされても pre-set のファイル名はこの値を使い続ける
#    -c core.quotePath=false: 非 ASCII ファイル名を八進エスケープせず生 UTF-8 で出力させる
#    （デフォルトのままだと CLAIMED の生文字列と文字列一致せず PHANTOM 偽陽性になる）
#    --ignore-submodules=dirty: サブモジュール work tree 内部の非コミット変更は無視しつつ、
#    サブモジュールのコミットポインタ変更（pointer bump）は親リポの1行申告として残す
#    （--ignore-submodules=all だと pointer bump まで消えてしまい正当な申告が PHANTOM 化するため）
{ git -C "$PROJECT_ROOT" -c core.quotePath=false diff --name-only --ignore-submodules=dirty
  git -C "$PROJECT_ROOT" -c core.quotePath=false ls-files --others --exclude-standard
} | sort -u > "$RUN_DIR/verify-${PRE_IMPL_INDEX}-pre.list"
```

> 起動時点で既に dirty なファイルはここに含まれ、後段の delta から自然に除外される（この実装 actor 起動での変更だけを delta が表す）。`.ai-pir-runs/` は .gitignore 済みなので RUN_DIR 内の中間ファイルは untracked に混入しない。shard 並列 / unit 直列時も pre-set はこの1回（初回起動の直前）のみ記録する。`PRE_IMPL_INDEX` は「失敗パス」で `IMPL_INDEX` がインクリメントされた後も pre-set のファイル名参照にのみ使う変数で、post-set / delta / CLAIMED は常に現在の `IMPL_INDEX` で計算する（詳細は次節）。

## post-set 記録・delta 計算・CLAIMED 抽出（実装 actor 完了後）

```bash
# 0. pre-set 存在確認（6-1 での記録漏れを silent 劣化させない。fail-loud のみでワークフロー自体は
#    止めない。ERROR が出た場合の運用はこのコードブロック直後の blockquote を参照）
[ -f "$RUN_DIR/verify-${PRE_IMPL_INDEX}-pre.list" ] || echo "ERROR: pre-set 未記録（verify-${PRE_IMPL_INDEX}-pre.list なし）。delta/UNDECLARED が計算不能。6-1 の pre-set 記録手順に戻り、pre-set を再記録した上で実装 actor を再実行せよ（今から記録しても post と同一になり delta は空＝無意味）" >&2

# 1. post-set（完了後の dirty 集合。quotePath/ignore-submodules は pre-set と同じ理由）
{ git -C "$PROJECT_ROOT" -c core.quotePath=false diff --name-only --ignore-submodules=dirty
  git -C "$PROJECT_ROOT" -c core.quotePath=false ls-files --others --exclude-standard
} | sort -u > "$RUN_DIR/verify-${IMPL_INDEX}-post.list"

# 2. delta = post - pre（この実装 actor 起動で新たに dirty になったファイル）
#    pre.list は PRE_IMPL_INDEX（pre-set 記録時点で固定した値）を参照する。
#    PHANTOM 再実行で IMPL_INDEX がインクリメントされても pre-set は据え置きのため。
comm -13 "$RUN_DIR/verify-${PRE_IMPL_INDEX}-pre.list" \
        "$RUN_DIR/verify-${IMPL_INDEX}-post.list" \
  > "$RUN_DIR/verify-${IMPL_INDEX}-delta.list"

# 3. CLAIMED 抽出（現ラウンドの implementation レポートのみが対象。PHANTOM 再実行で申告を訂正
#    したら訂正後の申告のみで判定されるようにするため、前ラウンド分とは和集合にしない。
#    前ラウンドで正当に申告済みだった変更が今回のレポートで再宣言されず delta に残っていた場合、
#    UNDECLARED_CHANGE として warn に出うるが非ブロッキングのため許容する（失敗パスの再実行指示で
#    「訂正後の完全な変更ファイル一覧を再宣言する」ことを求めているため通常は発生しない）。
#    「### 変更ファイル一覧」見出し → 次の `##`/`###` 見出し or EOF までを対象にし、コードフェンス
#    （```）内の行（テンプレート例示・引用）は事前に除去してから抽出する。
#    既知の限界（現実性は極めて低く、方向も fail-closed=偽 PHANTOM 側で安全）: フェンス除去は
#    「行頭 ``` （3個以上）でトグル」の単純な状態機械のため、4バッククォート等で外側フェンスの
#    内部に3バッククォートの ``` を含む「入れ子フェンス例示」があると、内部の ``` で誤ってトグルが
#    反転し、以降の内容が「フェンス外」と誤認されて decoy パスが CLAIMED に混入し得る。「### 変更
#    ファイル一覧」セクション内にそのような入れ子フェンス例示がある場合のみ発生し、混入した decoy
#    は git delta に無いため PHANTOM 誤検知（偽陽性・fail-closed）に倒れる。同型の限界は NO_OP 判定
#    （後述）のフェンス除去にも適用される。
for f in "$RUN_DIR"/implementation-${IMPL_INDEX}*.md; do
  [ -f "$f" ] || continue
  awk '/^```/{c=!c;next} !c' "$f" \
    | awk '/^### 変更ファイル一覧/{f=1;next} (/^## /||/^### /){if(f)exit} f' \
    | grep -E '^- *`'
done \
  | sed -E 's/^- *`([^`]+)`.*/\1/' \
  | sed -E "s|^$PROJECT_ROOT/||" \
  | sort -u > "$RUN_DIR/verify-${IMPL_INDEX}-claimed.list"

# 3b. CLAIMED を git 検証可能な集合に絞る（リポ外の絶対パス・チルダ記法・gitignore 対象・
#     サブモジュール内パスは git delta に現れないため PHANTOM 対象外＝「検証不能」であって
#     「捏造」ではない）。check-ignore の終了コードを3分岐で判定する:
#       exit 0            = gitignore 対象                              → untrackable
#       exit 1            = 非 ignore（通常の git 追跡対象）             → trackable
#       exit 128 等(fatal) = 検証不能（例: サブモジュール内パス）        → untrackable
: > "$RUN_DIR/verify-${IMPL_INDEX}-claimed-trackable.list"
: > "$RUN_DIR/verify-${IMPL_INDEX}-claimed-untrackable.list"
while IFS= read -r p; do
  [ -z "$p" ] && continue
  case "$p" in
    /*|"~"*) echo "$p" >> "$RUN_DIR/verify-${IMPL_INDEX}-claimed-untrackable.list"; continue ;;  # リポ相対化されず残った（絶対パス or `~`/`~user` 等チルダ記法）＝リポ外
  esac
  if git -C "$PROJECT_ROOT" check-ignore -q -- "$p" 2>/dev/null; then
    rc=0
  else
    rc=$?
  fi
  case "$rc" in
    0) echo "$p" >> "$RUN_DIR/verify-${IMPL_INDEX}-claimed-untrackable.list" ;;   # gitignore 対象
    1) echo "$p" >> "$RUN_DIR/verify-${IMPL_INDEX}-claimed-trackable.list" ;;     # 非 ignore（通常の git 追跡対象）
    *) echo "$p" >> "$RUN_DIR/verify-${IMPL_INDEX}-claimed-untrackable.list" ;;   # 検証不能（サブモジュール内パス等。fatal exit）
  esac
done < "$RUN_DIR/verify-${IMPL_INDEX}-claimed.list"
sort -u -o "$RUN_DIR/verify-${IMPL_INDEX}-claimed-trackable.list" "$RUN_DIR/verify-${IMPL_INDEX}-claimed-trackable.list"
sort -u -o "$RUN_DIR/verify-${IMPL_INDEX}-claimed-untrackable.list" "$RUN_DIR/verify-${IMPL_INDEX}-claimed-untrackable.list"

# 3c. git 検証不能な申告の実体確認（silent な抜け穴にしない）:
#     untrackable と分類された申告についても、実ファイルが存在するかどうかは test -f で確認できる。
#     存在しない場合は「検証不能かつ実体なし」として warn 記録する（git で dirty 判定できないため
#     PHANTOM の hard fail 対象にはしない。あくまで人間が気づけるようにする可視化）。
#     残存限界: 実在する gitignore 対象/リポ外ファイルへの虚偽申告（実体は在るが今回の実装では
#     変更していない）は test -f を通過し検出できない。これは設計 SSOT（docs/deepthink/
#     20260703-190750-Fable5.md 残存限界④⑥＝fail-open な事故計器であり攻撃防御ではない）と
#     同型で受容する既知の限界。
: > "$RUN_DIR/verify-${IMPL_INDEX}-claimed-untrackable-missing.list"
while IFS= read -r p; do
  [ -z "$p" ] && continue
  case "$p" in
    "~") expanded="$HOME" ;;
    "~"/*) expanded="${HOME}/${p#\~/}" ;;
    /*) expanded="$p" ;;
    "~"*) expanded="$p" ;;                # ~user 等は展開せずそのまま（存在しなければ missing warn）
    *) expanded="$PROJECT_ROOT/$p" ;;    # リポ相対（gitignore 対象）パスは PROJECT_ROOT にアンカー（shell cwd 非依存）
  esac
  [ -f "$expanded" ] || echo "$p" >> "$RUN_DIR/verify-${IMPL_INDEX}-claimed-untrackable-missing.list"
done < "$RUN_DIR/verify-${IMPL_INDEX}-claimed-untrackable.list"

# 4. PHANTOM 候補 = claimed-trackable に在るが post に無い（git 追跡可能なのに申告通り dirty でない＝捏造）
comm -23 "$RUN_DIR/verify-${IMPL_INDEX}-claimed-trackable.list" \
        "$RUN_DIR/verify-${IMPL_INDEX}-post.list" \
  > "$RUN_DIR/verify-${IMPL_INDEX}-phantom.list"

# 5. UNDECLARED 候補 = delta に在るが claimed に無い（実際に変わったが申告に無い）
#    delta は全て in-repo・非 ignore なので比較相手は full claimed でよい
comm -23 "$RUN_DIR/verify-${IMPL_INDEX}-delta.list" \
        "$RUN_DIR/verify-${IMPL_INDEX}-claimed.list" \
  > "$RUN_DIR/verify-${IMPL_INDEX}-undeclared.list"
```

> ⚠️ 上記手順0の ERROR（pre-set 未記録）が出力された場合、スキル本体は delta/UNDECLARED 判定を実行不能と扱い、6-1 の pre-set 記録手順に戻ってやり直す（＝pre-set を再記録した上で実装 actor を再実行する。今から pre.list を記録しても post と同一になり delta は空＝無意味なため）。PHANTOM 照合のみでの縮退運転はしない。

## 集合照合規則（判定）

| 条件 | 判定 | 扱い |
|---|---|---|
| `phantom.list` が非空（**git 追跡可能なのに**申告通り dirty でないファイルがある） | **PHANTOM_CLAIM** | hard fail |
| `claimed-trackable.list` が空 かつ `delta.list` が空 かつ NO_OP 免除なし（編集想定タスクなのに git 追跡可能な申告も実変更も無い） | **PHANTOM_CLAIM** | hard fail |
| `undeclared.list` が非空（申告外の dirty） | **UNDECLARED_CHANGE** | warn（非ブロッキング） |
| `claimed.list` が空 かつ `delta.list` が非空 | **UNDECLARED_CHANGE** | warn（非ブロッキング） |
| 上記いずれも該当せず | **PASS** | reviewer（/pir2 ステップ7）/ 後続処理へ進む |

> ℹ️ PHANTOM 判定行だけ `claimed-trackable.list`（3b でフィルタ後）を使い、UNDECLARED_CHANGE 判定行は（フィルタ前の）`claimed.list` を使う。これは非対称ではなく必然: delta（実 git 変更）はそもそも in-repo かつ非 ignore のファイルしか含み得ないため、UNDECLARED 側の比較相手はフィルタ不要（`claimed` でも `claimed-trackable` でも delta との差分結果は同一）。一方 PHANTOM 側は「git 検証不能な申告」を誤って捏造と判定しないためフィルタが必須。
- PHANTOM_CLAIM と UNDECLARED_CHANGE は同時に成立しうる（PHANTOM が優先＝hard fail）。
- UNDECLARED は formatter・lockfile・コード生成物の副産物で正常に発生しうるため warn 止まり。hard fail は PHANTOM のみ（偽陽性で実験を殺さない非対称検証）。

### NO_OP 免除

`claimed-trackable.list` が空 かつ `delta.list` が空のとき（git 追跡可能な申告も実変更も無い）、以下で免除判定する:

```bash
# コードフェンス除去 → 「### 注意点・未解決事項」セクションに限定 → 行頭アンカーでのみ判定
# （本文プローズ中の言及・フェンス内引用だけで免除が誤発動しないようにするため）。
# 番号リスト（`4. NO_OP_JUSTIFIED: 該当なし` 等、非 NO_OP 時の慣習的な言及）はあえて対象外とする。
# 番号リストまで許容すると「該当なし」という否定の申告文まで宣言と誤認しかねないため、
# implementer.md が規定する `NO_OP_JUSTIFIED: <理由>` の素の記法（箇条書き `-` の有無のみ許容）に絞る。
NO_OP_JUSTIFIED=0
for f in "$RUN_DIR"/implementation-${IMPL_INDEX}*.md; do
  [ -f "$f" ] || continue
  if awk '/^```/{c=!c;next} !c' "$f" \
      | awk '/^### 注意点・未解決事項/{f=1;next} (/^## /||/^### /){if(f)exit} f' \
      | grep -qE '^[[:space:]]*(-[[:space:]]*)?`?NO_OP_JUSTIFIED:`?'; then
    NO_OP_JUSTIFIED=1   # 実装 actor が「編集不要」を明示宣言 → PHANTOM 免除・PASS 扱い
    break
  fi
done
# NO_OP_JUSTIFIED=0 のまま → 宣言なし → PHANTOM_CLAIM（hard fail）
```

- /pir2: implementer は編集不要と判断した場合、実装完了レポートの `### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記する（`~/.claude/agents/implementer.md`「実装完了レポートのフォーマット」参照）。
- /pir2codex: Codex が「編集不要」と報告した場合、スキル本体が implementation-*.md の `### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記する（上記「Codex 報告の正規化」）。

## 判定結果の書き出し

判定結果を `{RUN_DIR}/verify-{IMPL_INDEX}.md` に書き出す:

```markdown
# 決定論的完了検証（IMPL_INDEX=NN）

- PRE_IMPL_INDEX: <NN>（pre-set 基準スナップショット）
- CLAIMED 情報源: <implementation-{IMPL_INDEX}*.md>（現ラウンドの実装レポートのみ。前ラウンド分とは和集合にしない）
- PHANTOM_RETRY_COUNT: <N>
- actor: <implementer-subagent / implementer-shards / implementer-sequential / codex-single / codex-shards / codex-sequential>
- CLAIMED（git 追跡可能）: <claimed-trackable.list の件数> 件（検証不能で除外: <claimed-untrackable.list の件数> 件、うち実体なし: <claimed-untrackable-missing.list の件数> 件）
- delta（実変更）: <delta.list の件数> 件
- 判定: <PASS / PHANTOM_CLAIM / UNDECLARED_CHANGE（warn）>

## PHANTOM（申告したが実体なし）
<phantom.list の内容 or "なし">

## UNDECLARED（実変更だが申告なし）
<undeclared.list の内容 or "なし">

## 検証不能として除外（PHANTOM 対象外）
<claimed-untrackable.list の内容 or "なし">
- うち実体を確認できず（`claimed-untrackable-missing.list`。warn・hard fail にはしない）: <claimed-untrackable-missing.list の内容 or "なし">
```

## 失敗パス（PHANTOM_CLAIM 検出時）

1. `PHANTOM_RETRY_COUNT` を確認する。
2. **1 回目の PHANTOM（`PHANTOM_RETRY_COUNT == 0`）**: `IMPL_INDEX` と `PHANTOM_RETRY_COUNT` をインクリメントし、実装 actor を **1 回だけ**再実行する。`PRE_IMPL_INDEX` は変更しない（据え置き）。再実行プロンプトに `{RUN_DIR}/verify-{直前 IMPL_INDEX}.md`（検証レポート）のパス／全文を渡し、「申告したが実際には変更されていない以下のファイルを実際に編集せよ、または申告を実体に一致させよ。**再実行後のレポートの `### 変更ファイル一覧` には、前ラウンド分も含めた訂正後の完全な変更ファイル一覧を再宣言すること**（CLAIMED は現ラウンドのレポートのみを情報源にするため）」と**原因を逐語注入**する（ブラインドリトライではない＝原因が特定済み）。
   - /pir2: implementer サブエージェントを再起動。
   - /pir2codex: Codex を `codex-reply`（同 threadId で実装文脈を保つ）または新 Codex セッションで再実行。
   - 再起動後、pre-set は `verify-${PRE_IMPL_INDEX}-pre.list`（初回起動時点のスナップショット）を据え置きで参照し続け、post-set / delta は新しい `IMPL_INDEX` で再計算する。CLAIMED は「post-set記録・delta計算・CLAIMED 抽出」節のとおり**現ラウンド（新しい `IMPL_INDEX`）の implementation レポートのみ**を情報源にする（前ラウンドの申告とは和集合にしない。申告を訂正すればその訂正が判定に反映されるようにするため）。前ラウンドで正当だった申告が再宣言されず delta に残っていた場合 UNDECLARED_CHANGE の warn（非ブロッキング）に出うるが、上記の「完全な一覧を再宣言」指示により通常は発生しない。`INNER_LOOP_COUNT` は増やさない（reviewer FAIL ループとは別系統）。
3. **2 回目も PHANTOM（`PHANTOM_RETRY_COUNT >= 1`）**: **reviewer を起動せず**、以下のユーザーゲートを開く（捏造の上にレビューを積まない）。CLAUDE.md「ブラインドリトライ禁止」（初回＋再試行1回＝計2回で停止）と整合。

### ユーザーゲート（2 回目 PHANTOM 時）

```
## 決定論的完了検証 FAIL — PHANTOM_CLAIM（再実行1回後も未解消）

実装（implementer / Codex）が変更したと申告したが、実際の git 作業ツリーに反映されていないファイルを検出しました。

- 申告集合（CLAIMED、git 追跡可能）: <claimed-trackable.list>
- 実変更集合（delta）: <delta.list>
- 申告のみで実体なし（PHANTOM）: <phantom.list>
- 検証不能として除外（PHANTOM 対象外）: <claimed-untrackable.list>（うち実体を確認できず: <claimed-untrackable-missing.list>）

以下の実 git 変更を参考にしてください（自動巻き戻しは行いません）:
<git -C "$PROJECT_ROOT" diff の要約（--stat）>

続行方法を選んでください:
- (A) 手動調査してから再開: git diff を確認し原因を特定。追加指示付きで実装 actor を再起動（IMPL_INDEX++）するか手動修正 → 検証を再実行【推奨】
- (B) PHANTOM を承知でそのまま reviewer へ進む（申告漏れ/検証の偽陽性とユーザーが判断した場合のみ）
- (C) ワークフローを中止

[A / B / C]
```

- **補償は `git diff` 全 hunk のユーザー提示のみ。`git restore` / `git checkout -- <file>` による自動巻き戻しは絶対にしない**（CLAUDE.md Git ルール）。PHANTOM は「申告ファイルが dirty でない」状態なので巻き戻す対象自体がなく、提示するのは実際に dirty な変更の実体。
- **Auto mode でも本ゲートはユーザー応答を待つ**（仕様変更判断ゲートのため Auto mode 例外）。
- ゲート発火と選択は `{RUN_DIR}/user-decisions.md` に追記する。

## スキップ条件

- /pir2 の `IMPLEMENTATION_ACTOR=main` のときは本ステップ全体をスキップ（pre-set 記録・照合ともに不要）。next-steps.md の「ステップ 6-3」checkbox は「main のためスキップ」と付記して `[x]` にする。
- /pir2codex はスキップ条件なし（全 actor が Codex 経由で自己申告境界を持つため常時適用）。

## 完了後

/pir2 では ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の「ステップ 6-3」checkbox を `[x]` に更新する。PHANTOM 再実行で `IMPL_INDEX` が増えた場合も最初の 1 回のみマークし、詳細は「中断・再開ログ」に追記する。/pir2codex では 6-1 完了後の checkbox 更新に含める。
```

---

## 2. `.claude/skills/pir2/SKILL.md` の 6-3 関連部分

### ステップ6 冒頭のカウンタ初期化行（579行中の抜粋）

```markdown
## ステップ 6: 実装（implementer）

`INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0`、`PHANTOM_RETRY_COUNT = 0` から開始してください。
```

### 6-1 の pre-set 記録指示（implementer 起動前）

```markdown
### 6-1: implementer 起動

#### implementer 起動前の pre-set 記録（決定論的完了検証 6-3 用・必須）

`IMPLEMENTATION_ACTOR` が `main` 以外のとき、implementer を起動する **前** に、決定論的完了検証（共通プロトコル `~/.claude/skills/pir2/references/deterministic-completion-check.md`「pre-set 記録」）の基準スナップショットとして作業ツリーの dirty 集合を記録する。`main` 実装時は 6-3 自体を適用しないため記録も不要。shard/sequential 時も pre-set はこの1回（並列/直列起動の直前）のみ記録する。
```

### 新ステップ「6-3」節の全文

```markdown
### 6-3: 決定論的完了検証（`IMPLEMENTATION_ACTOR` が `main` 以外のとき必須）

詳細プロトコル: `~/.claude/skills/pir2/references/deterministic-completion-check.md` を参照（適用対象 actor / pre-set・post-set 記録 bash / 集合照合規則 PHANTOM_CLAIM・UNDECLARED_CHANGE・NO_OP 免除 / 判定結果書き出し / 失敗パスのユーザーゲート）。本 reference は pir2 6-3 と pir2codex 6-1 の共通プロトコル。

要点: implementer 完了報告（および 6-2 統合確認）の直後、reviewer 起動（ステップ7）より前に、`implementation-{IMPL_INDEX}*.md` の `### 変更ファイル一覧` から抽出した申告集合 CLAIMED と、6-1 で記録した pre-set からの git delta を純 bash で集合照合する。**PHANTOM_CLAIM（申告したが実際は dirty でないファイルがある／編集想定タスクなのに申告も変更も空で `NO_OP_JUSTIFIED` 宣言なし）は hard fail**。検出時は検証レポート `{RUN_DIR}/verify-{IMPL_INDEX}.md` を逐語注入して implementer を **1 回だけ**再実行（`IMPL_INDEX` と `PHANTOM_RETRY_COUNT` をインクリメント）し再検証する。**2 回目も PHANTOM なら reviewer を起動せずユーザーゲート**（捏造の上にレビューを積まない）。UNDECLARED_CHANGE（申告外の dirty。formatter/生成物副作用等）は warn として `{RUN_DIR}/verify-{IMPL_INDEX}.md` に記録し報告に含めるが**非ブロッキング**。`IMPLEMENTATION_ACTOR=main` は自己申告境界が存在しないため本ステップをスキップする。

> ℹ️ 6-3 は resume 時の追跡粒度を上げるため next-steps.md 上で「ステップ6」とは独立した checkbox を持つ（既存の「hyphen 番号は親ステップと checkbox を共有する」という慣習からの意図的な例外）。

### 完了後

ステップ 5.6-2 に従い `{RUN_DIR}/next-steps.md` の該当 checkbox（「ステップ6」「ステップ6-3」双方）を `[x]` に更新する（`IMPL_INDEX` が複数回ループする場合は最初の 1 回のみマーク。PHANTOM 再実行で `IMPL_INDEX` が増えた場合も同様。2 回目以降のループは「中断・再開ログ」セクションに追記する）。`main` で 6-3 をスキップした場合は「ステップ6-3」チェックボックスを「main のためスキップ」と付記して `[x]` にする。
```

### ステップ12「決定論的完了検証」結果ブロック（最終サマリーテンプレート内）

```markdown
### 決定論的完了検証（6-3）
- PHANTOM_CLAIM: [検出なし / 検出→再実行1回で解消 / 検出→再失敗でユーザーエスカレーション / main のためスキップ]
- UNDECLARED_CHANGE: [なし / N 件（非ブロッキング・{RUN_DIR}/verify-*.md に記録）]
- PHANTOM_RETRY_COUNT: [回数]
```

（このブロックはステップ12「最終サマリーの提示」テンプレート全体の中の一節。前後には「レビュー結果」「リファクタ提案（refactor-advisor）」ブロックが続く）

---

## 3. `.claude/skills/pir2codex/SKILL.md` の変更部分

### ステップ6 冒頭のカウンタ初期化行

```markdown
## ステップ 6: 実装（Codex）★ pir2codex の差分本体

`INNER_LOOP_COUNT = 0`、`OUTER_LOOP_COUNT = 0`、`PHANTOM_RETRY_COUNT = 0` から開始してください。

ここが通常 /pir2 との唯一の実質差分です。implementer サブエージェント（Claude）の代わりに **Codex セッション（`mcp__codex__codex`）が実装**します。
```

### 6-1「wrapper 起動前の pre-set 記録」

```markdown
#### wrapper 起動前の pre-set 記録（決定論的完了検証 6-3 用・必須）

Codex wrapper（6-1a/6-1b/6-1c いずれか）を起動する **前** に、決定論的完了検証（共通プロトコル `~/.claude/skills/pir2/references/deterministic-completion-check.md`「pre-set 記録」）の基準スナップショットを記録する。codex-shards の並列起動時・codex-sequential の直列起動時も、pre-set はこの1回（初回起動の直前）のみ記録する。pir2codex には `main` actor が存在しない（全て Codex）ため本記録は常時実行する。
```

### 6-1「wrapper 返り後のスキル本体の処理（共通・順序厳守）」全文（6-3 検証と report Write の順序が分かる形）

```markdown
#### wrapper 返り後のスキル本体の処理（共通・順序厳守）

決定論的完了検証（6-3）は `implementation-{IMPL_INDEX}*.md` の `### 変更ファイル一覧` を情報源とするため、**その報告ファイルを Write してから検証する**順序でなければならない（先に検証すると CLAIMED が常に空になり誤判定する）。

1. **implementation レポートを Write**: `{RUN_DIR}/implementation-{IMPL_INDEX}.md`（shard 時 `-{SHARD_ID}`、unit 時 `-unit-{UNIT_ID}`）に、Codex の変更ファイル一覧＋実装概要＋注意点を `~/.claude/agents/implementer.md`「実装完了レポートのフォーマット」に合わせて書き出す。**Codex の変更ファイル報告（markdown 構造未指定）は、`deterministic-completion-check.md`「Codex 報告の正規化」に従って `### 変更ファイル一覧` の `` - `<リポ相対パス>` — <概要> `` 行に整形して書く**（6-3 の抽出 bash が pir2 と同一に機能するため）。Codex が「編集不要」と報告した場合は `### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記する（6-3 の NO_OP 免除）。
2. **決定論的完了検証（6-3・必須）**: 手順1で Write した implementation レポートを情報源に、共通プロトコル `~/.claude/skills/pir2/references/deterministic-completion-check.md` に従い、Codex の申告変更ファイル集合（CLAIMED）と 6-1 pre-set からの実 git delta（unstaged + untracked）を集合照合し、PHANTOM_CLAIM（hard fail）/ UNDECLARED_CHANGE（warn）を判定する。Codex の自己申告を信じない（CLAUDE.md「ツール結果の捏造の絶対禁止」と同根。Codex も自己申告しうる）。PHANTOM 検出時の再実行1回→再失敗ユーザーゲートも同 reference の「失敗パス」に従う（再実行は Codex codex-reply または新セッション）。プラン外への波及（プラン範囲逸脱）の意味的判断は決定論層の対象外で、後段 reviewer（ステップ7）が拾う。
3. **threadId を保持**（inner-loop の `codex-reply` 継続用）
```

> ℹ️ 上記手順の順序が「1. Write → 2. 検証」であることが本節の核。もし逆にすると CLAIMED が常に空になり NO_OP 免除の分岐（申告なし＝ PHANTOM_CLAIM）に誤って落ちる、という注意書きが手順の直前段落に明記されている。

### 6-1a/6-1b/6-1c への適用記述

```markdown
### 6-1a: codex-single（デフォルト）

wrapper を **1 体**起動 → implementation-{IMPL_INDEX}.md を Write → 決定論的完了検証（6-3） → threadId 保持。

### 6-1b: codex-shards（plan に `IMPLEMENTATION_SHARDS`・独立ゲート通過時）

delegation.md「shard 許可条件」を全て満たした各 shard を、**別々の wrapper Agent として同一メッセージ内に並列起動**（各 wrapper が独立した Codex セッション）。各 Codex プロンプトに当該 shard の許可/禁止ファイルを明記し「許可集合の外を編集するな」と指示。各 wrapper は「wrapper 返り後のスキル本体の処理」手順1に従い `implementation-{IMPL_INDEX}-{SHARD_ID}.md` を Write する。全 shard 完了後、スキル本体が delegation.md「shard 統合確認」（全 `implementation-{IMPL_INDEX}-*.md` を Read + git diff で競合・命名不整合・未接続を確認）を実施し、その**後**に決定論的完了検証（6-3。全 shard の申告 = `implementation-{IMPL_INDEX}-*.md` の和集合を対象に 1 回だけ実施。詳細は `~/.claude/skills/pir2/references/deterministic-completion-check.md`「適用タイミング」節）を行う。問題があれば codex-single に戻して統合修正。

### 6-1c: codex-sequential（plan に `IMPLEMENTATION_UNITS`・unit ゲート通過時）

delegation.md「unit 許可条件」を満たした unit を `UNIT_ID` 昇順に **1 体ずつ直列**に wrapper 起動（先行 unit の完了を待ってから次を起動）。各 unit:

- **新しい Codex セッション（新 threadId）= コンテキストまっさら**
- スキル本体が**先行 unit の `git diff` と `implementation-{IMPL_INDEX}-unit-*.md` を Read し、当該 unit の wrapper プロンプトに埋め込む**（Codex 実装プロンプトの「先行 unit の成果」欄）。「先行 unit の命名・抽象・データ形状に従え」を明記
- Codex は当該 unit の範囲のみ実装

全 unit 完了後、スキル本体が delegation.md「unit 統合確認」（全 `implementation-{IMPL_INDEX}-unit-*.md` を Read + git diff で unit 境界の命名不整合・重複抽象・未接続を確認）を実施し、その**後**に決定論的完了検証（6-3。全 unit の申告 = `implementation-{IMPL_INDEX}-unit-*.md` の和集合を対象に 1 回だけ実施。詳細は `~/.claude/skills/pir2/references/deterministic-completion-check.md`「適用タイミング」節）を行う。問題があれば codex-single に戻して統合修正。

> ℹ️ v1 では codex-sequential / codex-shards は**初回実装のみ**。reviewer/tester FAIL 後の再実装は統合済み diff に対し codex-single で行う（6-2）。
```

### 6-2「inner-loop の再実装」で 6-3 が対象外であることの明記

```markdown
### 6-2: inner-loop の再実装（reviewer FAIL 後）

- **codex-single**: `mcp__codex__codex-reply({ threadId, prompt: <FAIL を返した全 review-*.md の全文> })` で**同スレッド継続**（Codex が実装文脈を保ったまま修正）。wrapper Agent 経由で呼び、返り後に implementation-{新 IMPL_INDEX}.md を Write → `git diff` による軽量自己チェック（決定論的完了検証 6-3 は初回実装点（6-1）のみ適用するスコープのため、ここでは対象外。適用スコープの整理は `~/.claude/skills/pir2/references/deterministic-completion-check.md`「適用タイミング」節を参照）
- **codex-shards / codex-sequential の初回後**: 統合済み diff に対し codex-single（新規 Codex セッション or 直近 threadId への reply）で修正する
```

### ステップ12「決定論的完了検証」結果ブロック（最終サマリーテンプレート内）

```markdown
### 決定論的完了検証（6-3）
- PHANTOM_CLAIM: [検出なし / 検出→再実行1回で解消 / 検出→再失敗でユーザーエスカレーション]
- UNDECLARED_CHANGE: [なし / N 件（非ブロッキング・{RUN_DIR}/verify-*.md に記録）]
- PHANTOM_RETRY_COUNT: [回数]
```

（pir2 版と異なり「main のためスキップ」の選択肢が無い。理由: pir2codex は「pir2codex に `main` actor が存在しない」ため常時適用であり、スキップ分岐自体が存在しない）

---

## 4. `.claude/agents/implementer.md` の NO_OP_JUSTIFIED マーカー段落

「実装完了レポートのフォーマット」節の直後（107行目）にある段落全文:

```markdown
> **無編集完了（no-op）時**: プラン内容が既に満たされている等でコード変更が一切不要と判断した場合は、`### 変更ファイル一覧` を「なし」とし、`### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記すること。これはスキル本体の決定論的完了検証（pir2 ステップ 6-3 / `~/.claude/skills/pir2/references/deterministic-completion-check.md`）が「申告も変更も空」を捏造（PHANTOM_CLAIM）と誤判定しないための免除マーカー。理由なく変更ゼロで完了報告してはならない。
```

この段落が参照している直前の「実装完了レポートのフォーマット」（比較用に併記）:

```markdown
## 実装完了レポートのフォーマット

\`\`\`
## 実装完了レポート

### 変更ファイル一覧
- `path/to/file1` — [変更内容の概要]
- `path/to/file2` — [変更内容の概要]
- `path/to/file1_test` — [テスト内容の概要]

### 実装概要
[何を実装したか1〜3文で]

### 注意点・未解決事項
[レビュワーに伝えるべきこと（なければ「なし」）]
\`\`\`
```

---

## 5. `.claude/skills/pir2/references/verify-deterministic-check.sh`（全文・386行）

```bash
#!/usr/bin/env bash
# verify-deterministic-check.sh
#
# deterministic-completion-check.md（決定論的完了検証の共通プロトコル。pir2 6-3 /
# pir2codex 6-1）に埋め込まれた ```bash フェンスブロックを機械検証する。
# 位置づけは `verify-sanitized-cwd.sh` と同型（SSOT の bash が壊れていないかを
# 機械検出し、pre-commit / CI /手動実行に組み込める形にする）。
#
# --- 落とし穴（設計メモ・必読） -------------------------------------------------
# reference の bash には、md 自身の中で fenced code block を扱うための
#   awk '/^```/{c=!c;next} !c'
# のような行が含まれ、この行自体に **リテラルの ``` が埋め込まれている**（フェンス
# 判定用の正規表現の一部として）。ナイーブに「``` を含む行ならフェンス境界」とみなす
# 抽出（grep '```' や、行内のどこかに ``` があれば良いとする awk）をすると、この
# 埋め込み行を誤って閉じフェンスと誤認し、ブロックが途中で切れる false NG になる
# （実際に呼び出し元のアドホック検証がこれで壊れた実績あり）。
#
# 本スクリプトは commonmark のフェンス仕様に倣い、「行を trim（前後の空白除去）した
# 結果が完全に ```bash / ``` と一致する行のみ」をフェンス境界とみなす。埋め込み ```
# は行の前後に他の文字がある（`awk '/^` や `#    （` 等）ため trim 一致にならず、
# 正しくフェンス境界として無視される。
#
# --- 使い方 ---------------------------------------------------------------------
#   bash ~/.claude/skills/pir2/references/verify-deterministic-check.sh
#   bash ~/.claude/skills/pir2/references/verify-deterministic-check.sh --syntax-only
#
# デフォルトは (1) 全 ```bash ブロックの `bash -n` 構文チェック、(2) mktemp -d の
# scratch git repo での E2E フィクスチャ（PHANTOM / UNDECLARED / NO_OP / 非ASCII
# ファイル名 / フェンス内例示 / サブモジュール の 6 シナリオ）の両方を実行する。
# `--syntax-only` を付けると (2) をスキップし構文チェックのみ行う（軽量・高速）。
#
# フィクスチャは reference のブロック構成（```bash が正確に3個・pre-set / post-set
# 系・NO_OP 判定の順）に依存する。reference を大改編してブロック数・順序が変わった
# 場合は本スクリプトのフィクスチャ部分も追従修正が必要（verify-sanitized-cwd.sh も
# 同種の前提脆弱性を抱えており、同じ流儀）。
#
# 後始末: mktemp -d で作った作業ディレクトリは `trap ... EXIT` で削除する。
# `rm -rf` は使わず `find -delete` を使う（破壊的操作の誤爆防止）。
#
# 揺れ・構文エラー・フィクスチャ不一致を検出した場合は exit 1 を返す。

set -euo pipefail

REFERENCE_MD="${HOME}/.claude/skills/pir2/references/deterministic-completion-check.md"

RUN_FIXTURES=1
if [[ "${1:-}" == "--syntax-only" ]]; then
  RUN_FIXTURES=0
fi

if [[ ! -f "$REFERENCE_MD" ]]; then
  echo "NG: reference file not found: $REFERENCE_MD"
  exit 1
fi

WORK_DIR="$(mktemp -d)"
# shellcheck disable=SC2329  # trap 経由（EXIT）で呼ばれるため静的解析からは未使用に見える
cleanup() {
  if [[ -n "${WORK_DIR:-}" && -d "$WORK_DIR" ]]; then
    find "$WORK_DIR" -mindepth 1 -delete 2>/dev/null || true
    rmdir "$WORK_DIR" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# --- 1. ```bash ブロックの境界（開始行・終了行）を抽出 --------------------------
# trim した行が完全に ```bash / ``` と一致する行のみをフェンス境界とみなす。
BLOCK_RANGES=()
while IFS= read -r range; do
  [ -z "$range" ] && continue
  BLOCK_RANGES+=("$range")
done < <(awk '
  {
    line = $0
    trimmed = line
    gsub(/^[ \t]+|[ \t]+$/, "", trimmed)
    if (!in_block) {
      if (trimmed == "```bash") { start = NR; in_block = 1 }
    } else {
      if (trimmed == "```") { print start" "NR; in_block = 0 }
    }
  }
' "$REFERENCE_MD")

if (( ${#BLOCK_RANGES[@]} == 0 )); then
  echo "NG: no \`\`\`bash blocks found in $REFERENCE_MD（抽出ロジックが壊れているか、reference の構造が変わった可能性）"
  exit 1
fi

echo "found ${#BLOCK_RANGES[@]} \`\`\`bash block(s) in $REFERENCE_MD"

SYNTAX_FAILURES=0
i=0
for range in "${BLOCK_RANGES[@]}"; do
  i=$((i + 1))
  start="${range% *}"
  end="${range#* }"
  block_file="$WORK_DIR/block-${i}.sh"
  sed -n "$((start + 1)),$((end - 1))p" "$REFERENCE_MD" > "$block_file"
  if ! bash -n "$block_file" 2>"$WORK_DIR/block-${i}.err"; then
    SYNTAX_FAILURES=$((SYNTAX_FAILURES + 1))
    echo "NG: block $i (lines $((start + 1))-$((end - 1))) failed bash -n:"
    sed 's/^/  /' "$WORK_DIR/block-${i}.err"
  fi
done

if (( SYNTAX_FAILURES > 0 )); then
  echo "NG: ${SYNTAX_FAILURES} block(s) failed syntax check"
  exit 1
fi

echo "OK: ${#BLOCK_RANGES[@]} bash blocks syntax-valid"

if (( RUN_FIXTURES == 0 )); then
  exit 0
fi

# --- 2. フィクスチャ（scratch git repo での E2E 検証） ---------------------------
# reference は現在 ```bash ブロックを 3 個持つ想定:
#   block-1 = pre-set 記録
#   block-2 = post-set 記録・delta 計算・CLAIMED 抽出・PHANTOM/UNDECLARED 判定
#   block-3 = NO_OP 免除判定
# 構成が変わっていたらフィクスチャは前提が崩れるためスキップする（構文チェックの
# 結果はそのまま有効）。
if (( ${#BLOCK_RANGES[@]} != 3 )); then
  echo "WARN: ${#BLOCK_RANGES[@]} bash block(s) found (fixture は 3 ブロック構成を前提としている）。フィクスチャをスキップする。verify-deterministic-check.sh の追従修正が必要。"
  exit 0
fi

PRE_SET_BLOCK="$WORK_DIR/block-1.sh"
POST_SET_BLOCK="$WORK_DIR/block-2.sh"
NOOP_BLOCK="$WORK_DIR/block-3.sh"

FIXTURE_FAILURES=0

fail() {
  FIXTURE_FAILURES=$((FIXTURE_FAILURES + 1))
  echo "  FIXTURE FAIL: $1"
}

assert_empty() {
  local file="$1" desc="$2"
  if [[ -s "$file" ]]; then
    fail "$desc: expected empty, got: $(tr '\n' '|' < "$file")"
  fi
}

assert_contains() {
  local file="$1" needle="$2" desc="$3"
  if [[ ! -f "$file" ]] || ! grep -qxF "$needle" "$file"; then
    fail "$desc: expected line '$needle' in $file"
  fi
}

assert_not_contains_substr() {
  local file="$1" needle="$2" desc="$3"
  if [[ -f "$file" ]] && grep -qF "$needle" "$file"; then
    fail "$desc: expected '$needle' NOT to appear in $file"
  fi
}

# scratch git repo を1つ作り、pre-set を記録した状態で返す（repo path を echo）
setup_scratch_repo() {
  local name="$1"
  local repo="$WORK_DIR/repo-${name}"
  mkdir -p "$repo"
  git -C "$repo" -c init.defaultBranch=main init -q
  git -C "$repo" config user.email "verify@example.com"
  git -C "$repo" config user.name "verify"
  # scratch repo は使い捨てフィクスチャなので、グローバル pre-commit dispatcher
  # （gitleaks 等）をこのリポジトリだけ無効化してノイズと実行時間を削る
  git -C "$repo" config core.hooksPath /dev/null
  printf '.ai-pir-runs/\n' > "$repo/.gitignore"
  printf 'seed\n' > "$repo/seed.txt"
  git -C "$repo" add .gitignore seed.txt
  git -C "$repo" commit -q -m seed
  echo "$repo"
}

# pre-set（block-1）を実行する
run_pre_set() {
  local repo="$1" run_dir="$2"
  env PROJECT_ROOT="$repo" RUN_DIR="$run_dir" IMPL_INDEX=01 bash "$PRE_SET_BLOCK" || true
}

# post-set/delta/claimed/phantom/undeclared（block-2）を実行する
run_post_set() {
  local repo="$1" run_dir="$2"
  env PROJECT_ROOT="$repo" RUN_DIR="$run_dir" IMPL_INDEX=01 PRE_IMPL_INDEX=01 bash "$POST_SET_BLOCK" || true
}

# NO_OP 免除判定（block-3）を実行し NO_OP_JUSTIFIED の値を stdout に出す
capture_noop_flag() {
  local run_dir="$1"
  (
    set +e
    # shellcheck disable=SC2034  # NOOP_BLOCK が source 先で参照する変数（静的解析からは見えない）
    RUN_DIR="$run_dir" IMPL_INDEX=01
    # shellcheck disable=SC1090
    source "$NOOP_BLOCK" >/dev/null 2>&1
    echo "$NO_OP_JUSTIFIED"
  )
}

echo ""
echo "--- fixture: PHANTOM ---"
repo="$(setup_scratch_repo phantom)"
run_dir="$repo/.ai-pir-runs/run1"
mkdir -p "$run_dir"
run_pre_set "$repo" "$run_dir"
cat > "$run_dir/implementation-01.md" <<'EOF'
## 実装完了レポート

### 変更ファイル一覧
- `claimed_but_missing.txt` — 存在しない変更の申告（PHANTOM 検証用フィクスチャ）

### 実装概要
fixture: phantom scenario

### 注意点・未解決事項
なし
EOF
run_post_set "$repo" "$run_dir"
assert_contains "$run_dir/verify-01-phantom.list" "claimed_but_missing.txt" "PHANTOM: phantom.list"
assert_empty "$run_dir/verify-01-undeclared.list" "PHANTOM: undeclared.list"
assert_empty "$run_dir/verify-01-claimed-untrackable.list" "PHANTOM: claimed-untrackable.list"

echo "--- fixture: UNDECLARED ---"
repo="$(setup_scratch_repo undeclared)"
run_dir="$repo/.ai-pir-runs/run1"
mkdir -p "$run_dir"
run_pre_set "$repo" "$run_dir"
printf 'claimed\n' > "$repo/claimed_and_changed.txt"
printf 'undeclared\n' > "$repo/undeclared_change.txt"
cat > "$run_dir/implementation-01.md" <<'EOF'
## 実装完了レポート

### 変更ファイル一覧
- `claimed_and_changed.txt` — 申告どおりの変更

### 実装概要
fixture: undeclared scenario

### 注意点・未解決事項
なし
EOF
run_post_set "$repo" "$run_dir"
assert_empty "$run_dir/verify-01-phantom.list" "UNDECLARED: phantom.list"
assert_contains "$run_dir/verify-01-undeclared.list" "undeclared_change.txt" "UNDECLARED: undeclared.list"
assert_not_contains_substr "$run_dir/verify-01-undeclared.list" "claimed_and_changed.txt" "UNDECLARED: undeclared.list に申告済みファイルが混入していないか"

echo "--- fixture: NO_OP ---"
repo="$(setup_scratch_repo noop)"
run_dir="$repo/.ai-pir-runs/run1"
mkdir -p "$run_dir"
run_pre_set "$repo" "$run_dir"
cat > "$run_dir/implementation-01.md" <<'EOF'
## 実装完了レポート

### 変更ファイル一覧
なし

### 実装概要
fixture: no-op scenario

### 注意点・未解決事項
- NO_OP_JUSTIFIED: 対象コードは既に期待仕様を満たしていたため変更不要
EOF
run_post_set "$repo" "$run_dir"
assert_empty "$run_dir/verify-01-claimed-trackable.list" "NO_OP: claimed-trackable.list"
assert_empty "$run_dir/verify-01-delta.list" "NO_OP: delta.list"
assert_empty "$run_dir/verify-01-phantom.list" "NO_OP: phantom.list"
noop_flag="$(capture_noop_flag "$run_dir")"
if [[ "$noop_flag" != "1" ]]; then
  fail "NO_OP: NO_OP_JUSTIFIED should be 1, got '$noop_flag'"
fi

echo "--- fixture: 非ASCIIファイル名 ---"
repo="$(setup_scratch_repo nonascii)"
run_dir="$repo/.ai-pir-runs/run1"
mkdir -p "$run_dir"
run_pre_set "$repo" "$run_dir"
printf 'x\n' > "$repo/日本語ファイル.txt"
cat > "$run_dir/implementation-01.md" <<'EOF'
## 実装完了レポート

### 変更ファイル一覧
- `日本語ファイル.txt` — 非ASCIIファイル名の検証

### 実装概要
fixture: non-ascii filename scenario

### 注意点・未解決事項
なし
EOF
run_post_set "$repo" "$run_dir"
assert_contains "$run_dir/verify-01-claimed-trackable.list" "日本語ファイル.txt" "非ASCII: claimed-trackable.list"
assert_empty "$run_dir/verify-01-phantom.list" "非ASCII: phantom.list（quotePath=false で post.list と文字列一致するか）"
assert_empty "$run_dir/verify-01-undeclared.list" "非ASCII: undeclared.list"

echo "--- fixture: フェンス内例示 ---"
repo="$(setup_scratch_repo fenced)"
run_dir="$repo/.ai-pir-runs/run1"
mkdir -p "$run_dir"
run_pre_set "$repo" "$run_dir"
printf 'y\n' > "$repo/real_change.txt"
cat > "$run_dir/implementation-01.md" <<'EOF'
## 実装完了レポート

### 変更ファイル一覧
- `real_change.txt` — 本当の変更

例（レポート記法の参考。以下はフェンス内の引用でありCLAIMEDには含めない）:
```
- `decoy/fake/path.txt` — このパスは例示であり実際の申告ではない
```

### 実装概要
fixture: fenced decoy scenario

### 注意点・未解決事項
なし
EOF
run_post_set "$repo" "$run_dir"
assert_contains "$run_dir/verify-01-claimed-trackable.list" "real_change.txt" "フェンス内例示: claimed-trackable.list に本物の申告が含まれるか"
assert_not_contains_substr "$run_dir/verify-01-claimed.list" "decoy" "フェンス内例示: claimed.list にフェンス内の decoy パスが混入していないか"
assert_empty "$run_dir/verify-01-phantom.list" "フェンス内例示: phantom.list（decoy が誤って PHANTOM 扱いされていないか）"

echo "--- fixture: サブモジュール（pointer bump + 内部パス申告） ---"
# サブモジュールの「取得元」用リポジトリをローカルに用意する（ネットワーク不要。
# protocol.file.allow=always は最近の git のローカルパス submodule 制限
# （CVE-2022-39253 対策）を回避するためテスト環境依存を減らす目的で明示指定する）。
sub_src="$WORK_DIR/submodule-src"
mkdir -p "$sub_src"
git -C "$sub_src" -c init.defaultBranch=main init -q
git -C "$sub_src" config user.email "verify@example.com"
git -C "$sub_src" config user.name "verify"
git -C "$sub_src" config core.hooksPath /dev/null
printf 'v1\n' > "$sub_src/inner.md"
git -C "$sub_src" add inner.md
git -C "$sub_src" commit -q -m v1

repo="$(setup_scratch_repo submodule)"
git -c protocol.file.allow=always -C "$repo" submodule add -q "$sub_src" mysub
git -C "$repo" commit -q -m "add submodule"
run_dir="$repo/.ai-pir-runs/run1"
mkdir -p "$run_dir"
run_pre_set "$repo" "$run_dir"

# サブモジュール側で新規コミット（v2）を作り、親リポのポインタは更新しないまま
# サブモジュールの work tree だけを v2 へ進める（= 親リポから見て「pointer bump」が
# unstaged で発生している状態を再現する）
printf 'v2\n' >> "$sub_src/inner.md"
git -C "$sub_src" add inner.md
git -C "$sub_src" commit -q -m v2
git -c protocol.file.allow=always -C "$repo/mysub" fetch -q origin main
git -C "$repo/mysub" checkout -q origin/main

cat > "$run_dir/implementation-01.md" <<'EOF'
## 実装完了レポート

### 変更ファイル一覧
- `mysub` — サブモジュールのポインタ更新
- `mysub/inner.md` — サブモジュール内ファイルの変更（検証不能想定）

### 実装概要
fixture: submodule scenario

### 注意点・未解決事項
なし
EOF
run_post_set "$repo" "$run_dir"
assert_contains "$run_dir/verify-01-claimed-trackable.list" "mysub" "サブモジュール: pointer bump が claimed-trackable.list に入るか（--ignore-submodules=dirty で post に復元されるか）"
assert_contains "$run_dir/verify-01-claimed-untrackable.list" "mysub/inner.md" "サブモジュール: 内部パス申告が claimed-untrackable.list に入るか（check-ignore exit 128 の3分岐判定）"
assert_empty "$run_dir/verify-01-phantom.list" "サブモジュール: phantom.list（pointer bump は post に存在し、内部パスは untrackable で PHANTOM 対象外のため空のはず）"
assert_empty "$run_dir/verify-01-claimed-untrackable-missing.list" "サブモジュール: claimed-untrackable-missing.list（mysub/inner.md は物理的に実在するため missing にならないはず）"

echo ""
if (( FIXTURE_FAILURES > 0 )); then
  echo "NG: ${FIXTURE_FAILURES} fixture assertion(s) failed"
  exit 1
fi

echo "OK: 6 fixture scenarios (PHANTOM / UNDECLARED / NO_OP / 非ASCIIファイル名 / フェンス内例示 / サブモジュール) all matched expected判定"
exit 0
```

---

## 6. `next-steps-queue.md` の 6-3 checkbox 行 / `implementation-delegation.md` の 6-2↔6-3 相互参照ノート / `sanitized-cwd.md`・`verify-sanitized-cwd.sh` の epic 登録差分

### 6a. `.claude/skills/pir2/references/next-steps-queue.md` の 6-3 checkbox 行

初期 Write テンプレート（5.6-1）の「残ステップ」チェックリスト全文（63行中の該当部分。前後の他ステップ行も含めて文脈を保持）:

```markdown
## 残ステップ

- [ ] ステップ 5.7: 破壊的変更チェックリスト
- [ ] ステップ 5.8: 直前追加 feedback の自己照合ゲート
- [ ] ステップ 6: implementer 起動 (IMPL_INDEX=01)
- [ ] ステップ 6-3: 決定論的完了検証（/pir2 の main 実装時はスキップ。/pir2codex には main actor が無いため常時適用）
- [ ] ステップ 6.5: 実装者の未解決事項ユーザー確認（該当時のみ）
- [ ] ステップ 7: reviewer ハイブリッド並列起動 (REVIEW_INDEX=01)
- [ ] ステップ 7.5: refactor-advisor 起動（reviewer 全員 PASS 後 1 回のみ）
- [ ] ステップ 8: tester 起動 (TEST_INDEX=01)
- [ ] ステップ 9: ウォークスルー生成
- [ ] ステップ 10: メモリへの記録
- [ ] ステップ 11: retrospector 起動
- [ ] ステップ 11.5: handoff.md 完了判定と後処理
- [ ] ステップ 12: 最終サマリーの提示
- [ ] ステップ 13: ウォークスルーの提示
```

「ステップ 6」と「ステップ 6-3」が**別行の独立 checkbox**として並記されている点に注意（deterministic-completion-check.md 側の「6-3 は resume 時の追跡粒度を上げるため next-steps.md 上で『ステップ6』とは独立した checkbox を持つ（既存の『hyphen 番号は親ステップと checkbox を共有する』という慣習からの意図的な例外）」という記述と対応）。

### 6b. `.claude/skills/pir2/references/implementation-delegation.md` の 6-2↔6-3 相互参照ノート（2箇所、全く同一文言）

**「shard 統合確認」節の直後（1箇所目、67行目）**:

```markdown
> ℹ️ ここ（6-2）は shard/unit 境界の **LLM 層の整合レビュー**（命名不整合・重複抽象・未接続の検出）。申告集合 vs 実 git diff の **決定論的 claim-vs-diff 集合照合**（PHANTOM_CLAIM / UNDECLARED_CHANGE）は 6-3（`~/.claude/skills/pir2/references/deterministic-completion-check.md`）が担い、デフォルト actor（pir2 の implementer-subagent）および Codex actor（pir2codex）を含む全実装 actor に適用する。6-3 は本節（shard/sequential 限定）の「一般化」であり、両者は別レイヤーで補完し合う。
```

**「unit 統合確認」節の直後（2箇所目、114行目、文言は1箇所目と一言一句同一）**:

```markdown
> ℹ️ ここ（6-2）は shard/unit 境界の **LLM 層の整合レビュー**（命名不整合・重複抽象・未接続の検出）。申告集合 vs 実 git diff の **決定論的 claim-vs-diff 集合照合**（PHANTOM_CLAIM / UNDECLARED_CHANGE）は 6-3（`~/.claude/skills/pir2/references/deterministic-completion-check.md`）が担い、デフォルト actor（pir2 の implementer-subagent）および Codex actor（pir2codex）を含む全実装 actor に適用する。6-3 は本節（shard/sequential 限定）の「一般化」であり、両者は別レイヤーで補完し合う。
```

冒頭のファイルヘッダ（W1 セッション内で 6-3 の存在を前提に追記されたと見られる導入節、5〜7行目）:

```markdown
このファイルの `implementer-shards` と `review-fix shard` は試験実装として扱う。実験の状態、観測ログ、採用/廃止判断は `~/.claude/skills/pir2/references/experimental.md` の `pir2-implementer-shards-and-review-fix-shards` を SSOT とし、retrospector が毎回評価・更新する。

`implementer-sequential`（順序付き unit の直列 fresh 実装）も試験実装で、SSOT は同 `experimental.md` の `pir2-implementer-sequential-units`。
```

> 補足: `implementation-delegation.md` 冒頭ヘッダには 6-3 への直接言及はない。6-2↔6-3 の相互参照は上記2箇所（「shard 統合確認」節末尾・「unit 統合確認」節末尾）のみで、いずれも文言は完全に一致している（DRY のためコピペ由来と推測されるが、片方だけ将来更新されて乖離するリスクは構造的に残る）。

### 6c. `.claude/skills/pir2/references/sanitized-cwd.md` の epic 登録差分

「参照側のファイル一覧」表の全文（`epic` が 10 番目の行として登録済み。現時点のファイル内容そのまま）:

```markdown
## 参照側のファイル一覧

このリファレンスを参照する 10 ファイル（各ファイルで sed 式は同一・入力ソースは上記表の通り）:

| # | ファイル | 入力系統 |
|---|---|---|
| 1 | `~/.claude/skills/pir2/SKILL.md` | pwd 系 |
| 2 | `~/.claude/skills/pir2async/SKILL.md` | pwd 系 |
| 3 | `~/.claude/skills/debug/SKILL.md` | pwd 系 |
| 4 | `~/.claude/skills/ir/SKILL.md` | pwd 系 |
| 5 | `~/.claude/skills/reviewer/SKILL.md` | pwd 系 |
| 6 | `~/.claude/skills/review-pr/SKILL.md` | pwd 系 |
| 7 | `~/.claude/skills/writing-plan/SKILL.md` | pwd 系 |
| 8 | `~/.claude/skills/refactor-advisor/SKILL.md` | pwd 系 |
| 9 | `~/.claude/skills/retro/SKILL.md` | target_path 系 |
| 10 | `~/.claude/skills/epic/SKILL.md` | pwd 系 |
```

### 6d. `.claude/skills/pir2/references/verify-sanitized-cwd.sh` の epic 登録差分

`SKILL_FILES` 配列定義全文（`epic/SKILL.md` が配列末尾に追加済み。現時点のファイル内容そのまま）:

```bash
SKILL_FILES=(
  "${HOME}/.claude/skills/pir2/SKILL.md"
  "${HOME}/.claude/skills/pir2async/SKILL.md"
  "${HOME}/.claude/skills/debug/SKILL.md"
  "${HOME}/.claude/skills/ir/SKILL.md"
  "${HOME}/.claude/skills/reviewer/SKILL.md"
  "${HOME}/.claude/skills/review-pr/SKILL.md"
  "${HOME}/.claude/skills/writing-plan/SKILL.md"
  "${HOME}/.claude/skills/refactor-advisor/SKILL.md"
  "${HOME}/.claude/skills/retro/SKILL.md"
  "${HOME}/.claude/skills/epic/SKILL.md"
)
```

冒頭コメント（このスクリプトのスコープ説明。2026-07-02 移行メモを含む全文）:

```bash
#!/usr/bin/env bash
# verify-sanitized-cwd.sh
#
# PIR² 系 10 SKILL.md の sanitize 正規表現が SSOT と一致していることを検証する。
# SSOT: ~/.claude/skills/pir2/references/sanitized-cwd.md
#
# 揺れを検出した場合は exit 1 を返す（pre-commit / CI 組み込み可）。
#
# 使い方:
#   bash ~/.claude/skills/pir2/references/verify-sanitized-cwd.sh
#
# 2026-07-02 移行メモ: RUN_DIR / HANDOFF_PATH の基底パスは PROJECT_ROOT ローカル化
# （~/.claude/skills/pir2/references/run-dir-base.md）により sanitized_cwd 不要になった。
# 本スクリプトが検証する `sanitized_cwd=` 行は、各 SKILL.md がなお PROJECT_MEMORY_DIR
# （~/.claude/projects/<sanitized-cwd>/memory）の導出に使っているものを指す。
# その行が SKILL.md から消える場合は、本スクリプトの前提が崩れるため要更新。
```

> 補足: `epic` 登録は `.claude/skills/epic/` 新設（`.claude/agents/epic-planner.md` 新設と同時期）に伴う W1 とは別軸の副次変更で、6-3（決定論的完了検証）機能そのものとは直接関係しない。ただし `git status --short` で両ファイルとも同一セッションの `M`（変更）扱いであるため、本レポートでは「現在の実ファイル状態」として収録している。

---

## 補足情報（構造的観察・deliberator 向けメモ）

以下は逐語収録の过程で気づいた構造的な事実。判断・評価は行わず、事実のみ記載する。

1. **PHANTOM 判定 vs UNDECLARED 判定で参照リストが非対称**（`claimed-trackable.list` vs `claimed.list`）。理由は deterministic-completion-check.md 本文中に明記されている（PHANTOM は「検証不能な申告」を誤って捏造扱いしないためフィルタが必要、UNDECLARED は delta 自体が in-repo/非-ignore のみのためフィルタ不要）。
2. **NO_OP 免除の正規表現は「行頭アンカー + 箇条書き `-` のみ許容、番号リストは非対応」**という設計上の非対称がある（本文コメントに理由明記: 番号リストまで許容すると「該当なし」を宣言と誤認するリスクがあるため）。
3. **フェンス除去ロジックの既知の限界**（「行頭 ``` （3個以上）でトグル」の単純状態機械であるため、入れ子フェンス例示で decoy パスが CLAIMED に混入しうる）が、CLAIMED 抽出・NO_OP 判定の両方に同型で存在すると明記されている。ただし方向は fail-closed（偽陽性 PHANTOM 側）であり安全側と位置づけられている。
4. **サブモジュール内部パスの申告は「検証不能（untrackable）」**として扱われ、PHANTOM 対象外になるが、`test -f` による実体確認（missing warn）で無条件の抜け穴にはしない設計になっている。この設計思想は「設計 SSOT（`docs/deepthink/20260703-190750-Fable5.md` 残存限界④⑥）と同型で受容する既知の限界」と明記されている（このファイル自体は本探索の対象外だが、コメント内で参照されている旨のみ記録）。
5. **6-3 の適用スコープは「初回実装点のみ」**であり、reviewer FAIL 後の再実装（7-4）・tester FAIL 後の再実装（8-2）・pir2codex の inner-loop 再実装（6-2）には適用されない、という限定が繰り返し明記されている（deterministic-completion-check.md「適用タイミング」節、pir2codex SKILL.md 6-2 節の両方に同旨の記述）。
6. **「本 run（W1 実装 run）で行った `verify-02` の適用」という自己言及**が deterministic-completion-check.md「適用タイミング」節末尾にある。これは「上記スコープが明文化される前に実施したドッグフーディングによる拡大適用であり、正式仕様の一部ではない」と明記されており、実装時に実際に verify-02（2回目の検証、おそらく reviewer FAIL 後の再実装点）まで適用してしまった経緯がある可能性を示唆する（本探索では該当する RUN_DIR の verify-*.md 実体は確認していない。必要なら別途 explorer に当該 run のログ確認を依頼されたい）。
7. **pir2 と pir2codex で「main スキップ」選択肢の有無が非対称**（pir2 の最終サマリーテンプレートには「main のためスキップ」の選択肢があるが、pir2codex の同テンプレートには無い）。理由は「pir2codex に `main` actor が存在しない」という設計上の事実に対応しており矛盾ではない。

## 呼び出し元への依頼

- 本レポートは指定された 6 項目の逐語収録のみを目的としており、各ファイルの**設計妥当性の評価・矛盾点の指摘**は意図的に行っていない（deliberator の熟考対象と切り分けるため）。設計評価が必要な場合は本レポートを入力として deliberator 側で実施されたい。
- 「本 run（W1 実装 run）で行った `verify-02` の適用」の経緯確認や、`docs/deepthink/20260703-190750-Fable5.md`（本文中で参照されている設計 SSOT）の内容確認が deliberator の判断に必要な場合、追加の explorer 起動をスキル本体側で検討されたい（本探索はスコープ外として深掘りしていない）。
