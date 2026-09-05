#!/usr/bin/env bash
# Isolated fixture tests for etc/dotfiles-autosync.sh.
#
# Every repository, bare remote, submodule, hook, and generator in this file
# lives below one mktemp directory.  The real dotfiles checkout and its remotes
# are never used as a test target.

set -euo pipefail

TEST_SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_SOURCE="${TEST_SCRIPT_DIR}/dotfiles-autosync.sh"
if [ ! -f "$ENGINE_SOURCE" ]; then
  printf 'fixture error: missing %s\n' "$ENGINE_SOURCE" >&2
  exit 1
fi

TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/dotfiles-autosync-fixture.XXXXXX")"
trap 'rm -rf "$TEST_ROOT"' EXIT

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR \
  GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_NAMESPACE \
  GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS GIT_CONFIG_SYSTEM GIT_TEMPLATE_DIR \
  GIT_ATTRIBUTES_FILE GIT_IGNORE_GLOBAL || true
export HOME="${TEST_ROOT}/home"
export GIT_CONFIG_NOSYSTEM=1
export GIT_CONFIG_GLOBAL="${TEST_ROOT}/gitconfig"
export GIT_TERMINAL_PROMPT=0
mkdir -p "$HOME"
git config --global user.name 'dotfiles-autosync fixture'
git config --global user.email 'dotfiles-autosync-fixture@example.invalid'

fail() {
  printf 'fixture FAIL: %s\n' "$*" >&2
  exit 1
}

assert_file_contains() {
  local file="$1"
  local expected="$2"
  grep -F -- "$expected" "$file" >/dev/null || fail "${file} does not contain ${expected}"
}

assert_file_not_contains() {
  local file="$1"
  local unexpected="$2"
  if grep -F -- "$unexpected" "$file" >/dev/null 2>&1; then
    fail "${file} unexpectedly contains ${unexpected}"
  fi
}

assert_empty() {
  local value="$1"
  local description="$2"
  [ -z "$value" ] || fail "$description: ${value}"
}

assert_equal() {
  local actual="$1"
  local expected="$2"
  local description="$3"
  [ "$actual" = "$expected" ] || fail "$description: expected=${expected} actual=${actual}"
}

assert_same_directory() {
  local actual="$1"
  local expected="$2"
  local description="$3"
  local actual_physical expected_physical
  actual_physical="$(cd -P "$actual" && pwd)" || fail "$description: actual directory is unavailable: ${actual}"
  expected_physical="$(cd -P "$expected" && pwd)" || fail "$description: expected directory is unavailable: ${expected}"
  assert_equal "$actual_physical" "$expected_physical" "$description"
}

git_in() {
  local repo="$1"
  shift
  git -C "$repo" "$@"
}

select_master_branch() {
  local repo="$1"

  if git_in "$repo" show-ref --verify --quiet refs/heads/master; then
    git_in "$repo" switch master >/dev/null
  else
    git_in "$repo" switch --track origin/master >/dev/null
  fi
}

configure_repo() {
  local repo="$1"
  git_in "$repo" config user.name 'dotfiles-autosync fixture'
  git_in "$repo" config user.email 'dotfiles-autosync-fixture@example.invalid'
}

copy_engine() {
  local repo="$1"
  mkdir -p "$repo/etc"
  cp "$ENGINE_SOURCE" "$repo/etc/dotfiles-autosync.sh"
  chmod +x "$repo/etc/dotfiles-autosync.sh"
}

install_generators() {
  local repo="$1"
  local name
  for name in sync-codex sync-opencode sync-cursor sync-antigravity; do
    printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail' \
      'printf "%s\\n" "'"$name"'" >> generator-calls.log' \
      'mkdir -p generated' \
      'printf "%s\\n" "'"$name"'" > "generated/'"$name"'.txt"' \
      > "$repo/etc/${name}.sh"
    chmod +x "$repo/etc/${name}.sh"
  done
}

prepare_bare_repository() {
  local case_dir="$1"
  local name="$2"
  local bare="${case_dir}/${name}.git"
  local seed="${case_dir}/${name}-seed"

  git init --bare --initial-branch=master "$bare" >/dev/null
  git init --initial-branch=master "$seed" >/dev/null
  configure_repo "$seed"
  printf 'base\n' > "$seed/tracked.txt"
  printf 'base-conflict\n' > "$seed/conflict.txt"
  : > "$seed/generator-calls.log"
  git_in "$seed" add -- tracked.txt conflict.txt generator-calls.log
  git_in "$seed" commit -m 'fixture base' >/dev/null
  git_in "$seed" remote add origin "$bare"
  git_in "$seed" push -u origin master >/dev/null
  printf '%s\n' "$bare"
}

clone_fixture() {
  local bare="$1"
  local destination="$2"
  git clone "$bare" "$destination" >/dev/null
  configure_repo "$destination"
}

run_success() {
  local repo="$1"
  local log_file="$2"
  if ! bash "$repo/etc/dotfiles-autosync.sh" "$repo" > "$log_file" 2>&1; then
    cat "$log_file" >&2
    fail "autosync unexpectedly failed for $repo"
  fi
}

run_failure() {
  local repo="$1"
  local log_file="$2"
  if bash "$repo/etc/dotfiles-autosync.sh" "$repo" > "$log_file" 2>&1; then
    cat "$log_file" >&2
    fail "autosync unexpectedly succeeded for $repo"
  fi
}

