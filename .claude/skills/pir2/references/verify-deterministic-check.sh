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
# ファイル名 / フェンス内例示 / サブモジュール / staged申告（git add 後の申告が
# PHANTOM 化しないか）/ pre-existing-staged（pir2 開始前から staged のファイルが
# delta に誤混入しないか）の 8 シナリオ）の両方を実行する。
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

echo "--- fixture: staged申告（git add 後に申告 → PHANTOM 化しないこと。R1 是正の確認） ---"
repo="$(setup_scratch_repo staged_claim)"
run_dir="$repo/.ai-pir-runs/run1"
mkdir -p "$run_dir"
run_pre_set "$repo" "$run_dir"
# 実装 actor が新規ファイルを作成しさらに git add で stage する（申告規律の禁止事項
# だが、6-3 検証が実集合を unstaged/untracked/staged の union で見るため実害が
# 無いことをフィクスチャで裏取りする）
printf 'staged content\n' > "$repo/staged_and_claimed.txt"
git -C "$repo" add staged_and_claimed.txt
cat > "$run_dir/implementation-01.md" <<'EOF'
## 実装完了レポート

### 変更ファイル一覧
- `staged_and_claimed.txt` — git add 済みの申告（staged 申告 PASS 検証用フィクスチャ）

### 実装概要
fixture: staged claim scenario

### 注意点・未解決事項
なし
EOF
run_post_set "$repo" "$run_dir"
assert_contains "$run_dir/verify-01-claimed-trackable.list" "staged_and_claimed.txt" "staged申告: claimed-trackable.list に staged 済みファイルが入るか"
assert_contains "$run_dir/verify-01-delta.list" "staged_and_claimed.txt" "staged申告: delta.list に staged 済みファイルが入るか（--cached union で post に現れるか）"
assert_empty "$run_dir/verify-01-phantom.list" "staged申告: phantom.list（git add 済みの正当な申告が PHANTOM 化していないか。R1 是正の中心検証）"
assert_empty "$run_dir/verify-01-undeclared.list" "staged申告: undeclared.list"

echo "--- fixture: pre-existing-staged（pir2 開始前から staged のファイルが delta に誤混入しないこと。pre/post 対称性の確認） ---"
repo="$(setup_scratch_repo pre_existing_staged)"
# pir2 開始（pre-set 記録）より前に、ユーザーが既に別ファイルを stage 済みという状況を再現する
printf 'user staged before pir2 start\n' > "$repo/pre_existing_staged.txt"
git -C "$repo" add pre_existing_staged.txt
run_dir="$repo/.ai-pir-runs/run1"
mkdir -p "$run_dir"
run_pre_set "$repo" "$run_dir"
# 実装 actor は pre_existing_staged.txt には触れず、別の実ファイルだけを変更・申告する
printf 'real change\n' > "$repo/real_change.txt"
cat > "$run_dir/implementation-01.md" <<'EOF'
## 実装完了レポート

### 変更ファイル一覧
- `real_change.txt` — 本当の変更

### 実装概要
fixture: pre-existing-staged scenario

### 注意点・未解決事項
なし
EOF
run_post_set "$repo" "$run_dir"
assert_contains "$run_dir/verify-01-delta.list" "real_change.txt" "pre-existing-staged: delta.list に本当の変更が入るか"
assert_not_contains_substr "$run_dir/verify-01-delta.list" "pre_existing_staged.txt" "pre-existing-staged: delta.list に開始前から staged 済みのファイルが誤混入していないか（pre/post 対称性の中心検証）"
assert_empty "$run_dir/verify-01-phantom.list" "pre-existing-staged: phantom.list（申告した real_change.txt が正しく検出されるか）"
assert_empty "$run_dir/verify-01-undeclared.list" "pre-existing-staged: undeclared.list（pre_existing_staged.txt が偽 UNDECLARED として現れていないか）"

echo ""
if (( FIXTURE_FAILURES > 0 )); then
  echo "NG: ${FIXTURE_FAILURES} fixture assertion(s) failed"
  exit 1
fi

echo "OK: 8 fixture scenarios (PHANTOM / UNDECLARED / NO_OP / 非ASCIIファイル名 / フェンス内例示 / サブモジュール / staged申告 / pre-existing-staged) all matched expected判定"
exit 0
