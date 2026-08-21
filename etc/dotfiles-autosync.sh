#!/usr/bin/env bash
# Explicit dotfiles-only synchronization engine.
#
# This script is intentionally the only implementation used by the four
# dotfiles-autosync skill entry points.  It preserves local work in commits,
# merges upstream with an explicit non-rebase pull, regenerates adapter output,
# and pushes only after all local consistency checks pass.

set -euo pipefail

SCRIPT_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_ROOT="$(cd -P "${SCRIPT_DIR}/.." && pwd)"

log() {
  printf '[dotfiles-autosync] %s\n' "$*"
}

marker() {
  printf '%s\n' "$*"
}

failure() {
  local code="$1"
  shift
  marker "AUTOSYNC_FAILURE:${code}:$*" >&2
  exit 1
}

make_temp_file() {
  mktemp "${TMPDIR:-/tmp}/dotfiles-autosync.XXXXXX"
}

phase_start() {
  marker "AUTOSYNC_PHASE:$1:START"
}

phase_done() {
  marker "AUTOSYNC_PHASE:$1:OK"
}

if [ "$#" -gt 1 ]; then
  failure USAGE "expected zero or one repository-root argument"
fi

ROOT_INPUT="${1:-$DEFAULT_ROOT}"
if [ ! -d "$ROOT_INPUT" ]; then
  failure ROOT_NOT_DIRECTORY "$ROOT_INPUT"
fi
if ! ROOT_CANDIDATE="$(cd -P "$ROOT_INPUT" && pwd)"; then
  failure ROOT_RESOLUTION_FAILED "$ROOT_INPUT"
fi
if ! ROOT_DISCOVERED="$(git -C "$ROOT_CANDIDATE" rev-parse --show-toplevel 2>/dev/null)"; then
  failure NOT_A_GIT_WORKTREE "$ROOT_CANDIDATE"
fi
if ! ROOT="$(cd -P "$ROOT_DISCOVERED" && pwd)"; then
  failure ROOT_RESOLUTION_FAILED "$ROOT_DISCOVERED"
fi
if [ "$ROOT" != "$ROOT_CANDIDATE" ]; then
  failure ROOT_NOT_TOPLEVEL "requested=$ROOT_CANDIDATE discovered=$ROOT"
fi

declare -a DIRTY_PATHS=()
declare -a SUBMODULE_PATHS=()
declare -a SUBMODULE_SKIP_PATHS=()
declare -a COMMIT_SUMMARY=()
declare -a PUSH_SUMMARY=()

PREFLIGHT_BRANCH=''
PREFLIGHT_UPSTREAM=''
PREFLIGHT_UPSTREAM_REMOTE=''
PREFLIGHT_UPSTREAM_BRANCH=''
SUBMODULE_EXPECTED_HEAD=''
SUBMODULE_EXPECTED_PARENT=''
SUBMODULE_EXPECTED_PARENT_COMMIT=''
PUSH_COUNT=0

operation_state() {
  local repo="$1"
  local marker_name marker_path

  if git -C "$repo" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    printf 'merge'
    return 0
  fi
  for marker_name in REBASE_HEAD CHERRY_PICK_HEAD REVERT_HEAD; do
    if marker_path="$(git -C "$repo" rev-parse --git-path "$marker_name" 2>/dev/null)" && [ -e "$marker_path" ]; then
      printf '%s' "$marker_name"
      return 0
    fi
  done
  for marker_name in rebase-merge rebase-apply; do
    if marker_path="$(git -C "$repo" rev-parse --git-path "$marker_name" 2>/dev/null)" && [ -d "$marker_path" ]; then
      printf '%s' "$marker_name"
      return 0
    fi
  done
  return 1
}

