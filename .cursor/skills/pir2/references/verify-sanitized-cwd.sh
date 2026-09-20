#!/usr/bin/env bash
# Verify the executable run-directory contract embedded in sanitized-cwd.md.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REFERENCE_MD="${SCRIPT_DIR}/sanitized-cwd.md"

if [[ ! -f "$REFERENCE_MD" ]]; then
  echo "NG: run-directory reference is missing: $REFERENCE_MD"
  exit 1
fi

WORK_DIR="$(mktemp -d)"
cleanup() {
  if [[ -n "${WORK_DIR:-}" && -d "$WORK_DIR" ]]; then
    find "$WORK_DIR" -mindepth 1 -delete 2>/dev/null || true
    rmdir "$WORK_DIR" 2>/dev/null || true
  fi
}
trap cleanup EXIT HUP INT TERM

RUN_SCRIPT="$WORK_DIR/run-directory.sh"
awk '
  {
    line = $0
    trimmed = line
    gsub(/^[ \t]+|[ \t]+$/, "", trimmed)
    if (!seen && trimmed == "```bash") {
      seen = 1
      in_block = 1
      next
    }
    if (in_block && trimmed == "```") {
      exit
    }
    if (in_block) {
      print
    }
  }
' "$REFERENCE_MD" > "$RUN_SCRIPT"

if [[ ! -s "$RUN_SCRIPT" ]]; then
  echo "NG: no executable bash block found in $REFERENCE_MD"
  exit 1
fi

if ! bash -n "$RUN_SCRIPT" 2>"$WORK_DIR/bash-n.err"; then
  echo "NG: embedded run-directory block failed bash -n"
  sed 's/^/  /' "$WORK_DIR/bash-n.err"
  exit 1
fi
echo "OK: embedded run-directory block is syntax-valid"

FAKE_BIN="$WORK_DIR/bin"
mkdir "$FAKE_BIN"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'if [[ "${1-}" == "+%Y%m%d-%H%M%S" ]]; then' \
  '  printf "%s\\n" "20260912-010203"' \
  'else' \
  '  exec /bin/date "$@"' \
  'fi' > "$FAKE_BIN/date"
chmod 700 "$FAKE_BIN/date"

FAILURES=0
FIXTURES=0

fail() {
  FAILURES=$((FAILURES + 1))
  echo "  FAIL: $1"
}

assert_eq() {
  local expected="$1"
  local actual="$2"
  local description="$3"
  [[ "$actual" == "$expected" ]] || fail "$description: expected '$expected', got '$actual'"
}

assert_private_dir() {
  local path="$1"
  local description="$2"
  if [[ ! -d "$path" || -L "$path" ]]; then
    fail "$description: expected a real directory at $path"
    return
  fi
  if [[ "$(find "$path" -prune -type d -perm 700 -print)" != "$path" ]]; then
    fail "$description: expected mode 700"
  fi
}

setup_project() {
  local name="$1"
  local project="$WORK_DIR/$name"
  mkdir "$project"
  git -C "$project" -c init.defaultBranch=main init -q
  printf '%s\n' "$project"
}

run_reference() {
  local project="$1"
  local fixture_home="$2"
  local arguments="$3"
  local use_handoff="$4"
  local label="$5"
  mkdir -p "$fixture_home"
  RUN_OUT="$WORK_DIR/$label.out"
  RUN_ERR="$WORK_DIR/$label.err"
  set +e
  (
    cd "$project"
    env HOME="$fixture_home" PATH="$FAKE_BIN:$PATH" \
      ARGUMENTS="$arguments" USE_HANDOFF="$use_handoff" \
      bash "$RUN_SCRIPT"
  ) >"$RUN_OUT" 2>"$RUN_ERR"
  RUN_RC=$?
  set -e
}

output_value() {
  local key="$1"
  tr ' ' '\n' < "$RUN_OUT" | sed -n "s/^${key}=//p" | tail -n 1
}

echo "--- fixture: path calculation and private creation ---"
FIXTURES=$((FIXTURES + 1))
project="$(setup_project project.path-1)"
fixture_home="$WORK_DIR/home-path"
arguments='Feature / one'
run_reference "$project" "$fixture_home" "$arguments" false path-first
assert_eq 0 "$RUN_RC" "first run exit"
canonical_project="$(cd "$project" && pwd -P)"
sanitized="$(printf '%s' "$canonical_project" | sed 's|[^a-zA-Z0-9]|-|g')"
feature="$(printf '%s' "$arguments" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g; s/^-//; s/-$//' | cut -c1-40)"
expected_run="$fixture_home/.ai-pir-runs/$sanitized/20260912-010203-$feature"
expected_memory="$fixture_home/.cursor/projects/$sanitized/memory"
actual_run="$(output_value RUN_DIR)"
actual_memory="$(output_value PROJECT_MEMORY_DIR)"
assert_eq "$expected_run" "$actual_run" "RUN_DIR calculation"
assert_eq "$expected_memory" "$actual_memory" "PROJECT_MEMORY_DIR calculation"
assert_private_dir "$actual_run" "created RUN_DIR"
if [[ -n "$actual_run" && -d "$actual_run" && "$actual_run" == "$fixture_home/.ai-pir-runs/"* ]]; then
  printf 'preserve\n' > "$actual_run/sentinel"
