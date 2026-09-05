# 決定論的完了検証（worker-delegation 共通 SSOT）

runnerを明示的に選択し、artifact identity・実行モデル・effort・変更集合を決定論的に確認する必要がある job 向けの任意の証拠ゲートです。worker-delegation の完了レポートが申告した変更ファイル集合と、実際の git 作業ツリーの変更集合を純 bash で照合し、PHANTOM_CLAIM（申告したが実変更にないファイル）と UNDECLARED_CHANGE（実変更だが申告にないファイル）を reviewer / tester の品質判定から分離して記録します。native collaboration や Astra の直接実装には適用しません。

- runnerを使う concrete job（単一 job、shard、review-fix、tester FAIL 後の修正を含む）では、実装開始前に pre-set を記録し、完了直後に post-set と delta を計算します。新しい workflow は、runner-owned artifact や変更集合の決定論的証拠が必要な場合だけこの SSOT を使います。
- Astra は worker の自由形式の完了出力を、RUN_DIR/implementation-IMPL_INDEX.md の canonical report に正規化します。canonical report の変更ファイル一覧は、実測した相対パスを1行1件で記載します。
- PHANTOM_CLAIM は hard fail、UNDECLARED_CHANGE は warn として記録します。PHANTOM を検出したら reviewer を起動せず、原因を示したうえで1回だけ worker を再実行できます。2回目も解消しない場合はユーザー確認を待ちます。
- Sol worker（`expert` / `expert_max`）の場合も、実装後に親Astraが同じ canonical report を作成してこのゲートを通します。runnerを選択した実装経路で証拠ゲートを適用する場合は、actorにかかわらず省略しません。
- canonical report と verifier report は actor を `luna|terra|sol`、実測 model を `gpt-5.6-luna|gpt-5.6-terra|gpt-5.6-sol`、実測 effort を `max|high` として記録します。Terra の `high|max` と Sol worker の `high|max` を混同せず、runner の自動切替は行わず `automatic_fallback=no` を記録します。runnerを使わない job にはこの report、pre/post、8 fixture、meta gate を要求しません。

機械検証は次で実行します。

bash $PROJECT_ROOT/.codex/skills/worker-delegation/scripts/verify-deterministic-check.sh

この verifier は本ファイルの3つの bash ブロックを構文検証し、scratch git repository で PHANTOM / UNDECLARED / NO_OP / 非ASCIIファイル名 / フェンス内例示 / サブモジュール / staged申告 / pre-existing-staged の8シナリオを実行します。

## 適用タイミング

適用対象の runner job を起動する直前に pre-set を1回記録し、runner job の完了後、Astra acceptance と reviewer 起動の前に post-set / delta / CLAIMED を計算します。reviewer や tester が FAIL して修正 runner job を起動する場合は、その修正 job の直前にも新しい pre-set を記録し、完了後に同じゲートを再実行します。既存の pre-set は上書きせず、PRE_IMPL_INDEX を固定します。

## 検証の情報源


- **申告集合 CLAIMED**: `{RUN_DIR}/implementation-{IMPL_INDEX}*.md` の `### 変更ファイル一覧` セクションの各 `` - `path` `` 行
  - worker-single: `implementation-{IMPL_INDEX}.md`
  - worker-shards: `implementation-{IMPL_INDEX}-*.md`（全 shard の和集合）
  - worker-sequential: `implementation-{IMPL_INDEX}-unit-*.md`（全 unit の和集合）
