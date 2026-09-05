#!/usr/bin/env bash

set -euo pipefail
umask 077

TEST_DIR="$(cd -- "$(dirname -- "$0")" && pwd -P)"
RUNNER="$TEST_DIR/../scripts/run-worker.sh"
TEST_ROOT=$(mktemp -d /tmp/worker-mutable-paths.XXXXXX)
FAKE_CODEX="$TEST_ROOT/fake-codex"

cleanup() {
    if [ -n "$TEST_ROOT" ] && [ -d "$TEST_ROOT" ]; then
        rm -rf "$TEST_ROOT"
    fi
}
trap cleanup EXIT HUP INT TERM

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

assert_contains() {
    assert_needle="$1"
    assert_file="$2"
    grep -Fq -- "$assert_needle" "$assert_file" || {
        printf '%s\n' "--- $assert_file ---" >&2
        sed -n '1,160p' "$assert_file" >&2 || true
        fail "expected $assert_file to contain: $assert_needle"
    }
}

cat >"$FAKE_CODEX" <<'FAKE_CODEX'
#!/bin/sh
set -eu
: > "$FAKE_EXEC_MARKER"
: > "$FAKE_ARGV"
for fake_arg do
    printf '%s\n' "$fake_arg" >> "$FAKE_ARGV"
done
fake_output=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        -o) fake_output="$2"; shift 2 ;;
        *) shift ;;
    esac
done
case "$FAKE_MUTATION" in
    default) chmod 0640 "$TEST_REPO/.codex/mutable/change.txt" ;;
    authorized)
        printf '%s\n' changed >> "$TEST_REPO/.codex/mutable/change.txt"
        printf '%s\n' created > "$TEST_REPO/.codex/mutable/created.txt"
        printf '%s\n' child-created > "$TEST_REPO/.codex/mutable/child/created.txt"
        rm -f "$TEST_REPO/.codex/mutable/delete.txt"
        ;;
    sibling) chmod 0640 "$TEST_REPO/.codex/sibling.txt" ;;
    unsafe-mode) chmod 0666 "$TEST_REPO/.codex/mutable/unsafe-mode.txt" ;;
    unsafe-symlink) ln -s "$TEST_OUTSIDE" "$TEST_REPO/.codex/mutable/unsafe-link" ;;
    git-metadata)
        mkdir -p "$TEST_REPO/.codex/mutable/.git"
        printf '%s\n' malicious > "$TEST_REPO/.codex/mutable/.git/config"
        ;;
    none) ;;
    *) exit 19 ;;
esac
printf '%s\n' 'ACTOR: luna' > "$fake_output"
printf '%s\n' 'ACTUAL_MODEL: gpt-5.6-luna' >> "$fake_output"
printf '%s\n' 'ACTUAL_EFFORT: max' >> "$fake_output"
printf '%s\n' 'STATUS: completed' >> "$fake_output"
printf '%s\n' 'CHANGED_FILES: fixture' >> "$fake_output"
printf '%s\n' 'OBSERVED_RESULTS: fake Codex mutation' >> "$fake_output"
printf '%s\n' 'BLOCKERS: none' >> "$fake_output"
printf '%s\n' 'ESCALATION_REASON: none' >> "$fake_output"
FAKE_CODEX
chmod 700 "$FAKE_CODEX"

new_fixture() {
    fixture_name="$1"
    fixture_repo="$TEST_ROOT/$fixture_name"
    fixture_marker="$TEST_ROOT/$fixture_name.codex-ran"
    fixture_stdout="$TEST_ROOT/$fixture_name.stdout"
    fixture_stderr="$TEST_ROOT/$fixture_name.stderr"
    fixture_argv="$TEST_ROOT/$fixture_name.argv"
    fixture_outside="$TEST_ROOT/$fixture_name.outside"
    git init -q "$fixture_repo"
    mkdir -p "$fixture_repo/.codex/mutable/child" "$fixture_repo/.codex/sibling" "$fixture_repo/output"
    printf '%s\n' original > "$fixture_repo/.codex/mutable/change.txt"
    printf '%s\n' delete-me > "$fixture_repo/.codex/mutable/delete.txt"
    printf '%s\n' child > "$fixture_repo/.codex/mutable/child/existing.txt"
    printf '%s\n' sibling > "$fixture_repo/.codex/sibling.txt"
    printf '%s\n' unsafe > "$fixture_repo/.codex/mutable/unsafe-mode.txt"
    printf '%s\n' outside > "$fixture_outside"
    printf '%s\n' task > "$fixture_repo/task.md"
    printf '%s\n' '- R1: deterministic fake runner fixture' > "$fixture_repo/requirements.md"
}

