#!/bin/sh

set -eu

usage() {
    printf '%s\n' "Usage: $0 --cwd DIR --task-file FILE --requirements-file FILE --output-file FILE"
}

cwd=""
task_file=""
requirements_file=""
output_file=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --cwd)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            cwd="$2"
            shift 2
            ;;
        --task-file)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            task_file="$2"
            shift 2
            ;;
        --requirements-file)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            requirements_file="$2"
            shift 2
            ;;
        --output-file)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            output_file="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown argument: %s\n' "$1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

[ -n "$cwd" ] || { printf '%s\n' 'ERROR: --cwd is required' >&2; exit 2; }
[ -n "$task_file" ] || { printf '%s\n' 'ERROR: --task-file is required' >&2; exit 2; }
[ -n "$requirements_file" ] || { printf '%s\n' 'ERROR: --requirements-file is required' >&2; exit 2; }
[ -n "$output_file" ] || { printf '%s\n' 'ERROR: --output-file is required' >&2; exit 2; }
[ -d "$cwd" ] || { printf 'ERROR: cwd is not a directory: %s\n' "$cwd" >&2; exit 2; }
[ -s "$task_file" ] || { printf 'ERROR: task file is missing or empty: %s\n' "$task_file" >&2; exit 2; }
[ -s "$requirements_file" ] || { printf 'ERROR: requirements file is missing or empty: %s\n' "$requirements_file" >&2; exit 2; }
grep -Eq '^[[:space:]]*-[[:space:]]+R[0-9]+:' "$requirements_file" || {
    printf 'ERROR: requirements must contain at least one "- R<number>:" criterion\n' >&2
    exit 2
}

output_dir=$(dirname "$output_file")
[ -d "$output_dir" ] || { printf 'ERROR: output directory does not exist: %s\n' "$output_dir" >&2; exit 2; }
[ ! -e "$output_file" ] || { printf 'ERROR: output file already exists: %s\n' "$output_file" >&2; exit 2; }

if [ -n "${LUNA_MAX_CODEX_BIN:-}" ]; then
    codex_bin=$LUNA_MAX_CODEX_BIN
elif [ -f "$HOME/AppData/Roaming/npm/codex.cmd" ]; then
    # Git Bash on Windows may resolve an older Desktop-bundled codex first.
    codex_bin="$HOME/AppData/Roaming/npm/codex.cmd"
else
    codex_bin=codex
fi

if [ ! -f "$codex_bin" ] && ! command -v "$codex_bin" >/dev/null 2>&1; then
    printf 'ERROR: codex command not found: %s\n' "$codex_bin" >&2
    exit 127
fi

scratch_dir=$(mktemp -d "${TMPDIR:-/tmp}/luna-max-worker.XXXXXX")
prompt_file="$scratch_dir/prompt.md"
cleanup() {
    rm -f "$prompt_file"
    rmdir "$scratch_dir" 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM

{
    printf '%s\n\n' '# Role'
    printf '%s\n' 'You are the execution worker for a task already planned by the parent Sol agent.'
    printf '%s\n' 'Perform only the concrete task below. Do not redesign the task, expand scope, invoke luna-max-worker, or spawn other agents.'
    printf '%s\n' 'Do not commit, push, discard existing user changes, or use destructive git commands.'
    printf '%s\n' 'If the instructions are insufficient or require a new decision, stop and report the exact blocker.'
    printf '%s\n\n' '# Task'
    cat "$task_file"
    printf '%s\n\n' '# Acceptance criteria'
    cat "$requirements_file"
    printf '%s\n\n' '# Completion report'
    printf '%s\n' 'Report changed files, commands run, observed results, and blockers. Your report is not the acceptance decision; the parent Sol agent verifies every criterion independently.'
} > "$prompt_file"

"$codex_bin" exec \
    --json \
    --skip-git-repo-check \
    -m gpt-5.6-luna \
    -c 'model_reasoning_effort="max"' \
    -s workspace-write \
    -C "$cwd" \
    -o "$output_file" \
    - < "$prompt_file"