else
  fail "created RUN_DIR is not a safe fixture path; collision sentinel was not written"
fi
case "$actual_run" in
  "$canonical_project"|"$canonical_project"/*) fail "RUN_DIR must be outside PROJECT_ROOT" ;;
esac

echo "--- fixture: same-timestamp collision ---"
FIXTURES=$((FIXTURES + 1))
run_reference "$project" "$fixture_home" "$arguments" false path-second
assert_eq 0 "$RUN_RC" "collision run exit"
collision_run="$(output_value RUN_DIR)"
assert_eq "${expected_run}-1" "$collision_run" "collision suffix"
assert_private_dir "$collision_run" "collision RUN_DIR"
[[ -d "$expected_run" ]] || fail "collision handling removed or overwrote the first RUN_DIR"
assert_eq preserve "$(sed -n '1p' "$expected_run/sentinel" 2>/dev/null || true)" "collision preserved the first RUN_DIR contents"

echo "--- fixture: symlink RUN_ROOT rejection ---"
FIXTURES=$((FIXTURES + 1))
project="$(setup_project project-symlink-root)"
fixture_home="$WORK_DIR/home-symlink-root"
mkdir -p "$fixture_home" "$WORK_DIR/symlink-target"
ln -s "$WORK_DIR/symlink-target" "$fixture_home/.ai-pir-runs"
run_reference "$project" "$fixture_home" task false symlink-root
[[ "$RUN_RC" -ne 0 ]] || fail "symlink RUN_ROOT was accepted"
grep -qF 'RUN_ROOT must not be a symlink' "$RUN_ERR" || fail "symlink RUN_ROOT rejection reason missing"

echo "--- fixture: non-directory RUN_ROOT rejection ---"
FIXTURES=$((FIXTURES + 1))
project="$(setup_project project-file-root)"
fixture_home="$WORK_DIR/home-file-root"
mkdir -p "$fixture_home"
printf 'not a directory\n' > "$fixture_home/.ai-pir-runs"
run_reference "$project" "$fixture_home" task false file-root
[[ "$RUN_RC" -ne 0 ]] || fail "regular-file RUN_ROOT was accepted"
grep -qF 'RUN_ROOT exists but is not a directory' "$RUN_ERR" || fail "regular-file RUN_ROOT rejection reason missing"

echo "--- fixture: in-project RUN_ROOT rejection ---"
FIXTURES=$((FIXTURES + 1))
project="$(setup_project project-in-root)"
run_reference "$project" "$project" task false in-project-root
[[ "$RUN_RC" -ne 0 ]] || fail "RUN_ROOT inside PROJECT_ROOT was accepted"
grep -qF 'RUN_ROOT must be outside PROJECT_ROOT' "$RUN_ERR" || fail "in-project RUN_ROOT rejection reason missing"

echo "--- fixture: symlink project bucket rejection ---"
FIXTURES=$((FIXTURES + 1))
project="$(setup_project project-symlink-bucket)"
fixture_home="$WORK_DIR/home-symlink-bucket"
mkdir -p "$fixture_home/.ai-pir-runs" "$WORK_DIR/bucket-target"
canonical_project="$(cd "$project" && pwd -P)"
sanitized="$(printf '%s' "$canonical_project" | sed 's|[^a-zA-Z0-9]|-|g')"
ln -s "$WORK_DIR/bucket-target" "$fixture_home/.ai-pir-runs/$sanitized"
run_reference "$project" "$fixture_home" task false symlink-bucket
[[ "$RUN_RC" -ne 0 ]] || fail "symlink project bucket was accepted"
[[ -z "$(find "$WORK_DIR/bucket-target" -mindepth 1 -print -quit)" ]] || fail "symlink project bucket target was modified"

if [[ "$FAILURES" -gt 0 ]]; then
  echo "NG: $FAILURES failure(s) across $FIXTURES run-directory fixtures"
  exit 1
fi

echo "OK: $FIXTURES run-directory fixtures passed"