test_wip_merge_push() {
  local case_dir="${TEST_ROOT}/wip-merge"
  local bare local_repo peer log_file call_count
  mkdir -p "$case_dir"
  bare="$(prepare_bare_repository "$case_dir" main)"
  local_repo="${case_dir}/local"
  peer="${case_dir}/peer"
  clone_fixture "$bare" "$local_repo"
  clone_fixture "$bare" "$peer"
  copy_engine "$local_repo"
  install_generators "$local_repo"

  printf 'local WIP\n' >> "$local_repo/tracked.txt"
  printf 'staged-only WIP\n' > "$local_repo/staged-only.txt"
  git_in "$local_repo" add -- staged-only.txt
  mkdir -p "$local_repo/wip"
  printf 'untracked WIP\n' > "$local_repo/wip/untracked.txt"

  printf 'remote divergent change\n' > "$peer/remote.txt"
  git_in "$peer" add -- remote.txt
  git_in "$peer" commit -m 'fixture remote change' >/dev/null
  git_in "$peer" push origin master >/dev/null

  log_file="${case_dir}/autosync.log"
  run_success "$local_repo" "$log_file"
  assert_empty "$(git_in "$local_repo" status --porcelain)" 'WIP merge worktree'
  assert_equal "$(git_in "$local_repo" rev-list --count HEAD..origin/master)" '0' 'WIP merge behind count'
  assert_file_contains <(git_in "$local_repo" log --format=%s --all) 'chore(dotfiles): preserve local changes before autosync'
  assert_file_contains <(git_in "$local_repo" log --format=%s --all) 'chore(dotfiles): align generated files and submodule pointers'
  assert_file_contains "$local_repo/tracked.txt" 'local WIP'
  assert_file_contains "$local_repo/staged-only.txt" 'staged-only WIP'
  assert_file_contains "$local_repo/wip/untracked.txt" 'untracked WIP'
  assert_file_contains "$local_repo/remote.txt" 'remote divergent change'
  for name in sync-codex sync-opencode sync-cursor sync-antigravity; do
    [ -f "$local_repo/generated/${name}.txt" ] || fail "missing generated/${name}.txt"
  done
  call_count="$(wc -l < "$local_repo/generator-calls.log" | tr -d '[:space:]')"
  assert_equal "$call_count" '4' 'four generator calls'
  assert_file_contains "$log_file" 'AUTOSYNC_PULL:parent:no-rebase-no-edit'
  assert_file_contains "$log_file" 'AUTOSYNC_PUSHED:parent:'
  printf 'fixture PASS: WIP preservation, divergent merge, generators, and push\n'
}

test_content_conflict_is_preserved() {
  local case_dir="${TEST_ROOT}/conflict"
  local bare local_repo peer log_file local_head remote_head
  mkdir -p "$case_dir"
  bare="$(prepare_bare_repository "$case_dir" conflict)"
  local_repo="${case_dir}/local"
  peer="${case_dir}/peer"
  clone_fixture "$bare" "$local_repo"
  clone_fixture "$bare" "$peer"
  copy_engine "$local_repo"
  install_generators "$local_repo"

  printf 'local conflicting WIP\n' > "$local_repo/conflict.txt"
  printf 'remote conflicting WIP\n' > "$peer/conflict.txt"
  git_in "$peer" add -- conflict.txt
  git_in "$peer" commit -m 'fixture conflicting remote change' >/dev/null
  git_in "$peer" push origin master >/dev/null

  log_file="${case_dir}/autosync.log"
  run_failure "$local_repo" "$log_file"
  assert_file_contains "$log_file" 'AUTOSYNC_CONFLICT:parent:kind=content'
  assert_file_contains "$log_file" 'AUTOSYNC_FAILURE:CONTENT_CONFLICT:parent kind=content'
  [ -n "$(git_in "$local_repo" ls-files -u)" ] || fail 'conflict index entries were not retained'
  local_head="$(git_in "$local_repo" log -1 --format=%s)"
  assert_equal "$local_head" 'chore(dotfiles): preserve local changes before autosync' 'conflict preserve commit'
  remote_head="$(git --git-dir="$bare" rev-parse refs/heads/master)"
  assert_equal "$remote_head" "$(git_in "$peer" rev-parse HEAD)" 'conflict remote was not rewritten'
  assert_file_not_contains "$log_file" 'AUTOSYNC_GENERATOR:'
  printf 'fixture PASS: content conflict state and WIP commit retained\n'
}

install_rejecting_receive_hook() {
  local bare="$1"
  local count_file="$2"
  local hook="$bare/hooks/pre-receive"
  {
    printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail'
    printf 'printf "1\\n" >> %q\n' "$count_file"
    printf '%s\n' 'exit 1'
  } > "$hook"
  chmod +x "$hook"
}

test_push_failure_keeps_local_commits() {
  local case_dir="${TEST_ROOT}/push-failure"
  local bare local_repo log_file count local_count
  mkdir -p "$case_dir"
  bare="$(prepare_bare_repository "$case_dir" push-failure)"
  local_repo="${case_dir}/local"
  clone_fixture "$bare" "$local_repo"
  copy_engine "$local_repo"
  install_generators "$local_repo"
  install_rejecting_receive_hook "$bare" "$case_dir/hook-count"

  printf 'local push failure WIP\n' >> "$local_repo/tracked.txt"
  log_file="${case_dir}/autosync.log"
  run_failure "$local_repo" "$log_file"
  assert_file_contains "$log_file" 'AUTOSYNC_PUSH_FAILED:parent:COUNT=1'
  assert_file_contains "$log_file" 'AUTOSYNC_FAILURE:PUSH_FAILED:parent local commits retained'
  count="$(wc -l < "$case_dir/hook-count" | tr -d '[:space:]')"
  assert_equal "$count" '1' 'push attempted exactly once'
  assert_empty "$(git_in "$local_repo" status --porcelain)" 'push failure local worktree'
  local_count="$(git_in "$local_repo" rev-list --count origin/master..HEAD)"
  [ "$local_count" -gt 0 ] || fail 'local commits disappeared after push failure'
  assert_file_contains <(git_in "$local_repo" log --format=%s --all) 'chore(dotfiles): preserve local changes before autosync'
  assert_file_contains <(git_in "$local_repo" log --format=%s --all) 'chore(dotfiles): align generated files and submodule pointers'
  printf 'fixture PASS: push failure leaves local commits and avoids retry\n'
}

