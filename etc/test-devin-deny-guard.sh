#!/usr/bin/env bash
# Isolated fixture tests for the Devin PreToolUse deny guard
# (etc/devin-deny-guard.py).
#
# The fixture points DEVIN_CONFIG / DEVIN_PROJECT_DIR at a temp dir and feeds
# hook payloads on stdin.  The real ~/.config/devin and any project config
# are never read or modified.

set -euo pipefail

TEST_SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
GUARD="${TEST_SCRIPT_DIR}/devin-deny-guard.py"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/devin-deny-guard-test.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

USER_CONFIG="${TEST_ROOT}/config.json"
PROJ_DIR="${TEST_ROOT}/proj"
mkdir -p "$PROJ_DIR/.devin"

cat > "$USER_CONFIG" <<'JSON'
{
  "permissions": {
    "deny": [
      "Exec(rm -rf)",
      "Exec(sudo)",
      "Exec(su)",
      "Exec(git push --force)",
      "Exec(git reset --hard)",
      "Read(**/node_modules/**)",
      "Read(**/*.lock)",
      "Write(**/secrets/**)",
      "Fetch(domain:evil.example)",
      "mcp__dangerous*",
      "browser_preview"
    ]
  }
}
JSON

cat > "$PROJ_DIR/.devin/config.json" <<'JSON'
{"permissions": {"deny": ["Exec(proj-only-deny)"]}}
JSON

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

run_guard() {
  # stdin payload → guard output (env pins the fixture config/project)
  DEVIN_CONFIG="$USER_CONFIG" DEVIN_PROJECT_DIR="$PROJ_DIR" \
    python3 "$GUARD" <<<"$1"
}

assert_block() {
  local payload="$1" label="$2" out
  out="$(run_guard "$payload")"
  printf '%s' "$out" | jq -e '
    type == "object" and
    .decision == "block" and
    (.reason | type == "string" and length > 0)
  ' >/dev/null || fail "${label}: expected block JSON, got: ${out}"
}

assert_allow() {
  local payload="$1" label="$2" out
  out="$(run_guard "$payload")"
  [ -z "$out" ] || fail "${label}: expected silent allow, got: ${out}"
}

# --- Exec matching (prefix + word boundary) ---
assert_block '{"tool_name":"exec","tool_input":{"command":"rm -rf /tmp/x"}}' 'rm -rf'
assert_block '{"tool_name":"exec","tool_input":{"command":"sudo apt update"}}' 'sudo prefix'
assert_block '{"tool_name":"exec","tool_input":{"command":"su"}}' 'su exact'
assert_block '{"tool_name":"exec","tool_input":{"command":"git push --force origin main"}}' 'git push --force'
assert_block '{"tool_name":"exec","tool_input":{"command":"git reset --hard HEAD~1"}}' 'git reset --hard'
assert_block '{"tool_name":"exec","tool_input":{"command":"  rm -rf /tmp/x"}}' 'leading whitespace'
assert_allow '{"tool_name":"exec","tool_input":{"command":"ls"}}' 'ls'
assert_allow '{"tool_name":"exec","tool_input":{"command":"rm file.txt"}}' 'plain rm'
assert_allow '{"tool_name":"exec","tool_input":{"command":"sudoer-tool --help"}}' 'word boundary sudo'
assert_allow '{"tool_name":"exec","tool_input":{"command":"git push --force-with-lease origin main"}}' 'force-with-lease'
assert_allow '{"tool_name":"exec","tool_input":{"command":"git status"}}' 'git status'

# --- Exec path args vs Read/Write globs ---
assert_block '{"tool_name":"exec","tool_input":{"command":"cat node_modules/x/index.js"}}' 'exec path in node_modules'
assert_block '{"tool_name":"exec","tool_input":{"command":"ls /repo/node_modules"}}' 'exec denied dir itself'
assert_block '{"tool_name":"exec","tool_input":{"command":"cat ./x.lock"}}' 'exec relative *.lock'
assert_block '{"tool_name":"exec","tool_input":{"command":"echo hi > secrets/token.txt"}}' 'exec redirect into Write deny'
assert_allow '{"tool_name":"exec","tool_input":{"command":"ls /repo/src"}}' 'exec normal path'
assert_allow '{"tool_name":"exec","tool_input":{"command":"echo node_modules"}}' 'bare word is not a dir fallback'
assert_allow '{"tool_name":"exec","tool_input":{"command":"npm run build"}}' 'bare script name no dir fallback'

# --- Non-exec rule kinds ---
assert_block '{"tool_name":"read","tool_input":{"file_path":"/repo/node_modules/x/index.js"}}' 'Read glob'
assert_block '{"tool_name":"read","tool_input":{"file_path":"/repo/yarn.lock"}}' 'Read *.lock'
assert_allow '{"tool_name":"read","tool_input":{"file_path":"/repo/src/index.js"}}' 'read normal file'
assert_block '{"tool_name":"write","tool_input":{"file_path":"/repo/secrets/token.txt"}}' 'Write glob'
assert_allow '{"tool_name":"edit","tool_input":{"file_path":"/repo/src/a.ts"}}' 'edit normal file'
assert_block '{"tool_name":"webfetch","tool_input":{"url":"https://evil.example/x"}}' 'Fetch domain:'
assert_allow '{"tool_name":"webfetch","tool_input":{"url":"https://example.com/"}}' 'fetch normal url'
assert_block '{"tool_name":"mcp__dangerous__rm","tool_input":{}}' 'mcp__ prefix'
assert_block '{"tool_name":"browser_preview","tool_input":{"url":"http://x"}}' 'bare tool name'
assert_block '{"tool_name":"exec","tool_input":{"command":"proj-only-deny --now"}}' 'project config Exec'

# --- Robustness: never blocks on bad input ---
assert_allow 'not json' 'malformed stdin'
assert_allow '{"tool_name":"exec"}' 'missing tool_input'
assert_allow '{}' 'empty payload'
out="$(DEVIN_CONFIG="${TEST_ROOT}/nonexistent.json" DEVIN_PROJECT_DIR="" \
  python3 "$GUARD" <<<'{"tool_name":"exec","tool_input":{"command":"rm -rf /x"}}')"
[ -z "$out" ] || fail "missing config should stay silent, got: ${out}"

printf 'PASS: devin-deny-guard blocks deny-matched calls with reason and stays silent otherwise\n'
