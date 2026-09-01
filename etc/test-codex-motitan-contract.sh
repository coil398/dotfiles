#!/usr/bin/env bash
# shellcheck disable=SC2016

# codex-motitan の profile / launcher / runtime link 契約テスト。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
DOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd -P)"
PROFILE="${DOT_DIR}/.codex/motitan.config.toml"
LAUNCHER="${DOT_DIR}/bin/codex-motitan"
RUNTIME_LINKER="${DOT_DIR}/etc/link-codex-runtime.sh"
LINK_SCRIPT="${DOT_DIR}/etc/link.sh"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/codex-motitan-contract.XXXXXX")"
cleanup() {
    rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

fail() {
    printf '[codex-motitan-contract] FAIL: %s\n' "$*" >&2
    exit 1
}

assert_file() {
    [ -f "$1" ] || fail "missing file: $1"
}

assert_contains() {
    needle="$1"
    file="$2"
    grep -F -- "$needle" "$file" >/dev/null || fail "missing '$needle' in $file"
}

assert_file "$PROFILE"
assert_file "$LAUNCHER"
assert_file "$RUNTIME_LINKER"
assert_file "$LINK_SCRIPT"

TOML_PYTHON=""
for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 \
        && "$candidate" -c 'import tomllib' >/dev/null 2>&1; then
        TOML_PYTHON="$candidate"
        break
    fi
done
[ -n "$TOML_PYTHON" ] || fail 'Python 3.11+ with tomllib is required for TOML validation'

"$TOML_PYTHON" -c '
import pathlib
import sys
import tomllib

data = tomllib.loads(pathlib.Path(sys.argv[1]).read_text())
if data.get("sandbox_mode") != "danger-full-access":
    raise SystemExit("motitan profile must use danger-full-access")
if data.get("approval_policy") != "never":
    raise SystemExit("motitan profile must use approval_policy=never")
' "$PROFILE"

assert_contains 'git rev-parse --show-toplevel' "$LAUNCHER"
assert_contains "basename \"\$AUTOMATA_ROOT\"" "$LAUNCHER"
assert_contains 'scripts/unity-cli.sh' "$LAUNCHER"
assert_contains 'motitan_app' "$LAUNCHER"
assert_contains 'AGENTS.md' "$LAUNCHER"
assert_contains "exec codex -p motitan -C \"\$AUTOMATA_ROOT\" --add-dir \"\$APP_ROOT\" \"\$@\"" "$LAUNCHER"
assert_contains 'motitan.config.toml' "$RUNTIME_LINKER"
assert_contains 'link_motitan_launcher' "$LINK_SCRIPT"
assert_contains 'HOME/bin/codex-motitan' "$LINK_SCRIPT"
assert_contains 'refusing to replace non-symlink' "$LINK_SCRIPT"

assert_contains 'codex-motitan' "${DOT_DIR}/README.md"
assert_contains 'codex-motitan' "${DOT_DIR}/CLAUDE.md"
assert_contains '.codex/<name>.config.toml' "${DOT_DIR}/AI-WORKFLOW-SPEC.md"

grep -F 'sandbox_mode = "workspace-write"' "${DOT_DIR}/.codex/config.base.toml" >/dev/null \
    || fail 'normal Codex sandbox mode changed'
grep -F 'approval_policy = "on-request"' "${DOT_DIR}/.codex/config.base.toml" >/dev/null \
    || fail 'normal Codex approval policy changed'

# launcher の実引数を stub Codex で確認する。
VALID_ROOT="${TMP_ROOT}/motitan-automata"
APP_ROOT="${TMP_ROOT}/motitan_app"
STUB_BIN="${TMP_ROOT}/stub-bin"
ARGS_FILE="${TMP_ROOT}/codex-args"
mkdir -p "${VALID_ROOT}/scripts" "${VALID_ROOT}/work" "${APP_ROOT}" "${STUB_BIN}"
VALID_ROOT="$(cd -P "$VALID_ROOT" && pwd -P)"
APP_ROOT="$(cd -P "$APP_ROOT" && pwd -P)"
printf '%s\n' '# test automata guidance' > "${VALID_ROOT}/AGENTS.md"
printf '%s\n' '# test app guidance' > "${APP_ROOT}/AGENTS.md"
printf '%s\n' '#!/bin/sh' 'exit 0' > "${VALID_ROOT}/scripts/unity-cli.sh"
chmod +x "${VALID_ROOT}/scripts/unity-cli.sh"
git init -q "$VALID_ROOT"
printf '%s\n' '#!/bin/sh' 'printf "%s\\n" "$@" > "$CODEX_ARGS_FILE"' > "${STUB_BIN}/codex"
chmod +x "${STUB_BIN}/codex"

(
    cd "${VALID_ROOT}/work"
    PATH="${STUB_BIN}:/usr/bin:/bin" CODEX_ARGS_FILE="${ARGS_FILE}" \
        "$LAUNCHER" --help
)

actual_args=()
while IFS= read -r arg; do
    actual_args[${#actual_args[@]}]="$arg"
done < "$ARGS_FILE"
expected_args=(
    -p motitan
    -C "$VALID_ROOT"
    --add-dir "$APP_ROOT"
    --help
)
[ "${#actual_args[@]}" -eq "${#expected_args[@]}" ] \
    || fail "unexpected launcher argument count: ${#actual_args[@]}"
for i in "${!expected_args[@]}"; do
    [ "${actual_args[$i]}" = "${expected_args[$i]}" ] \
        || fail "unexpected launcher argument ${i}: ${actual_args[$i]}"
done

if (
    cd "$TMP_ROOT"
    PATH="${STUB_BIN}:/usr/bin:/bin" CODEX_ARGS_FILE="${ARGS_FILE}" \
        "$LAUNCHER" --help >/dev/null 2>&1
); then
    fail 'launcher must reject a non-motitan-automata cwd'
fi

if (
    cd "${VALID_ROOT}/work"
    PATH="${STUB_BIN}:/usr/bin:/bin" CODEX_ARGS_FILE="${ARGS_FILE}" \
        "$LAUNCHER" -p other >/dev/null 2>&1
); then
    fail 'launcher must reject a profile override'
fi

for forbidden_arg in --approve-for-me -pother '-s=workspace-write' -sworkspace-write '-a=on-request' -aon-request '-c=approval_policy="on-request"' '-capproval_policy="on-request"'; do
    if (
        cd "${VALID_ROOT}/work"
        PATH="${STUB_BIN}:/usr/bin:/bin" CODEX_ARGS_FILE="${ARGS_FILE}" \
            "$LAUNCHER" "$forbidden_arg" >/dev/null 2>&1
    ); then
        fail "launcher must reject permission/config override: $forbidden_arg"
    fi
done

# runtime profile link は隔離 HOME で実測する。
RUNTIME_HOME="${TMP_ROOT}/runtime-home"
mkdir -p "$RUNTIME_HOME"
HOME="$RUNTIME_HOME" bash "$RUNTIME_LINKER" --write-file motitan.config.toml
HOME="$RUNTIME_HOME" bash "$RUNTIME_LINKER" --check-file motitan.config.toml
RUNTIME_PROFILE="${RUNTIME_HOME}/.codex/motitan.config.toml"
[ -L "$RUNTIME_PROFILE" ] || fail 'runtime profile is not a symlink'
[ "$RUNTIME_PROFILE" -ef "$PROFILE" ] || fail 'runtime profile points to the wrong source'

# link.sh の専用modeは既存の実 bin と対象外ファイルを保持し、
# motitan profile とlauncherだけを追加する。
LINK_SOURCE="${TMP_ROOT}/link-source"
LINK_HOME="${TMP_ROOT}/link-home"
LINK_TEST_BIN="${TMP_ROOT}/link-test-bin"
mkdir -p "${LINK_SOURCE}/etc" "${LINK_SOURCE}/bin" "${LINK_SOURCE}/.codex" \
    "${LINK_HOME}/bin" "${LINK_TEST_BIN}"
cp "$LINK_SCRIPT" "${LINK_SOURCE}/etc/link.sh"
cp "$RUNTIME_LINKER" "${LINK_SOURCE}/etc/link-codex-runtime.sh"
cp "$LAUNCHER" "${LINK_SOURCE}/bin/codex-motitan"
cp "$PROFILE" "${LINK_SOURCE}/.codex/motitan.config.toml"
chmod +x "${LINK_SOURCE}/bin/codex-motitan"
printf '%s\n' 'keep this command' > "${LINK_HOME}/bin/other-command"
printf '%s\n' '#!/bin/sh' 'exit 0' > "${LINK_TEST_BIN}/git"
chmod +x "${LINK_TEST_BIN}/git"
printf '%s\n' '#!/bin/sh' 'exit 127' > "${LINK_TEST_BIN}/jq"
chmod +x "${LINK_TEST_BIN}/jq"

(
    HOME="$LINK_HOME" PATH="${LINK_TEST_BIN}:/usr/bin:/bin" \
        bash "${LINK_SOURCE}/etc/link.sh" --codex-motitan-only
)

LINKED_LAUNCHER="${LINK_HOME}/bin/codex-motitan"
[ -L "$LINKED_LAUNCHER" ] || fail 'link.sh did not create launcher symlink'
[ "$LINKED_LAUNCHER" -ef "${LINK_SOURCE}/bin/codex-motitan" ] \
    || fail 'link.sh launcher symlink points to the wrong source'
[ -d "${LINK_HOME}/bin" ] && [ ! -L "${LINK_HOME}/bin" ] \
    || fail 'link.sh replaced the existing bin directory'
[ -f "${LINK_HOME}/bin/other-command" ] \
    || fail 'link.sh removed an unrelated bin command'

rm -f "$LINKED_LAUNCHER"
printf '%s\n' 'protected launcher' > "$LINKED_LAUNCHER"
if (
    HOME="$LINK_HOME" PATH="${LINK_TEST_BIN}:/usr/bin:/bin" \
        bash "${LINK_SOURCE}/etc/link.sh" --codex-motitan-only >/dev/null 2>&1
); then
    fail 'link.sh must fail closed for a non-symlink launcher target'
fi
[ "$(cat "$LINKED_LAUNCHER")" = 'protected launcher' ] \
    || fail 'link.sh changed a protected non-symlink launcher target'

printf '%s\n' 'PASS: profile, launcher, runtime link, and link.sh contracts'