prepare_submodule_case() {
  local case_dir="$1"
  local child_bare child_seed parent_bare parent_seed child_path

  child_bare="$(prepare_bare_repository "$case_dir" child)"
  child_seed="${case_dir}/child-seed"
  printf 'child base\n' > "$child_seed/child.txt"
  git_in "$child_seed" add -- child.txt
  git_in "$child_seed" commit -m 'fixture child content' >/dev/null
  git_in "$child_seed" push origin master >/dev/null

  parent_bare="${case_dir}/parent.git"
  parent_seed="${case_dir}/parent-seed"
  git init --bare --initial-branch=master "$parent_bare" >/dev/null
  git init --initial-branch=master "$parent_seed" >/dev/null
  configure_repo "$parent_seed"
  printf 'parent base\n' > "$parent_seed/parent.txt"
  git_in "$parent_seed" add -- parent.txt
  git_in "$parent_seed" commit -m 'fixture parent base' >/dev/null
  git_in "$parent_seed" remote add origin "$parent_bare"
  git -C "$parent_seed" -c protocol.file.allow=always submodule add "$child_bare" modules/child >/dev/null
  child_path="$parent_seed/modules/child"
  select_master_branch "$child_path"
  git_in "$parent_seed" add -- .gitmodules modules/child
  git_in "$parent_seed" commit -m 'fixture add child submodule' >/dev/null
  git_in "$parent_seed" push -u origin master >/dev/null
  printf '%s\n' "$parent_bare"
}

prepare_nested_submodule_case() {
  local case_dir="$1"
  local nested_bare nested_seed child_bare child_seed parent_bare parent_seed nested_path child_path

  nested_bare="$(prepare_bare_repository "$case_dir" nested)"
  nested_seed="${case_dir}/nested-seed"
  printf 'nested content\n' > "$nested_seed/nested.txt"
  git_in "$nested_seed" add -- nested.txt
  git_in "$nested_seed" commit -m 'fixture nested content' >/dev/null
  git_in "$nested_seed" push origin master >/dev/null

  child_bare="$(prepare_bare_repository "$case_dir" child)"
  child_seed="${case_dir}/child-seed"
  git -C "$child_seed" -c protocol.file.allow=always submodule add "$nested_bare" nested >/dev/null
  nested_path="$child_seed/nested"
  select_master_branch "$nested_path"
  git_in "$child_seed" add -- .gitmodules nested
  git_in "$child_seed" commit -m 'fixture add nested submodule' >/dev/null
  git_in "$child_seed" push origin master >/dev/null

  parent_bare="${case_dir}/parent.git"
  parent_seed="${case_dir}/parent-seed"
  git init --bare --initial-branch=master "$parent_bare" >/dev/null
  git init --initial-branch=master "$parent_seed" >/dev/null
  configure_repo "$parent_seed"
  printf 'parent base\n' > "$parent_seed/parent.txt"
  git_in "$parent_seed" add -- parent.txt
  git_in "$parent_seed" commit -m 'fixture parent base' >/dev/null
  git_in "$parent_seed" remote add origin "$parent_bare"
  git -C "$parent_seed" -c protocol.file.allow=always submodule add "$child_bare" modules/child >/dev/null
  child_path="$parent_seed/modules/child"
  select_master_branch "$child_path"
  git_in "$parent_seed" add -- .gitmodules modules/child
  git_in "$parent_seed" commit -m 'fixture add child submodule' >/dev/null
  git_in "$parent_seed" push -u origin master >/dev/null
  printf '%s\n' "$parent_bare"
}

test_dirty_submodule_pushes_before_parent_pointer() {
  local case_dir="${TEST_ROOT}/submodule-order"
  local parent_bare parent_repo child_repo log_file child_line parent_preserve_line parent_push_line child_head pointer_head call_count
  mkdir -p "$case_dir"
  parent_bare="$(prepare_submodule_case "$case_dir")"
  parent_repo="${case_dir}/parent-local"
  git -c protocol.file.allow=always clone --recurse-submodules "$parent_bare" "$parent_repo" >/dev/null
  configure_repo "$parent_repo"
  child_repo="$parent_repo/modules/child"
  select_master_branch "$child_repo"
  copy_engine "$parent_repo"
  install_generators "$parent_repo"

  printf 'child local WIP\n' >> "$child_repo/child.txt"
  printf 'child untracked WIP\n' > "$child_repo/untracked.txt"
  log_file="${case_dir}/autosync.log"
  run_success "$parent_repo" "$log_file"

  assert_empty "$(git_in "$parent_repo" status --porcelain)" 'parent submodule-order worktree'
  assert_empty "$(git_in "$child_repo" status --porcelain)" 'child submodule-order worktree'
  child_line="$(grep -n 'AUTOSYNC_PUSHED:submodule:modules/child:' "$log_file" | cut -d: -f1)"
  parent_preserve_line="$(grep -n 'AUTOSYNC_COMMIT:parent:PRESERVE:' "$log_file" | cut -d: -f1)"
  parent_push_line="$(grep -n 'AUTOSYNC_PUSHED:parent:' "$log_file" | cut -d: -f1)"
  [ -n "$child_line" ] || fail 'child push marker missing'
  [ -n "$parent_preserve_line" ] || fail 'parent pointer preserve marker missing'
  [ -n "$parent_push_line" ] || fail 'parent push marker missing'
  [ "$child_line" -lt "$parent_preserve_line" ] || fail 'parent pointer was handled before child push'
  [ "$parent_preserve_line" -lt "$parent_push_line" ] || fail 'parent push happened before parent pointer commit'
  child_head="$(git_in "$child_repo" rev-parse HEAD)"
  pointer_head="$(git_in "$parent_repo" ls-tree HEAD modules/child | awk '{print $3}')"
  assert_equal "$pointer_head" "$child_head" 'parent points at pushed child commit'
  assert_equal "$(git --git-dir="${case_dir}/child.git" rev-parse refs/heads/master)" "$child_head" 'child commit reached child origin'
  call_count="$(wc -l < "$parent_repo/generator-calls.log" | tr -d '[:space:]')"
  assert_equal "$call_count" '4' 'submodule case generator calls'
  printf 'fixture PASS: dirty submodule push precedes parent pointer push\n'
}