- **実集合**: 作業ツリーの dirty 集合 = `git diff --name-only --ignore-submodules=dirty`（unstaged 変更。サブモジュール work tree 内部の非コミット変更は無視するが、サブモジュールのコミットポインタ変更（pointer bump）は親リポ側で「サブモジュールパス 1 行」として検出される）＋ `git diff --cached --name-only`（staged 変更）＋ `git ls-files --others --exclude-standard`（untracked）の union。**staged は pre-set / post-set の両方に対称で含める**（片側だけだと開始前から staged 済みのファイルが delta に誤混入し UNDECLARED 偽陽性を生む。過去の FIX-5/FIX-F regression と同型の穴を再演しないため対称性が必須）。
  - **staged を含める理由（R1 是正）**: 従来「staged 集合は対象外」としていたのは、実装 job が申告ファイルを `git add` した瞬間そのファイルが `git diff --name-only`（unstaged 専用）の出力から消え、実際には変更されているのに実集合に現れず、正当な申告が **PHANTOM_CLAIM（fail-closed・再実行しても直らない unrecoverable hard fail）**として誤検出される穴があったため。`--cached` を実集合へ加えてこの fail-closed FP を塞ぐ。
  - **この変更の既知の副作用（fail-open への転換）**: 「staged ⊆ 実際に変更されたファイル」という前提は厳密には成立しない。worker workflow 実行開始前から**ユーザーが既に stage していたファイル**への虚偽申告は、この変更前なら実集合に現れず PHANTOM_CLAIM（結果的な真陽性）として捕捉されていたが、変更後は当該ファイルが pre-set・post-set の両時点で staged 集合として実集合に含まれ続けるため **silent PASS（新規の偽陰性）**になる。つまり本変更は「fail-closed FP（common・unrecoverable）を fail-open FN（pre-existing-staged 集合に限定・rare）に転換する」修正であり、偽陰性ゼロを保証するものではない。この副作用は後述「既知の残存限界（R1〜R13）」の R6（pre-existing-dirty への虚偽申告が silent PASS になる限界）と**同型・同一の受容根拠**（git-oracle の domain 境界＋脅威モデルは accident であり adversary でないこと）に合流するとして受容する。
  - サブモジュール**内部のファイル単位**の申告（例: `mysub/inner.md`）は 3b の `check-ignore` が exit 128（`fatal: pathspec is in submodule`）を返すため git 追跡可能性を判定できず、検証不能（untrackable）扱いとなる（後述「git 検証不能な申告の扱い」を参照）。一方、サブモジュールのポインタ変更そのもの（例: `mysub`）は git 追跡可能な通常の申告として扱う（親で `git add mysub` して staged にした pointer bump も `--cached` union により同時に実集合へ含まれる）。
- **git 検証不能な申告の扱い（重要・偽陽性防止）**: CLAIMED のうち **リポジトリ外**（`$PROJECT_ROOT` 配下でない絶対パス、または `~/...` のようなチルダ記法。例: `~/.codex/projects/.../memory/*` のメモリログ）または **gitignore 対象**（例: `.ai-pir-runs/` 配下の handoff.md 等）のパスは、実集合（git delta）に原理的に現れないため **PHANTOM 判定の対象外**とする（git で dirty かを検証できない＝「捏造」ではなく「検証不能」）。実装 job はこれら bookkeeping ファイルを `### 変更ファイル一覧` に載せることがあり、載っていても hard fail にしてはならない。PHANTOM 照合は **git 追跡可能な申告集合（`claimed-trackable`）** に対してのみ行う。ただし「検証不能」を無条件の抜け穴にはしない。「git 検証不能な申告の実体確認」で `test -f` により実ファイルの存在を確認し、存在しない申告は warn として可視化する（後述）。

### 完了レポートの正規化

worker-delegation の runner は自由形式の完了出力を返すため、Sol はそれを読み、実際に確認した相対パスを canonical report の「### 変更ファイル一覧」に1行1件で正規化します。パスはリポジトリルート相対、重複なし、ファイル単位で記載します。編集不要なら一覧を「なし」とし、「### 注意点・未解決事項」に NO_OP_JUSTIFIED: <理由> を明記します。推測でパスを補いません。

## pre-set 記録（実装 job 起動の直前に実行）

runner job（Luna、Terra、または Sol worker）を開始する **前** に、必要と判断した場合の基準スナップショットを記録します。呼び出し元は runner を選択した job にだけこの記録を行います:

