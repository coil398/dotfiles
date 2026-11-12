#!/usr/bin/env bash
# Verify init propagates required setup failures while optional sync failures continue.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_SCRIPT="${SCRIPT_DIR}/init.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/init-contracts.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

fail=0
pass=0

ok() { echo "PASS: $*"; pass=$((pass + 1)); }
bad() { echo "FAIL: $*" >&2; fail=$((fail + 1)); }

make_fixture() {
  local name="$1" private_status="$2" homebrew_status="$3" set_status="$4" link_status="$5" mcp_status="$6"
  local root="${WORK}/${name}/dotfiles"
  mkdir -p "${root}/etc/install/homebrew" "${WORK}/${name}/home"
  cat >"${root}/etc/sync-private-skills.sh" <<'SH'
#!/bin/sh
printf 'private\n' >>"$INIT_CALLS"
exit "$PRIVATE_STATUS"
SH
  cat >"${root}/etc/install/homebrew/install.sh" <<'SH'
#!/bin/sh
printf 'homebrew\n' >>"$INIT_CALLS"
exit "$HOMEBREW_STATUS"
SH
  cat >"${root}/etc/set.sh" <<'SH'
#!/bin/sh
printf 'set\n' >>"$INIT_CALLS"
exit "$SET_STATUS"
SH
  cat >"${root}/etc/link.sh" <<'SH'
#!/bin/sh
printf 'link\n' >>"$INIT_CALLS"
exit "$LINK_STATUS"
SH
  cat >"${root}/etc/sync-mcp.sh" <<'SH'
#!/bin/sh
printf 'mcp\n' >>"$INIT_CALLS"
exit "$MCP_STATUS"
SH
  chmod +x "${root}/etc/sync-private-skills.sh" \
    "${root}/etc/install/homebrew/install.sh" "${root}/etc/set.sh" \
    "${root}/etc/link.sh" "${root}/etc/sync-mcp.sh"
  printf '%s\n' "$root"
}

run_case() {
  local name="$1" private_status="$2" homebrew_status="$3" set_status="$4" link_status="$5" mcp_status="$6"
  local expected_status="$7" expected_calls="$8" expected_message="$9"
  local root calls output actual_status actual_calls
  root="$(make_fixture "$name" "$private_status" "$homebrew_status" "$set_status" "$link_status" "$mcp_status")"
  calls="${WORK}/${name}/calls.log"
  output="${WORK}/${name}/output.log"
  if HOME="${WORK}/${name}/home" DOTFILES_DIR="$root" \
    PRIVATE_SKILLS_DIR="${WORK}/${name}/private-skills" INIT_CALLS="$calls" \
    PRIVATE_STATUS="$private_status" HOMEBREW_STATUS="$homebrew_status" \
    SET_STATUS="$set_status" LINK_STATUS="$link_status" MCP_STATUS="$mcp_status" \
    sh "$INIT_SCRIPT" >"$output" 2>&1; then
    actual_status=0
  else
    actual_status=$?
  fi
  if [ -f "$calls" ]; then
    actual_calls="$(cat "$calls")"
  else
    actual_calls="<missing call log>"
  fi
  if [ "$actual_status" = "$expected_status" ] && [ "$actual_calls" = "$expected_calls" ] \
    && { [ -z "$expected_message" ] || grep -Fq "$expected_message" "$output"; }; then
    ok "$name (exit=$actual_status calls=$(printf '%s' "$actual_calls" | tr '\n' ','))"
  else
    bad "$name (exit=$actual_status calls=$(printf '%s' "$actual_calls" | tr '\n' ',') output=$(cat "$output"))"
  fi
}

run_case "homebrew-failure" 0 23 0 0 0 23 "private
homebrew" "homebrew installation failed: exit 23"
run_case "settings-failure" 0 0 24 0 0 24 "private
homebrew
set" "settings setup failed: exit 24"
run_case "link-failure" 0 0 0 25 0 25 "private
homebrew
set
link" "dotfile linking failed: exit 25"
run_case "successful-setup" 0 0 0 0 0 0 "private
homebrew
set
link
mcp" ""
run_case "optional-private-failure" 31 0 0 0 0 0 "private
homebrew
set
link
mcp" "private acquisition failed"
run_case "optional-mcp-failure" 0 0 0 0 32 0 "private
homebrew
set
link
mcp" "MCP sync failed: optional"

echo "init contract tests: ${pass} passed, ${fail} failed"
[ "$fail" -eq 0 ]