test_clean_detached_submodules_skip_at_recorded_gitlinks() {
  local case_dir="${TEST_ROOT}/submodule-detached-clean"
  local parent_bare parent_repo child_repo nested_repo log_file child_head nested_head child_pointer nested_pointer
  mkdir -p "$case_dir"
  parent_bare="$(prepare_nested_submodule_case "$case_dir")"
  parent_repo="${case_dir}/parent-local"
  git -c protocol.file.allow=always clone --recurse-submodules "$parent_bare" "$parent_repo" >/dev/null
  configure_repo "$parent_repo"
  child_repo="$parent_repo/modules/child"
  nested_repo="$child_repo/nested"
  git_in "$child_repo" switch --detach HEAD >/dev/null
  git_in "$nested_repo" switch --detach HEAD >/dev/null
  copy_engine "$parent_repo"
  install_generators "$parent_repo"

  child_head="$(git_in "$child_repo" rev-parse HEAD)"
  nested_head="$(git_in "$nested_repo" rev-parse HEAD)"
  log_file="${case_dir}/autosync.log"
  run_success "$parent_repo" "$log_file"

  if git_in "$child_repo" symbolic-ref --quiet --short HEAD >/dev/null 2>&1; then
    fail 'clean detached child unexpectedly became branch-attached'
  fi
  if git_in "$nested_repo" symbolic-ref --quiet --short HEAD >/dev/null 2>&1; then
    fail 'clean detached nested submodule unexpectedly became branch-attached'
  fi
  assert_equal "$(git_in "$child_repo" rev-parse HEAD)" "$child_head" 'clean detached child head'
  assert_equal "$(git_in "$nested_repo" rev-parse HEAD)" "$nested_head" 'clean detached nested head'
  assert_empty "$(git_in "$parent_repo" status --porcelain)" 'clean detached parent worktree'
  assert_empty "$(git_in "$child_repo" status --porcelain)" 'clean detached child worktree'
  assert_empty "$(git_in "$nested_repo" status --porcelain)" 'clean detached nested worktree'
  assert_file_contains "$log_file" 'AUTOSYNC_PREFLIGHT:DETACHED_SKIP:submodule:modules/child:'
  assert_file_contains "$log_file" 'AUTOSYNC_PREFLIGHT:DETACHED_SKIP:submodule:modules/child/nested:'
  assert_file_contains "$log_file" 'parent=modules/child:'
  assert_file_contains "$log_file" 'AUTOSYNC_SUBMODULE_SYNC:SKIP:modules/child:detached-head-at-expected-gitlink'
  assert_file_contains "$log_file" 'AUTOSYNC_SUBMODULE_SYNC:SKIP:modules/child/nested:detached-head-at-expected-gitlink'
  assert_file_not_contains "$log_file" 'AUTOSYNC_FETCH:submodule:modules/child'
  assert_file_not_contains "$log_file" 'AUTOSYNC_PULL:submodule:modules/child'
  assert_file_not_contains "$log_file" 'AUTOSYNC_PUSH_ATTEMPT:submodule:modules/child'
  assert_file_not_contains "$log_file" 'AUTOSYNC_FETCH:submodule:modules/child/nested'
  assert_file_not_contains "$log_file" 'AUTOSYNC_PULL:submodule:modules/child/nested'
  assert_file_not_contains "$log_file" 'AUTOSYNC_PUSH_ATTEMPT:submodule:modules/child/nested'
  child_pointer="$(git_in "$parent_repo" ls-tree HEAD modules/child | awk '{print $3}')"
  nested_pointer="$(git_in "$child_repo" ls-tree HEAD nested | awk '{print $3}')"
  assert_equal "$child_pointer" "$child_head" 'clean detached child parent gitlink'
  assert_equal "$nested_pointer" "$nested_head" 'clean detached nested direct-parent gitlink'
  printf 'fixture PASS: clean detached submodules skip network sync at direct-parent gitlinks\n'
}

test_dirty_detached_submodule_fails_before_mutation() {
  local case_dir="${TEST_ROOT}/submodule-detached-dirty"
  local parent_bare parent_repo child_repo log_file parent_head child_head parent_remote_head child_remote_head
  mkdir -p "$case_dir"
  parent_bare="$(prepare_submodule_case "$case_dir")"
  parent_repo="${case_dir}/parent-local"
  git -c protocol.file.allow=always clone --recurse-submodules "$parent_bare" "$parent_repo" >/dev/null
  configure_repo "$parent_repo"
  child_repo="$parent_repo/modules/child"
  git_in "$child_repo" switch --detach HEAD >/dev/null
  copy_engine "$parent_repo"
  install_generators "$parent_repo"

  printf 'detached dirty WIP\n' >> "$child_repo/child.txt"
  printf 'detached dirty untracked\n' > "$child_repo/untracked.txt"
  parent_head="$(git_in "$parent_repo" rev-parse HEAD)"
  child_head="$(git_in "$child_repo" rev-parse HEAD)"
  parent_remote_head="$(git --git-dir="$parent_bare" rev-parse refs/heads/master)"
  child_remote_head="$(git --git-dir="${case_dir}/child.git" rev-parse refs/heads/master)"
  log_file="${case_dir}/autosync.log"
  run_failure "$parent_repo" "$log_file"

  assert_file_contains "$log_file" 'AUTOSYNC_PREFLIGHT:DETACHED_DIRTY:submodule:modules/child:'
  assert_file_contains "$log_file" 'AUTOSYNC_FAILURE:PREFLIGHT_DETACHED_DIRTY:submodule:modules/child'
  assert_file_not_contains "$log_file" 'AUTOSYNC_COMMIT:parent:PRESERVE:'
  assert_file_not_contains "$log_file" 'AUTOSYNC_FETCH:'
  assert_file_not_contains "$log_file" 'AUTOSYNC_PULL:'
  assert_file_not_contains "$log_file" 'AUTOSYNC_PUSH_ATTEMPT:'
  assert_equal "$(git_in "$parent_repo" rev-parse HEAD)" "$parent_head" 'dirty detached parent head unchanged'
  assert_equal "$(git_in "$child_repo" rev-parse HEAD)" "$child_head" 'dirty detached child head unchanged'
  assert_equal "$(git --git-dir="$parent_bare" rev-parse refs/heads/master)" "$parent_remote_head" 'dirty detached parent remote unchanged'
  assert_equal "$(git --git-dir="${case_dir}/child.git" rev-parse refs/heads/master)" "$child_remote_head" 'dirty detached child remote unchanged'
  printf 'fixture PASS: dirty detached submodule fails before preservation and network mutation\n'
}

