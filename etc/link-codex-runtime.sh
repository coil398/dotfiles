#!/bin/sh
# shellcheck disable=SC1007

# Codex runtime links are owned here so every deploy path uses the same
# inventory, link validation, and non-link protection rules.
set -u

usage() {
    printf 'Usage: %s --check|--write|--check-file <name>|--write-file <name>\n' "$0" >&2
}

error() {
    printf '[link-codex-runtime] error: %s\n' "$*" >&2
}

is_windows() {
    case "$(uname -s 2>/dev/null || printf '%s' unknown)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
        *) return 1 ;;
    esac
}

has_windows_tools() {
    is_windows && command -v powershell.exe >/dev/null 2>&1 && command -v cygpath >/dev/null 2>&1
}

windows_path_literal() {
    local_path=$(cygpath -w "$1" 2>/dev/null) || return 1
    [ -n "$local_path" ] || return 1
    printf '%s' "$local_path" | sed "s/'/''/g"
}

windows_is_link() {
    local_path="$(windows_path_literal "$1")" || return 1
    [ -n "$local_path" ] || return 1
    powershell.exe -NoProfile -NonInteractive -Command \
        "\$i=Get-Item -LiteralPath '$local_path' -Force -EA SilentlyContinue; if(\$i -and (\$i.LinkType -eq 'SymbolicLink' -or \$i.LinkType -eq 'Junction')){exit 0}; exit 1" \
        >/dev/null 2>&1
}

is_link() {
    # Git Bash resolves ordinary native symlinks and Junctions here.  Avoid
    # launching PowerShell unless its POSIX view cannot recognise the link.
    [ -L "$1" ] && return 0
    if has_windows_tools; then
        windows_is_link "$1"
        return $?
    fi
    return 1
}

windows_link_matches() {
    target_path="$(windows_path_literal "$1")" || return 1
    source_path="$(windows_path_literal "$2")" || return 1
    [ -n "$target_path" ] && [ -n "$source_path" ] || return 1
    powershell.exe -NoProfile -NonInteractive -Command \
        "\$d=Get-Item -LiteralPath '$target_path' -Force -EA SilentlyContinue; \$s=Get-Item -LiteralPath '$source_path' -Force -EA SilentlyContinue; if(\$null -eq \$d -or \$null -eq \$s){exit 1}; if(\$d.LinkType -ne 'SymbolicLink' -and \$d.LinkType -ne 'Junction'){exit 1}; \$t=Get-Item -LiteralPath ([string]@(\$d.Target)[0]) -Force -EA SilentlyContinue; if(\$t -and \$t.FullName -eq \$s.FullName){exit 0}; exit 1" \
        >/dev/null 2>&1
}

target_exists() {
    if [ -e "$1" ] || [ -L "$1" ]; then
        return 0
    fi
    if has_windows_tools; then
        local_path=$(windows_path_literal "$1") || return 1
        powershell.exe -NoProfile -NonInteractive -Command \
            "if(Get-Item -LiteralPath '$local_path' -Force -EA SilentlyContinue){exit 0}; exit 1" \
            >/dev/null 2>&1
        return $?
    fi
    return 1
}

target_matches() {
    target="$1"
    source="$2"
    target_exists "$target" || return 1
    is_link "$target" || return 1
    # Prefer Git Bash's own inode/path resolution.  Windows-only link forms
    # that Git Bash cannot compare fall through to the PowerShell fallback.
    [ "$target" -ef "$source" ] && return 0
    if has_windows_tools; then
        windows_link_matches "$target" "$source"
        return $?
    fi
    return 1
}

check_target() {
    source="$1"
    target="$2"
    label="$3"

    if ! target_exists "$source"; then
        error "managed source is missing: $source"
        return 1
    fi
    if ! target_exists "$target"; then
        error "runtime target is missing: $target ($label)"
        return 1
    fi
    if ! target_matches "$target" "$source"; then
        error "runtime target is not the managed symlink or Junction: $target -> $source ($label)"
        return 1
    fi
    return 0
}

remove_link() {
    target="$1"
    if has_windows_tools; then
        target_path="$(windows_path_literal "$target")" || return 1
        powershell.exe -NoProfile -NonInteractive -Command \
            "Remove-Item -LiteralPath '$target_path' -Force -EA Stop" \
            >/dev/null 2>&1
    else
        rm -f "$target"
    fi
}