```bash
PRE_IMPL_INDEX="$IMPL_INDEX"   # pre-set 記録時点の IMPL_INDEX を固定保持。PHANTOM 再実行で IMPL_INDEX が
                                # インクリメントされても pre-set のファイル名はこの値を使い続ける
#    -c core.quotePath=false: 非 ASCII ファイル名を八進エスケープせず生 UTF-8 で出力させる
#    （デフォルトのままだと CLAIMED の生文字列と文字列一致せず PHANTOM 偽陽性になる）
#    --ignore-submodules=dirty: サブモジュール work tree 内部の非コミット変更は無視しつつ、
#    サブモジュールのコミットポインタ変更（pointer bump）は親リポの1行申告として残す
#    （--ignore-submodules=all だと pointer bump まで消えてしまい正当な申告が PHANTOM 化するため）
#    diff --cached --name-only: staged 変更を実集合に含める（R1 是正。「staged は対象外」の
#    旧仕様は git add した瞬間に正当な申告が PHANTOM 化する fail-closed 穴だったため撤回した。
#    pre-set / post-set の両方に対称で入れること。片側のみだと開始前から staged 済みの
#    ファイルが delta に誤混入し偽 UNDECLARED を生む）
{ git -C "$PROJECT_ROOT" -c core.quotePath=false diff --name-only --ignore-submodules=dirty
  git -C "$PROJECT_ROOT" -c core.quotePath=false diff --cached --name-only
  git -C "$PROJECT_ROOT" -c core.quotePath=false ls-files --others --exclude-standard
} | sort -u > "$RUN_DIR/verify-${PRE_IMPL_INDEX}-pre.list"
```

> 起動時点で既に dirty または staged なファイルはここに含まれ、後段の delta から自然に除外される（この実装 job 起動での変更だけを delta が表す）。`.ai-pir-runs/` は .gitignore 済みなので RUN_DIR 内の中間ファイルは untracked に混入しない。shard / unit を含む各 job の直前に、その job 用の pre-set を1回だけ記録します。`PRE_IMPL_INDEX` は「失敗パス」で `IMPL_INDEX` がインクリメントされた後も pre-set のファイル名参照にのみ使う変数で、post-set / delta / CLAIMED は常に現在の `IMPL_INDEX` で計算します（詳細は次節）。

## post-set 記録・delta 計算・CLAIMED 抽出（実装 job 完了後）

```bash
# 0. pre-set 存在確認（worker 起動前の記録漏れを silent 劣化させない。fail-loud のみでワークフロー自体は
#    止めない。ERROR が出た場合の運用はこのコードブロック直後の blockquote を参照）
[ -f "$RUN_DIR/verify-${PRE_IMPL_INDEX}-pre.list" ] || echo "ERROR: pre-set 未記録（verify-${PRE_IMPL_INDEX}-pre.list なし）。delta/UNDECLARED が計算不能。worker 起動前の pre-set 記録手順に戻り、pre-set を再記録した上で実装 job を再実行せよ（今から記録しても post と同一になり delta は空＝無意味）" >&2

# 1. post-set（完了後の dirty 集合。quotePath/ignore-submodules/--cached は pre-set と同じ理由。
#    --cached は pre-set と対称で必須 — 片側だけだと staged 状態の変化が delta に誤混入する）
{ git -C "$PROJECT_ROOT" -c core.quotePath=false diff --name-only --ignore-submodules=dirty
  git -C "$PROJECT_ROOT" -c core.quotePath=false diff --cached --name-only
  git -C "$PROJECT_ROOT" -c core.quotePath=false ls-files --others --exclude-standard
} | sort -u > "$RUN_DIR/verify-${IMPL_INDEX}-post.list"

# 2. delta = post - pre（この実装 job 起動で新たに dirty になったファイル）
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

> ⚠️ 上記手順0の ERROR（pre-set 未記録）が出力された場合、呼び出し元 workflow は delta/UNDECLARED 判定を実行不能と扱い、worker 起動前の pre-set 記録手順に戻ってやり直す（＝pre-set を再記録した上で実装 job を再実行する。今から pre.list を記録しても post と同一になり delta は空＝無意味なため）。PHANTOM 照合のみでの縮退運転はしない。

## 集合照合規則（判定）

| 条件 | 判定 | 扱い |
|---|---|---|
| `phantom.list` が非空（**git 追跡可能なのに**申告通り dirty でないファイルがある） | **PHANTOM_CLAIM** | hard fail |
| `claimed-trackable.list` が空 かつ `delta.list` が空 かつ NO_OP 免除なし（編集想定タスクなのに git 追跡可能な申告も実変更も無い） | **PHANTOM_CLAIM** | hard fail |
| `undeclared.list` が非空（申告外の dirty） | **UNDECLARED_CHANGE** | warn（非ブロッキング） |
| `claimed.list` が空 かつ `delta.list` が非空 | **UNDECLARED_CHANGE** | warn（非ブロッキング） |
| 上記いずれも該当せず | **PASS** | reviewer / 呼び出し元 workflow の後続処理へ進む |

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
# canonical report が規定する `NO_OP_JUSTIFIED: <理由>` の素の記法（箇条書き `-` の有無のみ許容）に絞る。
NO_OP_JUSTIFIED=0
for f in "$RUN_DIR"/implementation-${IMPL_INDEX}*.md; do
  [ -f "$f" ] || continue
  if awk '/^```/{c=!c;next} !c' "$f" \
      | awk '/^### 注意点・未解決事項/{f=1;next} (/^## /||/^### /){if(f)exit} f' \
      | grep -qE '^[[:space:]]*(-[[:space:]]*)?`?NO_OP_JUSTIFIED:`?'; then
    NO_OP_JUSTIFIED=1   # 実装 job が「編集不要」を明示宣言 → PHANTOM 免除・PASS 扱い
    break
  fi