test_detached_pointer_mismatch_fails_before_mutation() {
  local case_dir="${TEST_ROOT}/submodule-detached-mismatch"
  local parent_bare parent_repo child_repo log_file parent_head child_head parent_remote_head child_remote_head
  mkdir -p "$case_dir"
  parent_bare="$(prepare_submodule_case "$case_dir")"
  parent_repo="${case_dir}/parent-local"
  git -c protocol.file.allow=always clone --recurse-submodules "$parent_bare" "$parent_repo" >/dev/null
  configure_repo "$parent_repo"
  child_repo="$parent_repo/modules/child"
  git_in "$child_repo" switch --detach HEAD^ >/dev/null
  copy_engine "$parent_repo"
  install_generators "$parent_repo"

  parent_head="$(git_in "$parent_repo" rev-parse HEAD)"
  child_head="$(git_in "$child_repo" rev-parse HEAD)"
  parent_remote_head="$(git --git-dir="$parent_bare" rev-parse refs/heads/master)"
  child_remote_head="$(git --git-dir="${case_dir}/child.git" rev-parse refs/heads/master)"
  log_file="${case_dir}/autosync.log"
  run_failure "$parent_repo" "$log_file"

  assert_file_contains "$log_file" 'AUTOSYNC_PREFLIGHT:DETACHED_POINTER_MISMATCH:submodule:modules/child:'
  assert_file_contains "$log_file" 'AUTOSYNC_FAILURE:PREFLIGHT_DETACHED_POINTER_MISMATCH:submodule:modules/child'
  assert_file_not_contains "$log_file" 'AUTOSYNC_COMMIT:parent:PRESERVE:'
  assert_file_not_contains "$log_file" 'AUTOSYNC_FETCH:'
  assert_file_not_contains "$log_file" 'AUTOSYNC_PULL:'
  assert_file_not_contains "$log_file" 'AUTOSYNC_PUSH_ATTEMPT:'
  assert_equal "$(git_in "$parent_repo" rev-parse HEAD)" "$parent_head" 'detached mismatch parent head unchanged'
  assert_equal "$(git_in "$child_repo" rev-parse HEAD)" "$child_head" 'detached mismatch child head unchanged'
  assert_equal "$(git --git-dir="$parent_bare" rev-parse refs/heads/master)" "$parent_remote_head" 'detached mismatch parent remote unchanged'
  assert_equal "$(git --git-dir="${case_dir}/child.git" rev-parse refs/heads/master)" "$child_remote_head" 'detached mismatch child remote unchanged'
  printf 'fixture PASS: detached pointer mismatch fails before preservation and network mutation\n'
}

test_push_target_and_secret_log() {
  local case_dir="${TEST_ROOT}/push-target-secret"
  local secret bare local_repo upstream_bare upstream_seed log_file local_head origin_feature upstream_master
  mkdir -p "$case_dir"
  secret='fixture-origin-secret-7f2a'
  bare="$(prepare_bare_repository "$case_dir" origin)"
  local_repo="${case_dir}/local"
  upstream_bare="${case_dir}/upstream.git"
  upstream_seed="${case_dir}/upstream-seed"
  clone_fixture "$bare" "$local_repo"
  git_in "$local_repo" config "url.${bare}.insteadOf" "https://${secret}.invalid/dotfiles.git"
  git_in "$local_repo" remote set-url origin "https://${secret}.invalid/dotfiles.git"
  git clone --bare "$bare" "$upstream_bare" >/dev/null
  git clone "$upstream_bare" "$upstream_seed" >/dev/null
  configure_repo "$upstream_seed"
  printf 'tracking upstream change\n' > "$upstream_seed/upstream.txt"
  git_in "$upstream_seed" add -- upstream.txt
  git_in "$upstream_seed" commit -m 'fixture tracking upstream change' >/dev/null
  git_in "$upstream_seed" push origin master >/dev/null

  git_in "$local_repo" remote add upstream "$upstream_bare"
  git_in "$local_repo" fetch upstream >/dev/null
  git_in "$local_repo" branch -m feature
  git_in "$local_repo" branch --set-upstream-to=upstream/master
  copy_engine "$local_repo"
  install_generators "$local_repo"

  printf 'push target local WIP\n' >> "$local_repo/tracked.txt"
  log_file="${case_dir}/autosync.log"
  run_success "$local_repo" "$log_file"

  local_head="$(git_in "$local_repo" rev-parse HEAD)"
  origin_feature="$(git --git-dir="$bare" rev-parse refs/heads/feature)"
  upstream_master="$(git --git-dir="$upstream_bare" rev-parse refs/heads/master)"
  assert_equal "$origin_feature" "$local_head" 'push target origin/local branch'
  assert_equal "$(git_in "$local_repo" rev-list --count HEAD..upstream/master)" '0' 'tracking upstream fully merged'
  assert_equal "$(git --git-dir="$bare" rev-parse refs/heads/master)" "$(git_in "$local_repo" rev-parse refs/remotes/origin/master)" 'origin master was not selected for push'
  assert_equal "$upstream_master" "$(git_in "$local_repo" rev-parse refs/remotes/upstream/master)" 'configured upstream was fetched'
  assert_file_contains "$local_repo/upstream.txt" 'tracking upstream change'
  assert_file_contains "$log_file" 'AUTOSYNC_PREFLIGHT:OK:parent:branch=feature:upstream=upstream/master:origin=present'
  assert_file_contains "$log_file" 'AUTOSYNC_FETCH:parent:remote=upstream:branch=master'
  assert_file_contains "$log_file" 'AUTOSYNC_PUSH_ATTEMPT:parent:COUNT=1:remote=origin:branch=feature'
  assert_file_contains "$log_file" 'AUTOSYNC_PUSHED:parent:'
  assert_file_not_contains "$log_file" "$secret"
  printf 'fixture PASS: origin/local-branch push target and secret URL non-disclosure\n'
}

