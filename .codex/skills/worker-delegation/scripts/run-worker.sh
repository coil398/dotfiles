#!/bin/sh

# Worker reports and all runner-created scratch files are private by default.
umask 077
set -eu

# Return a stable filesystem identity for a path without following a symlink.
# GNU coreutils stat and macOS/BSD stat use different format flags, so try the
# GNU form first and the BSD form second.  The record intentionally contains
# only values used for the boundary checks: device, inode, owner UID, mode.
worker_stat_identity() {
    worker_stat_path="$1"
    if worker_stat_record=$(stat -c '%d %i %u %a' "$worker_stat_path" 2>/dev/null); then
        printf '%s\n' "$worker_stat_record"
        return 0
    fi
    if worker_stat_record=$(stat -f '%d %i %u %Lp' "$worker_stat_path" 2>/dev/null); then
        printf '%s\n' "$worker_stat_record"
        return 0
    fi
    return 1
}

# Validate ownership and permissions for any non-symlink path.  The caller
# compares the returned identity with its initial value to detect replacement
# or mode/owner tampering.  Group/world write bits are rejected; owner writes
# remain allowed because the worker is expected to modify its source files.
worker_secure_path_identity() {
    worker_secure_path="$1"
    worker_secure_label="$2"
    [ ! -L "$worker_secure_path" ] || {
        printf 'ERROR: %s must not be a symlink: %s\n' "$worker_secure_label" "$worker_secure_path" >&2
        return 1
    }
    [ -e "$worker_secure_path" ] || {
        printf 'ERROR: %s does not exist: %s\n' "$worker_secure_label" "$worker_secure_path" >&2
        return 1
    }
    worker_secure_record=$(worker_stat_identity "$worker_secure_path") || {
        printf 'ERROR: could not inspect %s: %s\n' "$worker_secure_label" "$worker_secure_path" >&2
        return 1
    }
    # Deliberately split the four machine-generated stat fields.
    # shellcheck disable=SC2086
    set -- $worker_secure_record
    [ "$#" -eq 4 ] || {
        printf 'ERROR: unexpected identity record for %s: %s\n' "$worker_secure_label" "$worker_secure_path" >&2
        return 1
    }
    worker_secure_uid="$3"
    worker_secure_mode="$4"
    [ "$worker_secure_uid" = "$worker_current_uid" ] || {
        printf 'ERROR: %s is not owned by the current UID: %s\n' "$worker_secure_label" "$worker_secure_path" >&2
        return 1
    }
    worker_secure_mode_decimal=$(printf '%d' "0$worker_secure_mode" 2>/dev/null) || {
        printf 'ERROR: could not parse mode for %s: %s\n' "$worker_secure_label" "$worker_secure_path" >&2
        return 1
    }
    case "$worker_secure_mode_decimal" in
        ''|*[!0-9]*)
            printf 'ERROR: could not parse mode for %s: %s\n' "$worker_secure_label" "$worker_secure_path" >&2
            return 1
            ;;
    esac
    if [ $((worker_secure_mode_decimal & 18)) -ne 0 ]; then
        printf 'ERROR: %s is group/world writable: %s\n' "$worker_secure_label" "$worker_secure_path" >&2
        return 1
    fi
    printf '%s\n' "$worker_secure_record"
}

worker_secure_directory_identity() {
    worker_secure_dir="$1"
    worker_secure_dir_label="$2"
    [ -d "$worker_secure_dir" ] || {
        printf 'ERROR: %s is not a directory: %s\n' "$worker_secure_dir_label" "$worker_secure_dir" >&2
        return 1
    }
    worker_secure_path_identity "$worker_secure_dir" "$worker_secure_dir_label"
}

# Build the complete physical directory chain from an allowed root through an
# output parent.  The runner authorizes the chain itself, not only its two
# endpoints: every component is a non-symlink directory owned by the current
# UID and free of group/world write bits.  One tab-delimited record is emitted
# per component as `absolute-path<TAB>device inode uid mode`.
worker_capture_directory_chain() {
    worker_chain_root="$1"
    worker_chain_leaf="$2"
    worker_chain_label="$3"

    case "$worker_chain_leaf" in
        "$worker_chain_root")
            worker_chain_remainder=""
            ;;
        "$worker_chain_root"/*)
            worker_chain_remainder=${worker_chain_leaf#"$worker_chain_root"/}
            ;;
        *)
            printf 'ERROR: %s is outside its allowed root: %s (root %s)\n' \
                "$worker_chain_label" "$worker_chain_leaf" "$worker_chain_root" >&2
            return 1
            ;;
    esac

    worker_chain_current="$worker_chain_root"
    worker_chain_identity=$(worker_secure_directory_identity \
        "$worker_chain_current" "$worker_chain_label component") || return 1
    printf '%s\t%s\n' "$worker_chain_current" "$worker_chain_identity"

    while [ -n "$worker_chain_remainder" ]; do
        case "$worker_chain_remainder" in
            */*)
                worker_chain_component=${worker_chain_remainder%%/*}
                worker_chain_remainder=${worker_chain_remainder#*/}
                ;;
            *)
                worker_chain_component="$worker_chain_remainder"
                worker_chain_remainder=""
                ;;
        esac
        [ -n "$worker_chain_component" ] || continue
        worker_chain_current="$worker_chain_current/$worker_chain_component"
        worker_chain_identity=$(worker_secure_directory_identity \
            "$worker_chain_current" "$worker_chain_label component") || return 1
        printf '%s\t%s\n' "$worker_chain_current" "$worker_chain_identity"
    done
}