managed_skill_source() {
    target="$1"
    link_target="$(readlink "$target" 2>/dev/null || true)"
    if [ -n "$link_target" ]; then
        case "$link_target" in
            "$CODEX_SOURCE_DIR"/skills/*)
                source_path="$link_target"
                [ "$source_path" != "$CODEX_SOURCE_DIR/skills/" ] || return 1
                printf '%s' "$source_path"
                return 0
                ;;
        esac
    fi

    # Git Bash's readlink does not expose native Junction targets.  Ask
    # PowerShell for the link target even when that target no longer exists,
    # then convert it back to the POSIX path used by the rest of this script.
    if has_windows_tools; then
        target_path="$(windows_path_literal "$target")" || return 1
        link_target="$(powershell.exe -NoProfile -NonInteractive -Command \
            "\$i=Get-Item -LiteralPath '$target_path' -Force -EA SilentlyContinue; if(\$i -and (\$i.LinkType -eq 'Junction' -or \$i.LinkType -eq 'SymbolicLink')){Write-Output ([string]@(\$i.Target)[0])}" \
            2>/dev/null || true)"
        [ -n "$link_target" ] || return 1
        source_path="$(printf '%s' "$link_target" | tr -d '\r')"
        source_path="$(cygpath -u "$source_path" 2>/dev/null || true)"
        [ -n "$source_path" ] || return 1
        case "$source_path" in
            "$CODEX_SOURCE_DIR"/skills/*)
                [ "$source_path" != "$CODEX_SOURCE_DIR/skills/" ] || return 1
                printf '%s' "$source_path"
                return 0
                ;;
        esac
    fi
    return 1
}

managed_skill_source_exists() {
    source_path="$1"
    [ -d "$source_path" ] || return 1
    [ -f "$source_path/SKILL.md" ] || return 1
}

check_orphan_skill_links() {
    orphan_status=0
    target=""
    source_path=""

    [ -d "$CODEX_RUNTIME_DIR/skills" ] || return 0
    for target in "$CODEX_RUNTIME_DIR"/skills/*; do
        is_link "$target" || continue
        source_path="$(managed_skill_source "$target" 2>/dev/null || true)"
        [ -n "$source_path" ] || continue
        if ! managed_skill_source_exists "$source_path"; then
            error "orphan managed skill link: $target -> $source_path"
            orphan_status=1
        fi
    done

    return "$orphan_status"
}

cleanup_orphan_skill_links() {
    orphan_cleanup_status=0
    target=""
    source_path=""

    [ -d "$CODEX_RUNTIME_DIR/skills" ] || return 0
    for target in "$CODEX_RUNTIME_DIR"/skills/*; do
        is_link "$target" || continue
        source_path="$(managed_skill_source "$target" 2>/dev/null || true)"
        [ -n "$source_path" ] || continue
        if managed_skill_source_exists "$source_path"; then
            continue
        fi
        if remove_link "$target"; then
            printf 'CODEX_RUNTIME_ORPHAN_REMOVED: %s -> %s\n' "$target" "$source_path"
        else
            error "failed to remove orphan managed skill link: $target -> $source_path"
            orphan_cleanup_status=1
        fi
    done

    return "$orphan_cleanup_status"
}

create_file_link() {
    source="$1"
    target="$2"
    if is_windows; then
        MSYS=winsymlinks:nativestrict ln -s "$source" "$target"
    else
        ln -s "$source" "$target"
    fi
}

create_dir_link() {
    source="$1"
    target="$2"
    if has_windows_tools; then
        source_path="$(windows_path_literal "$source")" || return 1
        target_path="$(windows_path_literal "$target")" || return 1
        powershell.exe -NoProfile -NonInteractive -Command \
            "New-Item -ItemType Junction -Path '$target_path' -Target '$source_path' -EA Stop | Out-Null" \
            >/dev/null 2>&1
    else
        ln -s "$source" "$target"
    fi
}

write_target() {
    source="$1"
    target="$2"
    kind="$3"
    label="$4"

    if ! target_exists "$source"; then
        error "managed source is missing: $source"
        return 1
    fi

    if target_matches "$target" "$source"; then
        return 0
    fi

    if target_exists "$target"; then
        if ! is_link "$target"; then
            error "refusing to replace non-link runtime target: $target ($label)"
            return 1
        fi
        if ! remove_link "$target"; then
            error "failed to remove existing runtime link: $target ($label)"
            return 1
        fi
    fi

    parent="$(dirname "$target")"
    if ! mkdir -p "$parent"; then
        error "failed to create runtime parent directory: $parent"
        return 1
    fi

    if [ "$kind" = file ]; then
        if ! create_file_link "$source" "$target"; then
            error "failed to create runtime file link: $target -> $source"
            return 1
        fi
    else
        if ! create_dir_link "$source" "$target"; then
            error "failed to create runtime directory link: $target -> $source"
            return 1
        fi
    fi

    printf 'CODEX_RUNTIME_RELINKED: %s -> %s\n' "$target" "$source"
    return 0
}

check_all() {
    status=0
    source=""
    name=""
    target=""

    for name in $CODEX_ROOT_FILE_ALLOWLIST; do
        source="$CODEX_SOURCE_DIR/$name"
        [ -f "$source" ] || continue
        target="$CODEX_RUNTIME_DIR/$name"
        check_target "$source" "$target" "file" || status=1
    done

    if [ -d "$CODEX_SOURCE_DIR/agents" ]; then
        target="$CODEX_RUNTIME_DIR/agents"
        check_target "$CODEX_SOURCE_DIR/agents" "$target" "agents" || status=1
    fi

    for source in "$CODEX_SOURCE_DIR"/skills/*; do
        [ -d "$source" ] || continue
        [ -f "$source/SKILL.md" ] || continue
        name="$(basename "$source")"
        target="$CODEX_RUNTIME_DIR/skills/$name"
        check_target "$source" "$target" "skill/$name" || status=1
    done

    check_orphan_skill_links || status=1

    return "$status"
}

write_all() {
    status=0
    source=""
    name=""
    target=""

    if ! mkdir -p "$CODEX_RUNTIME_DIR" "$CODEX_RUNTIME_DIR/skills"; then
        error "failed to create Codex runtime directories under $CODEX_RUNTIME_DIR"
        return 1
    fi

    cleanup_status=0
    cleanup_orphan_skill_links || cleanup_status=$?

    for name in $CODEX_ROOT_FILE_ALLOWLIST; do
        source="$CODEX_SOURCE_DIR/$name"
        [ -f "$source" ] || continue
        target="$CODEX_RUNTIME_DIR/$name"
        write_target "$source" "$target" file "file/$name" || status=1
    done

    if [ -d "$CODEX_SOURCE_DIR/agents" ]; then
        target="$CODEX_RUNTIME_DIR/agents"
        write_target "$CODEX_SOURCE_DIR/agents" "$target" dir "agents" || status=1
    fi

    for source in "$CODEX_SOURCE_DIR"/skills/*; do
        [ -d "$source" ] || continue
        [ -f "$source/SKILL.md" ] || continue
        name="$(basename "$source")"
        target="$CODEX_RUNTIME_DIR/skills/$name"
        write_target "$source" "$target" dir "skill/$name" || status=1
    done

    [ "$cleanup_status" -eq 0 ] && [ "$status" -eq 0 ]
}

is_allowed_root_file() {
    requested="$1"
    for name in $CODEX_ROOT_FILE_ALLOWLIST; do
        [ "$name" = "$requested" ] && return 0
    done
    return 1
}

check_one_file() {
    name="$1"
    is_allowed_root_file "$name" || {
        error "root file is not allowlisted: $name"
        return 1
    }
    check_target "$CODEX_SOURCE_DIR/$name" "$CODEX_RUNTIME_DIR/$name" "file/$name"
}

write_one_file() {
    name="$1"
    is_allowed_root_file "$name" || {
        error "root file is not allowlisted: $name"
        return 1
    }
    write_target "$CODEX_SOURCE_DIR/$name" "$CODEX_RUNTIME_DIR/$name" file "file/$name"
}

first_arg="${1:-}"
case "$#:$first_arg" in
    1:--check|1:--write) mode="$1"; selected_file="" ;;
    2:--check-file|2:--write-file) mode="$1"; selected_file="$2" ;;
    *) usage; exit 2 ;;
esac

if [ -z "${HOME:-}" ]; then
    error 'HOME is not set'
    exit 1
fi

if is_windows && [ -n "${USERPROFILE:-}" ] && command -v cygpath >/dev/null 2>&1; then
    HOME="$(cygpath -u "$USERPROFILE" 2>/dev/null || printf '%s' "$HOME")"
fi

SCRIPT_DIR="$(CDPATH= cd -P "$(dirname "$0")" 2>/dev/null && pwd -P)" || {
    error "cannot resolve helper directory: $0"
    exit 1
}
DOT_DIRECTORY="$(CDPATH= cd -P "$SCRIPT_DIR/.." 2>/dev/null && pwd -P)" || {
    error "cannot resolve dotfiles directory from: $SCRIPT_DIR"
    exit 1
}
CODEX_SOURCE_DIR="$DOT_DIRECTORY/.codex"
CODEX_RUNTIME_DIR="$HOME/.codex"
CODEX_ROOT_FILE_ALLOWLIST='config.toml motitan.config.toml AGENTS.md format.md pir-handoff.md user-feedback-protocol.md agent-delegation.md pir2-protocol.md dev-server.md subagent-permissions.md'

if [ ! -d "$CODEX_SOURCE_DIR" ]; then
    error "Codex source directory is missing: $CODEX_SOURCE_DIR"
    exit 1
fi

if [ "$mode" = --check-file ]; then
    check_one_file "$selected_file"
    exit $?
fi

if [ "$mode" = --write-file ]; then
    write_status=0
    write_one_file "$selected_file" || write_status=$?
    check_status=0
    check_one_file "$selected_file" || check_status=$?
    if [ "$write_status" -ne 0 ] || [ "$check_status" -ne 0 ]; then
        exit 1
    fi
    exit 0
fi

if [ "$mode" = --check ]; then
    if check_all; then
        exit 0
    fi
    exit 1
fi

write_all || write_status=$?
write_status="${write_status:-0}"
check_status=0
check_all || check_status=$?
if [ "$write_status" -ne 0 ] || [ "$check_status" -ne 0 ]; then
    exit 1
fi
exit 0
