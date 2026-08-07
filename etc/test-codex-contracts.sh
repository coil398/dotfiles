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
assert_executable() {
  if [ -x "$1" ]; then ok "executable $1"; else bad "not executable $1"; fi
}
assert_contains() {
  local file="$1" needle="$2"
  if grep -Fq -- "$needle" "$file"; then
    ok "${file#"$DOT_DIR/"} contains ${needle}"
  else
    bad "${file#"$DOT_DIR/"} missing ${needle}"
  fi
}
assert_not_contains() {
  local file="$1" needle="$2"
  if grep -Fq -- "$needle" "$file"; then
    bad "${file#"$DOT_DIR/"} must not contain ${needle}"
  else
    ok "${file#"$DOT_DIR/"} omits ${needle}"
  fi
}

assert_consultation_fields() {
  local file="$1"
  local task_name target

  task_name="$(sed -nE 's/^[[:space:]]*task_name="([^"]+)".*/\1/p' "$file")"
  target="$(sed -nE 's/^[[:space:]]*target="([^"]+)".*/\1/p' "$file")"
  if [ -n "$task_name" ] \
    && [[ "$task_name" =~ ^[a-z0-9_]+$ ]] \
    && [[ "$task_name" =~ ^codex_consultation_[a-z0-9_]+$ ]] \
    && [ "$target" = "$task_name" ]; then
    ok "consultation task_name and followup target use the same valid task name"
  else
    bad "consultation task_name/target must use the same ^[a-z0-9_]+$ task name"
  fi
}

assert_forwarded_arg() {
  local file="$1" expected="$2" description="$3"
  if grep -Fxq -- "$expected" "$file"; then
    ok "$description"
  else
    bad "$description"
  fi
}

assert_forwarded_pair() {
  local file="$1" flag="$2" expected="$3" description="$4"
  if awk -v flag="$flag" -v expected="$expected" '
    $0 == flag {
      if (getline next_value && next_value == expected) found = 1
    }
    END { exit(found ? 0 : 1) }
  ' "$file"; then
    ok "$description"
  else
    bad "$description"
  fi
}

assert_forwarded_pair_once() {
  local file="$1" flag="$2" expected="$3" description="$4"
  local count
  count="$(awk -v flag="$flag" -v expected="$expected" '
    $0 == flag {
      if (getline next_value && next_value == expected) count++
    }
    END { print count + 0 }
  ' "$file")"
  if [ "$count" -eq 1 ]; then
    ok "$description"
  else
    bad "$description (expected exactly one pair, found $count)"
  fi
}

assert_workflow_raw_canonical_contract() {
  local workflow="$1" workflow_file="$2"
  local direct_canonical_pattern='--output-file[[:space:]]+[^[:space:]]*implementation-'
  local raw_line normalization_line deterministic_line acceptance_line reviewer_line tester_line

  assert_file "$workflow_file"
  assert_contains "$workflow_file" "WORKER_RAW_OUTPUT"
  assert_contains "$workflow_file" "IMPLEMENTATION_REPORT_PATH"
  assert_contains "$workflow_file" 'worker-output-'
  assert_contains "$workflow_file" 'implementation-'
  assert_contains "$workflow_file" '--output-file "$WORKER_RAW_OUTPUT"'
  assert_contains "$workflow_file" "canonical report"
  assert_contains "$workflow_file" "CLAIMED"
  assert_contains "$workflow_file" "acceptance"
  assert_contains "$workflow_file" "reviewer"
  assert_contains "$workflow_file" "tester"

  if grep -Eiq -- "$direct_canonical_pattern" "$workflow_file"; then
    bad "$workflow direct --output-file canonical implementation path"
  else
    ok "$workflow has no direct --output-file implementation-* command"
  fi

  # Use phase-specific anchors rather than the first occurrence of each word:
  # workflow introductions mention reviewer/tester before the implementation
  # sequence, so a global grep would produce false ordering failures.
  raw_line="$(grep -n -m1 -- '--output-file \"\$WORKER_RAW_OUTPUT\"' "$workflow_file" | cut -d: -f1 || true)"
  normalization_line="$(awk -v start="$raw_line" 'NR > start && /canonical report|正規化|normalization/ { print NR; exit }' "$workflow_file")"
  deterministic_line="$(awk -v start="$normalization_line" 'NR > start && (/deterministic/ || /決定論.*ゲート/) && (/CLAIMED/ || /gate/ || /ゲート/) { print NR; exit }' "$workflow_file")"
  acceptance_line="$(awk -v start="$deterministic_line" 'NR > start && /acceptance/ { print NR; exit }' "$workflow_file")"
  reviewer_line="$(awk -v start="$acceptance_line" 'NR > start && /reviewer/ { print NR; exit }' "$workflow_file")"
  tester_line="$(awk -v start="$reviewer_line" 'NR > start && /tester/ { print NR; exit }' "$workflow_file")"
  if [ -n "$raw_line" ] && [ -n "$normalization_line" ] \
    && [ -n "$deterministic_line" ] && [ -n "$acceptance_line" ] \
    && [ -n "$reviewer_line" ] && [ -n "$tester_line" ] \
    && [ "$raw_line" -lt "$normalization_line" ] \
    && [ "$normalization_line" -lt "$deterministic_line" ] \
    && [ "$deterministic_line" -lt "$acceptance_line" ] \
    && [ "$acceptance_line" -lt "$reviewer_line" ] \
    && [ "$reviewer_line" -lt "$tester_line" ]; then
    ok "$workflow orders raw -> Sol normalization -> deterministic/CLAIMED -> acceptance -> reviewer -> tester"
  else
    bad "$workflow must order raw -> Sol normalization -> deterministic/CLAIMED -> acceptance -> reviewer -> tester"
  fi
}

test_raw_canonical_claimed_fixture() {
  local fixture_root fixture_run pre_block post_block claimed_file
  fixture_root="$(mktemp -d "${TMPDIR:-/tmp}/codex-raw-canonical.XXXXXX")"
  fixture_run="$fixture_root/.ai-pir-runs/run"
  mkdir -p "$fixture_root/.codex" "$fixture_run"
  git -C "$fixture_root" init -q
  git -C "$fixture_root" config user.email "codex-contracts@example.com"
  git -C "$fixture_root" config user.name "codex-contracts"
  git -C "$fixture_root" config core.hooksPath /dev/null
  printf '.ai-pir-runs/\n' > "$fixture_root/.gitignore"
  printf 'seed\n' > "$fixture_root/seed.txt"
  git -C "$fixture_root" add .gitignore seed.txt
  git -C "$fixture_root" commit -q -m seed

  pre_block="$fixture_root/pre-set.sh"
  post_block="$fixture_root/post-set.sh"
  awk '
    {
      line = $0
      trimmed = line
      gsub(/^[ \t]+|[ \t]+$/, "", trimmed)
      if (!inside && trimmed == "```bash") {
        block++
        if (block == 2) inside = 1
        next
      }
      if (inside && trimmed == "```") exit
      if (inside) print
    }
  ' "$DETERMINISTIC_REFERENCE" > "$post_block"
  awk '
    {
      line = $0
      trimmed = line
      gsub(/^[ \t]+|[ \t]+$/, "", trimmed)
      if (!inside && trimmed == "```bash") {
        block++
        if (block == 1) inside = 1
        next
      }
      if (inside && trimmed == "```") exit
      if (inside) print
    }
  ' "$DETERMINISTIC_REFERENCE" > "$pre_block"
  env PROJECT_ROOT="$fixture_root" RUN_DIR="$fixture_run" IMPL_INDEX=01 PRE_IMPL_INDEX=01 bash "$pre_block"

  printf 'changed\n' > "$fixture_root/expected.txt"
  cat > "$fixture_run/worker-output-01.md" <<'EOF'
ACTOR: luna
ACTUAL_MODEL: gpt-5.6-luna
ACTUAL_EFFORT: max
STATUS: completed
CHANGED_FILES: raw-only.txt
OBSERVED_RESULTS: worker observed raw-only.txt
BLOCKERS: none
ESCALATION_REASON: none

### 変更ファイル一覧
- `raw-only.txt` — worker申告（Sol未確認）

### 注意点・未解決事項
なし
EOF
  cat > "$fixture_run/implementation-01.md" <<'EOF'
ACTOR: luna
ACTUAL_MODEL: gpt-5.6-luna
ACTUAL_EFFORT: max
STATUS: completed
CHANGED_FILES: expected.txt
OBSERVED_RESULTS: Sol verified expected.txt
BLOCKERS: none
ESCALATION_REASON: none

### 変更ファイル一覧
- `expected.txt` — Solが独立確認したcanonical path

### 注意点・未解決事項
なし
EOF
  env PROJECT_ROOT="$fixture_root" RUN_DIR="$fixture_run" IMPL_INDEX=01 PRE_IMPL_INDEX=01 bash "$post_block"
  claimed_file="$fixture_run/verify-01-claimed.list"
  assert_contains "$claimed_file" "expected.txt"
  assert_not_contains "$claimed_file" "raw-only.txt"
  ok "focused fixture extracts CLAIMED from Sol canonical report, not raw CHANGED_FILES"

  rm -f "$fixture_run/implementation-01.md"
  env PROJECT_ROOT="$fixture_root" RUN_DIR="$fixture_run" IMPL_INDEX=01 PRE_IMPL_INDEX=01 bash "$post_block"
  if [ ! -s "$claimed_file" ]; then
    ok "raw-only report is not a CLAIMED source"
  else
    bad "raw-only report must not populate CLAIMED"
  fi
  rm -rf "$fixture_root"
}

CODEX_SKILL_FILE="${DOT_DIR}/.codex/skills/codex/SKILL.md"
assert_file "$CODEX_SKILL_FILE"
assert_contains "$CODEX_SKILL_FILE" "spawn_agent"
assert_contains "$CODEX_SKILL_FILE" "followup_task"
assert_contains "$CODEX_SKILL_FILE" "READ_ONLY_CONSULTATION"
assert_contains "$CODEX_SKILL_FILE" 'model="gpt-5.6-luna"'
assert_contains "$CODEX_SKILL_FILE" 'reasoning_effort="low"'
assert_contains "$CODEX_SKILL_FILE" 'fork_turns="none"'
assert_consultation_fields "$CODEX_SKILL_FILE"
assert_not_contains "$CODEX_SKILL_FILE" 'consultant='
assert_contains "$CODEX_SKILL_FILE" "/deepthink"
assert_contains "$CODEX_SKILL_FILE" "/research"
assert_contains "$CODEX_SKILL_FILE" "worker-delegation"
assert_contains "$CODEX_SKILL_FILE" "read-only"
assert_contains "$CODEX_SKILL_FILE" "policy/prompt-based boundary"
assert_contains "$CODEX_SKILL_FILE" "not capability isolation"
assert_contains "$CODEX_SKILL_FILE" "does not enforce filesystem sandbox permissions"
assert_contains "$CODEX_SKILL_FILE" "gpt-5.6"
assert_not_contains "$CODEX_SKILL_FILE" "codex exec"
assert_not_contains "$CODEX_SKILL_FILE" "codex-runner"
assert_not_contains "$CODEX_SKILL_FILE" "nohup"
assert_not_contains "$CODEX_SKILL_FILE" "polling"
assert_not_contains "$CODEX_SKILL_FILE" "completion-marker"
assert_not_contains "$CODEX_SKILL_FILE" "SendMessage"
assert_not_contains "$CODEX_SKILL_FILE" "completion marker"
assert_not_contains "$CODEX_SKILL_FILE" "Agent tool"
assert_not_contains "$CODEX_SKILL_FILE" "Agent Teams"
assert_not_contains "$CODEX_SKILL_FILE" "workspace-write"

assert_file "${DOT_DIR}/etc/seed-codex-overlay.sh"
assert_dir "${DOT_DIR}/.codex/agents"
assert_dir "${DOT_DIR}/.codex/skills"

WORKER_SKILL_DIR="${DOT_DIR}/.codex/skills/worker-delegation"
WORKER_RUNNER="${WORKER_SKILL_DIR}/scripts/run-worker.sh"
assert_dir "$WORKER_SKILL_DIR"
assert_file "${WORKER_SKILL_DIR}/SKILL.md"
assert_file "${WORKER_SKILL_DIR}/agents/openai.yaml"
assert_file "$WORKER_RUNNER"
assert_executable "$WORKER_RUNNER"

for old_path in \
  "${DOT_DIR}/.codex/skills/luna-max-worker" \
  "${DOT_DIR}/.codex/skills/luna-max-worker/SKILL.md" \
  "${DOT_DIR}/.codex/skills/luna-max-worker/scripts/run-luna-max.sh"; do
  if [ -e "$old_path" ] || [ -L "$old_path" ]; then
    bad "old worker path must be absent: $old_path"
  else
    ok "old worker path absent: $old_path"
  fi
done

# The forbidden names are intentionally present in this contract script, so
# exclude this file while checking the repository for stale package references.
old_reference_found=0
contract_file_list="$(mktemp "${TMPDIR:-/tmp}/codex-contracts.XXXXXX")"
runner_test_dir=""
runner_fake_home=""
runner_original_home="${HOME-}"
runner_original_home_set=0
[ -n "${HOME-}" ] && runner_original_home_set=1
cleanup_contract_files() {
  rm -f "$contract_file_list"
  if [ -n "$runner_test_dir" ] && [ -d "$runner_test_dir" ]; then
    rm -rf "$runner_test_dir"
  fi
  if [ "$runner_original_home_set" -eq 1 ]; then
    HOME="$runner_original_home"
    export HOME
  else
    unset HOME
  fi
}
trap cleanup_contract_files EXIT HUP INT TERM
find "$DOT_DIR" -type f -print > "$contract_file_list"
while IFS= read -r file; do
  case "$file" in
    "${DOT_DIR}/etc/test-codex-contracts.sh"|"${DOT_DIR}/.git/"*|"${DOT_DIR}/.ai-pir-runs/"*) continue ;;
  esac
  if grep -Eq 'luna-max-worker|run-luna-max(\.sh)?' "$file" 2>/dev/null; then
    bad "stale worker reference in ${file#"$DOT_DIR/"}"
    old_reference_found=1
  fi
done < "$contract_file_list"
if [ "$old_reference_found" -eq 0 ]; then
  ok "no stale luna-max-worker references"
fi

assert_contains "$WORKER_RUNNER" 'luna)'
assert_contains "$WORKER_RUNNER" 'model="gpt-5.6-luna"'
assert_contains "$WORKER_RUNNER" 'terra)'
assert_contains "$WORKER_RUNNER" 'model="gpt-5.6-terra"'
assert_contains "$WORKER_RUNNER" 'sol)'
assert_contains "$WORKER_RUNNER" 'model="gpt-5.6-sol"'
assert_contains "$WORKER_RUNNER" '--effort'
assert_contains "$WORKER_RUNNER" '--add-dir "$codex_dir_physical"'
assert_contains "$WORKER_RUNNER" 'git_root_physical'
assert_contains "$WORKER_RUNNER" 'codex_dir_physical'
assert_contains "$WORKER_RUNNER" 'find -P "$codex_dir_physical" -type l'
assert_contains "$WORKER_RUNNER" 'artifact_root="$HOME/.ai-pir-runs"'
assert_contains "$WORKER_RUNNER" 'output_allowed_root'
assert_contains "$WORKER_RUNNER" 'umask 077'
assert_contains "$WORKER_RUNNER" "stat -c '%d %i %u %a'"
assert_contains "$WORKER_RUNNER" "stat -f '%d %i %u %Lp'"
assert_contains "$WORKER_RUNNER" 'worker_validate_boundary_state'
assert_contains "$WORKER_RUNNER" "'pre-codex'"
assert_contains "$WORKER_RUNNER" "'post-codex'"
assert_contains "$WORKER_RUNNER" 'worker_output_allowed_root_identity'
assert_contains "$WORKER_RUNNER" 'worker_output_parent_identity'
assert_contains "$WORKER_RUNNER" 'worker_current_uid'
assert_not_contains "$WORKER_RUNNER" 'rm -rf'
assert_contains "$WORKER_RUNNER" 'mktemp "$output_dir_physical/.worker-result.XXXXXX"'
assert_contains "$WORKER_RUNNER" 'ln "$codex_output" "$output_file_physical"'
assert_not_contains "$WORKER_RUNNER" '--skip-git-repo-check'
assert_not_contains "$WORKER_RUNNER" 'danger-full-access'
assert_not_contains "$WORKER_RUNNER" 'dangerously-bypass-approvals-and-sandbox'
assert_not_contains "$WORKER_RUNNER" '--bypass-approvals-and-sandbox'
assert_not_contains "$WORKER_RUNNER" 'chmod'
if grep -Eiq 'fallback|フォールバック' "$WORKER_RUNNER"; then
  bad "worker runner must not implement automatic fallback"
else
  ok "worker runner has no automatic fallback"
fi

# Exercise the runner without invoking a real Codex binary or modifying any
# repository overlay. Every accepted case uses a real temporary Git root with
# a real .codex directory; the fake executable captures argv/stdin and writes
# only the requested temporary worker report.
make_git_root() {
  local root="$1"
  mkdir -p "$root/.codex" "$root/output"
  git -C "$root" init -q
}

write_runner_inputs() {
  local root="$1" label="$2"
  printf '%s\n' "Temporary $label task." > "$root/task.md"
  printf '%s\n' '- R1: temporary runner requirement.' > "$root/requirements.md"
}

test_worker_runner_forwarding() {
  local fake_codex overlay_before overlay_after
  local test_case actor expected_model expected_effort explicit_effort
  local case_dir root root_physical task_file requirements_file output_file
  local args_file stdin_file help_file temp_output status

  if [ ! -x "$WORKER_RUNNER" ]; then
    bad "worker runner forwarding test cannot run: runner is not executable"
    return
  fi

  runner_test_dir="$(mktemp -d "${TMPDIR:-/tmp}/codex-runner-forwarding.XXXXXX")" || {
    bad "worker runner forwarding test could not create a temporary directory"
    return
  }
  runner_fake_home="$runner_test_dir/home"
  mkdir -p "$runner_fake_home/.ai-pir-runs"
  HOME="$runner_fake_home"
  export HOME
  fake_codex="$runner_test_dir/fake-codex"
  cat > "$fake_codex" <<'EOF'
#!/bin/sh
set -eu

printf '%s\n' "$@" > "$FAKE_CODEX_ARGS_FILE"
cat > "$FAKE_CODEX_STDIN_FILE"

output_file=""
codex_dir=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -C)
      [ "$#" -ge 2 ] || exit 2
      shift 2
      ;;
    --add-dir)
      [ "$#" -ge 2 ] || exit 2
      codex_dir="$2"
      shift 2
      ;;
    -o)
      [ "$#" -ge 2 ] || exit 2
      output_file="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

[ -n "$output_file" ] || exit 2
if [ "${FAKE_CODEX_REPLACE_CODEX:-}" = "1" ]; then
  [ -n "$codex_dir" ] || exit 2
  mv "$codex_dir" "${codex_dir}.replaced"
  mkdir "$codex_dir"
fi
if [ "${FAKE_CODEX_REPLACE_OUTPUT_PARENT:-}" = "1" ]; then
  output_parent="$(dirname "$output_file")"
  mv "$output_parent" "${output_parent}.replaced"
  mkdir "$output_parent"
fi
if [ "${FAKE_CODEX_COLLISION:-}" = "file" ]; then
  printf '%s\n' 'raced existing output' > "$FAKE_CODEX_FINAL_OUTPUT"
elif [ "${FAKE_CODEX_COLLISION:-}" = "symlink" ]; then
  ln -s "$FAKE_CODEX_OUTSIDE_TARGET" "$FAKE_CODEX_FINAL_OUTPUT"
fi
expected_actor="$(sed -n 's/^Expected actor: //p' "$FAKE_CODEX_STDIN_FILE" | sed -n '1p')"
expected_model="$(sed -n 's/^Expected model: //p' "$FAKE_CODEX_STDIN_FILE" | sed -n '1p')"
expected_effort="$(sed -n 's/^Expected effort: //p' "$FAKE_CODEX_STDIN_FILE" | sed -n '1p')"
[ -n "$expected_actor" ] && [ -n "$expected_model" ] && [ -n "$expected_effort" ] || exit 2
report_actor="$expected_actor"
report_model="$expected_model"
report_effort="$expected_effort"
report_status="completed"
report_case="${FAKE_CODEX_REPORT_CASE:-${FAKE_CODEX_REPORT_MODE:-valid}}"
case "$report_case" in
  valid) ;;
  missing-actor) report_actor="" ;;
  duplicate-actor) ;;
  actor-mismatch) report_actor="wrong-actor" ;;
  model-mismatch) report_model="wrong-model" ;;
  effort-mismatch) report_effort="wrong-effort" ;;
  status-invalid) report_status="done" ;;
  *) exit 2 ;;