test_operation_state_boundaries() {
  local case_dir="${TEST_ROOT}/operation-state"
  local bare stale_repo active_repo git_dir log_file state head_before
  mkdir -p "$case_dir"
  bare="$(prepare_bare_repository "$case_dir" operation-state)"

  stale_repo="${case_dir}/stale-rebase-head"
  clone_fixture "$bare" "$stale_repo"
  copy_engine "$stale_repo"
  install_generators "$stale_repo"
  git_dir="$(git_in "$stale_repo" rev-parse --absolute-git-dir)"
  git_in "$stale_repo" rev-parse HEAD > "$git_dir/REBASE_HEAD"
  log_file="${case_dir}/stale-rebase-head.log"
  run_success "$stale_repo" "$log_file"
  assert_file_contains "$log_file" 'AUTOSYNC_PREFLIGHT:OK:parent:'

  active_repo="${case_dir}/active"
  clone_fixture "$bare" "$active_repo"
  copy_engine "$active_repo"
  install_generators "$active_repo"
  git_dir="$(git_in "$active_repo" rev-parse --absolute-git-dir)"
  head_before="$(git_in "$active_repo" rev-parse HEAD)"

  for state in rebase-merge rebase-apply; do
    mkdir "$git_dir/$state"
    log_file="${case_dir}/${state}.log"
    run_failure "$active_repo" "$log_file"
    assert_file_contains "$log_file" "AUTOSYNC_FAILURE:PREFLIGHT_UNFINISHED_OPERATION:parent state=$state"
    rmdir "$git_dir/$state"
  done

  for state in MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD; do
    git_in "$active_repo" rev-parse HEAD > "$git_dir/$state"
    log_file="${case_dir}/${state}.log"
    run_failure "$active_repo" "$log_file"
    if [ "$state" = 'MERGE_HEAD' ]; then
      assert_file_contains "$log_file" 'AUTOSYNC_FAILURE:PREFLIGHT_UNFINISHED_OPERATION:parent state=merge'
    else
      assert_file_contains "$log_file" "AUTOSYNC_FAILURE:PREFLIGHT_UNFINISHED_OPERATION:parent state=$state"
    fi
    rm "$git_dir/$state"
  done

  assert_equal "$(git_in "$active_repo" rev-parse HEAD)" "$head_before" 'unfinished operations do not create commits'
  printf 'fixture PASS: stale REBASE_HEAD allowed; active operation states rejected\n'
}

test_indexed_ignored_update_is_preserved() {
  local case_dir="${TEST_ROOT}/indexed-ignored"
  local bare local_repo log_file index
  mkdir -p "$case_dir"
  bare="$(prepare_bare_repository "$case_dir" indexed-ignored)"
  local_repo="${case_dir}/local"
  clone_fixture "$bare" "$local_repo"
  copy_engine "$local_repo"
  install_generators "$local_repo"

  printf '%s\n' 'ignored-report.md' 'ignored-untracked.md' > "$local_repo/.gitignore"
  printf 'initial report\n' > "$local_repo/ignored-report.md"
  git_in "$local_repo" add -f -- ignored-report.md
  printf 'updated report\n' > "$local_repo/ignored-report.md"
  printf 'must remain untracked\n' > "$local_repo/ignored-untracked.md"
  mkdir -p "$local_repo/batch"
  for index in $(seq 1 40); do
    printf 'indexed %s before\n' "$index" > "$local_repo/batch/indexed-$index.txt"
    git_in "$local_repo" add -- "batch/indexed-$index.txt"
    printf 'indexed %s after\n' "$index" > "$local_repo/batch/indexed-$index.txt"
    printf 'untracked %s\n' "$index" > "$local_repo/batch/untracked-$index.txt"
  done
  printf 'special indexed before\n' > "$local_repo/batch/indexed [literal]*?.txt"
  git_in "$local_repo" --literal-pathspecs add -- 'batch/indexed [literal]*?.txt'
  printf 'special indexed after\n' > "$local_repo/batch/indexed [literal]*?.txt"
  printf 'special untracked\n' > "$local_repo/batch/untracked [literal]*?.txt"

  log_file="${case_dir}/autosync.log"
  run_success "$local_repo" "$log_file"
  assert_equal "$(git_in "$local_repo" show HEAD:ignored-report.md)" 'updated report' 'indexed ignored file content'
  assert_equal "$(git_in "$local_repo" show 'HEAD:batch/indexed-40.txt')" 'indexed 40 after' 'batched indexed content'
  assert_equal "$(git_in "$local_repo" show 'HEAD:batch/untracked-40.txt')" 'untracked 40' 'batched untracked content'
  assert_equal "$(git_in "$local_repo" cat-file blob 'HEAD:batch/indexed [literal]*?.txt')" 'special indexed after' 'literal indexed path content'
  assert_equal "$(git_in "$local_repo" cat-file blob 'HEAD:batch/untracked [literal]*?.txt')" 'special untracked' 'literal untracked path content'
  if git_in "$local_repo" ls-files --error-unmatch -- ignored-untracked.md >/dev/null 2>&1; then
    fail 'untracked ignored file was added without an explicit force-add'
  fi
  [ -f "$local_repo/ignored-untracked.md" ] || fail 'untracked ignored file was removed'
  printf 'fixture PASS: indexed ignored update preserved without force-adding ignored untracked file\n'
}