# Re-inspect every component captured by worker_capture_directory_chain and
# require an exact identity match.  This detects intermediate-directory
# replacement, not only root/leaf replacement, and therefore fails closed if a
# path component becomes a symlink or changes device, inode, owner, or mode.
worker_validate_directory_chain() {
    worker_chain_records="$1"
    worker_chain_phase="$2"
    worker_chain_label="$3"
    worker_chain_ifs_tab="$(printf '\t')"
    while IFS="$worker_chain_ifs_tab" read -r worker_chain_path worker_chain_expected; do
        [ -n "$worker_chain_path" ] || continue
        worker_chain_actual=$(worker_secure_directory_identity \
            "$worker_chain_path" "$worker_chain_label component") || return 1
        [ "$worker_chain_actual" = "$worker_chain_expected" ] || {
            printf 'ERROR: %s detected %s identity change (race/tampering): %s\n' \
                "$worker_chain_phase" "$worker_chain_label" "$worker_chain_path" >&2
            return 1
        }
    done <<EOF
$worker_chain_records
EOF
}

usage() {
    printf '%s\n' "Usage: $0 --actor luna|terra|sol [--effort high|max] --cwd DIR --task-file FILE --requirements-file FILE --output-file FILE"
    printf '%s\n' '  luna: --effort max only (default max)'
    printf '%s\n' '  terra: --effort high or max (default high)'
    printf '%s\n' '  sol: --effort high or max (default high; exceptional Sol worker only)'
}

actor=""
effort=""
cwd=""
task_file=""
requirements_file=""
output_file=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --actor)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            actor="$2"
            shift 2
            ;;
        --effort)
            [ "$#" -ge 2 ] || { usage >&2; exit 2; }
            effort="$2"
            shift 2
            ;;
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

case "$actor" in
    luna)
        model="gpt-5.6-luna"
        default_effort="max"
        ;;
    terra)
        model="gpt-5.6-terra"
        default_effort="high"
        ;;
    sol)
        model="gpt-5.6-sol"
        default_effort="high"
        ;;
    "")
        printf '%s\n' 'ERROR: --actor is required' >&2
        exit 2
        ;;
    *)
        printf 'ERROR: unknown actor: %s\n' "$actor" >&2
        exit 2
        ;;
esac

if [ -z "$effort" ]; then
    effort="$default_effort"
fi

case "$effort" in
    high|max)
        ;;
    *)
        printf 'ERROR: unknown effort: %s\n' "$effort" >&2
        exit 2
        ;;
esac

if [ "$actor" = "luna" ] && [ "$effort" != "max" ]; then
    printf '%s\n' 'ERROR: luna supports --effort max only' >&2
    exit 2
fi

[ -n "$cwd" ] || { printf '%s\n' 'ERROR: --cwd is required' >&2; exit 2; }
[ -n "$task_file" ] || { printf '%s\n' 'ERROR: --task-file is required' >&2; exit 2; }
[ -n "$requirements_file" ] || { printf '%s\n' 'ERROR: --requirements-file is required' >&2; exit 2; }
[ -n "$output_file" ] || { printf '%s\n' 'ERROR: --output-file is required' >&2; exit 2; }
[ -d "$cwd" ] || { printf 'ERROR: cwd is not a directory: %s\n' "$cwd" >&2; exit 2; }
worker_current_uid="$(id -u 2>/dev/null)" || {
    printf '%s\n' 'ERROR: could not determine the current UID' >&2
    exit 2
}

# Resolve the requested working directory before handing it to Codex.  Codex
# must operate at the physical Git repository root, not at a symlinked path,
# repository subdirectory, or unrelated non-Git directory.
cwd_physical="$(cd -P "$cwd" 2>/dev/null && pwd -P)" || {
    printf 'ERROR: could not canonicalize cwd: %s\n' "$cwd" >&2
    exit 2
}
git_root="$(git -C "$cwd_physical" rev-parse --show-toplevel 2>/dev/null)" || {
    printf 'ERROR: cwd is not inside a Git repository: %s\n' "$cwd" >&2
    exit 2
}
git_root_physical="$(cd -P "$git_root" 2>/dev/null && pwd -P)" || {
    printf 'ERROR: could not canonicalize Git top-level: %s\n' "$git_root" >&2
    exit 2
}
if [ "$cwd_physical" != "$git_root_physical" ]; then
    printf 'ERROR: cwd must be the physical Git top-level (got %s, expected %s)\n' \
        "$cwd_physical" "$git_root_physical" >&2
    exit 2