preflight_repo() {
  local repo="$1"
  local label="$2"
  local allow_detached="${3:-0}"
  local branch upstream upstream_remote upstream_branch

  if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    failure PREFLIGHT_NOT_WORKTREE "$label"
  fi
  if ! git -C "$repo" rev-parse --verify HEAD^{commit} >/dev/null 2>&1; then
    failure PREFLIGHT_NO_HEAD "$label"
  fi
  if operation_state_name="$(operation_state "$repo" 2>/dev/null)"; then
    failure PREFLIGHT_UNFINISHED_OPERATION "$label state=$operation_state_name"
  fi
  if [ "$allow_detached" -eq 1 ]; then
    if ! branch="$(git -C "$repo" symbolic-ref --quiet --short HEAD 2>/dev/null)" || [ -z "$branch" ]; then
      PREFLIGHT_BRANCH=''
      PREFLIGHT_UPSTREAM=''
      PREFLIGHT_UPSTREAM_REMOTE=''
      PREFLIGHT_UPSTREAM_BRANCH=''
      marker "AUTOSYNC_PREFLIGHT:DETACHED:${label}:tracking=not-required"
      return 0
    fi
  fi
  if ! git -C "$repo" remote get-url origin >/dev/null 2>&1; then
    failure PREFLIGHT_ORIGIN_MISSING "$label"
  fi
  if ! branch="$(git -C "$repo" symbolic-ref --quiet --short HEAD 2>/dev/null)" || [ -z "$branch" ]; then
    failure PREFLIGHT_DETACHED "$label"
  fi
  if ! upstream="$(git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)" || [ -z "$upstream" ] || [[ "$upstream" != */* ]]; then
    failure PREFLIGHT_UPSTREAM_MISSING "$label branch=$branch"
  fi
  upstream_remote="${upstream%%/*}"
  upstream_branch="${upstream#*/}"
  if [ -z "$upstream_remote" ] || [ -z "$upstream_branch" ]; then
    failure PREFLIGHT_UPSTREAM_INVALID "$label upstream=$upstream"
  fi
  if ! git -C "$repo" remote get-url "$upstream_remote" >/dev/null 2>&1; then
    failure PREFLIGHT_UPSTREAM_REMOTE_MISSING "$label upstream=$upstream"
  fi
  if ! git -C "$repo" rev-parse --verify "$upstream^{commit}" >/dev/null 2>&1; then
    failure PREFLIGHT_UPSTREAM_REF_MISSING "$label upstream=$upstream"
  fi

  PREFLIGHT_BRANCH="$branch"
  PREFLIGHT_UPSTREAM="$upstream"
  PREFLIGHT_UPSTREAM_REMOTE="$upstream_remote"
  PREFLIGHT_UPSTREAM_BRANCH="$upstream_branch"
  marker "AUTOSYNC_PREFLIGHT:OK:${label}:branch=${branch}:upstream=${upstream}:origin=present"
}

collect_dirty_paths() {
  local repo="$1"
  local label="$2"
  local raw path existing duplicate

  raw="$(make_temp_file)"
  if ! {
    git -C "$repo" diff --name-only -z HEAD
    git -C "$repo" ls-files --others --exclude-standard -z
  } > "$raw"; then
    rm -f "$raw"
    failure DIRTY_PATHS_FAILED "$label"
  fi

  DIRTY_PATHS=()
  while IFS= read -r -d '' path; do
    duplicate=0
    if [ "${#DIRTY_PATHS[@]}" -gt 0 ]; then
      for existing in "${DIRTY_PATHS[@]}"; do
        if [ "$existing" = "$path" ]; then
          duplicate=1
          break
        fi
      done
    fi
    if [ "$duplicate" -eq 0 ]; then
      DIRTY_PATHS+=("$path")
    fi
  done < "$raw"
  rm -f "$raw"
}

print_cached_diff() {
  local repo="$1"
  local label="$2"

  if git -C "$repo" diff --cached --quiet; then
    failure CACHED_DIFF_EMPTY "$label"
  fi
  marker "AUTOSYNC_CACHED_DIFF:${label}:BEGIN"
  if ! git -C "$repo" diff --cached --name-status; then
    failure CACHED_DIFF_READ_FAILED "$label"
  fi
  if ! git -C "$repo" diff --cached --stat; then
    failure CACHED_DIFF_READ_FAILED "$label"
  fi
  marker "AUTOSYNC_CACHED_DIFF:${label}:END"
}

stage_dirty_paths() {
  local repo="$1"
  local label="$2"
  local path

  if [ "${#DIRTY_PATHS[@]}" -gt 0 ]; then
    for path in "${DIRTY_PATHS[@]}"; do
      marker "AUTOSYNC_STAGE_PATH:${label}:$(printf '%q' "$path")"
      if ! git -C "$repo" add -- "$path"; then
        failure STAGE_FAILED "$label path=$(printf '%q' "$path")"
      fi
    done
  fi
  print_cached_diff "$repo" "$label"
}

preserve_dirty_changes() {
  local repo="$1"
  local label="$2"
  local message="$3"
  local before after

  collect_dirty_paths "$repo" "$label"
  if [ "${#DIRTY_PATHS[@]}" -eq 0 ]; then
    marker "AUTOSYNC_DIRTY:${label}:NONE"
    return 0
  fi
  marker "AUTOSYNC_DIRTY:${label}:COUNT=${#DIRTY_PATHS[@]}"
  stage_dirty_paths "$repo" "$label"
  if ! before="$(git -C "$repo" rev-parse HEAD)"; then
    failure HEAD_READ_FAILED "$label"
  fi
  if ! git -C "$repo" commit -m "$message"; then
    failure COMMIT_FAILED "$label message=$(printf '%q' "$message")"
  fi
  if ! after="$(git -C "$repo" rev-parse HEAD)"; then
    failure COMMIT_HASH_FAILED "$label"
  fi
  COMMIT_SUMMARY+=("${label}:preserve:${after}")
  marker "AUTOSYNC_COMMIT:${label}:PRESERVE:${after}:${before}..${after}"
  collect_dirty_paths "$repo" "$label"
  if [ "${#DIRTY_PATHS[@]}" -ne 0 ]; then
    failure PRESERVE_NOT_CLEAN "$label"
  fi
}

print_conflict_paths() {
  local repo="$1"
  local label="$2"
  local raw path

  raw="$(make_temp_file)"
  if ! git -C "$repo" diff --name-only --diff-filter=U -z > "$raw"; then
    rm -f "$raw"
    failure CONFLICT_PATHS_FAILED "$label"
  fi
  while IFS= read -r -d '' path; do
    marker "AUTOSYNC_CONFLICT_PATH:${label}:$(printf '%q' "$path")"
  done < "$raw"
  rm -f "$raw"
}

has_unmerged_entries() {
  local repo="$1"

  git -C "$repo" ls-files -u | awk 'NR > 0 { found = 1 } END { exit(found ? 0 : 1) }'
}

conflict_kind() {
  local repo="$1"
  if git -C "$repo" ls-files -u | awk '$1 == "160000" { found = 1 } END { exit(found ? 0 : 1) }'; then
    printf 'gitlink'
  else
    printf 'content'
  fi
}

fetch_and_pull() {
  local repo="$1"
  local label="$2"
  local before after kind

  before="$(git -C "$repo" rev-parse HEAD)"
  marker "AUTOSYNC_FETCH:${label}:remote=${PREFLIGHT_UPSTREAM_REMOTE}:branch=${PREFLIGHT_UPSTREAM_BRANCH}"
  if ! git -C "$repo" fetch "$PREFLIGHT_UPSTREAM_REMOTE" "$PREFLIGHT_UPSTREAM_BRANCH" >/dev/null 2>&1; then
    failure FETCH_FAILED "$label remote=$PREFLIGHT_UPSTREAM_REMOTE branch=$PREFLIGHT_UPSTREAM_BRANCH"
  fi
  marker "AUTOSYNC_PULL:${label}:no-rebase-no-edit"
  if ! git -C "$repo" pull --no-rebase --no-edit >/dev/null 2>&1; then
    if ! has_unmerged_entries "$repo"; then
      failure PULL_FAILED "$label"
    fi
    kind="$(conflict_kind "$repo")"
    marker "AUTOSYNC_CONFLICT:${label}:kind=${kind}"
    print_conflict_paths "$repo" "$label"
    marker "AUTOSYNC_RECOVERY:${label}:resolve-unmerged-paths-and-continue-with-user-guidance" >&2
    failure CONTENT_CONFLICT "$label kind=$kind"
  fi
  after="$(git -C "$repo" rev-parse HEAD)"
  marker "AUTOSYNC_RANGE:${label}:PULL:${before}..${after}"
}

push_repo() {
  local repo="$1"
  local label="$2"
  local remote='origin'
  local branch="$PREFLIGHT_BRANCH"
  local head

  PUSH_COUNT=$((PUSH_COUNT + 1))
  marker "AUTOSYNC_PUSH_ATTEMPT:${label}:COUNT=${PUSH_COUNT}:remote=${remote}:branch=${branch}"
  if ! git -C "$repo" push "$remote" "HEAD:${branch}" >/dev/null 2>&1; then
    marker "AUTOSYNC_PUSH_FAILED:${label}:COUNT=${PUSH_COUNT}:local_head=$(git -C "$repo" rev-parse HEAD)" >&2
    git -C "$repo" status -sb >&2 || true
    git -C "$repo" log --oneline "$PREFLIGHT_UPSTREAM..HEAD" >&2 || true
    failure PUSH_FAILED "$label local commits retained; no retry attempted"
  fi
  head="$(git -C "$repo" rev-parse HEAD)"
  PUSH_SUMMARY+=("${label}:${head}")
  marker "AUTOSYNC_PUSHED:${label}:${head}"
}

collect_submodules() {
  local repo="$1"
  local label="$2"
  local status_file raw line path existing duplicate

  status_file="$(make_temp_file)"
  if ! git -C "$repo" submodule status --recursive > "$status_file"; then
    rm -f "$status_file"
    failure SUBMODULE_STATUS_FAILED "$label"
  fi
  while IFS= read -r line; do
    case "$line" in
      -*)
        rm -f "$status_file"
        failure SUBMODULE_UNINITIALIZED "$label"
        ;;
      U*)
        rm -f "$status_file"
        failure SUBMODULE_UNMERGED "$label"
        ;;
    esac
  done < "$status_file"
  rm -f "$status_file"

  raw="$(make_temp_file)"
  if ! git -C "$repo" submodule foreach --quiet --recursive 'printf "%s\\0" "$displaypath"' > "$raw"; then
    rm -f "$raw"
    failure SUBMODULE_ENUM_FAILED "$label"
  fi
  SUBMODULE_PATHS=()
  while IFS= read -r -d '' path; do
    duplicate=0
    if [ "${#SUBMODULE_PATHS[@]}" -gt 0 ]; then
      for existing in "${SUBMODULE_PATHS[@]}"; do
        if [ "$existing" = "$path" ]; then
          duplicate=1
          break
        fi
      done
    fi
    if [ "$duplicate" -eq 0 ]; then
      SUBMODULE_PATHS+=("$path")
    fi
  done < "$raw"
  rm -f "$raw"

  sort_submodule_paths
}