test_git_path_states_are_staged_without_pathspec_failure() {
  local case_dir="${TEST_ROOT}/git-path-states"
  local bare local_repo log_file rename_source rename_target
  local staged_delete unstaged_delete ignored_tracked special_path call_count already_staged_count
  mkdir -p "$case_dir"
  bare="$(prepare_bare_repository "$case_dir" git-path-states)"
  local_repo="${case_dir}/local"
  clone_fixture "$bare" "$local_repo"
  copy_engine "$local_repo"
  install_generators "$local_repo"

  unstaged_delete='unstaged delete [literal]*?.txt'
  ignored_tracked='ignored tracked [literal]*?.txt'
  printf '%s\n' 'delete in worktree' > "$local_repo/$unstaged_delete"
  printf '%s\n' 'ignored before' > "$local_repo/$ignored_tracked"
  git_in "$local_repo" --literal-pathspecs add -- "$unstaged_delete" "$ignored_tracked"
  git_in "$local_repo" commit -m 'fixture path-state setup' >/dev/null
  git_in "$local_repo" config diff.renames false

  rename_source='tracked.txt'
  rename_target='rename target $meta;[]?.txt'
  git_in "$local_repo" --literal-pathspecs mv -- "$rename_source" "$rename_target"

  staged_delete='conflict.txt'
  git_in "$local_repo" --literal-pathspecs rm -- "$staged_delete"

  rm -- "$local_repo/$unstaged_delete"

  printf '%s\n' "$ignored_tracked" > "$local_repo/.gitignore"
  printf '%s\n' 'ignored after' > "$local_repo/$ignored_tracked"

  special_path='special path [literal]*?.txt'
  printf '%s\n' 'special untracked' > "$local_repo/$special_path"

  log_file="${case_dir}/autosync.log"
  run_success "$local_repo" "$log_file"
  assert_empty "$(git_in "$local_repo" status --porcelain)" 'path-state worktree'
  assert_equal "$(git_in "$local_repo" cat-file blob "HEAD:$rename_target")" 'base' 'staged rename target'
  if git_in "$local_repo" cat-file -e "HEAD:$rename_source" >/dev/null 2>&1; then
    fail 'staged rename source remained in HEAD'
  fi
  if git_in "$local_repo" cat-file -e "HEAD:$staged_delete" >/dev/null 2>&1; then
    fail 'staged deletion remained in HEAD'
  fi
  if git_in "$local_repo" cat-file -e "HEAD:$unstaged_delete" >/dev/null 2>&1; then
    fail 'unstaged deletion remained in HEAD'
  fi
  assert_equal "$(git_in "$local_repo" cat-file blob "HEAD:$ignored_tracked")" 'ignored after' 'ignored tracked update'
  assert_equal "$(git_in "$local_repo" cat-file blob "HEAD:$special_path")" 'special untracked' 'special untracked path'
  already_staged_count="$(grep -F -c 'already-staged-deletion' "$log_file" || true)"
  assert_equal "$already_staged_count" '2' 'staged rename/deletion classification'
  assert_file_not_contains "$log_file" 'STAGE_FAILED'
  call_count="$(wc -l < "$local_repo/generator-calls.log" | tr -d '[:space:]')"
  assert_equal "$call_count" '4' 'path-state generator calls'
  printf 'fixture PASS: staged rename/deletion, unstaged deletion, ignored tracked, and special paths\n'
}

