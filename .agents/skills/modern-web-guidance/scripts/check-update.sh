#!/usr/bin/env bash
# modern-web-guidance の固定版を確かめ、新しい版へ上げるための補助script。
#   引数なし      : 固定中の版と npm の最新版を比べ、差分を出力する (最新なら 0、更新あり 10)
#   --apply <版>  : 指定版を取得し、固定版の書き換えを当てて原本を置き換える
# 環境変数 MWG_SKILL_DIR で対象のスキルディレクトリを上書きできる。
# CLI (modern-web.mjs) は実行しない。npm view / npm pack だけを使う。
set -euo pipefail

PKG="modern-web-guidance"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="${MWG_SKILL_DIR:-$(dirname "$SCRIPT_DIR")}"
SKILL_MD="$SKILL_DIR/SKILL.md"
VERSION_RE='^[0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.+-]+)?$'
# 外部通信・プロセス起動・書き込み・利用統計に関わる語
RISK_RE='fetch\(|https?://|XMLHttpRequest|WebSocket|child_process|spawn|exec(Sync|File)?\(|writeFile|appendFile|mkdir|rmSync|unlink|homedir|clearcut|telemetry|DISABLE_TELEMETRY|process\.env'

die() { echo "エラー: $*" >&2; exit 1; }

pinned_version() {
  local v
  v="$(grep -m1 'Pinned version' "$SKILL_MD" | grep -oE "$PKG@[0-9][^\` ]*" | head -1 | cut -d@ -f2 || true)"
  [ -n "$v" ] || die "$SKILL_MD から固定中の版を読めません (Pinned version 行が無い)"
  [[ "$v" =~ $VERSION_RE ]] || die "固定中の版が不正です: $v"
  printf '%s\n' "$v"
}

# fetch_pkg <版> <展開先>: npm pack で取得して <展開先>/package に展開する
fetch_pkg() {
  local ver="$1" dest="$2"
  mkdir -p "$dest"
  ( cd "$dest" && npm pack "$PKG@$ver" --ignore-scripts --silent >/dev/null 2>"$dest/.npm-err" ) || return 1
  tar xzf "$dest"/*.tgz -C "$dest" || return 1
  [ -d "$dest/package/skills/$PKG" ] || return 1
}

risk_lines() {
  local root="$1" f
  for f in modern-web.mjs watchdog/main.js legacy-scan.mjs search.mjs; do
    echo "## $f"
    if [ -f "$root/skills/$PKG/$f" ]; then
      # 圧縮された長大な行があるため、一致箇所の前後60文字だけを取り出す
      grep -oiE ".{0,60}($RISK_RE).{0,60}" "$root/skills/$PKG/$f" | sort -u || true
    else
      echo "(ファイルなし)"
    fi
  done
}

if [ "${1:-}" = "--apply" ]; then
  [ $# -eq 2 ] || die "使い方: check-update.sh --apply <版>"
  NEW="$2"
  [[ "$NEW" =~ $VERSION_RE ]] || die "版の形式が不正です: $NEW"
  [ -d "$SKILL_DIR" ] || die "スキルディレクトリがありません: $SKILL_DIR"
  W="$(mktemp -d)"
  trap 'rm -rf "$W"' EXIT
  fetch_pkg "$NEW" "$W/new" || die "$PKG@$NEW を取得できません: $(cat "$W/new/.npm-err" 2>/dev/null || true)"
  SRC="$W/new/package/skills/$PKG"
  for f in SKILL.md skill-version.txt; do [ -f "$SRC/$f" ] || die "$f が配布物にありません"; done
  [ -f "$W/new/package/LICENSE" ] || die "LICENSE が配布物にありません"
  SV="$(tr -d '[:space:]' < "$SRC/skill-version.txt")"
  [ -n "$SV" ] || die "skill-version.txt が空です"

  PIN_LINE="- **Pinned version**: Always run \`$PKG@$NEW\` with \`DISABLE_TELEMETRY=1\`. Do not use \`@latest\`, another version, or the \`install\` / \`update\` commands."
  # 書き換え 1, 2: 起動コマンドを固定版 + 利用統計停止へ。--skill-version は新版の値へ揃える
  # 書き換え 3: Runner & Permissions 行の直前に Pinned version 行を挿入
  sed -E \
    -e "s#npx -y $PKG@latest#DISABLE_TELEMETRY=1 npx -y $PKG@$NEW#g" \
    -e "s#pnpx $PKG@latest#DISABLE_TELEMETRY=1 pnpx $PKG@$NEW#g" \
    -e "s#--skill-version [0-9A-Za-z_-]+#--skill-version $SV#g" \
    "$SRC/SKILL.md" \
    | awk -v pin="$PIN_LINE" '
        /^- \*\*Runner & Permissions\*\*:/ && !done { print pin; done=1 }
        { print }
        END { if (!done) exit 3 }
      ' > "$W/SKILL.md.new" || die "挿入先 (Runner & Permissions 行) が見つかりません。原本は変更していません"

  # 検査
  # Pinned version 行は注意書きとして @latest を含むので除いて調べる
  ! grep -vF 'Pinned version' "$W/SKILL.md.new" | grep -qF '@latest' \
    || { grep -vF 'Pinned version' "$W/SKILL.md.new" | grep -nF '@latest' >&2; die "@latest が残っています。原本は変更していません"; }
  grep -qF "DISABLE_TELEMETRY=1 npx -y $PKG@$NEW" "$W/SKILL.md.new" \
    || die "固定した npx コマンドが含まれません。原本は変更していません"
  [ "$(grep -cF 'Pinned version' "$W/SKILL.md.new")" = 1 ] \
    || die "Pinned version 行が1つではありません。原本は変更していません"
  others="$(grep -oE "$PKG@[^ \`\"')]+" "$W/SKILL.md.new" | grep -vxF "$PKG@$NEW" || true)"
  [ -z "$others" ] || die "固定版以外の版指定が残っています: $others"

  # 一時ファイルに書いてから置き換える
  cp "$W/SKILL.md.new" "$SKILL_DIR/.SKILL.md.tmp.$$"
  cp "$SRC/skill-version.txt" "$SKILL_DIR/.skill-version.txt.tmp.$$"
  cp "$W/new/package/LICENSE" "$SKILL_DIR/.LICENSE.tmp.$$"
  mv "$SKILL_DIR/.SKILL.md.tmp.$$" "$SKILL_MD"
  mv "$SKILL_DIR/.skill-version.txt.tmp.$$" "$SKILL_DIR/skill-version.txt"
  mv "$SKILL_DIR/.LICENSE.tmp.$$" "$SKILL_DIR/LICENSE"
  echo "MWG_APPLIED:$NEW (skill-version $SV)"
  exit 0
fi

[ $# -eq 0 ] || die "使い方: check-update.sh [--apply <版>]"
[ -f "$SKILL_MD" ] || die "$SKILL_MD がありません"
OLD="$(pinned_version)"
NEW="$(npm view "$PKG" version 2>/dev/null)" || die "npm view に失敗しました"
[[ "$NEW" =~ $VERSION_RE ]] || die "npm の最新版の形式が不正です: $NEW"

if [ "$OLD" = "$NEW" ]; then
  echo "MWG_UP_TO_DATE:$OLD"
  exit 0
fi

# 作業ディレクトリは人が読めるよう残す
W="$(mktemp -d "${TMPDIR:-/tmp}/mwg-check.XXXXXX")"
fetch_pkg "$NEW" "$W/new" || die "$PKG@$NEW を取得できません: $(cat "$W/new/.npm-err" 2>/dev/null || true)"
OLD_OK=1
fetch_pkg "$OLD" "$W/old" || OLD_OK=0

echo "MWG_UPDATE_AVAILABLE:$OLD->$NEW"
echo
if [ "$OLD_OK" = 1 ]; then
  echo "=== 変更ファイル (diff -rq) ==="
  diff -rq "$W/old/package" "$W/new/package" || true
  echo
  echo "=== SKILL.md の差分 ==="
  diff -u "$W/old/package/skills/$PKG/SKILL.md" "$W/new/package/skills/$PKG/SKILL.md" || true
  echo
  echo "=== 外部通信・プロセス起動・書き込み・利用統計に関わる行の差分 (旧 -> 新) ==="
  risk_lines "$W/old/package" > "$W/risk-old.txt"
  risk_lines "$W/new/package" > "$W/risk-new.txt"
  diff -u "$W/risk-old.txt" "$W/risk-new.txt" || true
else
  echo "=== 旧版 $OLD を取得できないため、旧版との比較はできません ==="
  echo
  echo "=== 新版 $NEW の外部通信・プロセス起動・書き込み・利用統計に関わる行 ==="
  risk_lines "$W/new/package" | tee "$W/risk-new.txt"
fi
echo
echo "作業ディレクトリ: $W"
exit 10
