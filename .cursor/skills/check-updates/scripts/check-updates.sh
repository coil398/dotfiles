#!/usr/bin/env bash
set -euo pipefail

# Check explicitly supplied roots for independent git clones.  This script is
# intentionally runtime-neutral: it must not infer a home directory, project
# root, dotfiles repository, or another runtime's installation layout.

if [[ "$#" -eq 0 ]]; then
  printf 'Usage: %s ROOT [ROOT ...]\n' "$0" >&2
  printf 'ERROR: at least one explicit update root is required\n' >&2
  exit 2
fi

checked=0
updated=0
MAX_SCAN_DEPTH=3
errors=()
repos=()

record_error() {
  errors+=("$1")
}

canonical_dir() {
  local path="$1"
  (CDPATH='' cd -P -- "$path" && pwd -P)
}

is_independent_repo() {
  local candidate="$1"
  local candidate_top
  local candidate_abs
  local superproject

  [[ -e "$candidate/.git" ]] || return 1
  candidate_top="$(git -C "$candidate" rev-parse --show-toplevel 2>/dev/null)" || return 1
  candidate_abs="$(canonical_dir "$candidate")" || return 1
  candidate_top="$(canonical_dir "$candidate_top")" || return 1
  [[ "$candidate_abs" == "$candidate_top" ]] || return 1

  # A submodule has a .git file but is managed by its superproject, not an
  # independently installed clone.  Do not update it from this skill.
  superproject="$(git -C "$candidate" rev-parse --show-superproject-working-tree 2>/dev/null || true)"
  [[ -z "$superproject" ]]
}

add_repo() {
  local candidate="$1"
  local candidate_abs
  local existing

  candidate_abs="$(canonical_dir "$candidate")" || return 1
  if [[ "${#repos[@]}" -gt 0 ]]; then
    for existing in "${repos[@]}"; do
      [[ "$existing" == "$candidate_abs" ]] && return 0
    done
  fi
  repos+=("$candidate_abs")
}

scan_children() {
  local parent="$1"
  local depth="$2"
  local child
  local next_depth

  [[ "$depth" -le "$MAX_SCAN_DEPTH" ]] || return 0
  next_depth=$((depth + 1))
  shopt -s nullglob dotglob
  for child in "$parent"/*; do
    [[ -d "$child" ]] || continue
    [[ "$(basename "$child")" == ".git" ]] && continue
    if is_independent_repo "$child"; then
      add_repo "$child"
    elif [[ ! -e "$child/.git" ]]; then
      scan_children "$child" "$next_depth"
    fi
  done
  return 0
}

scan_root() {
  local root="$1"
  local root_abs

  if [[ ! -d "$root" ]]; then
    printf 'INVALID_ROOT: %s (directory does not exist)\n' "$root"
    record_error "INVALID_ROOT: $root"
    return 0
  fi

  root_abs="$(canonical_dir "$root")" || {
    printf 'INVALID_ROOT: %s (cannot resolve path)\n' "$root"
    record_error "INVALID_ROOT: $root"
    return 0
  }

  if is_independent_repo "$root_abs"; then
    add_repo "$root_abs"
    return 0
  fi

  # A root with a .git entry is either a managed repository or an invalid
  # repository.  Never descend into it looking for repositories to mutate.
  if [[ -e "$root_abs/.git" ]]; then
    printf 'SKIPPED_MANAGED_REPO: %s\n' "$root_abs"
    return 0
  fi

  # Marketplace/cache layouts currently place clones no deeper than three
  # directory levels below their supplied root.  Do not walk arbitrary depth.
  scan_children "$root_abs" 1
}

check_repo() {
  local repo="$1"
  local upstream_ref
  local remote
  local branch
  local dirty
  local counts
  local ahead
  local behind

  checked=$((checked + 1))

  if ! dirty="$(git -C "$repo" status --porcelain --untracked-files=all 2>/dev/null)"; then
    printf 'STATUS_FAILED: %s\n' "$repo"
    record_error "STATUS_FAILED: $repo"
    return 0
  fi
  if [[ -n "$dirty" ]]; then
    printf 'DIRTY: %s (preserved; no fetch or update)\n' "$repo"
    record_error "DIRTY: $repo"
    return 0
  fi

  if ! upstream_ref="$(git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)"; then
    printf 'NO_UPSTREAM: %s (preserved; configure an upstream branch)\n' "$repo"
    record_error "NO_UPSTREAM: $repo"
    return 0
  fi
  case "$upstream_ref" in
    */*)
      remote="${upstream_ref%%/*}"
      branch="${upstream_ref#*/}"
      ;;
    *)
      printf 'NO_UPSTREAM: %s (invalid upstream %s)\n' "$repo" "$upstream_ref"
      record_error "NO_UPSTREAM: $repo"
      return 0
      ;;
  esac

  if ! git -C "$repo" fetch --quiet "$remote" "$branch"; then
    printf 'FETCH_FAILED: %s (upstream %s)\n' "$repo" "$upstream_ref"
    record_error "FETCH_FAILED: $repo"
    return 0
  fi

  if ! counts="$(git -C "$repo" rev-list --left-right --count "HEAD...$upstream_ref" 2>/dev/null)"; then
    printf 'COMPARE_FAILED: %s (upstream %s)\n' "$repo" "$upstream_ref"
    record_error "COMPARE_FAILED: $repo"
    return 0
  fi
  read -r ahead behind <<< "$counts"

  if [[ "$ahead" -gt 0 && "$behind" -gt 0 ]]; then
    printf 'DIVERGED: %s (ahead %s, behind %s; preserved)\n' "$repo" "$ahead" "$behind"
    record_error "DIVERGED: $repo"
    return 0
  fi
  if [[ "$ahead" -gt 0 ]]; then
    printf 'AHEAD: %s (ahead %s; preserved, no push)\n' "$repo" "$ahead"
    record_error "AHEAD: $repo"
    return 0
  fi
  if [[ "$behind" -eq 0 ]]; then
    printf 'UP_TO_DATE: %s\n' "$repo"
    return 0
  fi

  # The worktree was verified clean above.  Only a fast-forward is allowed;
  # this never creates a merge commit and never invokes merge --abort.
  if ! git -C "$repo" merge --ff-only --quiet "$upstream_ref"; then
    printf 'FAST_FORWARD_FAILED: %s (upstream %s; preserved)\n' "$repo" "$upstream_ref"
    record_error "FAST_FORWARD_FAILED: $repo"
    return 0
  fi
  updated=$((updated + 1))
  printf 'UPDATED: %s (%s commits fast-forwarded)\n' "$repo" "$behind"
}

for root in "$@"; do
  scan_root "$root"
done

if [[ "${#repos[@]}" -gt 0 ]]; then
  for repo in "${repos[@]}"; do
    check_repo "$repo"
  done
fi

printf 'CHECKED: %s\n' "$checked"
printf 'UPDATED_COUNT: %s\n' "$updated"
if [[ "${#errors[@]}" -gt 0 ]]; then
  printf 'ERRORS: %s\n' "${#errors[@]}"
  exit 1
fi
printf 'ERRORS: 0\n'
exit 0