test_skill_entries_are_dotfiles_anchored() {
  local skill_file source_rel installed_rel command_line capture actual
  local isolated_home fake_root default_root override_root unrelated_project
  local missing_home missing_default_root missing_override_root missing_log missing_capture

  isolated_home="${TEST_ROOT}/skill-entry-home"
  fake_root="${TEST_ROOT}/skill-entry-dotfiles"
  default_root="${isolated_home}/dotfiles"
  override_root="${TEST_ROOT}/skill-entry-nonstandard-dotfiles"
  unrelated_project="${TEST_ROOT}/unrelated-project"
  capture="${TEST_ROOT}/skill-entry-root"
  mkdir -p "$isolated_home" "$fake_root/etc" "$default_root/etc" "$override_root/etc" "$unrelated_project"
  git init --initial-branch=master "$unrelated_project" >/dev/null
  printf '%s\n' '#!/usr/bin/env bash' 'printf "%s\\n" "$1" > "$AUTOSYNC_ROOT_CAPTURE"' > "$fake_root/etc/dotfiles-autosync.sh"
  chmod +x "$fake_root/etc/dotfiles-autosync.sh"
  cp "$fake_root/etc/dotfiles-autosync.sh" "$default_root/etc/dotfiles-autosync.sh"
  cp "$fake_root/etc/dotfiles-autosync.sh" "$override_root/etc/dotfiles-autosync.sh"
  chmod +x "$default_root/etc/dotfiles-autosync.sh" "$override_root/etc/dotfiles-autosync.sh"

  for skill_file in \
    .agents/skills/dotfiles-autosync/SKILL.md \
    .claude/skills/dotfiles-autosync/SKILL.md \
    .codex/skills/dotfiles-autosync/SKILL.md \
    .cursor/skills/dotfiles-autosync/SKILL.md; do
    case "$skill_file" in
      .agents/*)
        source_rel='.agents/skills/dotfiles-autosync'
        installed_rel='.agents/skills/dotfiles-autosync'
        ;;
      .claude/*)
        source_rel='.claude/skills/dotfiles-autosync'
        installed_rel='.claude/skills/dotfiles-autosync'
        ;;
      .codex/*)
        source_rel='.codex/skills/dotfiles-autosync'
        installed_rel='.codex/skills/dotfiles-autosync'
        ;;
      .cursor/*)
        source_rel='.cursor/skills/dotfiles-autosync'
        installed_rel='.cursor/skills/dotfiles-autosync'
        ;;
      *)
        fail "unknown skill path ${skill_file}"
        ;;
    esac
    mkdir -p "$fake_root/$source_rel" "$isolated_home/$(dirname "$installed_rel")"
    cp "$skill_file" "$fake_root/$source_rel/SKILL.md"
    case "$skill_file" in
      .cursor/*)
        mkdir -p "$isolated_home/$installed_rel"
        cp -a "$fake_root/$source_rel/." "$isolated_home/$installed_rel/"
        [ -d "$isolated_home/$installed_rel" ] || fail "missing materialized Cursor skill for ${skill_file}"
        [ ! -L "$isolated_home/$installed_rel" ] || fail "Cursor skill is unexpectedly a symlink for ${skill_file}"
        ;;
      *)
        ln -s "$fake_root/$source_rel" "$isolated_home/$installed_rel"
        [ -L "$isolated_home/$installed_rel" ] || fail "runtime skill is not a symlink for ${skill_file}"
        ;;
    esac
    assert_file_not_contains "$skill_file" 'git rev-parse --show-toplevel'
    assert_file_not_contains "$skill_file" 'readlink -f'
    assert_file_contains "$skill_file" 'cd -P'
    assert_file_contains "$skill_file" '${DOTFILES_ROOT:-$HOME/dotfiles}'
    assert_file_contains "$skill_file" 'etc/dotfiles-autosync.sh'
    command_line="$(sed -n '/^SKILL_FILE=/p' "$skill_file")"
    case "$skill_file" in
      .cursor/*)
        if ! (cd "$unrelated_project" && HOME="$isolated_home" DOTFILES_ROOT= AUTOSYNC_ROOT_CAPTURE="$capture" bash -c "$command_line"); then
          fail "Cursor default entry failed for ${skill_file}"
        fi
        actual="$(cat "$capture")"
        assert_same_directory "$actual" "$default_root" 'Cursor default runtime root'
        if ! (cd "$unrelated_project" && HOME="$isolated_home" DOTFILES_ROOT="$override_root" AUTOSYNC_ROOT_CAPTURE="$capture" bash -c "$command_line"); then
          fail "Cursor override entry failed for ${skill_file}"
        fi
        actual="$(cat "$capture")"
        assert_same_directory "$actual" "$override_root" 'Cursor override runtime root'

        missing_home="${TEST_ROOT}/skill-entry-missing-home"
        missing_default_root="${missing_home}/dotfiles"
        missing_override_root="${TEST_ROOT}/skill-entry-missing-override"
        missing_log="${TEST_ROOT}/skill-entry-missing.log"
        missing_capture="${TEST_ROOT}/skill-entry-missing-root"
        mkdir -p "$missing_home/.cursor/skills/dotfiles-autosync" \
          "$missing_default_root" "$missing_override_root"
        cp -a "$isolated_home/$installed_rel/." \
          "$missing_home/.cursor/skills/dotfiles-autosync/"
        [ -d "$missing_home/.cursor/skills/dotfiles-autosync" ] || \
          fail "missing materialized Cursor skill for ${skill_file}"
        [ ! -L "$missing_home/.cursor/skills/dotfiles-autosync" ] || \
          fail "missing Cursor skill is unexpectedly a symlink for ${skill_file}"

        printf '%s\n' 'not-invoked' > "$missing_capture"
        if (cd "$unrelated_project" && HOME="$missing_home" DOTFILES_ROOT= AUTOSYNC_ROOT_CAPTURE="$missing_capture" bash -c "$command_line" > "$missing_log" 2>&1); then
          fail "Cursor default missing-engine entry unexpectedly succeeded"
        fi
        assert_file_contains "$missing_log" "dotfiles-autosync: missing engine: ${missing_default_root}/etc/dotfiles-autosync.sh"
        assert_file_not_contains "$missing_log" "$unrelated_project"
        actual="$(cat "$missing_capture")"
        assert_equal "$actual" 'not-invoked' 'Cursor default missing-engine fake engine invocation'

        printf '%s\n' 'not-invoked' > "$missing_capture"
        if (cd "$unrelated_project" && HOME="$missing_home" DOTFILES_ROOT="$missing_override_root" AUTOSYNC_ROOT_CAPTURE="$missing_capture" bash -c "$command_line" > "$missing_log" 2>&1); then
          fail "Cursor override missing-engine entry unexpectedly succeeded"
        fi
        assert_file_contains "$missing_log" "dotfiles-autosync: missing engine: ${missing_override_root}/etc/dotfiles-autosync.sh"
        assert_file_not_contains "$missing_log" "$unrelated_project"
        actual="$(cat "$missing_capture")"
        assert_equal "$actual" 'not-invoked' 'Cursor override missing-engine fake engine invocation'
        ;;
      *)
        if ! (cd "$unrelated_project" && HOME="$isolated_home" DOTFILES_ROOT= AUTOSYNC_ROOT_CAPTURE="$capture" bash -c "$command_line"); then
          fail "runtime entry failed for ${skill_file}"
        fi
        actual="$(cat "$capture")"
        assert_same_directory "$actual" "$fake_root" "runtime root for ${skill_file}"
        ;;
    esac
  done
  printf 'fixture PASS: symlinked entries and materialized Cursor entries resolve outside current Git repo\n'
}

test_wip_merge_push
test_content_conflict_is_preserved
test_push_failure_keeps_local_commits
test_dirty_submodule_pushes_before_parent_pointer
test_clean_detached_submodules_skip_at_recorded_gitlinks
test_dirty_detached_submodule_fails_before_mutation
test_detached_pointer_mismatch_fails_before_mutation
test_push_target_and_secret_log
test_operation_state_boundaries
test_indexed_ignored_update_is_preserved
test_git_path_states_are_staged_without_pathspec_failure
test_skill_entries_are_dotfiles_anchored
printf 'AUTOSYNC_FIXTURE:PASS\n'
