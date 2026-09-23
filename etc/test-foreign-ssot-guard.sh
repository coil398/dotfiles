#!/usr/bin/env bash
# Focused fixtures for foreign-ssot-guard project identity and cache refresh.

set -euo pipefail

TEST_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
GUARD_SOURCE="$TEST_DIR/.claude/hooks/foreign-ssot-guard.sh"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/foreign-ssot-guard-test.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

prepare_repo() {
  local repo="$1"
  local origin="$2"
  local staged_text="$3"
  mkdir -p "$repo/.claude/hooks"
  git -C "$repo" init -q
  if [ -n "$origin" ]; then
    git -C "$repo" remote add origin "$origin"
  fi
  cp "$GUARD_SOURCE" "$repo/.claude/hooks/foreign-ssot-guard.sh"
  chmod +x "$repo/.claude/hooks/foreign-ssot-guard.sh"
  printf '%s\n' "$staged_text" > "$repo/AGENTS.md"
  git -C "$repo" add AGENTS.md
}

add_session() {
  local home="$1"
  local session_name="$2"
  local cwd="$3"
  local session_dir="$home/.claude/projects/$session_name"
  mkdir -p "$session_dir"
  jq -nc --arg cwd "$cwd" '{cwd: $cwd}' > "$session_dir/session.jsonl"
}

invoke_guard() {
  local home="$1"
  local repo="$2"
  RUN_OUTPUT=""
  if RUN_OUTPUT="$(cd "$repo" && HOME="$home" bash "$repo/.claude/hooks/foreign-ssot-guard.sh" 2>&1)"; then
    RUN_STATUS=0
  else
    RUN_STATUS=$?
  fi
}

assert_cache_has() {
  local cache="$1"
  local token="$2"
  grep -Fqx -- "$token" "$cache" || fail "expected identity token in generated cache: $token"
}

assert_cache_lacks() {
  local cache="$1"
  local token="$2"
  if grep -Fqx -- "$token" "$cache"; then
    fail "unexpected checkout/path alias in generated cache: $token"
  fi
}

set_mtime_after() {
  local target="$1"
  local reference="$2"
  python3 - "$target" "$reference" <<'PY'
import os
import sys

target, reference = sys.argv[1:]
mtime = os.stat(reference).st_mtime + 5
os.utime(target, (mtime, mtime))
PY
}

command -v jq >/dev/null 2>&1 || fail 'jq is required'

# A cwd in a repo subdirectory resolves to its origin identity, not the
# incidental directory name. The real foreign project token still blocks.
REMOTE_HOME="$TEST_ROOT/remote-home"
REMOTE_CURRENT="$TEST_ROOT/remote-current"
REMOTE_SOURCE="$TEST_ROOT/foreign-checkout"
prepare_repo "$REMOTE_CURRENT" "" "foreign-project mention"
prepare_repo "$REMOTE_SOURCE" "https://github.com/acme/foreign-project.git" "foreign-project mention"
mkdir -p "$REMOTE_SOURCE/services/api"
add_session "$REMOTE_HOME" remote-session "$REMOTE_SOURCE/services/api"
invoke_guard "$REMOTE_HOME" "$REMOTE_CURRENT"
[ "$RUN_STATUS" -eq 2 ] || fail 'valid foreign origin slug did not block an SSOT addition'
case "$RUN_OUTPUT" in
  *"detected tokens"*"foreign-project"*) ;;
  *) fail 'block output did not identify the foreign repo token' ;;
esac
assert_cache_has "$REMOTE_CURRENT/.claude/hooks/foreign-names.cache" acme
assert_cache_has "$REMOTE_CURRENT/.claude/hooks/foreign-names.cache" foreign-project
assert_cache_lacks "$REMOTE_CURRENT/.claude/hooks/foreign-names.cache" api

# A local checkout directory named api is not a project identity when its
# valid origin identifies another repository. Updating the guard must rebuild
# an already-populated cache so that the stale basename disappears.
ALIAS_HOME="$TEST_ROOT/alias-home"
ALIAS_CURRENT="$TEST_ROOT/alias-current"
ALIAS_SOURCE="$TEST_ROOT/api"
prepare_repo "$ALIAS_CURRENT" "" "api endpoint documentation"
prepare_repo "$ALIAS_SOURCE" "git@github.com:acme/real-project.git" "source repository"
add_session "$ALIAS_HOME" alias-session "$ALIAS_SOURCE"
ALIAS_CACHE="$ALIAS_CURRENT/.claude/hooks/foreign-names.cache"
printf 'api\n' > "$ALIAS_CACHE"
python3 - "$ALIAS_CURRENT/.claude/hooks/foreign-ssot-guard.sh" "$ALIAS_CACHE" <<'PY'
import os
import sys

