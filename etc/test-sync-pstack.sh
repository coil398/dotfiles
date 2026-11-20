#!/usr/bin/env bash
# sync-pstack.sh copies official pstack into Cursor's local plugin directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC="${SCRIPT_DIR}/sync-pstack.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/sync-pstack.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

fail=0
pass=0
ok() { echo "PASS: $*"; pass=$((pass + 1)); }
bad() { echo "FAIL: $*" >&2; fail=$((fail + 1)); }

git_repo() {
  repo="$1"
  shift
  git -C "$repo" -c core.hooksPath=/dev/null -c user.name=Fixture -c user.email=fixture@example.invalid "$@"
}

make_remote() {
  local remote="$1"
  mkdir -p "$remote/pstack/.cursor-plugin" "$remote/pstack/skills/poteto-mode" "$remote/other"
  printf '%s\n' '{' '  "name": "pstack"' '}' >"$remote/pstack/.cursor-plugin/plugin.json"
  printf '%s\n' 'upstream-v1' >"$remote/pstack/skills/poteto-mode/SKILL.md"
  printf '%s\n' 'other plugin' >"$remote/other/README.md"
  git init -q "$remote"
  git_repo "$remote" add pstack other
  git_repo "$remote" commit -qm seed
}

assert_file() {
  local label="$1" path="$2" expected="$3"
  if [ -f "$path" ] && [ "$(cat "$path")" = "$expected" ]; then
    ok "$label"
  else
    bad "$label (got $(cat "$path" 2>/dev/null || echo missing))"
  fi
}

REMOTE="$WORK/remote"
make_remote "$REMOTE"
HOME_A="$WORK/home-a"
mkdir -p "$HOME_A"
if HOME="$HOME_A" CURSOR_PLUGINS_DIR="$WORK/checkout-a" CURSOR_PLUGINS_REPO_URL="$REMOTE" \
  sh "$SYNC" >"$WORK/first.log" 2>&1; then
  ok "first run exits 0"
else
  bad "first run exits 0"
fi
assert_file "copies poteto-mode" \
  "$HOME_A/.cursor/plugins/local/pstack/skills/poteto-mode/SKILL.md" "upstream-v1"
assert_file "manifest name is pstack" \
  "$HOME_A/.cursor/plugins/local/pstack/.cursor-plugin/plugin.json" "$(printf '%s\n' '{' '  "name": "pstack"' '}')"
if [ ! -e "$HOME_A/.cursor/plugins/local/pstack/../other" ] && [ ! -d "$WORK/checkout-a/other" ]; then
  ok "sparse checkout omits other plugins"
else
  bad "sparse checkout omits other plugins"
fi
sha_a="$(git -C "$WORK/checkout-a" rev-parse HEAD)"
assert_file "marker records checkout sha" \
  "$HOME_A/.cursor/plugins/local/.pstack.dotfiles-managed" "$sha_a"
if grep -q 'installed path=' "$WORK/first.log"; then
  ok "first run logs install"
else
  bad "first run logs install"
fi

if HOME="$HOME_A" CURSOR_PLUGINS_DIR="$WORK/checkout-a" CURSOR_PLUGINS_REPO_URL="$REMOTE" \
  sh "$SYNC" >"$WORK/second.log" 2>&1; then
  ok "second run exits 0"
else
  bad "second run exits 0"
fi
if grep -q 'reason=already_current' "$WORK/second.log"; then
  ok "second run leaves the current copy"
else
  bad "second run leaves the current copy ($(cat "$WORK/second.log"))"
fi

printf '%s\n' 'upstream-v2' >"$REMOTE/pstack/skills/poteto-mode/SKILL.md"
git_repo "$REMOTE" add pstack/skills/poteto-mode/SKILL.md
git_repo "$REMOTE" commit -qm v2
if HOME="$HOME_A" CURSOR_PLUGINS_DIR="$WORK/checkout-a" CURSOR_PLUGINS_REPO_URL="$REMOTE" \
  sh "$SYNC" >"$WORK/update.log" 2>&1; then
  ok "update run exits 0"