run_worker() {
    mutation="$1"
    shift
    TEST_REPO="$fixture_repo" TEST_OUTSIDE="$fixture_outside" FAKE_MUTATION="$mutation" FAKE_EXEC_MARKER="$fixture_marker" FAKE_ARGV="$fixture_argv" WORKER_DELEGATION_CODEX_BIN="$FAKE_CODEX" "$RUNNER" --actor luna --effort max --cwd "$fixture_repo" --task-file "$fixture_repo/task.md" --requirements-file "$fixture_repo/requirements.md" --output-file "$fixture_repo/output/result.md" "$@" >"$fixture_stdout" 2>"$fixture_stderr"
}

assert_disable_hooks_once() {
    argv_file="$1"
    awk '
        BEGIN { count = 0; previous = "" }
        {
            if (previous == "--disable" && $0 == "hooks") {
                count++
            }
            previous = $0
        }
        END {
            if (count != 1) {
                printf "expected exactly one --disable hooks argv pair, got %d\\n", count > "/dev/stderr"
                exit 1
            }
        }
    ' "$argv_file"
}

check_invalid() {
    invalid_value="$1"
    rm -f "$fixture_marker"
    if run_worker none --mutable-path "$invalid_value"; then
        fail "invalid mutable path unexpectedly succeeded: $invalid_value"
    fi
    [ ! -e "$fixture_marker" ] || fail "invalid path invoked fake Codex: $invalid_value"
}

help_output="$TEST_ROOT/help.txt"
"$RUNNER" --help >"$help_output"
assert_contains '--mutable-path <repo-relative-path>' "$help_output"

new_fixture default-mutation
if run_worker default; then
    fail 'default .codex mutation unexpectedly succeeded'
fi
[ -e "$fixture_marker" ] || fail 'default mutation did not invoke the fake Codex'
assert_contains 'tree identity changed' "$fixture_stderr"

new_fixture authorized-mutation
if ! run_worker authorized --mutable-path .codex/mutable/child --mutable-path .codex/mutable --mutable-path .codex/mutable; then
    sed -n '1,200p' "$fixture_stderr" >&2 || true
    fail 'authorized create/change/delete mutation failed'
fi
[ -e "$fixture_marker" ] || fail 'authorized mutation did not invoke the fake Codex'
[ -f "$fixture_argv" ] || fail 'fake Codex argv was not recorded'
assert_disable_hooks_once "$fixture_argv"
[ -f "$fixture_repo/output/result.md" ] || fail 'authorized worker report was not published'
[ -f "$fixture_repo/output/result.md.provenance.tsv" ] || fail 'authorized provenance was not published'
[ -f "$fixture_repo/.codex/mutable/created.txt" ] || fail 'authorized create was not retained'
[ -f "$fixture_repo/.codex/mutable/child/created.txt" ] || fail 'authorized descendant create was not retained'
[ ! -e "$fixture_repo/.codex/mutable/delete.txt" ] || fail 'authorized delete was not retained'

new_fixture mutable-git-metadata
if run_worker git-metadata --mutable-path .codex/mutable; then
    fail 'mutable .git metadata mutation unexpectedly succeeded'
fi
[ -e "$fixture_marker" ] || fail 'mutable .git metadata mutation did not invoke the fake Codex'
[ ! -e "$fixture_repo/output/result.md" ] || fail 'mutable .git metadata published a worker report'
[ ! -e "$fixture_repo/output/result.md.provenance.tsv" ] || fail 'mutable .git metadata published provenance'
assert_contains '.git' "$fixture_stderr"

new_fixture unauthorized-sibling
if run_worker sibling --mutable-path .codex/mutable; then
    fail 'undeclared sibling mutation unexpectedly succeeded'
fi
[ -e "$fixture_marker" ] || fail 'sibling mutation did not invoke the fake Codex'
assert_contains 'tree identity changed' "$fixture_stderr"

new_fixture unsafe-mode
if run_worker unsafe-mode --mutable-path .codex/mutable; then
    fail 'unsafe mode mutation unexpectedly succeeded'
fi
assert_contains 'group/world writable' "$fixture_stderr"

new_fixture unsafe-symlink
if run_worker unsafe-symlink --mutable-path .codex/mutable; then
    fail 'unsafe symlink mutation unexpectedly succeeded'
fi
assert_contains 'escapes the Git root' "$fixture_stderr"

new_fixture invalid-values
invalid_absolute="$fixture_repo/.codex/mutable"
ln -s "$fixture_repo/.codex/mutable/child" "$fixture_repo/.codex/mutable/link"
check_invalid ''
check_invalid '.'
check_invalid '..'
check_invalid '/'
check_invalid '.codex'
check_invalid '.codex/'
check_invalid '.codex//mutable'
check_invalid '.codex/./mutable'
check_invalid '.codex/mutable/..'
check_invalid '.codex/.git'
check_invalid '.codex/mutable/link'
check_invalid '.codex\mutable'
check_invalid ".codex/mutable\\"
check_invalid 'C:/tmp/mutable'
check_invalid "$invalid_absolute"

printf '%s\n' 'OK: mutable-path runner regression coverage'
