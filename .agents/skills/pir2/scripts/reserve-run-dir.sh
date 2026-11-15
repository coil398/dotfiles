#!/bin/sh
set -eu

prog="$(basename "$0")"

usage() {
  cat <<USAGE
Usage: ${prog} --cwd <DIR> --slug <SLUG> [--bucket _bench] [--run-root <DIR>]

Reserve an exclusive run directory under ~/.ai-runs (or --run-root) with mode 0700.
Outputs PROJECT_ROOT, RUN_ROOT, PROJECT_RUN_ROOT, RUN_DIR, and HANDOFF_PATH.
USAGE
}

err() {
  printf '%s: %s\n' "$prog" "$1" >&2
  exit 1
}

resolve_candidate_path() {
  target="$1"
  suffix=""
  probe="$target"
  while [ ! -e "$probe" ]; do
    parent="$(dirname "$probe")"
    [ "$parent" != "$probe" ] || break
    base="$(basename "$probe")"
    if [ -n "$suffix" ]; then
      suffix="${base}/${suffix}"
    else
      suffix="$base"
    fi
    probe="$parent"
  done
  [ -d "$probe" ] || err "ancestor is not a directory: $probe"
  canon_base="$(CDPATH='' cd -- "$probe" && pwd -P)"
  if [ -n "$suffix" ]; then
    if [ "$canon_base" = "/" ]; then
      printf '/%s\n' "$suffix"
    else
      printf '%s/%s\n' "$canon_base" "$suffix"
    fi
  else
    printf '%s\n' "$canon_base"
  fi
}