done
# NO_OP_JUSTIFIED=0 のまま → 宣言なし → PHANTOM_CLAIM（hard fail）
```

- concrete worker-delegation workflow: worker が編集不要と判断した場合、canonical report の `### 注意点・未解決事項` に `NO_OP_JUSTIFIED: <理由>` を明記します（worker-delegation の報告形式に合わせます）。

## 判定結果の書き出し

判定結果を `{RUN_DIR}/verify-{IMPL_INDEX}.md` に書き出す:

```markdown
# 決定論的完了検証（IMPL_INDEX=NN）

- PRE_IMPL_INDEX: <NN>（pre-set 基準スナップショット）
- CLAIMED 情報源: <implementation-{IMPL_INDEX}*.md>（現ラウンドの実装レポートのみ。前ラウンド分とは和集合にしない）
- PHANTOM_RETRY_COUNT: <N>
- actor: <luna|terra|sol>
- actual_model: <実測モデル名>
- actual_effort: <max|high>
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
2. **1 回目の PHANTOM（`PHANTOM_RETRY_COUNT == 0`）**: `IMPL_INDEX` と `PHANTOM_RETRY_COUNT` をインクリメントし、実装 job を **1 回だけ**再実行する。`PRE_IMPL_INDEX` は変更しない（据え置き）。再実行プロンプトに `{RUN_DIR}/verify-{直前 IMPL_INDEX}.md`（検証レポート）のパス／全文を渡し、「申告したが実際には変更されていない以下のファイルを実際に編集せよ、または申告を実体に一致させよ。**再実行後のレポートの `### 変更ファイル一覧` には、前ラウンド分も含めた訂正後の完全な変更ファイル一覧を再宣言すること**（CLAIMED は現ラウンドのレポートのみを情報源にするため）」と**原因を逐語注入**する（ブラインドリトライではない＝原因が特定済み）。
   - 呼び出し元 workflow: 同じ task / requirements / actor を worker-delegation の runner で再起動し、訂正後の canonical report を作成する。
   - 再起動後、pre-set は `verify-${PRE_IMPL_INDEX}-pre.list`（初回起動時点のスナップショット）を据え置きで参照し続け、post-set / delta は新しい `IMPL_INDEX` で再計算する。CLAIMED は「post-set記録・delta計算・CLAIMED 抽出」節のとおり**現ラウンド（新しい `IMPL_INDEX`）の implementation レポートのみ**を情報源にする（前ラウンドの申告とは和集合にしない。申告を訂正すればその訂正が判定に反映されるようにするため）。前ラウンドで正当だった申告が再宣言されず delta に残っていた場合 UNDECLARED_CHANGE の warn（非ブロッキング）に出うるが、上記の「完全な一覧を再宣言」指示により通常は発生しない。PHANTOM retry は呼び出し元 workflow の reviewer/tester retry counter を消費しない。