esac
{
  [ -n "$report_actor" ] && printf '%s\n' "ACTOR: $report_actor"
  printf '%s\n' "ACTUAL_MODEL: $report_model"
  printf '%s\n' "ACTUAL_EFFORT: $report_effort"
  printf '%s\n' "STATUS: $report_status"
  printf '%s\n' 'CHANGED_FILES: none'
  printf '%s\n' 'OBSERVED_RESULTS: fake worker report'
  printf '%s\n' 'BLOCKERS: none'
  printf '%s\n' 'ESCALATION_REASON: none'
  if [ "$report_case" = duplicate-actor ]; then
    printf '%s\n' "ACTOR: $report_actor"
  fi
  printf '%s\n' '### 変更ファイル一覧'
  printf '%s\n' 'なし'
  printf '%s\n' '### 注意点・未解決事項'
  printf '%s\n' 'なし'
} > "$output_file"
exit "${FAKE_CODEX_EXIT_STATUS:-0}"
EOF
  chmod 700 "$fake_codex"

  help_file="$runner_test_dir/help.txt"
  if "$WORKER_RUNNER" --help > "$help_file"; then
    ok "worker runner --help succeeds"
  else
    bad "worker runner --help succeeds"
  fi
  assert_contains "$help_file" "--actor luna|terra|sol"
  assert_contains "$help_file" "--effort high|max"
  assert_contains "$help_file" "luna: --effort max only (default max)"
  assert_contains "$help_file" "terra: --effort high or max (default high)"
  assert_contains "$help_file" "sol: --effort high or max (default high"

  overlay_before="$(find "$WORKER_SKILL_DIR" -type f -exec cksum {} + | LC_ALL=C sort)"
  for test_case in luna-default terra-default terra-max sol-default sol-max; do
    case "$test_case" in
      luna-default)
        actor="luna"; expected_model="gpt-5.6-luna"; expected_effort="max"; explicit_effort="" ;;
      terra-default)
        actor="terra"; expected_model="gpt-5.6-terra"; expected_effort="high"; explicit_effort="" ;;
      terra-max)
        actor="terra"; expected_model="gpt-5.6-terra"; expected_effort="max"; explicit_effort="max" ;;
      sol-default)
        actor="sol"; expected_model="gpt-5.6-sol"; expected_effort="high"; explicit_effort="" ;;
      sol-max)
        actor="sol"; expected_model="gpt-5.6-sol"; expected_effort="max"; explicit_effort="max" ;;
    esac
    case_dir="$runner_test_dir/$test_case"
    root="$case_dir/repo"
    root_physical=""
    task_file="$root/task.md"
    requirements_file="$root/requirements.md"
    output_file="$root/output/worker-result.md"
    args_file="$case_dir/codex-args.txt"
    stdin_file="$case_dir/codex-stdin.md"
    mkdir -p "$case_dir"
    make_git_root "$root"
    root_physical="$(cd -P "$root" && pwd -P)"
    write_runner_inputs "$root" "$actor"

    if [ -n "$explicit_effort" ]; then
      if WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
        FAKE_CODEX_ARGS_FILE="$args_file" \
        FAKE_CODEX_STDIN_FILE="$stdin_file" \
        "$WORKER_RUNNER" --actor "$actor" --effort "$explicit_effort" \
          --cwd "$root" --task-file "$task_file" --requirements-file "$requirements_file" \
          --output-file "$output_file"; then status=0; else status=$?; fi
    else
      if WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
        FAKE_CODEX_ARGS_FILE="$args_file" \
        FAKE_CODEX_STDIN_FILE="$stdin_file" \
        "$WORKER_RUNNER" --actor "$actor" \
          --cwd "$root" --task-file "$task_file" --requirements-file "$requirements_file" \
          --output-file "$output_file"; then status=0; else status=$?; fi
    fi
    if [ "$status" -eq 0 ]; then ok "worker runner executes fake codex for $actor"; else bad "worker runner executes fake codex for $actor (got $status)"; fi

    assert_forwarded_arg "$args_file" "exec" "worker runner forwards exec for $actor"
    assert_forwarded_arg "$args_file" "--json" "worker runner forwards --json for $actor"
    assert_not_contains "$args_file" "--skip-git-repo-check"
    assert_forwarded_pair "$args_file" "-m" "$expected_model" "worker runner forwards pinned model for $actor"
    assert_forwarded_pair "$args_file" "-c" "model_reasoning_effort=\"$expected_effort\"" "worker runner forwards $expected_effort reasoning effort for $actor"
    assert_forwarded_pair "$args_file" "-s" "workspace-write" "worker runner forwards workspace-write sandbox for $actor"
    assert_forwarded_pair "$args_file" "-C" "$(cd -P "$root" && pwd -P)" "worker runner forwards canonical cwd for $actor"
    assert_forwarded_pair_once "$args_file" "--add-dir" "$(cd -P "$root/.codex" && pwd -P)" "worker runner forwards exactly one canonical repo-local .codex add-dir for $actor"
    assert_forwarded_arg "$args_file" "-" "worker runner forwards stdin marker for $actor"
    temp_output="$(awk '$0 == "-o" { if (getline value) print value }' "$args_file")"
    case "$temp_output" in
      "$root_physical/output/.worker-result."*) ok "worker runner uses output-parent temporary -o for $actor" ;;
      *) bad "worker runner uses output-parent temporary -o for $actor" ;;
    esac
    if [ ! -e "$temp_output" ]; then ok "worker runner cleans temporary -o for $actor"; else bad "worker runner cleans temporary -o for $actor"; fi
    assert_contains "$stdin_file" "You are the $actor execution worker for a task already planned by the parent Sol agent."
    assert_contains "$stdin_file" "# Task"
    assert_contains "$stdin_file" "Temporary $actor task."
    assert_contains "$stdin_file" "# Acceptance criteria"
    assert_contains "$stdin_file" '- R1: temporary runner requirement.'
    assert_contains "$stdin_file" "Expected actor: $actor"
    assert_contains "$stdin_file" "Expected model: $expected_model"
    assert_contains "$stdin_file" "Expected effort: $expected_effort"
    for report_field in ACTOR ACTUAL_MODEL ACTUAL_EFFORT STATUS CHANGED_FILES OBSERVED_RESULTS BLOCKERS ESCALATION_REASON; do
      assert_contains "$stdin_file" "${report_field}:"
    done
    assert_contains "$stdin_file" "not Sol acceptance"
    assert_contains "$stdin_file" "not a reviewer/tester PASS"
    assert_contains "$stdin_file" "# Completion report"
    assert_contains "$output_file" "fake worker report"
    assert_contains "$output_file.provenance.tsv" "started_at_utc$(printf '\t')ended_at_utc$(printf '\t')duration_ms$(printf '\t')actor$(printf '\t')model$(printf '\t')effort$(printf '\t')codex_exit$(printf '\t')validation_status"
    assert_contains "$output_file.provenance.tsv" "$(date -u '+%Y-%m-%dT')"
    assert_contains "$output_file.provenance.tsv" "$(printf '\t')$actor$(printf '\t')$expected_model$(printf '\t')$expected_effort$(printf '\t')0$(printf '\t')validated"
  done
  overlay_after="$(find "$WORKER_SKILL_DIR" -type f -exec cksum {} + | LC_ALL=C sort)"
  if [ "$overlay_before" = "$overlay_after" ]; then
    ok "worker runner forwarding test leaves its repository overlay unchanged"
  else
    bad "worker runner forwarding test must not modify its repository overlay"
  fi
}

test_worker_runner_forwarding

