#!/usr/bin/env bash
# Codex seed / inventory contracts (missing-only overlays).
#
#   bash etc/test-codex-contracts.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

fail=0
pass=0
ok() { echo "PASS: $*"; pass=$((pass + 1)); }
bad() { echo "FAIL: $*"; fail=$((fail + 1)); }

assert_file() {
  if [ -f "$1" ]; then ok "exists $1"; else bad "missing $1"; fi
}
assert_dir() {
  if [ -d "$1" ]; then ok "exists $1"; else bad "missing $1"; fi
}

assert_file "${DOT_DIR}/etc/seed-codex-overlay.sh"
assert_dir "${DOT_DIR}/.codex/agents"
assert_dir "${DOT_DIR}/.codex/skills"

for a in deliberator epic-planner gate hypothesizer synthesizer thinker explorer planner; do
  assert_file "${DOT_DIR}/.codex/agents/${a}.toml"
done

# codex-runner must stay absent on Codex
if [ -f "${DOT_DIR}/.codex/agents/codex-runner.toml" ]; then
  bad "codex-runner.toml must not exist on Codex"
else
  ok "codex-runner omitted on Codex"
fi

for s in deepthink research epic unity-mcp-skill pir2; do
  assert_file "${DOT_DIR}/.codex/skills/${s}/SKILL.md"
done

# seed is non-destructive
before="$(cksum "${DOT_DIR}/.codex/agents/explorer.toml" | awk '{print $1" "$2}')"
bash "${DOT_DIR}/etc/seed-codex-overlay.sh" >/dev/null
after="$(cksum "${DOT_DIR}/.codex/agents/explorer.toml" | awk '{print $1" "$2}')"
if [ "$before" = "$after" ]; then
  ok "seed does not overwrite explorer.toml"
else
  bad "seed mutated explorer.toml"
fi

# drift checker clean
if bash "${DOT_DIR}/etc/check-shared-drift.sh" >/dev/null; then
  ok "check-shared-drift clean"
else
  bad "check-shared-drift failed"
fi

echo
echo "codex contracts: ${pass} passed, ${fail} failed"
[ "$fail" -eq 0 ]