check_outside_project() {
  path_to_check="$1"
  project_root="$2"
  case "$path_to_check" in
    "$project_root"|"$project_root"/*)
      err "RUN_ROOT/RUN_DIR must be outside PROJECT_ROOT ($project_root): $path_to_check"
      ;;
  esac
}

cwd_arg=""
slug_arg=""
bucket_arg=""
run_root_arg=""

while [ $# -gt 0 ]; do
  case "$1" in
    --cwd)
      [ $# -ge 2 ] || err "--cwd requires a directory"
      cwd_arg="$2"
      shift 2
      ;;
    --slug)
      [ $# -ge 2 ] || err "--slug requires a value"
      slug_arg="$2"
      shift 2
      ;;
    --bucket)
      [ $# -ge 2 ] || err "--bucket requires a value"
      bucket_arg="$2"
      shift 2
      ;;
    --run-root)
      [ $# -ge 2 ] || err "--run-root requires a directory"
      run_root_arg="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      err "unknown option: $1"
      ;;
  esac
done

[ -n "$cwd_arg" ] || err "--cwd is required"
[ -n "$slug_arg" ] || err "--slug is required"
[ -d "$cwd_arg" ] || err "--cwd is not an existing directory: $cwd_arg"

if [ -n "$bucket_arg" ] && [ "$bucket_arg" != "_bench" ]; then
  err "--bucket only accepts _bench: $bucket_arg"
fi

cwd_canon="$(CDPATH='' cd -- "$cwd_arg" && pwd -P)"
if git_root="$(git -C "$cwd_canon" rev-parse --show-toplevel 2>/dev/null)"; then
  [ -d "$git_root" ] || err "git toplevel is not a directory: $git_root"
  PROJECT_ROOT="$(CDPATH='' cd -- "$git_root" && pwd -P)"
else
  PROJECT_ROOT="$cwd_canon"
fi

sanitized_cwd="$(printf '%s' "$PROJECT_ROOT" | LC_ALL=C sed 's|[^a-zA-Z0-9]|-|g')"
[ -n "$sanitized_cwd" ] || err "failed to sanitize PROJECT_ROOT: $PROJECT_ROOT"

run_slug="$(printf '%s' "$slug_arg" | LC_ALL=C tr 'A-Z' 'a-z' | LC_ALL=C tr -c 'a-z0-9' '-' | sed 's/--*/-/g; s/^-//; s/-$//' | cut -c1-40 | sed 's/-$//')"
[ -n "$run_slug" ] || run_slug="task"

if [ -z "$run_root_arg" ]; then
  [ -n "${HOME:-}" ] || err "HOME is required when --run-root is omitted"
  run_root_arg="${HOME}/.ai-runs"
fi

[ ! -L "$run_root_arg" ] || err "RUN_ROOT must not be a symlink: $run_root_arg"
if [ -e "$run_root_arg" ] && [ ! -d "$run_root_arg" ]; then
  err "RUN_ROOT exists but is not a directory: $run_root_arg"
fi

home_canon=""
if [ -n "${HOME:-}" ] && [ -d "${HOME}" ]; then
  home_canon="$(CDPATH='' cd -- "$HOME" && pwd -P)"
fi

candidate_root="$(resolve_candidate_path "$run_root_arg")"
[ "$candidate_root" != "/" ] || err "RUN_ROOT must not be /"
if [ -n "$home_canon" ] && [ "$candidate_root" = "$home_canon" ]; then
  err "RUN_ROOT must not be HOME: $candidate_root"
fi
check_outside_project "$candidate_root" "$PROJECT_ROOT"

if [ ! -e "$run_root_arg" ]; then
  (umask 077 && mkdir -p -- "$run_root_arg") || err "failed to create RUN_ROOT: $run_root_arg"
fi
[ -d "$run_root_arg" ] && [ ! -L "$run_root_arg" ] || err "RUN_ROOT is not a real directory: $run_root_arg"
RUN_ROOT="$(CDPATH='' cd -- "$run_root_arg" && pwd -P)"
[ "$RUN_ROOT" != "/" ] || err "RUN_ROOT must not be /"
if [ -n "$home_canon" ] && [ "$RUN_ROOT" = "$home_canon" ]; then
  err "RUN_ROOT must not be HOME: $RUN_ROOT"
fi
check_outside_project "$RUN_ROOT" "$PROJECT_ROOT"

if [ -n "$bucket_arg" ]; then
  bucket="$bucket_arg"
else
  bucket="$sanitized_cwd"
fi

PROJECT_RUN_ROOT="${RUN_ROOT}/${bucket}"
[ ! -L "$PROJECT_RUN_ROOT" ] || err "PROJECT_RUN_ROOT must not be a symlink: $PROJECT_RUN_ROOT"
if [ -e "$PROJECT_RUN_ROOT" ]; then
  [ -d "$PROJECT_RUN_ROOT" ] || err "PROJECT_RUN_ROOT exists but is not a directory: $PROJECT_RUN_ROOT"
else
  (umask 077 && mkdir -- "$PROJECT_RUN_ROOT") 2>/dev/null || {
    [ -d "$PROJECT_RUN_ROOT" ] && [ ! -L "$PROJECT_RUN_ROOT" ] || err "failed to create PROJECT_RUN_ROOT: $PROJECT_RUN_ROOT"
  }
fi
[ -d "$PROJECT_RUN_ROOT" ] && [ ! -L "$PROJECT_RUN_ROOT" ] || err "PROJECT_RUN_ROOT is not a real directory: $PROJECT_RUN_ROOT"
PROJECT_RUN_ROOT="$(CDPATH='' cd -- "$PROJECT_RUN_ROOT" && pwd -P)"
check_outside_project "$PROJECT_RUN_ROOT" "$PROJECT_ROOT"

if [ -n "$bucket_arg" ]; then
  HANDOFF_PATH=""
else
  HANDOFF_PATH="${PROJECT_RUN_ROOT}/handoff.md"
  if [ -L "$HANDOFF_PATH" ] || { [ -e "$HANDOFF_PATH" ] && [ ! -f "$HANDOFF_PATH" ]; }; then
    err "HANDOFF_PATH must be a regular non-symlink file: $HANDOFF_PATH"
  fi
fi

run_ts="$(date +%Y%m%d-%H%M%S)"
run_prefix="${PROJECT_RUN_ROOT}/${run_ts}-${run_slug}"
run_collision=0
RUN_DIR=""
while :; do
  if [ "$run_collision" -eq 0 ]; then
    candidate="$run_prefix"
  else
    candidate="${run_prefix}-${run_collision}"
  fi
  if (umask 077 && mkdir -- "$candidate") 2>/dev/null; then
    RUN_DIR="$candidate"
    break
  fi
  if [ ! -e "$candidate" ] && [ ! -L "$candidate" ]; then
    err "failed to create RUN_DIR: $candidate"
  fi
  run_collision=$((run_collision + 1))
  if [ "$run_collision" -gt 1000 ]; then
    err "too many RUN_DIR collisions under: $PROJECT_RUN_ROOT"
  fi
done

[ -d "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || err "RUN_DIR is not a real directory: $RUN_DIR"
RUN_DIR="$(CDPATH='' cd -- "$RUN_DIR" && pwd -P)"

printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT"
printf 'RUN_ROOT=%s\n' "$RUN_ROOT"
printf 'PROJECT_RUN_ROOT=%s\n' "$PROJECT_RUN_ROOT"
printf 'RUN_DIR=%s\n' "$RUN_DIR"
printf 'HANDOFF_PATH=%s\n' "$HANDOFF_PATH"