3. **2 回目も PHANTOM（`PHANTOM_RETRY_COUNT >= 1`）**: **reviewer を起動せず**、以下のユーザーゲートを開く（捏造の上にレビューを積まない）。Codex workflow rules「ブラインドリトライ禁止」（初回＋再試行1回＝計2回で停止）と整合。

### ユーザーゲート（2 回目 PHANTOM 時）

```
## 決定論的完了検証 FAIL — PHANTOM_CLAIM（再実行1回後も未解消）

実装（worker-delegation actor）が変更したと申告したが、実際の git 作業ツリーに反映されていないファイルを検出しました。

- 申告集合（CLAIMED、git 追跡可能）: <claimed-trackable.list>
- 実変更集合（delta）: <delta.list>
- 申告のみで実体なし（PHANTOM）: <phantom.list>
- 検証不能として除外（PHANTOM 対象外）: <claimed-untrackable.list>（うち実体を確認できず: <claimed-untrackable-missing.list>）

以下の実 git 変更を参考にしてください（自動巻き戻しは行いません）:
<git -C "$PROJECT_ROOT" diff の要約（--stat）>

続行方法を選んでください:
- (A) 手動調査してから再開: git diff を確認し原因を特定。追加指示付きで実装 job を再起動（IMPL_INDEX++）するか手動修正 → 検証を再実行【推奨】
- (B) PHANTOM を承知でそのまま reviewer へ進む（申告漏れ/検証の偽陽性とユーザーが判断した場合のみ）
- (C) ワークフローを中止

[A / B / C]
```

- **補償は `git diff` 全 hunk のユーザー提示のみ。`git restore` / `git checkout -- <file>` による自動巻き戻しは絶対にしない**（Codex workflow rules Git ルール）。PHANTOM は「申告ファイルが dirty でない」状態なので巻き戻す対象自体がなく、提示するのは実際に dirty な変更の実体。
- **Auto mode でも本ゲートはユーザー応答を待つ**（仕様変更判断ゲートのため Auto mode 例外）。
- ゲート発火と選択は `{RUN_DIR}/user-decisions.md` に追記する。

## 既知の残存限界（R1〜R13）

本ゲートは「完了検証（completion verifier）」ではなく **phantom-claim floor**（申告ファイル集合が実際に git 上で変更されたか＝file-set 存在の1次元のみを検証し、内容の正しさ・実装の妥当性・部分的な手抜き実装等の substance は一切検証しない）と位置づける。substance の検証は reviewer 層の責務であり、本ゲートがそれを代替するものではない。

git を独立観測 oracle に選んだことに由来する原理的な残存限界を、方向（**fail-open** = 虚偽申告を見逃す・**fail-closed** = 正当な申告を誤って PHANTOM 扱いする）・頻度・対応方針（3層: 「must-fix で解消」「commit 後の観測窓」「受容・文書化」）つきで以下に完全列挙する。