else
  bad "update run exits 0"
fi
assert_file "fast-forward replaces the local copy" \
  "$HOME_A/.cursor/plugins/local/pstack/skills/poteto-mode/SKILL.md" "upstream-v2"

printf '%s\n' 'local edit' >"$WORK/checkout-a/pstack/skills/poteto-mode/SKILL.md"
printf '%s\n' 'upstream-v3' >"$REMOTE/pstack/skills/poteto-mode/SKILL.md"
git_repo "$REMOTE" add pstack/skills/poteto-mode/SKILL.md
git_repo "$REMOTE" commit -qm v3
if HOME="$HOME_A" CURSOR_PLUGINS_DIR="$WORK/checkout-a" CURSOR_PLUGINS_REPO_URL="$REMOTE" \
  sh "$SYNC" >"$WORK/dirty.log" 2>&1; then
  ok "dirty run exits 0"
else
  bad "dirty run exits 0"
fi
assert_file "dirty checkout is preserved" \
  "$WORK/checkout-a/pstack/skills/poteto-mode/SKILL.md" "local edit"
assert_file "dirty checkout does not replace the installed copy" \
  "$HOME_A/.cursor/plugins/local/pstack/skills/poteto-mode/SKILL.md" "upstream-v2"
if grep -q 'reason=dirty_checkout' "$WORK/dirty.log"; then
  ok "dirty run logs the skip"
else
  bad "dirty run logs the skip ($(cat "$WORK/dirty.log"))"
fi

mkdir -p "$HOME_A/.cursor/plugins/cache/example"
printf '%s\n' '{ "name": "pstack" }' >"$HOME_A/.cursor/plugins/cache/example/plugin.json"
if HOME="$HOME_A" CURSOR_PLUGINS_DIR="$WORK/checkout-a" CURSOR_PLUGINS_REPO_URL="$REMOTE" \
  sh "$SYNC" >"$WORK/market.log" 2>&1; then
  ok "marketplace run exits 0"
else
  bad "marketplace run exits 0"
fi
if [ ! -e "$HOME_A/.cursor/plugins/local/pstack" ] \
  && [ ! -e "$HOME_A/.cursor/plugins/local/.pstack.dotfiles-managed" ]; then
  ok "marketplace pstack removes the managed copy"
else
  bad "marketplace pstack removes the managed copy"
fi
if grep -q 'reason=marketplace_pstack_present' "$WORK/market.log"; then
  ok "marketplace run logs the skip"
else
  bad "marketplace run logs the skip"
fi

HOME_B="$WORK/home-b"
mkdir -p "$HOME_B/.cursor/plugins/local/pstack"
printf '%s\n' 'user copy' >"$HOME_B/.cursor/plugins/local/pstack/KEEP"
if HOME="$HOME_B" CURSOR_PLUGINS_DIR="$WORK/checkout-b" CURSOR_PLUGINS_REPO_URL="$REMOTE" \
  sh "$SYNC" >"$WORK/user.log" 2>&1; then
  ok "unmanaged run exits 0"
else
  bad "unmanaged run exits 0"
fi
assert_file "unmanaged local directory stays" \
  "$HOME_B/.cursor/plugins/local/pstack/KEEP" "user copy"

HOME_C="$WORK/home-c"
mkdir -p "$HOME_C"
if HOME="$HOME_C" CURSOR_PLUGINS_DIR="$WORK/checkout-c" CURSOR_PLUGINS_REPO_URL="$WORK/missing-remote" \
  sh "$SYNC" >"$WORK/missing.log" 2>&1; then
  ok "missing remote exits 0"
else
  bad "missing remote exits 0"
fi
if [ ! -e "$WORK/checkout-c" ] && [ ! -e "$HOME_C/.cursor/plugins/local/pstack" ]; then
  ok "missing remote leaves no checkout or copy"
else
  bad "missing remote leaves no checkout or copy"
fi

echo "sync-pstack tests: ${pass} passed, ${fail} failed"
[ "$fail" -eq 0 ]
