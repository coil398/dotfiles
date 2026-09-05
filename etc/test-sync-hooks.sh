#!/usr/bin/env bash
# Isolated fixture tests for the Claude PostToolUse sync hooks.
#
# The fixture copies the hook scripts and supplies fake sync producers.  The
# real HOME, etc/sync-*.sh, repositories, and generated runtime files are
# never used or modified.

set -euo pipefail

TEST_SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
DOT_DIR="$(cd -P "${TEST_SCRIPT_DIR}/.." && pwd -P)"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/sync-hooks-test.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_contains() {
  local value="$1"
  local expected="$2"
  case "$value" in
    *"$expected"*) ;;
    *) fail "expected output to contain: $expected" ;;
  esac
}

assert_empty() {
  [ -z "$1" ] || fail "expected empty output, got: $1"
}

assert_hook_json() {
  local output="$1"
  printf '%s' "$output" | jq -e '
    type == "object" and
    .hookSpecificOutput.hookEventName == "PostToolUse" and
    (.hookSpecificOutput.additionalContext | type == "string")
  ' >/dev/null || fail "hook output was not PostToolUse additionalContext JSON: $output"
}

make_fake_producer() {
  local path="$1"
  local label="$2"
  cat > "$path" <<PRODUCER
#!/usr/bin/env bash
if [[ "\${FAKE_SYNC_RESULT:-success}" == "failure" ]]; then
  printf '%s producer stdout\n' '$label'
  printf '%s producer stderr\n' '$label' >&2
  exit 23
fi
printf '%s producer stdout\n' '$label'
PRODUCER
  chmod +x "$path"
}

run_hook() {
  local hook="$1"
  local path="$2"
  local result="$3"
  local payload
  local output
  local status

  payload="$(jq -nc --arg path "$path" '{tool_input: {file_path: $path}}')"
  set +e
  output="$(printf '%s\n' "$payload" | HOME="$TEST_ROOT/home" FAKE_SYNC_RESULT="$result" bash "$hook")"
  status=$?
  set -e
  [ "$status" -eq 0 ] || fail "hook returned $status: $hook"
  printf '%s' "$output"
}

command -v jq >/dev/null 2>&1 || fail 'jq is required for hook JSON tests'
mkdir -p "$TEST_ROOT/.claude/lib" "$TEST_ROOT/.codex" "$TEST_ROOT/.agents/skills/example" "$TEST_ROOT/etc" "$TEST_ROOT/home"
cp -p "$DOT_DIR/.claude/lib/sync-codex-hook.sh" "$TEST_ROOT/.claude/lib/sync-codex-hook.sh"
cp -p "$DOT_DIR/.claude/lib/sync-opencode-hook.sh" "$TEST_ROOT/.claude/lib/sync-opencode-hook.sh"
make_fake_producer "$TEST_ROOT/etc/sync-codex.sh" codex
make_fake_producer "$TEST_ROOT/etc/sync-opencode.sh" opencode

test_output="$(run_hook \
  "$TEST_ROOT/.claude/lib/sync-codex-hook.sh" \
  "$TEST_ROOT/AGENTS.md" success)"
assert_hook_json "$test_output"
test_context="$(printf '%s' "$test_output" | jq -r '.hookSpecificOutput.additionalContext')"
assert_contains "$test_context" '[codex-hook] sync completed:'
assert_contains "$test_context" 'codex producer stdout'

# The native Codex supplement is a generated-config source and must trigger
# the Codex producer just like the base config.
test_output="$(run_hook \
  "$TEST_ROOT/.claude/lib/sync-codex-hook.sh" \
  "$TEST_ROOT/.codex/codex-native-supplement.md" failure)"
assert_hook_json "$test_output"
test_context="$(printf '%s' "$test_output" | jq -r '.hookSpecificOutput.additionalContext')"
assert_contains "$test_context" '[codex-hook] sync failed (exit 23):'
assert_contains "$test_context" 'codex producer stdout'
assert_contains "$test_context" 'codex producer stderr'

# OpenCode success and failure both use the formal hook output contract.
test_output="$(run_hook \
  "$TEST_ROOT/.claude/lib/sync-opencode-hook.sh" \
  "$TEST_ROOT/.agents/skills/example/SKILL.md" success)"
assert_hook_json "$test_output"
test_context="$(printf '%s' "$test_output" | jq -r '.hookSpecificOutput.additionalContext')"
assert_contains "$test_context" '[opencode-hook] sync completed:'
assert_contains "$test_context" 'opencode producer stdout'

test_output="$(run_hook \
  "$TEST_ROOT/.claude/lib/sync-opencode-hook.sh" \
  "$TEST_ROOT/.claude/settings.json" failure)"
assert_hook_json "$test_output"
test_context="$(printf '%s' "$test_output" | jq -r '.hookSpecificOutput.additionalContext')"
assert_contains "$test_context" '[opencode-hook] sync failed (exit 23):'
assert_contains "$test_context" 'opencode producer stderr'

# Non-SSOT edits must remain an early no-op and must not invoke a producer.
test_output="$(run_hook \
  "$TEST_ROOT/.claude/lib/sync-codex-hook.sh" \
  "$TEST_ROOT/README.md" failure)"
assert_empty "$test_output"

echo 'PASS: sync hooks expose producer success/failure through PostToolUse additionalContext without touching real HOME'