test_worker_runner_rejects_invalid_reports() {
  local fake_codex report_case case_dir root output_file args_file status
  fake_codex="$runner_test_dir/fake-codex"
  for report_case in missing-actor duplicate-actor actor-mismatch model-mismatch effort-mismatch status-invalid; do
    case_dir="$runner_test_dir/invalid-report-$report_case"
    root="$case_dir/repo"
    output_file="$root/output/result.md"
    args_file="$case_dir/codex-args.txt"
    mkdir -p "$case_dir"
    make_git_root "$root"
    write_runner_inputs "$root" "invalid-report-$report_case"
    if HOME="$runner_fake_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
      FAKE_CODEX_ARGS_FILE="$args_file" FAKE_CODEX_STDIN_FILE="$case_dir/stdin" \
      FAKE_CODEX_REPORT_CASE="$report_case" "$WORKER_RUNNER" --actor luna --cwd "$root" \
      --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
      --output-file "$output_file"; then
      status=0
    else
      status=$?
    fi
    if [ "$status" -ne 0 ]; then ok "worker runner rejects invalid raw report $report_case"; else bad "worker runner must reject invalid raw report $report_case"; fi
    if [ ! -e "$output_file" ] && [ ! -L "$output_file" ]; then ok "invalid raw report $report_case is not published"; else bad "invalid raw report $report_case must not be published"; fi
    assert_contains "$output_file.provenance.tsv" "raw_invalid"
  done
}

test_worker_runner_rejects_invalid_reports

test_worker_runner_detects_boundary_replacement() {
  local fake_codex case_name case_dir root output_file args_file runner_status
  fake_codex="$runner_test_dir/fake-codex"
  for case_name in codex output-parent; do
    case_dir="$runner_test_dir/boundary-replacement-$case_name"
    root="$case_dir/repo"
    output_file="$root/output/result.md"
    args_file="$case_dir/codex-args.txt"
    mkdir -p "$case_dir"
    make_git_root "$root"
    write_runner_inputs "$root" "boundary-replacement-$case_name"

    if [ "$case_name" = "codex" ]; then
      if HOME="$runner_fake_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
        FAKE_CODEX_ARGS_FILE="$args_file" FAKE_CODEX_STDIN_FILE="$case_dir/stdin" \
        FAKE_CODEX_REPLACE_CODEX=1 "$WORKER_RUNNER" --actor luna --cwd "$root" \
        --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
        --output-file "$output_file"; then runner_status=0; else runner_status=$?; fi
    else
      if HOME="$runner_fake_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
        FAKE_CODEX_ARGS_FILE="$args_file" FAKE_CODEX_STDIN_FILE="$case_dir/stdin" \
        FAKE_CODEX_REPLACE_OUTPUT_PARENT=1 "$WORKER_RUNNER" --actor luna --cwd "$root" \
        --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
        --output-file "$output_file"; then runner_status=0; else runner_status=$?; fi
    fi
    if [ "$runner_status" -ne 0 ]; then
      ok "worker runner rejects invocation-time $case_name replacement"
    else
      bad "worker runner must reject invocation-time $case_name replacement"
    fi
    if [ -e "$args_file" ]; then
      ok "fake Codex executed for invocation-time $case_name replacement"
    else
      bad "fake Codex must execute for invocation-time $case_name replacement"
    fi
    if [ ! -e "$output_file" ] && [ ! -L "$output_file" ]; then
      ok "worker runner does not publish output after $case_name replacement"
    else
      bad "worker runner must not publish output after $case_name replacement"
    fi
  done
}

test_worker_runner_detects_boundary_replacement

test_worker_runner_rejects_insecure_permissions() {
  local fake_codex case_name case_dir root output_file args_file runner_status
  local case_home artifact_root artifact_parent
  fake_codex="$runner_test_dir/fake-codex"
  for case_name in repo-root codex-dir codex-descendant output-parent artifact-root; do
    case_dir="$runner_test_dir/insecure-permissions-$case_name"
    root="$case_dir/repo"
    output_file="$root/output/result.md"
    args_file="$case_dir/codex-args.txt"
    mkdir -p "$case_dir"
    make_git_root "$root"
    write_runner_inputs "$root" "insecure-permissions-$case_name"
    case "$case_name" in
      repo-root)
        chmod 777 "$root"
        ;;
      codex-dir)
        chmod 775 "$root/.codex"
        ;;
      codex-descendant)
        printf '%s\n' 'insecure descendant' > "$root/.codex/insecure.txt"
        chmod 666 "$root/.codex/insecure.txt"
        ;;
      output-parent)
        chmod 775 "$root/output"
        ;;
      artifact-root)
        case_home="$case_dir/home"
        artifact_root="$case_home/.ai-pir-runs"
        artifact_parent="$artifact_root/run"
        mkdir -p "$artifact_parent"
        chmod 775 "$artifact_root"
        output_file="$artifact_parent/result.md"
        ;;
    esac

    if [ "$case_name" = "artifact-root" ]; then
      if HOME="$case_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
        FAKE_CODEX_ARGS_FILE="$args_file" FAKE_CODEX_STDIN_FILE="$case_dir/stdin" \
        "$WORKER_RUNNER" --actor luna --cwd "$root" --task-file "$root/task.md" \
        --requirements-file "$root/requirements.md" --output-file "$output_file"; then
        runner_status=0
      else
        runner_status=$?
      fi
    else
      if HOME="$runner_fake_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
        FAKE_CODEX_ARGS_FILE="$args_file" FAKE_CODEX_STDIN_FILE="$case_dir/stdin" \
        "$WORKER_RUNNER" --actor luna --cwd "$root" --task-file "$root/task.md" \
        --requirements-file "$root/requirements.md" --output-file "$output_file"; then
        runner_status=0
      else
        runner_status=$?
      fi
    fi
    if [ "$runner_status" -eq 2 ]; then
      ok "worker runner rejects $case_name group/world-writable boundary"
    else
      bad "worker runner must reject $case_name group/world-writable boundary (got $runner_status)"
    fi
    if [ ! -e "$args_file" ]; then
      ok "worker runner does not invoke Codex for insecure $case_name boundary"
    else
      bad "worker runner must not invoke Codex for insecure $case_name boundary"
    fi
  done
}

test_worker_runner_rejects_insecure_permissions