| # | 残存限界 | 機序 | 方向 | 頻度 | 対応（3層割付） | 理由・注記 |
|---|---|---|---|---|---|---|
| R1 | staged 変更（一般） | `git add` で unstaged diff から消失 → 正当申告が PHANTOM 化・再実行で直らない | fail-closed（unrecoverable） | 中 | **must-fix #1 で解消** | fail-closed AND common AND clean-fix の3条件を満たす唯一の穴だったため優先解消。`--cached` union をフィクスチャ2本（stage 申告 PASS / pre-existing-staged 非混入）つきで実装 |
| R2 | submodule 内部パス虚偽申告 | `check-ignore` exit 128 → untrackable → PHANTOM 対象外 / `test -f` 実在 → silent | fail-open（silent） | 低（PROJECT_ROOT=親 × 内部パス申告の狭い交差） | 受容・文書化 | git-parent の domain 外。**(h) exit 128 は観測挙動接地であり文書化された契約ではない**。git 将来版で exit 1（trackable）に変われば方向が fail-closed hard fail に反転しうる。`verify-deterministic-check.sh` のサブモジュールフィクスチャが回帰検知の砦 |
| R3 | submodule pointer bump | trackable / `=dirty` が post に残る | 正当申告→PASS・虚偽申告→正しく hard fail（真陽性） | 低 | 受容（設計どおり健全） | `--ignore-submodules=dirty` が pointer bump の fail-closed FP を意図的に予防。穴でない |
| R4 | submodule staged pointer bump | 親で `git add mysub` → unstaged diff に不出 | fail-closed | 低 | **must-fix #1 に包含** | staged FP の submodule 顕現。`--cached` union が同時に閉塞する |
| R5 | 実在 gitignore への虚偽申告 | `check-ignore` exit 0 → untrackable / `test -f` 実在 → silent | fail-open（silent） | 低〜中 | 受容・文書化 | ignore の定義そのものが oracle domain 外。clean fix が存在しない |
| R6 | pre-existing-dirty への虚偽申告 | 既に dirty なファイル F を申告・実際は未編集 → F は post にも在り非 PHANTOM。delta からも除外されるため UNDECLARED も無反応 → 両検査から不可視 | fail-open（silent） | 最高（active dev の既 dirty 集合） | 受容・文書化（頻度警告つき） | name-set 粒度の原理的盲点。**#1 適用後は pre-existing-staged への虚偽申告も本行に合流する**（同型・同一の受容根拠。git-oracle の domain 境界＋脅威モデルが accident であり adversary でないこと）。adversarial 化や content-hashing の低コスト化が実現した場合に最初に再訪すべき箇所 |
| R7 | resume 中の外部 git 変化 | pre.list 記録後〜post.list 記録前の中断中にユーザーが commit/stash 等を行い作業ツリーが clean 化 → 申告した全ファイルが偽 PHANTOM 化 | fail-closed | 低 | commit 後観測（must-fix #2 の観測窓） | rare かつユーザーゲート（(A)手動調査 / (B)承知の上で進行 / (C)中止）で回復可能 |
| R8 | 入れ子フェンス（decoy 混入） | naive toggle awk のフェンス判定が入れ子 ``` で parity 反転し、decoy パスが CLAIMED に混入 | 主方向 fail-closed（decoy が git delta に無いため PHANTOM 誤検知）／副方向 fail-open | 極低 | 受容・文書化＋任意 hardening | 主方向は安全側に倒れる。より堅牢な parser（境界判定を trim 完全一致にする実装）は `verify-deterministic-check.sh` 側に既存だが、runtime 側（本ファイルの bash）への移植は任意（コスト対効果で見送り） |
| R9 | case-only rename（APFS 等） | 大文字小文字のみのファイル名変更は git のシグナルが空になり得る → PHANTOM | fail-closed | 低（稀な操作 × ファイルシステム依存） | 受容・文書化 | rare かつ clean fix が非自明 |
| R10 | net-zero 編集 | 編集して元の内容に戻す → delta が空になる → NO_OP 宣言なしで PHANTOM | fail-closed | 極低 | 受容・文書化 | `NO_OP_JUSTIFIED` 免除宣言で回避可能 |
| R11 | symlink 経由パス | symlink の実体先が git 追跡外にある場合、検証不能 | fail-open | 極低 | 受容・文書化 | git domain 外の同クラス |
| R12 | pre-set 記録漏れ | 呼び出し元 workflow の Astra parent が runner 起動前の pre-set 記録を失念 →「pre-set 存在確認」で ERROR → 縮退運転を許さない設計のため runner job の再実行を強制 | fail-closed 系（honest run のコスト。hard fail ではなく回復可能・正当性は無傷） | 低〜中（orchestrator の手順遵守率に依存・未測定） | 実行後観測（観測窓で発生数を計測） | fail-loud の意図的設計で correctness は守られるが、honest run が runner job の再実行というコストを一手順の失念だけで強制される点は台帳化して観測すべき。頻発時は「PHANTOM-only 縮退モード＋UNDECLARED 判定不能 warn」または pre-set 記録の hook 化を検討する |
| R13 | 申告粒度の不一致（ディレクトリ / glob / typo 申告） | `src/foo/` のようなディレクトリ申告・`src/*.ts` のような glob 申告・パスの typo は git 追跡可能扱いだが post のファイル単位エントリと一致せず PHANTOM 化する | fail-closed | 中（申告規律に依存） | 受容（in-band 回復可能・申告規律強制の副次機能） | staged FP と異なり **再実行1回で申告をファイル単位に訂正すれば回復する**（unrecoverable ではない）。ただし FP 統計上は PHANTOM に計上されるため、observation の原因分類（真の捏造 / staged 系 / 申告規律 / resume-stale / その他）で区別して記録しないと rollback トリガの閾値判定が汚染される。稀な亜種として、埋め込み plain git repo（submodule でない、リポジトリ内にネストした別 `.git`）内パスの申告も同クラスに含まれる |

### 追加の設計注記（(g)〜(i)）

- **(g) must-fix #1 の副作用**: `--cached` を実集合に加えたことで、pre-existing-staged（pir2 実行開始前からユーザーが stage していたファイル）への虚偽申告は R6 と同型の fail-open（silent PASS）として合流する。これは意図的なトレードオフであり、正確には「fail-closed FP（common・unrecoverable）を fail-open FN（rare・pre-existing-staged 集合に限定）に転換した」ものである。「偽陰性を生まない」という文言でこの変更を説明しないこと。
- **(h) submodule の方向確定は観測挙動接地**: R2 の fail-open 判定は `check-ignore` が exit 128 を返すという**観測された挙動**に依拠しており、文書化された git の契約ではない。将来の git バージョンで submodule 内部パスに対する終了コードが変われば（例: exit 1 で trackable 扱いに変わる等）、R2 の方向は fail-open から fail-closed の hard fail に反転しうる。`verify-deterministic-check.sh` のサブモジュールフィクスチャ（`claimed-untrackable.list` に `mysub/inner.md` が入ることを assert する部分）がこの回帰を検知する唯一の砦であり、git バージョンアップ後にこのフィクスチャが失敗し始めたら本節の記述を見直すこと。
- **(i) フィクスチャ盲点の系統性**: `verify-deterministic-check.sh` の既存フィクスチャは全て「機構が宣伝する挙動の確認型」（PHANTOM / UNDECLARED / NO_OP / 非ASCII / フェンス内例示 / サブモジュールという、設計時に想定した機能の動作確認）であり、「clean-tree 前提が破れる干渉型」（staged 状態・大小文字のみの rename・pre-existing-dirty・resume 中の外部 git 操作等）を1本もカバーしていなかった（本 must-fix で staged 系フィクスチャ2本を追加し一部是正）。この盲点は偶発ではなく、フィクスチャを「設計の機能リストから起こす」という導出方法自体に由来する系統的なものである。今後 verify スクリプトのフィクスチャを追加する際は、機能リストからでなく「clean-tree 前提がどう破れうるか」の列挙から起こすこと。

## 適用しない条件

- native collaboration、Astraの直接実装、または artifact identity と変更集合の決定論的証拠を必要としない小変更では、この gate を実行しない。canonical report、pre/post/CLAIMED、8 fixture、meta gate、観測台帳を作業の完了条件に追加してはならない。
- runnerを選択した job でこの gate を適用する場合は、pre-set の欠落や PHANTOM 判定不能を縮退運転で隠さず、本ファイルの手順と runner-owned artifact を使って実測する。

## 完了後

この gate を適用した呼び出し元 workflow だけが、自身の next-steps / run ledger の deterministic gate 項目を `[x]` に更新します。PHANTOM 再実行で `IMPL_INDEX` が増えた場合も最初の1回だけマークし、詳細は workflow 固有の run log に追記します。適用時は判定レポート `${RUN_DIR}/verify-${IMPL_INDEX}.md` のパスを Astra acceptance と reviewer/tester 起動記録に含めます。