fi

# A symlink alias in an ancestor such as /var -> /private/var is harmless, but
# an explicit symlink at or below the repository root is not a trusted cwd
# spelling.  Check after the physical root is known so ancestor aliases are
# ignored while repo-local aliases remain rejected.
path_has_symlink_at_or_below_root() {
    symlink_path="$1"
    symlink_root="$2"
    case "$symlink_path" in
        /*) ;;
        *) symlink_path="$(pwd -P)/$symlink_path" ;;
    esac

    symlink_remainder="${symlink_path#/}"
    symlink_current="/"
    symlink_physical_current="/"
    while :; do
        case "$symlink_remainder" in
            "") break ;;
            */*) symlink_component="${symlink_remainder%%/*}"; symlink_remainder="${symlink_remainder#*/}" ;;
            *) symlink_component="$symlink_remainder"; symlink_remainder="" ;;
        esac
        case "$symlink_component" in
            ""|.) continue ;;
        esac
        if [ "$symlink_current" = "/" ]; then
            symlink_candidate="/$symlink_component"
        else
            symlink_candidate="$symlink_current/$symlink_component"
        fi

        case "$symlink_physical_current" in
            "$symlink_root"|"$symlink_root"/*)
                [ ! -L "$symlink_candidate" ] || return 0
                ;;
        esac
        symlink_physical_next="$(cd -P "$symlink_candidate" 2>/dev/null && pwd -P)" || return 2
        case "$symlink_physical_next" in
            "$symlink_root"|"$symlink_root"/*)
                [ ! -L "$symlink_candidate" ] || return 0
                ;;
        esac
        symlink_current="$symlink_candidate"
        symlink_physical_current="$symlink_physical_next"
    done
    return 1
}

# Inspect every .codex descendant without following symlinks.  Besides the
# existing static-link rejection, every entry must remain owned by the current
# UID and must not be group/world writable.  This is deliberately a path scan:
# the Codex CLI accepts paths, not directory file descriptors.
worker_validate_codex_tree() {
    worker_tree_symlink="$(find -P "$codex_dir_physical" -type l -print -quit 2>/dev/null)" || {
        printf 'ERROR: could not scan cwd/.codex for symlinks: %s\n' "$codex_dir_physical" >&2
        return 1
    }
    if [ -n "$worker_tree_symlink" ]; then
        printf 'ERROR: cwd/.codex contains a symlink descendant: %s\n' "$worker_tree_symlink" >&2
        return 1
    fi

    worker_tree_entries="$(find -P "$codex_dir_physical" -mindepth 1 -print 2>/dev/null)" || {
        printf 'ERROR: could not scan cwd/.codex descendants: %s\n' "$codex_dir_physical" >&2
        return 1
    }
    while IFS= read -r worker_tree_entry; do
        [ -n "$worker_tree_entry" ] || continue
        [ ! -L "$worker_tree_entry" ] || {
            printf 'ERROR: cwd/.codex contains a symlink descendant: %s\n' "$worker_tree_entry" >&2
            return 1
        }
        worker_secure_path_identity "$worker_tree_entry" 'cwd/.codex descendant' >/dev/null || return 1
    done <<EOF
$worker_tree_entries
EOF
}

if path_has_symlink_at_or_below_root "$cwd" "$cwd_physical"; then
    printf 'ERROR: cwd contains a symlink component at or below the Git root: %s\n' "$cwd" >&2
    exit 2
else
    worker_cwd_symlink_status=$?
    [ "$worker_cwd_symlink_status" -eq 1 ] || {
        printf 'ERROR: could not inspect cwd path components: %s\n' "$cwd" >&2
        exit 2
    }
fi

# The extra Codex search path is deliberately limited to a real child of the
# canonical repository root.  Reject a symlinked .codex directory even when
# it points back inside the repository so the authorization boundary cannot
# change underneath the runner.
codex_dir="$cwd_physical/.codex"
[ -d "$codex_dir" ] || {
    printf 'ERROR: cwd/.codex is not a directory: %s\n' "$codex_dir" >&2
    exit 2
}
[ ! -L "$codex_dir" ] || {
    printf 'ERROR: cwd/.codex must be a real non-symlink directory: %s\n' "$codex_dir" >&2
    exit 2
}
codex_dir_physical="$(cd -P "$codex_dir" 2>/dev/null && pwd -P)" || {
    printf 'ERROR: could not canonicalize cwd/.codex: %s\n' "$codex_dir" >&2
    exit 2
}
case "$codex_dir_physical" in
    "$cwd_physical"/*) ;;
    *)
        printf 'ERROR: cwd/.codex must remain physically inside cwd: %s\n' "$codex_dir_physical" >&2
        exit 2
        ;;
esac

# Codex receives this directory through --add-dir, so every descendant must
# be a real, current-UID-owned, non-group/world-writable path.  The scan does
# not follow symlinked directories.
worker_validate_codex_tree || exit 2

[ -s "$task_file" ] || { printf 'ERROR: task file is missing or empty: %s\n' "$task_file" >&2; exit 2; }
[ -s "$requirements_file" ] || { printf 'ERROR: requirements file is missing or empty: %s\n' "$requirements_file" >&2; exit 2; }
grep -Eq '^[[:space:]]*-[[:space:]]+R[0-9]+:' "$requirements_file" || {
    printf '%s\n' 'ERROR: requirements must contain at least one "- R<number>:" criterion' >&2
    exit 2
}

# Resolve the output parent physically and require it to remain inside either
# the canonical cwd or the standard Sol artifact root.  The artifact root is
# intentionally fixed to $HOME/.ai-pir-runs; no caller-controlled broad root
# is accepted.  Resolve it opportunistically: cwd-local output is valid on its
# own, while an external output can match only an existing real root.
artifact_root=""
artifact_root_physical=""
if [ -n "${HOME:-}" ] && [ -d "$HOME" ]; then
    home_physical="$(cd -P "$HOME" 2>/dev/null && pwd -P || true)"
    if [ -n "$home_physical" ]; then
        artifact_root="$HOME/.ai-pir-runs"
        if [ -d "$artifact_root" ] && [ ! -L "$artifact_root" ]; then
            artifact_root_physical="$(cd -P "$artifact_root" 2>/dev/null && pwd -P || true)"
            case "$artifact_root_physical" in
                "$home_physical"/*) ;;
                *) artifact_root_physical="" ;;
            esac
        fi
    fi
fi

output_dir="$(dirname "$output_file")"
[ -d "$output_dir" ] || { printf 'ERROR: output directory does not exist: %s\n' "$output_dir" >&2; exit 2; }
output_dir_physical="$(cd -P "$output_dir" 2>/dev/null && pwd -P)" || {
    printf 'ERROR: could not canonicalize output directory: %s\n' "$output_dir" >&2
    exit 2
}
output_allowed_root=""
case "$output_dir_physical" in
    "$cwd_physical"|"$cwd_physical"/*)
        output_allowed_root="$cwd_physical"
        ;;
    "$artifact_root_physical"|"$artifact_root_physical"/*)
        if [ -z "$artifact_root_physical" ]; then
            printf "ERROR: output directory must be physically inside cwd or an existing real \$HOME/.ai-pir-runs: %s\n" "$output_dir" >&2
            exit 2
        fi
        output_allowed_root="$artifact_root_physical"
        ;;
    *)
        printf "ERROR: output directory must be physically inside cwd or \$HOME/.ai-pir-runs: %s\n" "$output_dir" >&2
        exit 2
        ;;
esac
if path_has_symlink_at_or_below_root "$output_dir" "$output_allowed_root"; then
    printf 'ERROR: output directory contains a symlink component at or below its allowed root: %s\n' "$output_dir" >&2
    exit 2
else
    worker_output_symlink_status=$?
    [ "$worker_output_symlink_status" -eq 1 ] || {
        printf 'ERROR: could not inspect output directory path components: %s\n' "$output_dir" >&2
        exit 2
    }
fi

output_name="$(basename "$output_file")"
case "$output_name" in
    ""|.|..)
        printf 'ERROR: output file must name a regular file: %s\n' "$output_file" >&2
        exit 2
        ;;
esac
output_file_physical="$output_dir_physical/$output_name"
[ ! -e "$output_file" ] && [ ! -L "$output_file" ] || {
    printf 'ERROR: output file already exists: %s\n' "$output_file" >&2
    exit 2
}
[ ! -e "$output_file_physical" ] && [ ! -L "$output_file_physical" ] || {
    printf 'ERROR: output file already exists: %s\n' "$output_file_physical" >&2
    exit 2
}

# The provenance path is a sibling of the final raw report.  It is a separate
# no-replace publication target and must be absent before the worker starts;
# checking both the caller spelling and its physical spelling handles aliases
# without allowing a raced file or symlink to be overwritten.
provenance_file="${output_file}.provenance.tsv"
provenance_file_physical="$output_dir_physical/${output_name}.provenance.tsv"
[ ! -e "$provenance_file" ] && [ ! -L "$provenance_file" ] || {
    printf 'ERROR: provenance sidecar already exists: %s\n' "$provenance_file" >&2
    exit 2
}
[ ! -e "$provenance_file_physical" ] && [ ! -L "$provenance_file_physical" ] || {
    printf 'ERROR: provenance sidecar already exists: %s\n' "$provenance_file_physical" >&2
    exit 2
}

worker_validate_output_slots() {
    worker_slots_phase="$1"
    [ ! -e "$output_file" ] && [ ! -L "$output_file" ] || {
        printf 'ERROR: %s found an existing final worker output: %s\n' \
            "$worker_slots_phase" "$output_file" >&2
        return 1
    }
    [ ! -e "$output_file_physical" ] && [ ! -L "$output_file_physical" ] || {
        printf 'ERROR: %s found an existing physical final worker output: %s\n' \
            "$worker_slots_phase" "$output_file_physical" >&2
        return 1
    }
    [ ! -e "$provenance_file" ] && [ ! -L "$provenance_file" ] || {
        printf 'ERROR: %s found an existing provenance sidecar: %s\n' \
            "$worker_slots_phase" "$provenance_file" >&2
        return 1
    }
    [ ! -e "$provenance_file_physical" ] && [ ! -L "$provenance_file_physical" ] || {
        printf 'ERROR: %s found an existing physical provenance sidecar: %s\n' \
            "$worker_slots_phase" "$provenance_file_physical" >&2
        return 1
    }
}

# Capture the first verified identity for every path that forms the runner's
# authorization boundary.  The endpoint identities are retained for the
# explicit root/parent checks, while the chain records cover every directory
# component between the selected allowed root and output parent.
worker_repo_root_identity="$(worker_secure_directory_identity "$git_root_physical" 'Git repository root')" || exit 2
worker_codex_identity="$(worker_secure_directory_identity "$codex_dir_physical" 'cwd/.codex')" || exit 2
worker_output_allowed_root_identity="$(worker_secure_directory_identity "$output_allowed_root" 'output allowed root')" || exit 2
worker_output_parent_identity="$(worker_secure_directory_identity "$output_dir_physical" 'output parent')" || exit 2
worker_output_chain_records="$(worker_capture_directory_chain \
    "$output_allowed_root" "$output_dir_physical" 'output boundary')" || exit 2

worker_validate_output_slots 'initial' || exit 2

worker_validate_boundary_state() {
    worker_boundary_phase="$1"

    worker_boundary_identity="$(worker_secure_directory_identity "$git_root_physical" 'Git repository root')" || return 1
    [ "$worker_boundary_identity" = "$worker_repo_root_identity" ] || {
        printf 'ERROR: %s detected Git repository root identity change (race/tampering)\n' "$worker_boundary_phase" >&2
        return 1
    }

    worker_boundary_identity="$(worker_secure_directory_identity "$codex_dir_physical" 'cwd/.codex')" || return 1
    [ "$worker_boundary_identity" = "$worker_codex_identity" ] || {
        printf 'ERROR: %s detected .codex identity change (race/tampering)\n' "$worker_boundary_phase" >&2
        return 1
    }

    worker_boundary_identity="$(worker_secure_directory_identity "$output_allowed_root" 'output allowed root')" || return 1
    [ "$worker_boundary_identity" = "$worker_output_allowed_root_identity" ] || {
        printf 'ERROR: %s detected output allowed root identity change (race/tampering)\n' "$worker_boundary_phase" >&2
        return 1
    }

    worker_boundary_identity="$(worker_secure_directory_identity "$output_dir_physical" 'output parent')" || return 1
    [ "$worker_boundary_identity" = "$worker_output_parent_identity" ] || {
        printf 'ERROR: %s detected output parent identity change (race/tampering)\n' "$worker_boundary_phase" >&2
        return 1
    }

    worker_validate_directory_chain "$worker_output_chain_records" \
        "$worker_boundary_phase" 'output boundary' || return 1

    if path_has_symlink_at_or_below_root "$output_dir" "$output_allowed_root"; then
        printf 'ERROR: %s detected a symlink in the output path (race/tampering)\n' "$worker_boundary_phase" >&2
        return 1
    else
        worker_boundary_symlink_status=$?
        [ "$worker_boundary_symlink_status" -eq 1 ] || {
            printf 'ERROR: %s could not inspect the output path (race/tampering)\n' "$worker_boundary_phase" >&2
            return 1
        }
    fi

    worker_validate_codex_tree || return 1
    worker_validate_output_slots "$worker_boundary_phase" || return 1
    return 0
}

codex_bin=${WORKER_DELEGATION_CODEX_BIN:-codex}
command -v "$codex_bin" >/dev/null 2>&1 || { printf 'ERROR: codex command not found: %s\n' "$codex_bin" >&2; exit 127; }

scratch_dir=$(mktemp -d "${TMPDIR:-/tmp}/worker-delegation.XXXXXX")
prompt_file="$scratch_dir/prompt.md"
codex_output=""
provenance_output=""
worker_scratch_parent="$(dirname "$scratch_dir")"
worker_scratch_parent_identity="$(worker_stat_identity "$worker_scratch_parent" 2>/dev/null || true)"
worker_scratch_dir_identity="$(worker_stat_identity "$scratch_dir" 2>/dev/null || true)"
cleanup() {
    if [ -n "${codex_output:-}" ]; then
        worker_cleanup_parent_identity="$(worker_stat_identity "$output_dir_physical" 2>/dev/null || true)"
        if [ "$worker_cleanup_parent_identity" = "$worker_output_parent_identity" ] \
            && [ -f "$codex_output" ] && [ ! -L "$codex_output" ]; then
            rm -f "$codex_output" 2>/dev/null || true
        fi
    fi
    if [ -n "${provenance_output:-}" ]; then
        worker_cleanup_provenance_parent_identity="$(worker_stat_identity "$output_dir_physical" 2>/dev/null || true)"
        if [ "$worker_cleanup_provenance_parent_identity" = "$worker_output_parent_identity" ] \
            && [ -f "$provenance_output" ] && [ ! -L "$provenance_output" ]; then
            rm -f "$provenance_output" 2>/dev/null || true
        fi
    fi
    if [ -n "${worker_scratch_parent_identity:-}" ]; then
        worker_cleanup_scratch_parent_identity="$(worker_stat_identity "$worker_scratch_parent" 2>/dev/null || true)"
        if [ "$worker_cleanup_scratch_parent_identity" = "$worker_scratch_parent_identity" ] \
            && [ -f "$prompt_file" ] && [ ! -L "$prompt_file" ]; then
            rm -f "$prompt_file" 2>/dev/null || true
        fi
    fi
    worker_cleanup_scratch_identity="$(worker_stat_identity "$scratch_dir" 2>/dev/null || true)"
    if [ -n "${worker_scratch_dir_identity:-}" ] \
        && [ "$worker_cleanup_scratch_identity" = "$worker_scratch_dir_identity" ] \
        && [ ! -L "$scratch_dir" ]; then
        rmdir "$scratch_dir" 2>/dev/null || true
    fi
}
trap cleanup EXIT HUP INT TERM

{
    printf '%s\n\n' '# Role'
    printf '%s\n' "You are the $actor execution worker for a task already planned by the parent Sol agent."
    printf '%s\n' 'Perform only the concrete task below. Do not redesign the task or expand its scope.'
    printf '%s\n' 'Do not invoke or spawn another agent, including another worker or reviewer/tester.'
    printf '%s\n' 'Do not stage changes, commit, or push.'
    printf '%s\n' 'Do not use destructive git commands such as reset, checkout, restore, clean, or stash, and do not otherwise discard existing changes made by the user or other agents.'
    printf '%s\n' 'Normal read-only git inspection, such as status, diff, and log, is allowed.'
    printf '%s\n' 'If the instructions, required judgment, or permissions are insufficient, stop and report the exact blocker to Sol.'
    printf '%s\n\n' 'Do not claim acceptance or PASS; Sol verifies every requirement from the actual files, diff, and command output.'
    printf '%s\n' '# Execution identity and canonical report schema'
    printf '%s\n' "Expected actor: $actor"
    printf '%s\n' "Expected model: $model"
    printf '%s\n' "Expected effort: $effort"
    printf '%s\n' 'Use the following fields exactly in the completion report (one field per line or clearly labeled section):'
    printf '%s\n' 'ACTOR: luna|terra|sol'
    printf '%s\n' 'ACTUAL_MODEL: observed model name (must match Expected model)'
    printf '%s\n' 'ACTUAL_EFFORT: high|max (must match Expected effort)'
    printf '%s\n' 'STATUS: completed|blocked|failed'
    printf '%s\n' 'CHANGED_FILES: measured repository-relative paths only; use NO_OP_JUSTIFIED with a reason when none'
    printf '%s\n' 'OBSERVED_RESULTS: commands run and observed output/results'
    printf '%s\n' 'BLOCKERS: none or exact blocker'
    printf '%s\n' 'ESCALATION_REASON: none unless Sol supplied an explicit measured escalation reason'
    printf '%s\n' 'The runner validates this raw report as untrusted input before publication. Report the expected actor/model/effort exactly, but do not treat these self-reported fields as measured identity; the runner-owned .provenance.tsv sidecar is authoritative for canonical identity and attempt metadata.'
    printf '%s\n' 'This report is factual handoff only: it is not Sol acceptance and is not a reviewer/tester PASS.'
    printf '%s\n' 'Task-scoped static checks, type checks, builds, code generation, or focused checks are allowed when required by task.md; independent tester verdict remains separate.'
    printf '%s\n\n' 'Do not run an unrelated full test suite unless task.md explicitly authorizes it.'
    printf '%s\n' '# Task'
    cat "$task_file"
    printf '%s\n\n' '# Acceptance criteria'
    cat "$requirements_file"
    printf '%s\n' '# Completion report'
    printf '%s\n' 'Report changed files, commands run, observed results, and blockers. Your report is not the acceptance decision; the parent Sol agent verifies every criterion independently.'
} > "$prompt_file"

# Treat Codex's report as untrusted input.  The report may contain multiline
# values (notably CHANGED_FILES and OBSERVED_RESULTS), so a field starts at a
# line labelled `FIELD:` and continues until the next known field.  Every
# canonical field must occur exactly once, have a non-empty value, and match
# the runner's selected actor/model/effort where applicable.  Only a report
# that passes this check may be linked into the final raw-output slot.
worker_validate_raw_output() {
    worker_report_path="$1"
    worker_expected_actor="$2"
    worker_expected_model="$3"
    worker_expected_effort="$4"

    [ -f "$worker_report_path" ] && [ ! -L "$worker_report_path" ] || {
        printf 'ERROR: temporary worker report is not a regular non-symlink file: %s\n' \
            "$worker_report_path" >&2
        return 1
    }
    worker_secure_path_identity "$worker_report_path" 'temporary worker report' >/dev/null || return 1

    awk -v expected_actor="$worker_expected_actor" \
        -v expected_model="$worker_expected_model" \
        -v expected_effort="$worker_expected_effort" '
        function trim(value) {
            sub(/^[[:space:]]+/, "", value)
            sub(/[[:space:]]+$/, "", value)
            return value
        }
        function append_value(field, value) {
            value = trim(value)
            if (value == "") {
                return
            }
            if (values[field] == "") {
                values[field] = value
            } else {
                values[field] = values[field] " " value
            }
        }
        BEGIN {
            field_count = 8
            fields[1] = "ACTOR"
            fields[2] = "ACTUAL_MODEL"
            fields[3] = "ACTUAL_EFFORT"
            fields[4] = "STATUS"
            fields[5] = "CHANGED_FILES"
            fields[6] = "OBSERVED_RESULTS"
            fields[7] = "BLOCKERS"
            fields[8] = "ESCALATION_REASON"
            current = ""
            valid = 1
        }
        {
            line = $0
            matched = 0
            for (field_index = 1; field_index <= field_count; field_index++) {
                field = fields[field_index]
                prefix = "^[[:space:]]*" field ":[[:space:]]*"
                if (line ~ prefix) {
                    matched = 1
                    if (seen[field]++) {
                        printf "ERROR: duplicate report field: %s\n", field > "/dev/stderr"
                        valid = 0
                    }
                    value = line
                    sub(prefix, "", value)
                    values[field] = trim(value)
                    current = field
                    break
                }
            }
            if (!matched && current != "") {
                append_value(current, line)
            }
        }
        END {
            for (field_index = 1; field_index <= field_count; field_index++) {
                field = fields[field_index]
                if (!seen[field]) {
                    printf "ERROR: missing report field: %s\n", field > "/dev/stderr"
                    valid = 0
                } else if (trim(values[field]) == "") {
                    printf "ERROR: empty report field: %s\n", field > "/dev/stderr"
                    valid = 0
                }
            }
            if (seen["ACTOR"] == 1 && values["ACTOR"] != expected_actor) {
                printf "ERROR: report ACTOR does not match runner actor\n" > "/dev/stderr"
                valid = 0
            }
            if (seen["ACTUAL_MODEL"] == 1 && values["ACTUAL_MODEL"] != expected_model) {
                printf "ERROR: report ACTUAL_MODEL does not match runner model\n" > "/dev/stderr"
                valid = 0
            }
            if (seen["ACTUAL_EFFORT"] == 1 && values["ACTUAL_EFFORT"] != expected_effort) {
                printf "ERROR: report ACTUAL_EFFORT does not match runner effort\n" > "/dev/stderr"
                valid = 0
            }
            if (seen["STATUS"] == 1 && values["STATUS"] !~ /^(completed|blocked|failed)$/) {
                printf "ERROR: report STATUS has an invalid enum value\n" > "/dev/stderr"
                valid = 0
            }
            exit(valid ? 0 : 1)
        }
    ' "$worker_report_path"
}

# BSD date lacks %N, while GNU date may provide it.  Use a high-resolution
# standard Perl module when that format is unavailable so a fast failed invocation is
# not recorded as a fabricated zero-duration attempt.
worker_epoch_millis() {
    worker_millis=$(date '+%s%3N' 2>/dev/null || true)
    case "$worker_millis" in *[!0-9]*|'')
        worker_millis=$(perl -MTime::HiRes=time -e 'printf "%.0f\n", time() * 1000' 2>/dev/null) || return 1
        ;;
    esac
    case "$worker_millis" in *[!0-9]*|'') return 1 ;; esac
    printf '%s\n' "$worker_millis"
}

# Pre-create an exclusive, same-filesystem output file.  Codex writes only to
# this temporary path; publication below uses a no-replace hard link so a
# raced final file or symlink can never be overwritten.
codex_output="$(mktemp "$output_dir_physical/.worker-result.XXXXXX")" || {
    printf 'ERROR: could not create temporary worker output in %s\n' "$output_dir_physical" >&2
    exit 1
}

# This is intentionally the last operation before invoking Codex.  The CLI
# accepts path strings rather than directory/file descriptors, so same-UID
# host-process TOCTOU is not claimed to be completely preventable; detectable
# boundary changes are nevertheless rejected before and after the invocation.
if ! worker_validate_boundary_state 'pre-codex'; then
    printf '%s\n' 'ERROR: pre-codex boundary validation failed' >&2
    exit 1
fi

worker_codex_status=0
worker_provenance_started_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null)" || {
    printf '%s\n' 'ERROR: could not create worker start timestamp' >&2
    exit 1
}
worker_provenance_started_ms="$(worker_epoch_millis)" || {
    printf '%s\n' 'ERROR: could not measure worker start time' >&2
    exit 1
}
"$codex_bin" exec \
    --json \
    -m "$model" \
    -c "model_reasoning_effort=\"$effort\"" \
    -s workspace-write \
    -C "$cwd_physical" \
    --add-dir "$codex_dir_physical" \
    -o "$codex_output" \
    - < "$prompt_file" || worker_codex_status=$?
worker_provenance_ended_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null)" || {
    printf '%s\n' 'ERROR: could not create worker end timestamp' >&2
    exit 1
}
worker_provenance_ended_ms="$(worker_epoch_millis)" || {
    printf '%s\n' 'ERROR: could not measure worker end time' >&2
    exit 1
}
worker_provenance_duration_ms=$((worker_provenance_ended_ms - worker_provenance_started_ms))
[ "$worker_provenance_duration_ms" -ge 0 ] || {
    printf '%s\n' 'ERROR: worker clock moved backwards while measuring attempt duration' >&2
    exit 1
}

# Always run the post-check, including when Codex exits non-zero.  A failed
# check is fail-closed and takes precedence over Codex's own exit status.
if ! worker_validate_boundary_state 'post-codex'; then
    printf '%s\n' 'ERROR: post-codex boundary validation failed (race/tampering)' >&2
    exit 1
fi

# Always create one runner-owned attempt record after the post-codex check,
# including a non-zero Codex exit or an invalid report.  A provenance sidecar
# is audit metadata, not a worker self-report, and is authoritative for the
# selected actor/model/effort.
worker_provenance_validation_status="codex_failed"
if [ "$worker_codex_status" -eq 0 ]; then
    if worker_validate_raw_output "$codex_output" "$actor" "$model" "$effort"; then
        worker_provenance_validation_status="validated"
    else
        worker_provenance_validation_status="raw_invalid"
    fi
else
    if [ ! -e "$codex_output" ] && [ ! -L "$codex_output" ]; then
        worker_provenance_validation_status="codex_failed_no_output"
    fi
fi

provenance_output="$(mktemp "$output_dir_physical/.worker-provenance.XXXXXX")" || {
    printf 'ERROR: could not create temporary provenance sidecar in %s\n' \
        "$output_dir_physical" >&2
    exit 1
}
[ -f "$provenance_output" ] && [ ! -L "$provenance_output" ] || {
    printf 'ERROR: temporary provenance sidecar is not a regular file: %s\n' \
        "$provenance_output" >&2
    exit 1
}
worker_secure_path_identity "$provenance_output" 'temporary provenance sidecar' >/dev/null || exit 1
{
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        'started_at_utc' 'ended_at_utc' 'duration_ms' 'actor' 'model' 'effort' 'codex_exit' 'validation_status'
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$worker_provenance_started_at" "$worker_provenance_ended_at" "$worker_provenance_duration_ms" "$actor" "$model" "$effort" \
        "$worker_codex_status" "$worker_provenance_validation_status"
} > "$provenance_output"

# Re-check immediately before either no-replace publication.  This covers all
# captured directory components and both final slots, including the sidecar.
if ! worker_validate_boundary_state 'pre-publish'; then
    printf '%s\n' 'ERROR: pre-publish boundary validation failed (race/tampering)' >&2
    exit 1
fi

if ln "$provenance_output" "$provenance_file_physical"; then
    worker_publish_parent_identity="$(worker_stat_identity "$output_dir_physical" 2>/dev/null || true)"
    if [ "$worker_publish_parent_identity" = "$worker_output_parent_identity" ] \
        && [ -f "$provenance_output" ] && [ ! -L "$provenance_output" ]; then
        rm -f "$provenance_output" 2>/dev/null || true
    fi
    provenance_output=""
else
    printf 'ERROR: provenance sidecar publication collided with an existing path: %s\n' \
        "$provenance_file_physical" >&2
    exit 1
fi

if [ "$worker_codex_status" -ne 0 ]; then
    exit "$worker_codex_status"
fi

if [ "$worker_provenance_validation_status" != "validated" ]; then
    printf '%s\n' 'ERROR: worker report failed canonical validation; raw report was not published' >&2
    exit 1
fi

if ln "$codex_output" "$output_file_physical"; then
    worker_publish_parent_identity="$(worker_stat_identity "$output_dir_physical" 2>/dev/null || true)"
    if [ "$worker_publish_parent_identity" = "$worker_output_parent_identity" ] \
        && [ -f "$codex_output" ] && [ ! -L "$codex_output" ]; then
        rm -f "$codex_output" 2>/dev/null || true
    fi
    codex_output=""
else
    printf 'ERROR: worker output publication collided with an existing path: %s\n' "$output_file_physical" >&2
    exit 1
fi