test_worker_runner_artifact_output() {
  local fake_codex case_dir root run_dir run_dir_physical alias_run_dir
  local output_file args_file status temp_output

  fake_codex="$runner_test_dir/fake-codex"
  case_dir="$runner_test_dir/workflow-run-dir"
  root="$case_dir/repo"
  mkdir -p "$case_dir"
  make_git_root "$root"
  write_runner_inputs "$root" workflow-run-dir

  # This mirrors the workflow convention: worker reports live below the
  # standard Sol artifact root rather than inside the repository checkout.
  run_dir="$HOME/.ai-pir-runs/workflow-run"
  mkdir -p "$run_dir"
  run_dir_physical="$(cd -P "$run_dir" && pwd -P)"
  alias_run_dir="$run_dir"
  case "$run_dir_physical" in
    /private/var/*)
      alias_run_dir="/var${run_dir_physical#/private/var}"
      ;;
  esac
  output_file="$alias_run_dir/implementation-01.md"
  args_file="$case_dir/codex-args.txt"
  if HOME="$runner_fake_home" \
    WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
    FAKE_CODEX_ARGS_FILE="$args_file" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" \
    "$WORKER_RUNNER" --actor luna --cwd "$root" \
      --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
      --output-file "$output_file"; then status=0; else status=$?; fi
  if [ "$status" -eq 0 ]; then
    ok "worker runner accepts workflow RUN_DIR artifact output"
  else
    bad "worker runner accepts workflow RUN_DIR artifact output (got $status)"
  fi
  assert_forwarded_pair_once "$args_file" "--add-dir" "$(cd -P "$root/.codex" && pwd -P)" \
    "workflow RUN_DIR fixture still forwards canonical repo-local .codex"
  temp_output="$(awk '$0 == "-o" { if (getline value) print value }' "$args_file")"
  case "$temp_output" in
    "$run_dir_physical/.worker-result."*) ok "workflow RUN_DIR uses an artifact-parent temporary -o" ;;
    *) bad "workflow RUN_DIR uses an artifact-parent temporary -o" ;;
  esac
  if [ ! -e "$temp_output" ]; then ok "workflow RUN_DIR cleans artifact temporary -o"; else bad "workflow RUN_DIR cleans artifact temporary -o"; fi
  assert_contains "$output_file" "fake worker report"
  assert_contains "$output_file.provenance.tsv" "validated"
}

test_worker_runner_artifact_output

test_worker_runner_invalid_inputs() {
  local fake_codex invalid_case actor effort case_dir root output_file args_file status
  fake_codex="$runner_test_dir/fake-codex"
  for invalid_case in unknown-actor legacy-actor unknown-effort luna-high; do
    case_dir="$runner_test_dir/invalid-$invalid_case"
    root="$case_dir/repo"
    output_file="$root/output/worker-result.md"
    args_file="$case_dir/codex-args.txt"
    mkdir -p "$case_dir"
    make_git_root "$root"
    write_runner_inputs "$root" "$invalid_case"
    actor="terra"; effort=""
    case "$invalid_case" in
      unknown-actor) actor="mars" ;;
      legacy-actor) actor="sol-direct" ;;
      unknown-effort) effort="low" ;;
      luna-high) actor="luna"; effort="high" ;;
    esac
    if [ -n "$effort" ]; then
      if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$args_file" \
        FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor "$actor" --effort "$effort" \
        --cwd "$root" --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
        --output-file "$output_file"; then status=0; else status=$?; fi
    else
      if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$args_file" \
        FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor "$actor" \
        --cwd "$root" --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
        --output-file "$output_file"; then status=0; else status=$?; fi
    fi
    if [ "$status" -eq 2 ]; then ok "worker runner rejects invalid actor/effort case $invalid_case with exit 2"; else bad "worker runner rejects invalid actor/effort case $invalid_case with exit 2 (got $status)"; fi
    if [ ! -e "$args_file" ]; then ok "worker runner does not invoke fake codex for invalid case $invalid_case"; else bad "worker runner must not invoke fake codex for invalid case $invalid_case"; fi
  done
}

test_worker_runner_invalid_inputs

test_record_observation_helper() {
  local helper obs_home run_dir raw_output sidecar before status outside bad_home
  local invalid_sidecar external_provenance group_parent control_run
  helper="$DOT_DIR/.codex/skills/worker-delegation/scripts/record-observation.sh"
  obs_home="$runner_test_dir/observation-home"
  run_dir="$obs_home/.ai-pir-runs/run-helper"
  mkdir -p "$obs_home/.ai-pir-runs"
  if HOME="$obs_home" "$helper" init --run-dir "$run_dir"; then status=0; else status=$?; fi
  if [ "$status" -eq 0 ]; then ok "record-observation init creates all ledgers"; else bad "record-observation init creates all ledgers"; fi
  run_dir="$(cd -P "$run_dir" && pwd -P)"
  for ledger in worker-observations-v1.tsv sol-acceptance-v1.tsv independent-verdicts-v1.tsv; do
    if [ -f "$run_dir/$ledger" ]; then ok "record-observation creates $ledger"; else bad "record-observation creates $ledger"; fi
    mode="$(stat -f '%Lp' "$run_dir/$ledger" 2>/dev/null || stat -c '%a' "$run_dir/$ledger")"
    case "$mode" in 600|0600) ok "record-observation $ledger is private" ;; *) bad "record-observation $ledger must be mode 0600 (got $mode)" ;; esac
  done
  before="$(cksum "$run_dir/worker-observations-v1.tsv")"
  HOME="$obs_home" "$helper" init --run-dir "$run_dir"
  if [ "$before" = "$(cksum "$run_dir/worker-observations-v1.tsv")" ]; then ok "record-observation init preserves existing header"; else bad "record-observation init must not rewrite existing ledger"; fi

  for invalid_attempt_key in 01-alpha 01-fix-alpha; do
    if HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$run_dir/worker-output-$invalid_attempt_key.md" --provenance "$run_dir/worker-output-$invalid_attempt_key.md.provenance.tsv" --job-id invalid-suffix --index "$invalid_attempt_key" --status blocked --sol-measurement-result blocked --mismatch not_comparable --mismatch-reason invalid-suffix --escalation-from none --escalation-to none --effort-escalation-from none --effort-escalation-to none --escalation-reason none --insufficiency-class none --input-sufficient not_applicable --measured-insufficiency-ref none; then status=0; else status=$?; fi
    if [ "$status" -ne 0 ]; then ok "record-observation rejects legacy attempt suffix $invalid_attempt_key"; else bad "record-observation must reject legacy attempt suffix $invalid_attempt_key"; fi
    if HOME="$obs_home" "$helper" acceptance --run-dir "$run_dir" --job-id invalid-suffix --index "$invalid_attempt_key" --requirement-id R1 --verdict FAIL --evidence-ref invalid-suffix.md; then status=0; else status=$?; fi
    if [ "$status" -ne 0 ]; then ok "record-observation acceptance rejects legacy attempt suffix $invalid_attempt_key"; else bad "record-observation acceptance must reject legacy attempt suffix $invalid_attempt_key"; fi
  done

  raw_output="$run_dir/worker-output-01.md"
  printf '%s\n' \
    'ACTOR: luna' \
    'ACTUAL_MODEL: gpt-5.6-luna' \
    'ACTUAL_EFFORT: max' \
    'STATUS: completed' \
    'CHANGED_FILES: none' \
    'OBSERVED_RESULTS: fixture' \
    'BLOCKERS: none' \
    'ESCALATION_REASON: none' > "$raw_output"
  sidecar="$raw_output.provenance.tsv"
  printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\n2026-08-06T00:00:00Z\t2026-08-06T00:00:01Z\t1000\tluna\tgpt-5.6-luna\tmax\t0\tvalidated\n' > "$sidecar"
  HOME="$obs_home" "$helper" acceptance --run-dir "$run_dir" --job-id job-observe --index 01 --requirement-id R1 --verdict PASS --evidence-ref sol-acceptance-01.md --evidence-summary "observed R1"
  HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$raw_output" --provenance "$sidecar" --job-id job-observe --index 01 --status completed --sol-measurement-result accepted --mismatch match --mismatch-reason none --escalation-from none --escalation-to none --effort-escalation-from none --effort-escalation-to none --escalation-reason none --insufficiency-class none --input-sufficient not_applicable --measured-insufficiency-ref none --report-ref implementation-01.md --notes "worker row"
  HOME="$obs_home" "$helper" verdict --run-dir "$run_dir" --job-id job-observe --target-attempt-index 01 --cycle 01 --role correctness --verdict PASS --report-ref review-01-correctness.md --model gpt-5.6-terra --effort high --evidence-ref review-evidence-01-correctness.md
  HOME="$obs_home" "$helper" verdict --run-dir "$run_dir" --job-id job-observe --target-attempt-index 01 --cycle 01 --role security --verdict FAIL --report-ref review-01-security.md --model gpt-5.6-terra --effort high --evidence-ref review-evidence-01-security.md
  HOME="$obs_home" "$helper" verdict --run-dir "$run_dir" --job-id job-observe --target-attempt-index 01 --cycle 01 --role tester --verdict FAIL --report-ref test-02.md --model gpt-5.6-terra --effort high --evidence-ref test-evidence-01.md
  assert_contains "$run_dir/worker-observations-v1.tsv" "gpt-5.6-luna"
  assert_contains "$run_dir/worker-observations-v1.tsv" "validated"
  assert_contains "$run_dir/worker-observations-v1.tsv" "accepted$(printf '\t')match"
  assert_contains "$run_dir/sol-acceptance-v1.tsv" "R1$(printf '\t')PASS$(printf '\t')sol-acceptance-01.md"
  assert_contains "$run_dir/independent-verdicts-v1.tsv" "correctness$(printf '\t')gpt-5.6-terra$(printf '\t')high"
  assert_contains "$run_dir/independent-verdicts-v1.tsv" "security$(printf '\t')gpt-5.6-terra$(printf '\t')high"
  assert_contains "$run_dir/independent-verdicts-v1.tsv" "run-helper:job-observe:review:01:correctness"
  assert_contains "$run_dir/independent-verdicts-v1.tsv" "run-helper:job-observe:review:01:security"
  assert_contains "$run_dir/independent-verdicts-v1.tsv" "tester$(printf '\t')gpt-5.6-terra$(printf '\t')high"
  if HOME="$obs_home" "$helper" verdict --run-dir "$run_dir" --job-id job-observe --index 01 --role reviewer --verdict PASS --report-ref generic.md; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects generic reviewer role"; else bad "record-observation must reject generic reviewer role"; fi

  raw_output="$run_dir/worker-output-02.md"
  printf '%s\n' \
    'ACTOR: luna' \
    'ACTUAL_MODEL: gpt-5.6-luna' \
    'ACTUAL_EFFORT: max' \
    'STATUS: blocked' \
    'CHANGED_FILES: none' \
    'OBSERVED_RESULTS: blocked fixture' \
    'BLOCKERS: raw invalid' \
    'ESCALATION_REASON: none' > "$raw_output"
  sidecar="$raw_output.provenance.tsv"
  printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\n2026-08-06T00:00:01Z\t2026-08-06T00:00:02Z\t1000\tluna\tgpt-5.6-luna\tmax\t1\tcodex_failed_no_output\n' > "$sidecar"
  rm "$raw_output"
  HOME="$obs_home" "$helper" acceptance --run-dir "$run_dir" --job-id job-observe --index 02 --requirement-id R2 --verdict FAIL --evidence-ref sol-acceptance-02.md --evidence-summary "blocked R2"
  HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$raw_output" --provenance "$sidecar" --job-id job-observe --index 02 --status blocked --sol-measurement-result blocked --mismatch not_comparable --mismatch-reason raw-not-published --escalation-from none --escalation-to none --effort-escalation-from none --effort-escalation-to none --escalation-reason none --insufficiency-class none --input-sufficient not_applicable --measured-insufficiency-ref none --report-ref implementation-02.md
  assert_contains "$run_dir/worker-observations-v1.tsv" "blocked$(printf '\t')1$(printf '\t')codex_failed_no_output$(printf '\t')not_provided$(printf '\t')blocked$(printf '\t')not_comparable$(printf '\t')raw-not-published"

  if HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$raw_output" --provenance "$sidecar" --job-id missing-enum --index 03 --status blocked --report-ref implementation-03.md; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation requires Sol measurement and mismatch enums"; else bad "record-observation must require Sol measurement and mismatch enums"; fi

  outside="$runner_test_dir/observation-outside"
  mkdir -p "$outside"
  external_provenance="$outside/external.provenance.tsv"
  printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\n2026-08-06T00:00:00Z\t2026-08-06T00:00:01Z\t1000\tluna\tgpt-5.6-luna\tmax\t0\tvalidated\n' > "$external_provenance"
  if HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$run_dir/worker-output-01.md" --provenance "$external_provenance" --job-id external-provenance --index 01 --status completed --sol-measurement-result accepted --mismatch match --report-ref implementation-01.md; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects external provenance path"; else bad "record-observation must reject external provenance path"; fi

  invalid_sidecar="$run_dir/worker-output-03.md.provenance.tsv"
  printf '%s\n' 'ACTOR: luna' > "$run_dir/worker-output-03.md"
  printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\nmalformed\t2026-08-06T00:00:01Z\t1000\tluna\tgpt-5.6-luna\tmax\t0\tvalidated\textra\n' > "$invalid_sidecar"
  if HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$run_dir/worker-output-03.md" --provenance "$invalid_sidecar" --job-id malformed-sidecar --index 03 --status completed --sol-measurement-result rejected --mismatch mismatch --report-ref implementation-03.md; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects malformed provenance columns"; else bad "record-observation must reject malformed provenance columns"; fi

  printf '%s\n' \
    'ACTOR: luna' \
    'ACTUAL_MODEL: gpt-5.6-luna' \
    'ACTUAL_EFFORT: max' \
    'STATUS: failed' \
    'CHANGED_FILES: none' \
    'OBSERVED_RESULTS: rejected fixture' \
    'BLOCKERS: requirement failed' \
    'ESCALATION_REASON: none' > "$run_dir/worker-output-03.md"
  printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\n2026-08-06T00:00:02Z\t2026-08-06T00:00:03Z\t1000\tluna\tgpt-5.6-luna\tmax\t1\tcodex_failed\n' > "$run_dir/worker-output-03.md.provenance.tsv"
  HOME="$obs_home" "$helper" acceptance --run-dir "$run_dir" --job-id job-observe --index 03 --requirement-id R3 --verdict FAIL --evidence-ref sol-acceptance-03.md --evidence-summary "rejected R3"
  HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$run_dir/worker-output-03.md" --provenance "$run_dir/worker-output-03.md.provenance.tsv" --job-id job-observe --index 03 --status failed --sol-measurement-result rejected --mismatch mismatch --mismatch-reason sol-requirement-rejected --escalation-from none --escalation-to none --effort-escalation-from none --effort-escalation-to none --escalation-reason none --insufficiency-class none --input-sufficient not_applicable --measured-insufficiency-ref none --report-ref implementation-03.md
  assert_contains "$run_dir/worker-observations-v1.tsv" "failed$(printf '\t')1$(printf '\t')codex_failed$(printf '\t')not_provided$(printf '\t')rejected$(printf '\t')mismatch$(printf '\t')sol-requirement-rejected"

  chmod 666 "$run_dir/worker-output-02.md.provenance.tsv"
  if HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$run_dir/worker-output-02.md" --provenance "$run_dir/worker-output-02.md.provenance.tsv" --job-id writable-sidecar --index 02 --status blocked --sol-measurement-result blocked --mismatch not_comparable --report-ref implementation-02.md; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects writable provenance sidecar"; else bad "record-observation must reject writable provenance sidecar"; fi
  chmod 600 "$run_dir/worker-output-02.md.provenance.tsv"

  printf '%s\n' 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\n2026-08-06T00:00:02Z\t2026-08-06T00:00:03Z\t1000\tluna\tgpt-5.6-luna\tmax\t1\tcodex_failed_no_output\n' > "$external_provenance"
  rm "$run_dir/worker-output-02.md.provenance.tsv"
  ln -s "$external_provenance" "$run_dir/worker-output-02.md.provenance.tsv"
  if HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$run_dir/worker-output-02.md" --provenance "$run_dir/worker-output-02.md.provenance.tsv" --job-id symlink-sidecar --index 02 --status blocked --sol-measurement-result blocked --mismatch not_comparable --report-ref implementation-02.md; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects symlink provenance sidecar"; else bad "record-observation must reject symlink provenance sidecar"; fi
  rm "$run_dir/worker-output-02.md.provenance.tsv"
  printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\n2026-08-06T00:00:01Z\t2026-08-06T00:00:02Z\t1000\tluna\tgpt-5.6-luna\tmax\t1\tcodex_failed_no_output\n' > "$run_dir/worker-output-02.md.provenance.tsv"

  if HOME="$obs_home" "$helper" init --run-dir "$outside/run"; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects run-dir outside artifact root"; else bad "record-observation must reject run-dir outside artifact root"; fi
  if HOME="$obs_home" "$helper" acceptance --run-dir "$run_dir" --job-id job-observe --index 99 --requirement-id R9 --verdict PASS --evidence-ref "bad$(printf '\t')value"; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects TSV injection"; else bad "record-observation must reject TSV injection"; fi

  control_run="$obs_home/.ai-pir-runs/bad$(printf '\t')run"
  if HOME="$obs_home" "$helper" init --run-dir "$control_run"; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects run-dir control characters"; else bad "record-observation must reject run-dir control characters"; fi

  chmod 775 "$obs_home/.ai-pir-runs"
  if HOME="$obs_home" "$helper" init --run-dir "$obs_home/.ai-pir-runs/group-writable"; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects group-writable artifact root"; else bad "record-observation must reject group-writable artifact root"; fi
  chmod 700 "$obs_home/.ai-pir-runs"
  group_parent="$obs_home/.ai-pir-runs/group-parent"
  mkdir -p "$group_parent"
  chmod 775 "$group_parent"
  if HOME="$obs_home" "$helper" init --run-dir "$group_parent/new-run"; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects group-writable intermediate"; else bad "record-observation must reject group-writable intermediate"; fi
  chmod 700 "$group_parent"

  bad_home="$runner_test_dir/observation-bad-home"
  mkdir -p "$bad_home"
  ln -s "$obs_home/.ai-pir-runs" "$bad_home/.ai-pir-runs"
  if HOME="$bad_home" "$helper" init --run-dir "$bad_home/.ai-pir-runs/run"; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "record-observation rejects symlinked artifact root"; else bad "record-observation must reject symlinked artifact root"; fi

  # Exercise concrete shard/correction attempts and all permitted actor/effort
  # rungs against the real helper, rather than relying on static SKILL text.
  raw_output="$run_dir/worker-output-02-review-fix-a.md"
  printf '%s\n' 'ACTOR: terra' 'ACTUAL_MODEL: gpt-5.6-terra' 'ACTUAL_EFFORT: high' 'STATUS: failed' 'CHANGED_FILES: none' 'OBSERVED_RESULTS: review correction fixture' 'BLOCKERS: none' 'ESCALATION_REASON: measured' > "$raw_output"
  sidecar="$raw_output.provenance.tsv"
  printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\n2026-08-06T00:01:00Z\t2026-08-06T00:01:02Z\t2000\tterra\tgpt-5.6-terra\thigh\t0\tvalidated\n' > "$sidecar"
  HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$raw_output" --provenance "$sidecar" --job-id review-fix-fixture --index 02-review-fix-a --status failed --sol-measurement-result rejected --mismatch mismatch --mismatch-reason review-fail-reproduced --escalation-from luna --escalation-to terra --effort-escalation-from none --effort-escalation-to none --escalation-reason cross-module-invariants --insufficiency-class local-reasoning --input-sufficient yes --measured-insufficiency-ref sol-escalation-luna-terra.md --report-ref implementation-02-review-fix-a.md
  HOME="$obs_home" "$helper" verdict --run-dir "$run_dir" --job-id review-fix-fixture --target-attempt-index 02-review-fix-a --cycle 01 --role correctness --verdict FAIL --report-ref review-01-correctness.md --model gpt-5.6-terra --effort high --evidence-ref review-01-correctness-evidence.md
  HOME="$obs_home" "$helper" verdict --run-dir "$run_dir" --job-id review-fix-fixture --target-attempt-index 02-review-fix-a --cycle 01 --role tester --verdict PASS --report-ref test-01.md --model gpt-5.6-terra --effort high --evidence-ref test-01-evidence.md
  assert_contains "$run_dir/worker-observations-v1.tsv" "02-review-fix-a$(printf '\t')terra$(printf '\t')gpt-5.6-terra$(printf '\t')high"
  assert_contains "$run_dir/worker-observations-v1.tsv" "cross-module-invariants"
  assert_contains "$run_dir/independent-verdicts-v1.tsv" "run-helper:review-fix-fixture:review:01:correctness"
  assert_contains "$run_dir/independent-verdicts-v1.tsv" "run-helper:review-fix-fixture:test:01:tester"
  assert_contains "$run_dir/independent-verdicts-v1.tsv" "run-helper:review-fix-fixture:02-review-fix-a"

  append_escalation_fixture() {
    fixture_actor=$1; fixture_model=$2; fixture_effort=$3; fixture_key=$4; fixture_from=$5; fixture_to=$6; fixture_effort_from=$7; fixture_effort_to=$8; fixture_ref=$9
    raw_output="$run_dir/worker-output-$fixture_key.md"
    printf '%s\n' "ACTOR: $fixture_actor" "ACTUAL_MODEL: $fixture_model" "ACTUAL_EFFORT: $fixture_effort" 'STATUS: failed' 'CHANGED_FILES: none' 'OBSERVED_RESULTS: escalation fixture' 'BLOCKERS: none' 'ESCALATION_REASON: measured' > "$raw_output"
    sidecar="$raw_output.provenance.tsv"
    printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\n2026-08-06T00:02:00Z\t2026-08-06T00:02:01Z\t1000\t%s\t%s\t%s\t0\tvalidated\n' "$fixture_actor" "$fixture_model" "$fixture_effort" > "$sidecar"
    HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$raw_output" --provenance "$sidecar" --job-id "ladder-$fixture_key" --index "$fixture_key" --status failed --sol-measurement-result rejected --mismatch mismatch --mismatch-reason measured-insufficiency --escalation-from "$fixture_from" --escalation-to "$fixture_to" --effort-escalation-from "$fixture_effort_from" --effort-escalation-to "$fixture_effort_to" --escalation-reason cross-module-invariants --insufficiency-class capability --input-sufficient yes --measured-insufficiency-ref "$fixture_ref" --report-ref "implementation-$fixture_key.md"
  }
  append_escalation_fixture terra gpt-5.6-terra max 03-shard-terra-max none none high max sol-terra-max.md
  append_escalation_fixture sol gpt-5.6-sol high 04-unit-sol-high terra sol none none sol-high.md
  append_escalation_fixture sol gpt-5.6-sol max 05-unit-sol-max none none high max sol-max.md
  assert_contains "$run_dir/worker-observations-v1.tsv" "gpt-5.6-terra$(printf '\t')max"
  assert_contains "$run_dir/worker-observations-v1.tsv" "gpt-5.6-sol$(printf '\t')high"
  assert_contains "$run_dir/worker-observations-v1.tsv" "gpt-5.6-sol$(printf '\t')max"
  assert_contains "$run_dir/worker-observations-v1.tsv" "none$(printf '\t')none$(printf '\t')cross-module-invariants$(printf '\t')high$(printf '\t')max$(printf '\t')no"
  assert_contains "$run_dir/worker-observations-v1.tsv" "terra$(printf '\t')sol$(printf '\t')cross-module-invariants$(printf '\t')none$(printf '\t')none$(printf '\t')no"

  append_current_actor_fixture() {
    current_actor=$1; current_model=$2; current_effort=$3; current_key=$4; current_from=$5; current_to=$6
    if [ "$current_from" = none ]; then current_reason=none; current_class=none; current_input=not_applicable; current_ref=none; else current_reason=measured-transition; current_class=capability; current_input=yes; current_ref="transition-$current_from-$current_to.md"; fi
    raw_output="$run_dir/worker-output-$current_key.md"
    printf '%s\n' "ACTOR: $current_actor" "ACTUAL_MODEL: $current_model" "ACTUAL_EFFORT: $current_effort" 'STATUS: failed' 'CHANGED_FILES: none' 'OBSERVED_RESULTS: continuous ladder fixture' 'BLOCKERS: none' "ESCALATION_REASON: $current_reason" > "$raw_output"
    sidecar="$raw_output.provenance.tsv"
    printf 'started_at_utc\tended_at_utc\tduration_ms\tactor\tmodel\teffort\tcodex_exit\tvalidation_status\n2026-08-06T00:03:00Z\t2026-08-06T00:03:01Z\t1000\t%s\t%s\t%s\t0\tvalidated\n' "$current_actor" "$current_model" "$current_effort" > "$sidecar"
    HOME="$obs_home" "$helper" worker --run-dir "$run_dir" --raw-output "$raw_output" --provenance "$sidecar" --job-id continuous-ladder --index "$current_key" --status failed --sol-measurement-result rejected --mismatch mismatch --mismatch-reason continuous-ladder --escalation-from "$current_from" --escalation-to "$current_to" --effort-escalation-from none --effort-escalation-to none --escalation-reason "$current_reason" --insufficiency-class "$current_class" --input-sufficient "$current_input" --measured-insufficiency-ref "$current_ref"
  }
  append_current_actor_fixture luna gpt-5.6-luna max 09 none none
  append_current_actor_fixture terra gpt-5.6-terra high 10 luna terra
  append_current_actor_fixture sol gpt-5.6-sol high 11 terra sol
  if awk -F '\t' 'NR==1 { for(i=1;i<=NF;i++) c[$i]=i; next } $(c["job_id"])=="continuous-ladder" && $(c["attempt_seq"])=="09" && $(c["actor"])=="luna" && $(c["escalation_from"])=="none" && $(c["escalation_to"])=="none" { found=1 } END { exit found ? 0 : 1 }' "$run_dir/worker-observations-v1.tsv"; then ok "continuous ladder initial Luna row has no transition"; else bad "continuous ladder initial Luna transition row"; fi
  if awk -F '\t' 'NR==1 { for(i=1;i<=NF;i++) c[$i]=i; next } $(c["job_id"])=="continuous-ladder" && $(c["attempt_seq"])=="10" && $(c["actor"])=="terra" && $(c["escalation_from"])=="luna" && $(c["escalation_to"])=="terra" { found=1 } END { exit found ? 0 : 1 }' "$run_dir/worker-observations-v1.tsv"; then ok "continuous ladder Terra row records Luna-to-current-Terra"; else bad "continuous ladder Terra transition row"; fi
  if awk -F '\t' 'NR==1 { for(i=1;i<=NF;i++) c[$i]=i; next } $(c["job_id"])=="continuous-ladder" && $(c["attempt_seq"])=="11" && $(c["actor"])=="sol" && $(c["escalation_from"])=="terra" && $(c["escalation_to"])=="sol" { found=1 } END { exit found ? 0 : 1 }' "$run_dir/worker-observations-v1.tsv"; then ok "continuous ladder Sol row records Terra-to-current-Sol"; else bad "continuous ladder Sol transition row"; fi
}

test_record_observation_helper

test_runner_to_observation_e2e() {
  local helper fake_codex e2e_home run_dir root case_name output_file runner_status validation_status
  local worker_status sol_result mismatch mismatch_reason raw_state
  helper="$DOT_DIR/.codex/skills/worker-delegation/scripts/record-observation.sh"
  fake_codex="$runner_test_dir/fake-codex"
  e2e_home="$runner_test_dir/runner-observation-home"
  run_dir="$e2e_home/.ai-pir-runs/runner-observation-e2e"
  root="$runner_test_dir/runner-observation-repo"
  mkdir -p "$e2e_home/.ai-pir-runs"
  make_git_root "$root"
  write_runner_inputs "$root" runner-observation-e2e
  HOME="$e2e_home" "$helper" init --run-dir "$run_dir"
  run_dir="$(cd -P "$run_dir" && pwd -P)"

  for case_name in 06-validated 07-raw-invalid 08-codex-failed; do
    output_file="$run_dir/worker-output-${case_name%%-*}.md"
    case "$case_name" in
      06-validated)
        if HOME="$e2e_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$run_dir/args-06.txt" FAKE_CODEX_STDIN_FILE="$run_dir/stdin-06.md" "$WORKER_RUNNER" --actor luna --cwd "$root" --task-file "$root/task.md" --requirements-file "$root/requirements.md" --output-file "$output_file"; then runner_status=0; else runner_status=$?; fi
        validation_status=validated; worker_status=completed; sol_result=accepted; mismatch=match; mismatch_reason=none; raw_state=present
        ;;
      07-raw-invalid)
        if HOME="$e2e_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$run_dir/args-07.txt" FAKE_CODEX_STDIN_FILE="$run_dir/stdin-07.md" FAKE_CODEX_REPORT_CASE=status-invalid "$WORKER_RUNNER" --actor luna --cwd "$root" --task-file "$root/task.md" --requirements-file "$root/requirements.md" --output-file "$output_file"; then runner_status=0; else runner_status=$?; fi
        validation_status=raw_invalid; worker_status=blocked; sol_result=blocked; mismatch=not_comparable; mismatch_reason=raw-invalid; raw_state=absent
        ;;
      08-codex-failed)
        if HOME="$e2e_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$run_dir/args-08.txt" FAKE_CODEX_STDIN_FILE="$run_dir/stdin-08.md" FAKE_CODEX_EXIT_STATUS=9 "$WORKER_RUNNER" --actor luna --cwd "$root" --task-file "$root/task.md" --requirements-file "$root/requirements.md" --output-file "$output_file"; then runner_status=0; else runner_status=$?; fi
        validation_status=codex_failed; worker_status=blocked; sol_result=blocked; mismatch=not_comparable; mismatch_reason=codex-nonzero; raw_state=absent
        ;;
    esac
    assert_contains "$output_file.provenance.tsv" "$validation_status"
    if [ "$raw_state" = present ] && [ -f "$output_file" ]; then ok "runner-observation $case_name publishes validated raw"; elif [ "$raw_state" = absent ] && [ ! -e "$output_file" ]; then ok "runner-observation $case_name leaves raw unpublished"; else bad "runner-observation $case_name raw publication state"; fi
    HOME="$e2e_home" "$helper" acceptance --run-dir "$run_dir" --job-id "runner-$case_name" --index "${case_name%%-*}" --requirement-id R1 --verdict "$([ "$sol_result" = accepted ] && printf PASS || printf FAIL)" --evidence-ref "sol-$case_name.md"
    HOME="$e2e_home" "$helper" worker --run-dir "$run_dir" --raw-output "$output_file" --provenance "$output_file.provenance.tsv" --job-id "runner-$case_name" --index "${case_name%%-*}" --status "$worker_status" --sol-measurement-result "$sol_result" --mismatch "$mismatch" --mismatch-reason "$mismatch_reason" --escalation-from none --escalation-to none --effort-escalation-from none --effort-escalation-to none --escalation-reason none --insufficiency-class none --input-sufficient not_applicable --measured-insufficiency-ref none --verification-ref "sol-$case_name.md"
    if [ "$case_name" = 06-validated ] && [ "$runner_status" -eq 0 ]; then ok "runner-observation validated runner exits zero"; elif [ "$case_name" != 06-validated ] && [ "$runner_status" -ne 0 ]; then ok "runner-observation $case_name runner exits nonzero"; else bad "runner-observation $case_name runner exit"; fi
  done
  assert_contains "$run_dir/worker-observations-v1.tsv" "validated$(printf '\t')completed$(printf '\t')accepted$(printf '\t')match"
  assert_contains "$run_dir/worker-observations-v1.tsv" "raw_invalid$(printf '\t')not_provided$(printf '\t')blocked$(printf '\t')not_comparable"
  assert_contains "$run_dir/worker-observations-v1.tsv" "codex_failed$(printf '\t')not_provided$(printf '\t')blocked$(printf '\t')not_comparable"
  assert_contains "$run_dir/sol-acceptance-v1.tsv" "runner-06-validated"
  assert_contains "$run_dir/sol-acceptance-v1.tsv" "runner-07-raw-invalid"
  assert_contains "$run_dir/sol-acceptance-v1.tsv" "runner-08-codex-failed"
}

test_runner_to_observation_e2e

test_worker_runner_path_validation() {
  local fake_codex root outside case_dir output_file args_file status outside_target
  local codex_descendant_case codex_link_target codex_args_file case_home artifact_args_file artifact_child_dir
  fake_codex="$runner_test_dir/fake-codex"

  case_dir="$runner_test_dir/non-git"
  root="$case_dir/repo"
  mkdir -p "$root/.codex" "$root/output"
  write_runner_inputs "$root" non-git
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$case_dir/args" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$root" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
    --output-file "$root/output/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects non-Git cwd"; else bad "worker runner rejects non-Git cwd (got $status)"; fi

  case_dir="$runner_test_dir/subdir"
  root="$case_dir/repo"
  mkdir -p "$case_dir"
  make_git_root "$root"
  mkdir -p "$root/subdir"
  write_runner_inputs "$root" subdir
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$case_dir/args" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$root/subdir" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
    --output-file "$root/output/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects cwd that is not the Git root"; else bad "worker runner rejects cwd that is not the Git root (got $status)"; fi

  case_dir="$runner_test_dir/cwd-symlink-mismatch"
  root="$case_dir/repo"
  mkdir -p "$case_dir"
  make_git_root "$root"
  mkdir -p "$root/nested"
  ln -s "$root/nested" "$case_dir/cwd-link"
  write_runner_inputs "$root" symlink-mismatch
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$case_dir/args" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$case_dir/cwd-link" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
    --output-file "$root/output/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects cwd symlink/root mismatch"; else bad "worker runner rejects cwd symlink/root mismatch (got $status)"; fi

  case_dir="$runner_test_dir/codex-symlink"
  root="$case_dir/repo"
  outside="$case_dir/outside"
  mkdir -p "$case_dir"
  make_git_root "$root"
  mkdir -p "$outside"
  mv "$root/.codex" "$root/codex-real"
  ln -s "$outside" "$root/.codex"
  write_runner_inputs "$root" codex-symlink
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$case_dir/args" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$root" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
    --output-file "$root/output/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects escaping .codex symlink"; else bad "worker runner rejects escaping .codex symlink (got $status)"; fi

  for codex_descendant_case in internal external; do
    case_dir="$runner_test_dir/codex-descendant-symlink-$codex_descendant_case"
    root="$case_dir/repo"
    outside="$case_dir/outside-target"
    mkdir -p "$case_dir"
    make_git_root "$root"
    mkdir -p "$root/.codex-target" "$outside"
    if [ "$codex_descendant_case" = internal ]; then
      codex_link_target="$root/.codex-target"
    else
      codex_link_target="$outside"
    fi
    ln -s "$codex_link_target" "$root/.codex/descendant-link"
    write_runner_inputs "$root" "codex-descendant-$codex_descendant_case"
    codex_args_file="$case_dir/args"
    if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$codex_args_file" \
      FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$root" \
      --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
      --output-file "$root/output/result.md"; then status=0; else status=$?; fi
    if [ "$status" -eq 2 ]; then
      ok "worker runner rejects $codex_descendant_case-pointing .codex descendant symlink"
    else
      bad "worker runner rejects $codex_descendant_case-pointing .codex descendant symlink (got $status)"
    fi
    if [ ! -e "$codex_args_file" ]; then
      ok "worker runner does not invoke fake codex for $codex_descendant_case-pointing .codex symlink"
    else
      bad "worker runner must not invoke fake codex for $codex_descendant_case-pointing .codex symlink"
    fi
  done

  case_dir="$runner_test_dir/output-outside"
  root="$case_dir/repo"
  outside="$case_dir/outside"
  mkdir -p "$case_dir"
  make_git_root "$root"
  mkdir -p "$outside"
  write_runner_inputs "$root" output-outside
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$case_dir/args" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$root" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
    --output-file "$outside/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects output parent outside cwd"; else bad "worker runner rejects output parent outside cwd (got $status)"; fi

  case_dir="$runner_test_dir/output-symlink"
  root="$case_dir/repo"
  outside="$case_dir/outside"
  mkdir -p "$case_dir"
  make_git_root "$root"
  mkdir -p "$outside"
  ln -s "$outside" "$root/output-link"
  write_runner_inputs "$root" output-symlink
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$case_dir/args" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$root" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
    --output-file "$root/output-link/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects symlinked output parent"; else bad "worker runner rejects symlinked output parent (got $status)"; fi

  case_dir="$runner_test_dir/artifact-root-symlink"
  root="$case_dir/repo"
  case_home="$case_dir/home"
  mkdir -p "$case_dir" "$case_home/artifact-real/run"
  make_git_root "$root"
  ln -s "$case_home/artifact-real" "$case_home/.ai-pir-runs"
  write_runner_inputs "$root" artifact-root-symlink
  artifact_args_file="$case_dir/args"
  if HOME="$case_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
    FAKE_CODEX_ARGS_FILE="$artifact_args_file" FAKE_CODEX_STDIN_FILE="$case_dir/stdin" \
    "$WORKER_RUNNER" --actor luna --cwd "$root" --task-file "$root/task.md" \
    --requirements-file "$root/requirements.md" \
    --output-file "$case_home/.ai-pir-runs/run/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects symlinked standard artifact root"; else bad "worker runner rejects symlinked standard artifact root (got $status)"; fi
  if [ ! -e "$artifact_args_file" ]; then ok "worker runner does not invoke fake codex for symlinked artifact root"; else bad "worker runner must not invoke fake codex for symlinked artifact root"; fi

  case_dir="$runner_test_dir/artifact-root-missing"
  root="$case_dir/repo"
  case_home="$case_dir/home"
  mkdir -p "$case_dir" "$case_home"
  make_git_root "$root"
  write_runner_inputs "$root" artifact-root-missing
  artifact_args_file="$case_dir/args"
  if HOME="$case_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
    FAKE_CODEX_ARGS_FILE="$artifact_args_file" FAKE_CODEX_STDIN_FILE="$case_dir/stdin" \
    "$WORKER_RUNNER" --actor luna --cwd "$root" --task-file "$root/task.md" \
    --requirements-file "$root/requirements.md" --output-file "$root/output/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 0 ]; then ok "worker runner accepts cwd output when standard artifact root is missing"; else bad "worker runner accepts cwd output when standard artifact root is missing (got $status)"; fi
  if [ -e "$artifact_args_file" ]; then ok "worker runner invokes fake codex for cwd output without standard artifact root"; else bad "worker runner must invoke fake codex for cwd output without standard artifact root"; fi
  assert_contains "$root/output/result.md" "fake worker report"

  mkdir -p "$case_home/other-artifacts/run"
  artifact_args_file="$case_dir/external-args"
  if HOME="$case_home" WORKER_DELEGATION_CODEX_BIN="$fake_codex" \
    FAKE_CODEX_ARGS_FILE="$artifact_args_file" FAKE_CODEX_STDIN_FILE="$case_dir/external-stdin" \
    "$WORKER_RUNNER" --actor luna --cwd "$root" --task-file "$root/task.md" \
    --requirements-file "$root/requirements.md" \
    --output-file "$case_home/other-artifacts/run/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects external output when standard artifact root is missing"; else bad "worker runner rejects external output when standard artifact root is missing (got $status)"; fi
  if [ ! -e "$artifact_args_file" ]; then ok "worker runner does not invoke fake codex for external output without standard artifact root"; else bad "worker runner must not invoke fake codex for external output without standard artifact root"; fi

  case_dir="$runner_test_dir/artifact-output-child-symlink"
  root="$case_dir/repo"
  outside="$case_dir/outside"
  mkdir -p "$case_dir" "$outside"
  make_git_root "$root"
  artifact_child_dir="$HOME/.ai-pir-runs/output-child-symlink"
  mkdir -p "$artifact_child_dir"
  ln -s "$outside" "$artifact_child_dir/link"
  write_runner_inputs "$root" artifact-output-child-symlink
  artifact_args_file="$case_dir/args"
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$artifact_args_file" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$root" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" \
    --output-file "$artifact_child_dir/link/result.md"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects symlinked artifact output child"; else bad "worker runner rejects symlinked artifact output child (got $status)"; fi
  if [ ! -e "$artifact_args_file" ]; then ok "worker runner does not invoke fake codex for symlinked artifact output child"; else bad "worker runner must not invoke fake codex for symlinked artifact output child"; fi

  case_dir="$runner_test_dir/output-preexisting"
  root="$case_dir/repo"
  mkdir -p "$case_dir"
  make_git_root "$root"
  write_runner_inputs "$root" preexisting
  output_file="$root/output/result.md"
  printf '%s\n' 'pre-existing output' > "$output_file"
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$case_dir/args" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$root" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" --output-file "$output_file"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects pre-existing output"; else bad "worker runner rejects pre-existing output (got $status)"; fi
  assert_contains "$output_file" "pre-existing output"

  case_dir="$runner_test_dir/provenance-preexisting"
  root="$case_dir/repo"
  mkdir -p "$case_dir"
  make_git_root "$root"
  write_runner_inputs "$root" provenance-preexisting
  output_file="$root/output/result.md"
  printf '%s\n' 'pre-existing provenance' > "$output_file.provenance.tsv"
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$case_dir/args" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" "$WORKER_RUNNER" --actor luna --cwd "$root" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" --output-file "$output_file"; then status=0; else status=$?; fi
  if [ "$status" -eq 2 ]; then ok "worker runner rejects pre-existing provenance sidecar"; else bad "worker runner must reject pre-existing provenance sidecar (got $status)"; fi
  if [ ! -e "$case_dir/args" ]; then ok "worker runner does not invoke Codex when provenance sidecar exists"; else bad "worker runner must not invoke Codex when provenance sidecar exists"; fi

  case_dir="$runner_test_dir/publication-collision"
  root="$case_dir/repo"
  mkdir -p "$case_dir"
  make_git_root "$root"
  write_runner_inputs "$root" publication-collision
  output_file="$root/output/result.md"
  args_file="$case_dir/args"
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$args_file" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" FAKE_CODEX_FINAL_OUTPUT="$output_file" \
    FAKE_CODEX_COLLISION=file "$WORKER_RUNNER" --actor luna --cwd "$root" \
    --task-file "$root/task.md" --requirements-file "$root/requirements.md" --output-file "$output_file"; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "worker runner rejects raced publication collision"; else bad "worker runner rejects raced publication collision"; fi
  assert_contains "$output_file" "raced existing output"

  case_dir="$runner_test_dir/publication-symlink-collision"
  root="$case_dir/repo"
  outside_target="$case_dir/outside-target"
  mkdir -p "$case_dir"
  make_git_root "$root"
  write_runner_inputs "$root" publication-symlink
  output_file="$root/output/result.md"
  printf '%s\n' 'outside remains unchanged' > "$outside_target"
  if WORKER_DELEGATION_CODEX_BIN="$fake_codex" FAKE_CODEX_ARGS_FILE="$case_dir/args" \
    FAKE_CODEX_STDIN_FILE="$case_dir/stdin" FAKE_CODEX_FINAL_OUTPUT="$output_file" \
    FAKE_CODEX_OUTSIDE_TARGET="$outside_target" FAKE_CODEX_COLLISION=symlink \
    "$WORKER_RUNNER" --actor luna --cwd "$root" --task-file "$root/task.md" \
    --requirements-file "$root/requirements.md" --output-file "$output_file"; then status=0; else status=$?; fi
  if [ "$status" -ne 0 ]; then ok "worker runner rejects raced symlink publication collision"; else bad "worker runner rejects raced symlink publication collision"; fi
  if [ -L "$output_file" ]; then ok "worker runner leaves raced final symlink untouched"; else bad "worker runner leaves raced final symlink untouched"; fi
  assert_contains "$outside_target" "outside remains unchanged"
}

test_worker_runner_path_validation

test_codex_adapter_conversion() {
  local function_file fixture converted
  function_file="$runner_test_dir/codexize-stream.sh"
  fixture="$runner_test_dir/claude-adapter-fixture.md"
  converted="$runner_test_dir/codex-adapter-fixture.md"
  awk '/^codexize_stream\(\) \{/{capture=1} capture {print} capture && /^\}/{exit}' \
    "$DOT_DIR/etc/sync-codex.sh" > "$function_file"
  cat > "$fixture" <<'EOF'
Agent Teams 機能（`TeamCreate` ツールで構成する）
`Agent` ツール
`Agent` tool
Agent ツール
Agent tool
`tools` に `Agent` を持つ planner は spawn する。
tools に `Agent` を持たない tester。
TeamCreate SendMessage subagent_type
EOF
  if bash -c 'set -e; . "$1"; codexize_stream < "$2" > "$3"' _ "$function_file" "$fixture" "$converted"; then
    ok "Codex adapter conversion function executes from sync source"
  else
    bad "Codex adapter conversion function executes from sync source"
  fi
  assert_contains "$converted" "spawn_agent"
  assert_contains "$converted" "agent_type"
  assert_contains "$converted" "collaboration API"
  assert_contains "$converted" '`send_message`'
  assert_not_contains "$converted" '`Agent` ツール'
  assert_not_contains "$converted" '`Agent` tool'
  assert_not_contains "$converted" 'Agent ツール'
  assert_not_contains "$converted" 'Agent tool'
  assert_not_contains "$converted" 'tools に `Agent`'
  assert_not_contains "$converted" 'tools に Agent'
}

test_codex_adapter_conversion

# instruction-refactor keeps planning and acceptance with Sol, while all
# concrete repository changes use the shared worker contract. This regression
# guard must fail if the old main-Codex direct-edit exception returns.
INSTRUCTION_REFACTOR_FILE="${DOT_DIR}/.codex/skills/instruction-refactor/SKILL.md"
PLANNER_AGENT_FILE="${DOT_DIR}/.codex/agents/planner.toml"
assert_file "$INSTRUCTION_REFACTOR_FILE"
assert_file "$PLANNER_AGENT_FILE"
assert_contains "$PLANNER_AGENT_FILE" 'implementation-{IMPL_INDEX}-shard-{SHARD_ID}.md'
assert_not_contains "$PLANNER_AGENT_FILE" 'implementation-{IMPL_INDEX}-{SHARD_ID}.md'
assert_contains "$INSTRUCTION_REFACTOR_FILE" ".codex/skills/worker-delegation/SKILL.md"
assert_contains "$INSTRUCTION_REFACTOR_FILE" "scripts/run-worker.sh"
assert_contains "$INSTRUCTION_REFACTOR_FILE" "--actor luna"
assert_contains "$INSTRUCTION_REFACTOR_FILE" "--actor terra"
assert_contains "$INSTRUCTION_REFACTOR_FILE" "Sol"
assert_contains "$INSTRUCTION_REFACTOR_FILE" "reviewer / tester"
assert_contains "$INSTRUCTION_REFACTOR_FILE" 'REPORT_SUFFIX="$IMPL_INDEX"'
assert_contains "$INSTRUCTION_REFACTOR_FILE" 'worker-output-${REPORT_SUFFIX}.md'
assert_contains "$INSTRUCTION_REFACTOR_FILE" 'implementation-${REPORT_SUFFIX}.md'
assert_contains "$INSTRUCTION_REFACTOR_FILE" 'sol-acceptance-${REPORT_SUFFIX}.md'
assert_not_contains "$INSTRUCTION_REFACTOR_FILE" 'worker-output-${IMPL_INDEX}.md'
assert_not_contains "$INSTRUCTION_REFACTOR_FILE" 'implementation-${IMPL_INDEX}.md'
instruction_single_run="$runner_test_dir/instruction-refactor-single"
mkdir -p "$instruction_single_run"
if RUN_DIR="$instruction_single_run" IMPL_INDEX=01 bash -c 'REPORT_SUFFIX="$IMPL_INDEX"; WORKER_RAW_OUTPUT="${RUN_DIR}/worker-output-${REPORT_SUFFIX}.md"; IMPLEMENTATION_REPORT_PATH="${RUN_DIR}/implementation-${REPORT_SUFFIX}.md"; ACCEPTANCE_REF="${RUN_DIR}/sol-acceptance-${REPORT_SUFFIX}.md"; [ "$WORKER_RAW_OUTPUT" = "$RUN_DIR/worker-output-01.md" ] && [ "$IMPLEMENTATION_REPORT_PATH" = "$RUN_DIR/implementation-01.md" ] && [ "$ACCEPTANCE_REF" = "$RUN_DIR/sol-acceptance-01.md" ]'; then
  ok "instruction-refactor single REPORT_SUFFIX paths are executable"
else
  bad "instruction-refactor single REPORT_SUFFIX paths are executable"
fi
assert_not_contains "$INSTRUCTION_REFACTOR_FILE" "メイン Codex が直接 Edit/Write"
assert_not_contains "$INSTRUCTION_REFACTOR_FILE" "メイン Codexが直接 Edit/Write"
if grep -Eiq '(メイン Codex|main Codex).*(直接|direct).*(Edit|Write|編集|修正)' "$INSTRUCTION_REFACTOR_FILE"; then
  bad "instruction-refactor contains a main-Codex direct repository edit instruction"
else
  ok "instruction-refactor has no main-Codex direct repository edit instruction"
fi

ARCHITECTURE_SPEC="${DOT_DIR}/AI-WORKFLOW-SPEC.md"
assert_file "$ARCHITECTURE_SPEC"
WORKER_SKILL_FILE="${WORKER_SKILL_DIR}/SKILL.md"
CODEX_GENERATED_GUIDANCE="${DOT_DIR}/.codex/AGENTS.md"
CODEX_GENERATED_AGENT_DELEGATION="${DOT_DIR}/.codex/agent-delegation.md"
assert_file "$CODEX_GENERATED_GUIDANCE"
assert_file "$CODEX_GENERATED_AGENT_DELEGATION"
assert_not_contains "$WORKER_SKILL_FILE" "sol-direct"
assert_not_contains "$ARCHITECTURE_SPEC" "sol-direct"
assert_not_contains "$CODEX_GENERATED_GUIDANCE" "sol-direct"
assert_not_contains "$CODEX_GENERATED_AGENT_DELEGATION" '`Agent` ツール'
assert_not_contains "$CODEX_GENERATED_AGENT_DELEGATION" '`Agent` tool'
assert_not_contains "$CODEX_GENERATED_AGENT_DELEGATION" 'Agent ツール'
assert_not_contains "$CODEX_GENERATED_AGENT_DELEGATION" 'Agent tool'
assert_not_contains "$CODEX_GENERATED_AGENT_DELEGATION" '`tools` に `Agent`'
assert_not_contains "$CODEX_GENERATED_AGENT_DELEGATION" 'tools に Agent'
assert_not_contains "${DOT_DIR}/etc/sync-codex.sh" "sol-direct"
assert_contains "$WORKER_SKILL_FILE" "親/main Solは具体的なリポジトリ実装を行わない"
assert_contains "$WORKER_SKILL_FILE" "source ownership"
assert_contains "$WORKER_SKILL_FILE" "所有範囲外のファイルを書き込む認可ではありません"
assert_contains "$WORKER_SKILL_FILE" "物理的に解決したcwdがGitの物理的なトップレベル"
assert_contains "$WORKER_SKILL_FILE" "no-replace hard link"
assert_contains "$WORKER_SKILL_FILE" "Luna Max → measured Terra High → evidence-only Terra Max → exceptional Sol High worker → evidence-only Sol Max"
assert_contains "$WORKER_SKILL_FILE" "multi-stage causality"
assert_contains "$WORKER_SKILL_FILE" "design contradiction"
assert_contains "$WORKER_SKILL_FILE" "cross-module invariants"
assert_contains "$WORKER_SKILL_FILE" "security/data-integrity risk"
assert_contains "$WORKER_SKILL_FILE" "Terra High insufficiency"
assert_contains "$WORKER_SKILL_FILE" "highest-complexity/high-risk evidence"
assert_contains "$WORKER_SKILL_FILE" "Sol High insufficiency"
assert_contains "$WORKER_SKILL_FILE" "要件不足や起動不能を理由に親/main Solが実装を引き取ってはいけません"
assert_contains "$WORKER_SKILL_FILE" "deterministic-completion-check.md"
assert_contains "$WORKER_SKILL_FILE" "verify-deterministic-check.sh"
assert_contains "$WORKER_SKILL_FILE" "PHANTOM_CLAIM"
assert_contains "$WORKER_SKILL_FILE" "UNDECLARED_CHANGE"
assert_contains "$WORKER_SKILL_FILE" '標準Sol artifact root `$HOME/.ai-pir-runs`'
assert_contains "$WORKER_SKILL_FILE" '.codex`配下のすべてのシンボリックリンク'
assert_contains "$WORKER_SKILL_FILE" "no-replace hard link"
assert_contains "$WORKER_SKILL_FILE" "malicious same-UID host process"
assert_contains "$WORKER_SKILL_FILE" "Codex CLIはpath文字列しか受け取らず"
assert_contains "$WORKER_SKILL_FILE" "別UID、OS sandbox、mount isolation"
assert_contains "$WORKER_SKILL_FILE" "atomic/openatで完全保護したとは記載・解釈しません"
for report_field in ACTOR ACTUAL_MODEL ACTUAL_EFFORT STATUS CHANGED_FILES OBSERVED_RESULTS BLOCKERS ESCALATION_REASON; do
  assert_contains "$WORKER_SKILL_FILE" "${report_field}:"
done
assert_contains "$ARCHITECTURE_SPEC" "default for **concrete repository-changing implementation across"
assert_contains "$ARCHITECTURE_SPEC" "parent/main Sol is commander only"
assert_contains "$ARCHITECTURE_SPEC" "never performs concrete repository implementation"
assert_contains "$ARCHITECTURE_SPEC" 'model = "gpt-5.6-sol"'
assert_contains "$ARCHITECTURE_SPEC" 'model_reasoning_effort = "high"'
assert_contains "$ARCHITECTURE_SPEC" "High is the normal commander setting"
assert_contains "$ARCHITECTURE_SPEC" "never the main default"
assert_contains "$ARCHITECTURE_SPEC" "Luna/Terra model pins belong to the worker-delegation runner"
assert_contains "$ARCHITECTURE_SPEC" "Luna Max → measured Terra High → evidence-only"
assert_contains "$ARCHITECTURE_SPEC" "Luna Max default worker"
assert_contains "$ARCHITECTURE_SPEC" "measured Terra escalation"
assert_contains "$ARCHITECTURE_SPEC" "multi-stage causality"
assert_contains "$ARCHITECTURE_SPEC" "design contradiction"
assert_contains "$ARCHITECTURE_SPEC" "cross-module invariants"
assert_contains "$ARCHITECTURE_SPEC" "security/data-integrity risk"
assert_contains "$ARCHITECTURE_SPEC" "highest-complexity/high-risk evidence"
assert_contains "$ARCHITECTURE_SPEC" "same-cause Terra Max attempt is limited to one"
assert_contains "$ARCHITECTURE_SPEC" "at most once for the same cause"
assert_contains "$ARCHITECTURE_SPEC" "no automatic"
assert_contains "$ARCHITECTURE_SPEC" "non-repository orchestration artifacts remain separate"
assert_contains "$ARCHITECTURE_SPEC" "reviewer and tester are separate"
assert_contains "$ARCHITECTURE_SPEC" 'pir2async` is'
assert_contains "$ARCHITECTURE_SPEC" "every concrete repository implementation and correction it"
assert_contains "$ARCHITECTURE_SPEC" "performs uses the shared worker-delegation ladder"
assert_contains "$ARCHITECTURE_SPEC" 'Luna Max -> measured Terra High -> evidence-only Terra Max -> exceptional Sol'
assert_contains "$ARCHITECTURE_SPEC" "source ownership boundary"
assert_contains "$ARCHITECTURE_SPEC" "authorize writes to out-of-scope files"
assert_contains "$ARCHITECTURE_SPEC" 'standard Sol artifact root'
assert_contains "$ARCHITECTURE_SPEC" '$HOME/.ai-pir-runs'
assert_contains "$ARCHITECTURE_SPEC" "rejects every symlink below that"
assert_contains "$ARCHITECTURE_SPEC" "configuration"
assert_contains "$ARCHITECTURE_SPEC" "detectable accidental races"
assert_contains "$ARCHITECTURE_SPEC" "same-UID host process"
assert_contains "$ARCHITECTURE_SPEC" "The Codex CLI"
assert_contains "$ARCHITECTURE_SPEC" "directory/file-descriptor"
assert_contains "$ARCHITECTURE_SPEC" "openat"
assert_contains "$ARCHITECTURE_SPEC" "atomic-open"
assert_not_contains "$ARCHITECTURE_SPEC" "experimental/quarantined"
assert_not_contains "$ARCHITECTURE_SPEC" "intentionally outside the worker ladder"

# Deterministic completion is a common worker-delegation SSOT consumed by all
# concrete Codex workflows; no generated adapter content is required here.
PIR2_REFERENCE_DIR="${DOT_DIR}/.codex/skills/pir2/references"
WORKER_REFERENCE_DIR="${DOT_DIR}/.codex/skills/worker-delegation/references"
WORKER_SCRIPT_DIR="${DOT_DIR}/.codex/skills/worker-delegation/scripts"
NEXT_STEPS_REFERENCE="${PIR2_REFERENCE_DIR}/next-steps-queue.md"
HANDOFF_REFERENCE="${PIR2_REFERENCE_DIR}/handoff-cleanup.md"
OBSERVABILITY_REFERENCE="${PIR2_REFERENCE_DIR}/worker-observability.md"
IMPLEMENTATION_DELEGATION_REFERENCE="${PIR2_REFERENCE_DIR}/implementation-delegation.md"
DETERMINISTIC_REFERENCE="${WORKER_REFERENCE_DIR}/deterministic-completion-check.md"
DETERMINISTIC_VERIFIER="${WORKER_SCRIPT_DIR}/verify-deterministic-check.sh"
assert_file "$NEXT_STEPS_REFERENCE"
assert_file "$HANDOFF_REFERENCE"
assert_file "$OBSERVABILITY_REFERENCE"
assert_file "$IMPLEMENTATION_DELEGATION_REFERENCE"
assert_file "$DETERMINISTIC_REFERENCE"
assert_file "$DETERMINISTIC_VERIFIER"
assert_contains "$NEXT_STEPS_REFERENCE" "Read"
assert_contains "$NEXT_STEPS_REFERENCE" "<!-- done: <ISO8601> -->"
assert_contains "$NEXT_STEPS_REFERENCE" "必須運用"
assert_contains "$HANDOFF_REFERENCE" "worker"
assert_contains "$HANDOFF_REFERENCE" "最終更新"
assert_contains "$OBSERVABILITY_REFERENCE" "worker-observations-v1.tsv"
assert_contains "$OBSERVABILITY_REFERENCE" "sol-acceptance-v1.tsv"
assert_contains "$OBSERVABILITY_REFERENCE" "independent-verdicts-v1.tsv"
assert_contains "$OBSERVABILITY_REFERENCE" "append-only"
assert_contains "$OBSERVABILITY_REFERENCE" "automatic_fallback"
assert_contains "$IMPLEMENTATION_DELEGATION_REFERENCE" '${IMPL_INDEX}-shard-${SHARD_ID}'
assert_contains "$IMPLEMENTATION_DELEGATION_REFERENCE" '${IMPL_INDEX}-review-fix-${REVIEW_FIX_SHARD_ID}'
assert_contains "$IMPLEMENTATION_DELEGATION_REFERENCE" '${IMPL_INDEX}-unit-${UNIT_ID}'
assert_not_contains "$IMPLEMENTATION_DELEGATION_REFERENCE" '${IMPL_INDEX}-${SHARD_ID}'
assert_not_contains "$IMPLEMENTATION_DELEGATION_REFERENCE" '${IMPL_INDEX}-fix-${REVIEW_FIX_SHARD_ID}'
assert_contains "$DETERMINISTIC_REFERENCE" "決定論的完了検証"
assert_contains "$DETERMINISTIC_REFERENCE" "PHANTOM_CLAIM"
assert_contains "$DETERMINISTIC_REFERENCE" "UNDECLARED_CHANGE"
assert_contains "$DETERMINISTIC_REFERENCE" "worker-delegation"
assert_contains "$DETERMINISTIC_REFERENCE" "Sol"
assert_contains "$DETERMINISTIC_VERIFIER" "deterministic-completion-check.md"
assert_contains "$DETERMINISTIC_VERIFIER" "--syntax-only"
if sh -n "$DETERMINISTIC_VERIFIER" && bash -n "$DETERMINISTIC_VERIFIER"; then
  ok "deterministic completion verifier syntax is valid"
else
  bad "deterministic completion verifier syntax is invalid"
fi
if bash "$DETERMINISTIC_VERIFIER" >/dev/null 2>&1; then
  ok "deterministic completion verifier passes"
else
  bad "deterministic completion verifier failed"
fi
if [ ! -e "${PIR2_REFERENCE_DIR}/deterministic-completion-check.md" ] \
  && [ ! -L "${PIR2_REFERENCE_DIR}/deterministic-completion-check.md" ] \
  && [ ! -e "${PIR2_REFERENCE_DIR}/verify-deterministic-check.sh" ] \
  && [ ! -L "${PIR2_REFERENCE_DIR}/verify-deterministic-check.sh" ]; then
  ok "obsolete PIR2 deterministic paths are absent"
else
  bad "obsolete PIR2 deterministic paths must be absent"
fi
stale_deterministic_refs=0
while IFS= read -r codex_file; do
  if grep -Eq '\.codex/skills/pir2/references/(deterministic-completion-check\.md|verify-deterministic-check\.sh)' "$codex_file"; then
    bad "stale PIR2 deterministic path reference in ${codex_file#"$DOT_DIR/"}"
    stale_deterministic_refs=1
  fi
done < <(find "${DOT_DIR}/.codex" -type f -print)
if [ "$stale_deterministic_refs" -eq 0 ]; then
  ok "no stale PIR2 deterministic path references in Codex overlay"
fi
# Concrete Codex workflows use the shared actor contract. Epic delegates its
# Ti work through PIR2, so its SSOT connection is checked separately below.
for workflow in debug ir instruction-refactor pir2 writing-plan pir2async; do
  workflow_file="${DOT_DIR}/.codex/skills/${workflow}/SKILL.md"
  assert_workflow_raw_canonical_contract "$workflow" "$workflow_file"
  assert_file "$workflow_file"
  assert_contains "$workflow_file" "worker-delegation"
  assert_contains "$workflow_file" "scripts/run-worker.sh"
  assert_contains "$workflow_file" "--actor luna"
  assert_contains "$workflow_file" "deterministic-completion-check.md"
  assert_contains "$workflow_file" "pre-set"
  assert_contains "$workflow_file" "post-set"
  assert_contains "$workflow_file" "PHANTOM_CLAIM"
  assert_contains "$workflow_file" "UNDECLARED_CHANGE"
  assert_contains "$workflow_file" '--effort-escalation-from "$EFFORT_ESCALATION_FROM"'
  assert_contains "$workflow_file" '--effort-escalation-to "$EFFORT_ESCALATION_TO"'
  assert_contains "$workflow_file" "reviewer"
  assert_contains "$workflow_file" "tester"
  assert_contains "$workflow_file" "spawn_agent(agent_type=\"tester\")"
  assert_contains "$workflow_file" "TEST_INDEX"
  assert_contains "$workflow_file" "test-"
  assert_contains "$workflow_file" "every reviewer"
  assert_contains "$workflow_file" "overall FAIL"
  assert_contains "$workflow_file" "hard stop"
done
test_raw_canonical_claimed_fixture
PIR2_FILE="${DOT_DIR}/.codex/skills/pir2/SKILL.md"
REFACTOR_ADVISOR_GATE_FILE="${PIR2_REFERENCE_DIR}/refactor-advisor-gate.md"
assert_contains "$PIR2_FILE" "deterministic-completion-check.md"
assert_contains "$PIR2_FILE" "verify-deterministic-check.sh"
assert_contains "$PIR2_FILE" "PHANTOM_CLAIM"
assert_contains "$PIR2_FILE" "UNDECLARED_CHANGE"
assert_contains "$PIR2_FILE" "Sol acceptance"
assert_contains "$PIR2_FILE" "pre-set"
assert_contains "$PIR2_FILE" "post-set"
assert_contains "$PIR2_FILE" "reviewer"
assert_contains "$PIR2_FILE" "tester"
assert_contains "$PIR2_FILE" "every reviewer in REVIEWER_SET returns PASS"
assert_contains "$PIR2_FILE" "INNER_LOOP_COUNT >= 3"
assert_contains "$PIR2_FILE" "overall FAIL"
assert_contains "$PIR2_FILE" "ユーザーの判断を求める"
assert_contains "$PIR2_FILE" "refactor-advisor、tester、または成功完了を進めない"
assert_not_contains "$PIR2_FILE" "FAIL で INNER_LOOP_COUNT 上限到達の場合はスキップしてステップ 8 へ"
assert_file "$REFACTOR_ADVISOR_GATE_FILE"
assert_contains "$REFACTOR_ADVISOR_GATE_FILE" 'every reviewer が `VERDICT: PASS`'
assert_contains "$REFACTOR_ADVISOR_GATE_FILE" "overall FAIL"
assert_contains "$REFACTOR_ADVISOR_GATE_FILE" "ユーザーの判断を求める hard stop"
assert_contains "$REFACTOR_ADVISOR_GATE_FILE" "tester、成功完了、または refactor-advisor の再実行へ進めない"
assert_not_contains "$REFACTOR_ADVISOR_GATE_FILE" "上限到達の場合はスキップしてテストフェーズへ直接進む"
assert_not_contains "$REFACTOR_ADVISOR_GATE_FILE" "上限到達時はテストフェーズへ強制移行"
EPIC_FILE="${DOT_DIR}/.codex/skills/epic/SKILL.md"
assert_file "$EPIC_FILE"
assert_contains "$EPIC_FILE" "worker-delegation"
assert_contains "$EPIC_FILE" ".codex/skills/worker-delegation/SKILL.md"

BRAINSTORM_FILE="${DOT_DIR}/.codex/skills/brainstorm/SKILL.md"
assert_file "$BRAINSTORM_FILE"
assert_contains "$BRAINSTORM_FILE" "設計専用"
assert_contains "$BRAINSTORM_FILE" "実装workerの起動は行いません"
assert_contains "$BRAINSTORM_FILE" "へ直接接続しません"
assert_not_contains "$BRAINSTORM_FILE" "scripts/run-worker.sh"

PIR2ASYNC_FILE="${DOT_DIR}/.codex/skills/pir2async/SKILL.md"
assert_file "$PIR2ASYNC_FILE"
assert_contains "$PIR2ASYNC_FILE" "spawn_agent"
assert_contains "$PIR2ASYNC_FILE" "send_message"
assert_contains "$PIR2ASYNC_FILE" "followup_task"
assert_contains "$PIR2ASYNC_FILE" "## ステップ 3: 非同期探索"
assert_contains "$PIR2ASYNC_FILE" "## ステップ 4: planner と再探索"
assert_contains "$PIR2ASYNC_FILE" "## ステップ 6: 具体実装は worker-delegation だけで行う"
assert_contains "$PIR2ASYNC_FILE" "## ステップ 7: 非同期 reviewer 連携"
assert_contains "$PIR2ASYNC_FILE" "## ステップ 8: tester と外側ループ"
assert_contains "$PIR2ASYNC_FILE" "## ステップ 9: 振り返りと handoff"
assert_contains "$PIR2ASYNC_FILE" "read-only"
assert_contains "$PIR2ASYNC_FILE" "worker-delegation"
assert_contains "$PIR2ASYNC_FILE" "scripts/run-worker.sh"
assert_contains "$PIR2ASYNC_FILE" "--actor luna"
assert_contains "$PIR2ASYNC_FILE" "--cwd"
assert_contains "$PIR2ASYNC_FILE" "--task-file"
assert_contains "$PIR2ASYNC_FILE" "--requirements-file"
assert_contains "$PIR2ASYNC_FILE" "--output-file"
assert_contains "$PIR2ASYNC_FILE" "implementation-IMPL_INDEX-shard-SHARD_ID.md"
assert_contains "$PIR2ASYNC_FILE" "implementation-IMPL_INDEX-review-fix-REVIEW_FIX_SHARD_ID.md"
assert_not_contains "$PIR2ASYNC_FILE" "implementation-IMPL_INDEX-SHARD_ID.md"
assert_not_contains "$PIR2ASYNC_FILE" "implementation-IMPL_INDEX-fix-REVIEW_FIX_SHARD_ID.md"
assert_contains "$PIR2ASYNC_FILE" "REVIEWER_SET"
assert_contains "$PIR2ASYNC_FILE" "OUTER_LOOP_COUNT"
assert_contains "$PIR2ASYNC_FILE" "INNER_LOOP_COUNT=0"
assert_contains "$PIR2ASYNC_FILE" "INNER_LOOP_COUNT += 1"
assert_contains "$PIR2ASYNC_FILE" "deterministic-completion-check.md"
assert_contains "$PIR2ASYNC_FILE" "すべての worker-delegation job とすべての correction"
assert_contains "$PIR2ASYNC_FILE" "initial implementation"
assert_contains "$PIR2ASYNC_FILE" "reviewer FAIL 後・tester FAIL 後"
assert_contains "$PIR2ASYNC_FILE" "pre-set"
assert_contains "$PIR2ASYNC_FILE" "post-set"
assert_contains "$PIR2ASYNC_FILE" "canonical worker report"
assert_contains "$PIR2ASYNC_FILE" "PHANTOM_CLAIM"
assert_contains "$PIR2ASYNC_FILE" "hard fail"
assert_contains "$PIR2ASYNC_FILE" "UNDECLARED_CHANGE"
assert_contains "$PIR2ASYNC_FILE" "warning"
assert_contains "$PIR2ASYNC_FILE" "Sol が acceptance を記録できます"
assert_contains "$PIR2ASYNC_FILE" "全 role の verdict が PASS"
assert_contains "$PIR2ASYNC_FILE" "every reviewer in REVIEWER_SET returns PASS"
assert_contains "$PIR2ASYNC_FILE" "overall FAIL"
assert_contains "$PIR2ASYNC_FILE" "ユーザーの判断を求める"
assert_contains "$PIR2ASYNC_FILE" "retry-cap hard stop"
assert_contains "$PIR2ASYNC_FILE" "correction job、tester、または成功完了を進めてはいけない"
assert_contains "$PIR2ASYNC_FILE" '以前に PASS だった role も含めた `REVIEWER_SET` の every reviewer'
assert_contains "$PIR2ASYNC_FILE" "tester へ進めたり成功完了を報告したりしてはいけない"
assert_contains "$PIR2ASYNC_FILE" '${PROJECT_ROOT}/.codex/skills/pir2/references/sanitized-cwd.md'
assert_contains "$PIR2ASYNC_FILE" '$PROJECT_ROOT/.codex/skills/pir2/references/next-steps-queue.md'
assert_contains "$PIR2ASYNC_FILE" '$PROJECT_ROOT/.codex/skills/pir2/references/handoff-cleanup.md'
# The literal legacy path is the contract string; suppress ShellCheck's
# tilde-expansion warning without changing the assertion value.
# shellcheck disable=SC2088
assert_not_contains "$PIR2ASYNC_FILE" '~/.agents/skills/pir2/'
assert_not_contains "$PIR2ASYNC_FILE" "codex exec"
assert_not_contains "$PIR2ASYNC_FILE" "Agent Teams"
assert_not_contains "$PIR2ASYNC_FILE" "Agent tool"
assert_not_contains "$PIR2ASYNC_FILE" "SendMessage"

WALKTHROUGH_REFERENCE_DIR="${DOT_DIR}/.codex/skills/walkthrough/references"
HTML_MODE_REFERENCE="${WALKTHROUGH_REFERENCE_DIR}/html-mode.md"
HTML_TEMPLATE="${WALKTHROUGH_REFERENCE_DIR}/html-template.html"
assert_file "$HTML_MODE_REFERENCE"
assert_file "$HTML_TEMPLATE"
assert_contains "$HTML_MODE_REFERENCE" "単一ファイル完結の HTML 版"
assert_contains "$HTML_MODE_REFERENCE" "外部リクエスト 0"
assert_contains "$HTML_MODE_REFERENCE" "references/html-template.html"
assert_contains "$HTML_MODE_REFERENCE" "セルフチェック"
assert_contains "$HTML_TEMPLATE" "<!doctype html>"
assert_contains "$HTML_TEMPLATE" "{{TITLE}}"
assert_contains "$HTML_TEMPLATE" "{{TOC}}"
assert_contains "$HTML_TEMPLATE" "{{CONTENT}}"
assert_contains "$HTML_TEMPLATE" "{{MD_PATH}}"
assert_contains "$HTML_TEMPLATE" "{{GENERATED_AT}}"

# Codex-native routing must not retain live Claude-era launch tokens. Scope the
# scan to Codex skills, agents, and protocol files so native Unity documentation
# remains out of the routing check. Match singular SendMessage only: Unity's
# legitimate SendMessages API reference is intentionally allowed.
TEAM_MEMBER_PROMPTS_FILE="${DOT_DIR}/.codex/skills/pir2/references/team-member-prompts.md"
if [ -e "$TEAM_MEMBER_PROMPTS_FILE" ] || [ -L "$TEAM_MEMBER_PROMPTS_FILE" ]; then
  bad "obsolete Codex team-member-prompts artifact must be absent"
else
  ok "obsolete Codex team-member-prompts artifact is absent"
fi
team_member_reference_found=0
while IFS= read -r file; do
  case "$file" in
    "${DOT_DIR}/.codex/"*) ;;
    *) continue ;;
  esac
  if grep -Fq -- "team-member-prompts" "$file" 2>/dev/null; then
    bad "obsolete team-member-prompts reference in ${file#"$DOT_DIR/"}"
    team_member_reference_found=1
  fi
done < "$contract_file_list"
if [ "$team_member_reference_found" -eq 0 ]; then
  ok "no Codex team-member-prompts references"
fi

codex_routing_residue_found=0
codex_routing_residue_pattern='subagent_type|Agent Teams|`Agent`[[:space:]]+ツール|`Agent`[[:space:]]+tool|Agent[[:space:]]+ツール|Agent[[:space:]]+tool|`tools`[^[:cntrl:]]*Agent|tools[^[:cntrl:]]*Agent|SendMessage([^[:alnum:]_]|$)|gpt-5[.]5|gpt-5[.]4-mini'
while IFS= read -r file; do
  case "$file" in
    "${DOT_DIR}/.codex/skills/"*|"${DOT_DIR}/.codex/agents/"*|"${DOT_DIR}/.codex/"*protocol*.md|"${CODEX_GENERATED_AGENT_DELEGATION}")
      if grep -nE "$codex_routing_residue_pattern" "$file" >/dev/null 2>&1; then
        bad "live Claude-era routing residue in ${file#"$DOT_DIR/"}"
        codex_routing_residue_found=1
      fi
      ;;
  esac
done < "$contract_file_list"
if [ "$codex_routing_residue_found" -eq 0 ]; then
  ok "no live Claude-era routing residues in Codex-native skills/agents/protocol"
fi

# Worker-specific routing must remain out of the shared core. The existing
# shared /codex consultation skill may describe its own Codex model choices;
# this guard specifically prevents the worker package/runner from leaking into
# .agents/**.
if find "${DOT_DIR}/.agents" -type f -print0 | xargs -0 grep -El 'worker-delegation|run-worker\.sh' >/dev/null 2>&1; then
  bad "worker delegation routing leaked into .agents/**"
else
  ok "worker delegation routing stays out of .agents/**"
fi
assert_not_contains "${DOT_DIR}/AGENTS.md" "gpt-5.6-luna"
assert_not_contains "${DOT_DIR}/AGENTS.md" "gpt-5.6-terra"
assert_contains "${DOT_DIR}/.codex/config.base.toml" "Codex-native model routing"
CODEX_BASE_CONFIG="${DOT_DIR}/.codex/config.base.toml"
CODEX_GENERATED_CONFIG="${DOT_DIR}/.codex/config.toml"
assert_file "$CODEX_BASE_CONFIG"
assert_file "$CODEX_GENERATED_CONFIG"
for config_file in "$CODEX_BASE_CONFIG" "$CODEX_GENERATED_CONFIG"; do
  assert_contains "$config_file" 'model = "gpt-5.6-sol"'
  assert_contains "$config_file" 'model_reasoning_effort = "high"'
  assert_not_contains "$config_file" 'model = "gpt-5.6-terra"'
  assert_not_contains "$config_file" 'model = "gpt-5.6-luna"'
  assert_contains "$config_file" 'max_depth = 2'
done
if python3 - "$CODEX_BASE_CONFIG" "$CODEX_GENERATED_CONFIG" <<'PY'
import sys
import tomllib

for config_path in sys.argv[1:]:
    with open(config_path, "rb") as config_stream:
        config = tomllib.load(config_stream)
    assert config["model"] == "gpt-5.6-sol"
    assert config["model_reasoning_effort"] == "high"
    assert config["agents"]["max_depth"] == 2
    assert "permissions" not in config
    assert "default_permissions" not in config
PY
then
  ok "Codex base/generated configs parse as TOML and pin main Sol/high"
else
  bad "Codex base/generated configs must parse as TOML and pin main Sol/high"
fi
assert_contains "$WORKER_RUNNER" 'model="gpt-5.6-terra"'

for a in deliberator epic-planner gate hypothesizer synthesizer thinker explorer planner; do
  assert_file "${DOT_DIR}/.codex/agents/${a}.toml"
done

# codex-runner must stay absent on Codex (running codex from codex is pointless)
if [ -f "${DOT_DIR}/.codex/agents/codex-runner.toml" ]; then
  bad "codex-runner.toml must not exist on Codex"
else
  ok "codex-runner omitted on Codex"
fi

for s in deepthink research epic unity-mcp-skill pir2; do
  assert_file "${DOT_DIR}/.codex/skills/${s}/SKILL.md"
done

# drift checker clean
if bash "${DOT_DIR}/etc/check-shared-drift.sh" >/dev/null; then
  ok "check-shared-drift clean"
else
  bad "check-shared-drift failed"
fi

echo
echo "codex contracts: ${pass} passed, ${fail} failed"
[ "$fail" -eq 0 ]