script, cache = sys.argv[1:]
cache_time = os.stat(cache).st_mtime
os.utime(script, (cache_time + 5, cache_time + 5))
PY
invoke_guard "$ALIAS_HOME" "$ALIAS_CURRENT"
[ "$RUN_STATUS" -eq 0 ] || fail 'stale api token remained after the guard source changed'
assert_cache_has "$ALIAS_CACHE" acme
assert_cache_has "$ALIAS_CACHE" real-project
assert_cache_lacks "$ALIAS_CACHE" api

# A changed Claude session cwd refreshes the cache too, removing an identity
# that no longer appears in the current session source.
SOURCE_HOME="$TEST_ROOT/source-home"
SOURCE_CURRENT="$TEST_ROOT/source-current"
SOURCE_OLD="$TEST_ROOT/previous-local-project"
SOURCE_NEW="$TEST_ROOT/new-checkout"
prepare_repo "$SOURCE_CURRENT" "" "neutral guidance"
prepare_repo "$SOURCE_OLD" "" "old local source"
prepare_repo "$SOURCE_NEW" "https://github.com/acme/current-project.git" "new source"
add_session "$SOURCE_HOME" changing-session "$SOURCE_OLD"
SOURCE_JSONL="$SOURCE_HOME/.claude/projects/changing-session/session.jsonl"
invoke_guard "$SOURCE_HOME" "$SOURCE_CURRENT"
[ "$RUN_STATUS" -eq 0 ] || fail 'neutral SSOT text unexpectedly blocked during cache setup'
SOURCE_CACHE="$SOURCE_CURRENT/.claude/hooks/foreign-names.cache"
assert_cache_has "$SOURCE_CACHE" previous-local-project
jq -nc --arg cwd "$SOURCE_NEW" '{cwd: $cwd}' > "$SOURCE_JSONL"
set_mtime_after "$SOURCE_JSONL" "$SOURCE_CACHE"
invoke_guard "$SOURCE_HOME" "$SOURCE_CURRENT"
[ "$RUN_STATUS" -eq 0 ] || fail 'neutral SSOT text unexpectedly blocked after session source update'
assert_cache_has "$SOURCE_CACHE" acme
assert_cache_has "$SOURCE_CACHE" current-project
assert_cache_lacks "$SOURCE_CACHE" previous-local-project

# Without a valid origin, use the canonical Git root basename, not a nested
# cwd directory. This keeps local foreign projects identifiable.
LOCAL_HOME="$TEST_ROOT/local-home"
LOCAL_CURRENT="$TEST_ROOT/local-current"
LOCAL_SOURCE="$TEST_ROOT/foreign-local-project"
prepare_repo "$LOCAL_CURRENT" "" "foreign-local-project note"
prepare_repo "$LOCAL_SOURCE" "" "local source"
mkdir -p "$LOCAL_SOURCE/packages/api"
add_session "$LOCAL_HOME" local-session "$LOCAL_SOURCE/packages/api"
invoke_guard "$LOCAL_HOME" "$LOCAL_CURRENT"
[ "$RUN_STATUS" -eq 2 ] || fail 'origin-less foreign Git root basename was not detected'
assert_cache_has "$LOCAL_CURRENT/.claude/hooks/foreign-names.cache" foreign-local-project
assert_cache_lacks "$LOCAL_CURRENT/.claude/hooks/foreign-names.cache" api

# Non-repository working directories do not supply a stable project identity.
NONREPO_HOME="$TEST_ROOT/nonrepo-home"
NONREPO_CURRENT="$TEST_ROOT/nonrepo-current"
NONREPO_CWD="$TEST_ROOT/nonrepo-api"
prepare_repo "$NONREPO_CURRENT" "" "api endpoint note"
mkdir -p "$NONREPO_CWD"
add_session "$NONREPO_HOME" nonrepo-session "$NONREPO_CWD"
invoke_guard "$NONREPO_HOME" "$NONREPO_CURRENT"
[ "$RUN_STATUS" -eq 0 ] || fail 'non-repository cwd basename was treated as a project token'
assert_cache_lacks "$NONREPO_CURRENT/.claude/hooks/foreign-names.cache" api


# Current origin owner/repository remain excluded from foreign identities.
SELF_HOME="$TEST_ROOT/self-home"
SELF_CURRENT="$TEST_ROOT/self-current"
prepare_repo "$SELF_CURRENT" "https://github.com/self/current-project.git" "self current-project guidance"
add_session "$SELF_HOME" self-session "$SELF_CURRENT"
invoke_guard "$SELF_HOME" "$SELF_CURRENT"
[ "$RUN_STATUS" -eq 0 ] || fail 'the current origin identity was treated as foreign'
assert_cache_lacks "$SELF_CURRENT/.claude/hooks/foreign-names.cache" self
assert_cache_lacks "$SELF_CURRENT/.claude/hooks/foreign-names.cache" current-project

echo 'PASS: foreign-ssot-guard uses canonical Git identity and refreshes stale cache'