submodule_depth() {
  local path="$1"
  local rest="$path"
  local depth=0
  while [[ "$rest" == */* ]]; do
    depth=$((depth + 1))
    rest="${rest#*/}"
  done
  printf '%s' "$depth"
}

sort_submodule_paths() {
  local i j depth_i depth_j path_i path_j

  for ((i = 0; i < ${#SUBMODULE_PATHS[@]}; i++)); do
    for ((j = i + 1; j < ${#SUBMODULE_PATHS[@]}; j++)); do
      path_i="${SUBMODULE_PATHS[$i]}"
      path_j="${SUBMODULE_PATHS[$j]}"
      depth_i="$(submodule_depth "$path_i")"
      depth_j="$(submodule_depth "$path_j")"
      if [ "$depth_j" -gt "$depth_i" ] || { [ "$depth_j" -eq "$depth_i" ] && [[ "$path_j" > "$path_i" ]]; }; then
        SUBMODULE_PATHS[$i]="$path_j"
        SUBMODULE_PATHS[$j]="$path_i"
      fi
    done
  done
}

ensure_repo_clean() {
  local repo="$1"
  local label="$2"

  collect_dirty_paths "$repo" "$label"
  if [ "${#DIRTY_PATHS[@]}" -ne 0 ]; then
    marker "AUTOSYNC_DIRTY_AFTER:${label}:COUNT=${#DIRTY_PATHS[@]}" >&2
    failure WORKTREE_NOT_CLEAN "$label"
  fi
}

validate_submodule_paths() {
  local path relative sub_top expected

  if [ "${#SUBMODULE_PATHS[@]}" -gt 0 ]; then
    for relative in "${SUBMODULE_PATHS[@]}"; do
      path="$ROOT/$relative"
      if [ ! -d "$path" ]; then
        failure SUBMODULE_PATH_MISSING "$relative"
      fi
      if ! sub_top="$(git -C "$path" rev-parse --show-toplevel 2>/dev/null)"; then
        failure SUBMODULE_NOT_WORKTREE "$relative"
      fi
      if ! expected="$(cd -P "$sub_top" && pwd)"; then
        failure SUBMODULE_ROOT_RESOLUTION_FAILED "$relative"
      fi
      if [ "$expected" != "$(cd -P "$path" && pwd)" ]; then
        failure SUBMODULE_ROOT_MISMATCH "$relative"
      fi
    done
  fi
}

submodule_expected_gitlink() {
  local relative="$1"
  local parent_relative child_path parent_repo entry parent_commit

  if [[ "$relative" == */* ]]; then
    parent_relative="${relative%/*}"
    child_path="${relative##*/}"
    parent_repo="$ROOT/$parent_relative"
  else
    parent_relative='.'
    child_path="$relative"
    parent_repo="$ROOT"
  fi
  if [ ! -d "$parent_repo" ]; then
    failure SUBMODULE_PARENT_PATH_MISSING "submodule=$relative parent=$parent_relative"
  fi
  if ! parent_repo="$(cd -P "$parent_repo" && pwd)"; then
    failure SUBMODULE_PARENT_ROOT_RESOLUTION_FAILED "submodule=$relative parent=$parent_relative"
  fi
  if ! parent_commit="$(git -C "$parent_repo" rev-parse --verify HEAD^{commit} 2>/dev/null)" || [ -z "$parent_commit" ]; then
    failure SUBMODULE_PARENT_NO_HEAD "submodule=$relative parent=$parent_relative"
  fi
  if ! entry="$(git -C "$parent_repo" ls-tree --format='%(objectmode) %(objecttype) %(objectname)' "$parent_commit" -- "$child_path")" || [ -z "$entry" ]; then
    failure SUBMODULE_GITLINK_READ_FAILED "submodule=$relative parent=$parent_relative commit=$parent_commit path=$child_path"
  fi
  if [[ "$entry" != '160000 commit '* ]]; then
    failure SUBMODULE_GITLINK_MISSING "submodule=$relative parent=$parent_relative commit=$parent_commit path=$child_path"
  fi

  SUBMODULE_EXPECTED_HEAD="${entry##* }"
  SUBMODULE_EXPECTED_PARENT="$parent_relative"
  SUBMODULE_EXPECTED_PARENT_COMMIT="$parent_commit"
}

classify_submodule() {
  local relative="$1"
  local path="$ROOT/$relative"
  local label="submodule:${relative}"
  local branch current_head

  SUBMODULE_EXPECTED_HEAD=''
  SUBMODULE_EXPECTED_PARENT=''
  SUBMODULE_EXPECTED_PARENT_COMMIT=''
  preflight_repo "$path" "$label" 1
  if branch="$(git -C "$path" symbolic-ref --quiet --short HEAD 2>/dev/null)" && [ -n "$branch" ]; then
    return 0
  fi

  collect_dirty_paths "$path" "$label"
  if [ "${#DIRTY_PATHS[@]}" -ne 0 ]; then
    marker "AUTOSYNC_PREFLIGHT:DETACHED_DIRTY:${label}:COUNT=${#DIRTY_PATHS[@]}"
    failure PREFLIGHT_DETACHED_DIRTY "$label count=${#DIRTY_PATHS[@]}"
  fi
  if ! current_head="$(git -C "$path" rev-parse --verify HEAD^{commit} 2>/dev/null)" || [ -z "$current_head" ]; then
    failure PREFLIGHT_NO_HEAD "$label"
  fi
  submodule_expected_gitlink "$relative"
  if [ "$current_head" = "$SUBMODULE_EXPECTED_HEAD" ]; then
    SUBMODULE_SKIP_PATHS+=("$relative")
    marker "AUTOSYNC_PREFLIGHT:DETACHED_SKIP:${label}:head=${current_head}:expected=${SUBMODULE_EXPECTED_HEAD}:parent=${SUBMODULE_EXPECTED_PARENT}:parent_commit=${SUBMODULE_EXPECTED_PARENT_COMMIT}"
    return 0
  fi
  marker "AUTOSYNC_PREFLIGHT:DETACHED_POINTER_MISMATCH:${label}:head=${current_head}:expected=${SUBMODULE_EXPECTED_HEAD}:parent=${SUBMODULE_EXPECTED_PARENT}:parent_commit=${SUBMODULE_EXPECTED_PARENT_COMMIT}"
  failure PREFLIGHT_DETACHED_POINTER_MISMATCH "$label head=$current_head expected=$SUBMODULE_EXPECTED_HEAD parent=$SUBMODULE_EXPECTED_PARENT"
}

submodule_was_skipped() {
  local relative="$1"
  local candidate

  if [ "${#SUBMODULE_SKIP_PATHS[@]}" -gt 0 ]; then
    for candidate in "${SUBMODULE_SKIP_PATHS[@]}"; do
      if [ "$candidate" = "$relative" ]; then
        return 0
      fi
    done
  fi
  return 1
}

preflight_submodules() {
  local relative

  SUBMODULE_SKIP_PATHS=()
  if [ "${#SUBMODULE_PATHS[@]}" -gt 0 ]; then
    for relative in "${SUBMODULE_PATHS[@]}"; do
      classify_submodule "$relative"
    done
  fi
}

sync_submodule() {
  local relative="$1"
  local path="$ROOT/$relative"
  local label="submodule:${relative}"

  preflight_repo "$path" "$label"
  preserve_dirty_changes "$path" "$label" "chore(submodule): preserve local changes before dotfiles autosync"
  ensure_repo_clean "$path" "$label"
  fetch_and_pull "$path" "$label"
  ensure_repo_clean "$path" "$label"
  push_repo "$path" "$label"
}

sync_parent_modules() {
  local status_file line relative path

  marker "AUTOSYNC_SUBMODULE_SYNC:BEGIN"
  if ! git -C "$ROOT" submodule sync --recursive; then
    failure SUBMODULE_SYNC_FAILED parent
  fi
  if ! git -C "$ROOT" submodule update --init --recursive; then
    failure SUBMODULE_UPDATE_FAILED parent
  fi
  collect_submodules "$ROOT" parent
  if [ "${#SUBMODULE_PATHS[@]}" -gt 0 ]; then
    for relative in "${SUBMODULE_PATHS[@]}"; do
      path="$ROOT/$relative"
      ensure_repo_clean "$path" "submodule:${relative}"
    done
  fi
  marker "AUTOSYNC_SUBMODULE_SYNC:OK"
}

run_generators() {
  local generator

  for generator in sync-codex.sh sync-opencode.sh sync-cursor.sh; do
    if [ ! -f "$ROOT/etc/$generator" ]; then
      failure GENERATOR_MISSING "$ROOT/etc/$generator"
    fi
    marker "AUTOSYNC_GENERATOR:${generator}:START"
    if ! (cd "$ROOT" && bash "etc/$generator"); then
      failure GENERATOR_FAILED "$generator"
    fi
    marker "AUTOSYNC_GENERATOR:${generator}:OK"
  done
}

ensure_recursive_submodules_clean() {
  local relative path status_file line

  collect_submodules "$ROOT" parent
  if [ "${#SUBMODULE_PATHS[@]}" -gt 0 ]; then
    for relative in "${SUBMODULE_PATHS[@]}"; do
      path="$ROOT/$relative"
      ensure_repo_clean "$path" "submodule:${relative}"
    done
  fi

  status_file="$(make_temp_file)"
  if ! git -C "$ROOT" submodule status --recursive > "$status_file"; then
    rm -f "$status_file"
    failure SUBMODULE_STATUS_FAILED parent-final
  fi
  while IFS= read -r line; do
    case "$line" in
      -*)
        rm -f "$status_file"
        failure SUBMODULE_UNINITIALIZED parent-final
        ;;
      +*)
        rm -f "$status_file"
        failure SUBMODULE_POINTER_MISMATCH parent-final
        ;;
      U*)
        rm -f "$status_file"
        failure SUBMODULE_UNMERGED parent-final
        ;;
    esac
  done < "$status_file"
  rm -f "$status_file"
}

commit_generated_and_pointer_changes() {
  local before after

  collect_dirty_paths "$ROOT" parent-generated
  if [ "${#DIRTY_PATHS[@]}" -eq 0 ]; then
    marker 'AUTOSYNC_GENERATED_DIFF:NONE'
    return 0
  fi
  marker "AUTOSYNC_GENERATED_DIFF:COUNT=${#DIRTY_PATHS[@]}"
  stage_dirty_paths "$ROOT" parent-generated
  before="$(git -C "$ROOT" rev-parse HEAD)"
  if ! git -C "$ROOT" commit -m "chore(dotfiles): align generated files and submodule pointers"; then
    failure GENERATED_COMMIT_FAILED parent
  fi
  after="$(git -C "$ROOT" rev-parse HEAD)"
  COMMIT_SUMMARY+=("parent:generated:${after}")
  marker "AUTOSYNC_COMMIT:parent:GENERATED:${after}:${before}..${after}"
}

verify_behind_zero() {
  local count

  if ! count="$(git -C "$ROOT" rev-list --count HEAD.."$PREFLIGHT_UPSTREAM")"; then
    failure BEHIND_CHECK_FAILED parent
  fi
  marker "AUTOSYNC_BEHIND:parent:${count}"
  if [ "$count" -ne 0 ]; then
    failure BEHIND_NONZERO "parent behind=$count upstream=$PREFLIGHT_UPSTREAM"
  fi
}

print_summary() {
  local item

  marker 'AUTOSYNC_SUMMARY:BEGIN'
  if [ "${#COMMIT_SUMMARY[@]}" -gt 0 ]; then
    for item in "${COMMIT_SUMMARY[@]}"; do
      marker "AUTOSYNC_SUMMARY:COMMIT:${item}"
    done
  fi
  if [ "${#PUSH_SUMMARY[@]}" -gt 0 ]; then
    for item in "${PUSH_SUMMARY[@]}"; do
      marker "AUTOSYNC_SUMMARY:PUSH:${item}"
    done
  fi
  marker "AUTOSYNC_SUMMARY:PUSH_COUNT:${PUSH_COUNT}"
  marker 'AUTOSYNC_SUMMARY:END'
}

phase_start preflight
preflight_repo "$ROOT" parent
phase_done preflight

phase_start submodules
collect_submodules "$ROOT" parent
validate_submodule_paths
preflight_submodules
if [ "${#SUBMODULE_PATHS[@]}" -gt 0 ]; then
  for SUBMODULE_RELATIVE in "${SUBMODULE_PATHS[@]}"; do
    if submodule_was_skipped "$SUBMODULE_RELATIVE"; then
      marker "AUTOSYNC_SUBMODULE_SYNC:SKIP:${SUBMODULE_RELATIVE}:detached-head-at-expected-gitlink"
      continue
    fi
    sync_submodule "$SUBMODULE_RELATIVE"
  done
fi
phase_done submodules

phase_start parent_preserve
preflight_repo "$ROOT" parent
preserve_dirty_changes "$ROOT" parent "chore(dotfiles): preserve local changes before autosync"
ensure_repo_clean "$ROOT" parent
phase_done parent_preserve

phase_start parent_upstream
preflight_repo "$ROOT" parent
fetch_and_pull "$ROOT" parent
ensure_repo_clean "$ROOT" parent
phase_done parent_upstream

phase_start reconcile
sync_parent_modules
ensure_repo_clean "$ROOT" parent-before-generators
run_generators
commit_generated_and_pointer_changes
phase_done reconcile

phase_start final_verify
ensure_repo_clean "$ROOT" parent
ensure_recursive_submodules_clean
preflight_repo "$ROOT" parent
verify_behind_zero
phase_done final_verify

phase_start push
push_repo "$ROOT" parent
phase_done push

print_summary
marker 'AUTOSYNC_STATUS:SUCCESS'
