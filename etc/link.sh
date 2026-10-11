#!/bin/sh

set -eu

if [ "${LINK_SH_LIB_ONLY:-0}" = 1 ]; then
    LINK_MODE=library
else
    case "${1:-}" in
        "") LINK_MODE=all ;;
        # Deploy only the Codex, Cursor, and shared skill trees.
        --codex-cursor-only) LINK_MODE=codex-cursor-only ;;
        # Canonical deployment entry for the AI runtime-owned trees only.
        --ai-runtimes-only) LINK_MODE=ai-runtimes-only ;;
        # Deploy only shared global instructions and the affected runtime entry files.
        --global-instructions-only) LINK_MODE=global-instructions-only ;;
        *) echo "Usage: $0 [--codex-cursor-only|--ai-runtimes-only|--global-instructions-only]" >&2; exit 2 ;;
    esac
fi

is_windows() {
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
        *) return 1 ;;
    esac
}

if is_windows; then
    HOME="$(cygpath -u "$USERPROFILE")"
fi

# Normally the repo lives at ~/dotfiles. In environments where it is checked
# out elsewhere (e.g. Claude Code on the web clones it under /home/user/dotfiles
# while HOME=/root), fall back to the repo root derived from this script's own
# physical location so the deploy still targets the right source tree.
DOT_DIRECTORY="${DOTFILES_DIR:-${HOME}/dotfiles}"
[ -d "$DOT_DIRECTORY" ] || DOT_DIRECTORY=$(cd -P "$(dirname "$0")/.." && pwd)
cd "$DOT_DIRECTORY"

# Git Bash's POSIX view does not expose every native Windows link form. Keep
# PowerShell path literals single-quoted and double embedded apostrophes.
windows_path_literal() {
    windows_local_path="$(cygpath -w "$1" 2>/dev/null)" || return 1
    [ -n "$windows_local_path" ] || return 1
    printf '%s' "$windows_local_path" | sed "s/'/''/g"
}

has_windows_tools() {
    is_windows && command -v powershell.exe >/dev/null 2>&1 && command -v cygpath >/dev/null 2>&1
}

windows_private_backup_acl() {
    windows_private_path="$(windows_path_literal "$1")" || return 1
    powershell.exe -NoProfile -NonInteractive -Command \
        "\$item=Get-Item -LiteralPath '$windows_private_path' -Force -EA Stop; if(\$item.LinkType -eq 'SymbolicLink' -or \$item.LinkType -eq 'Junction'){exit 1}; \$acl=([System.IO.DirectoryInfo]::new('$windows_private_path')).GetAccessControl(); if(\$acl.AreAccessRulesProtected -ne \$true){exit 1}; \$current_sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value; \$owner_sid=\$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value; \$allowed=@('S-1-5-18','S-1-5-32-544',\$current_sid); if(\$allowed -notcontains \$owner_sid){exit 1}; \$current_full=\$false; foreach(\$rule in \$acl.GetAccessRules(\$true,\$true,[System.Security.Principal.SecurityIdentifier])){ if(\$rule.IsInherited){exit 1}; if(\$rule.AccessControlType -eq 'Deny'){continue}; if(\$rule.AccessControlType -ne 'Allow'){exit 1}; try{\$sid=\$rule.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value}catch{exit 1}; if(\$allowed -notcontains \$sid){exit 1}; if(\$sid -eq \$current_sid -and ((\$rule.FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -eq [System.Security.AccessControl.FileSystemRights]::FullControl)){\$current_full=\$true} }; if(\$current_full){exit 0}; exit 1" \
        >/dev/null 2>&1
}

windows_initialize_private_backup_acl() {
    windows_private_path="$(windows_path_literal "$1")" || return 1
    powershell.exe -NoProfile -NonInteractive -Command \
        "\$item=Get-Item -LiteralPath '$windows_private_path' -Force -EA Stop; if(\$item.LinkType -eq 'SymbolicLink' -or \$item.LinkType -eq 'Junction'){exit 1}; \$acl=[System.Security.AccessControl.DirectorySecurity]::new(); \$acl.SetAccessRuleProtection(\$true,\$false); \$current=[System.Security.Principal.WindowsIdentity]::GetCurrent().User; \$inherit=[System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [System.Security.AccessControl.InheritanceFlags]::ObjectInherit; \$propagation=[System.Security.AccessControl.PropagationFlags]::None; \$rights=[System.Security.AccessControl.FileSystemRights]::FullControl; \$type=[System.Security.AccessControl.AccessControlType]::Allow; foreach(\$sid in @([System.Security.Principal.SecurityIdentifier]::new('S-1-5-18'),[System.Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'),\$current)){ \$rule=[System.Security.AccessControl.FileSystemAccessRule]::new(\$sid,\$rights,\$inherit,\$propagation,\$type); \$acl.AddAccessRule(\$rule) }; ([System.IO.DirectoryInfo]::new('$windows_private_path')).SetAccessControl(\$acl)" \
        >/dev/null 2>&1
}

windows_is_link() {
    windows_local_path="$(windows_path_literal "$1")" || return 1
    powershell.exe -NoProfile -NonInteractive -Command \
        "\$i=Get-Item -LiteralPath '$windows_local_path' -Force -EA SilentlyContinue; if(\$i -and (\$i.LinkType -eq 'SymbolicLink' -or \$i.LinkType -eq 'Junction')){exit 0}; exit 1" \
        >/dev/null 2>&1
}

is_link() {
    # Git Bash recognises ordinary native symlinks. Fall back to PowerShell for
    # Junctions and other Windows reparse-point forms it cannot inspect.
    [ -L "$1" ] && return 0
    if has_windows_tools; then
        windows_is_link "$1"
        return $?
    fi
    return 1
}

windows_link_matches() {
    windows_target_path="$(windows_path_literal "$1")" || return 1
    windows_source_path="$(windows_path_literal "$2")" || return 1
    powershell.exe -NoProfile -NonInteractive -Command \
        "\$d=Get-Item -LiteralPath '$windows_target_path' -Force -EA SilentlyContinue; \$s=Get-Item -LiteralPath '$windows_source_path' -Force -EA SilentlyContinue; if(\$null -eq \$d -or \$null -eq \$s){exit 1}; if(\$d.LinkType -ne 'SymbolicLink' -and \$d.LinkType -ne 'Junction'){exit 1}; \$t=Get-Item -LiteralPath ([string]@(\$d.Target)[0]) -Force -EA SilentlyContinue; if(\$t -and \$t.FullName -eq \$s.FullName){exit 0}; exit 1" \
        >/dev/null 2>&1
}

target_exists() {
    if [ -e "$1" ] || [ -L "$1" ]; then
        return 0
    fi
    if has_windows_tools; then
        windows_local_path="$(windows_path_literal "$1")" || return 1
        powershell.exe -NoProfile -NonInteractive -Command \
            "if(Get-Item -LiteralPath '$windows_local_path' -Force -EA SilentlyContinue){exit 0}; exit 1" \
            >/dev/null 2>&1
        return $?
    fi
    return 1
}

target_matches() {
    target_path="$1"
    source_path="$2"
    target_exists "$target_path" || return 1
    is_link "$target_path" || return 1
    # Prefer Git Bash's inode/path resolution. Windows-only link forms fall
    # through to the PowerShell comparison.
    [ "$target_path" -ef "$source_path" ] && return 0
    if has_windows_tools; then
        windows_link_matches "$target_path" "$source_path"
        return $?
    fi
    return 1
}

link_backup_root() {
    printf '%s' "${DOTFILES_BACKUP_DIR:-${HOME}/.local/state/dotfiles/link-backups}"
}

ensure_private_backup_root() {
    private_root="$1"
    if [ -L "$private_root" ]; then
        echo "[link.sh] error: refusing symlink private backup directory: $private_root" >&2
        return 1
    fi
    if [ -e "$private_root" ]; then
        if [ ! -d "$private_root" ]; then
            echo "[link.sh] error: private backup path is not a directory: $private_root" >&2
            return 1
        fi
        if is_windows; then
            if ! has_windows_tools || ! windows_private_backup_acl "$private_root"; then
                echo "[link.sh] error: refusing non-private backup directory (Windows ACL): $private_root" >&2
                return 1
            fi
        else
            # macOS may resolve stat to GNU coreutils, so pick the format by stat flavor.
            private_mode="$(stat -c '%a' "$private_root" 2>/dev/null || stat -f '%Lp' "$private_root" 2>/dev/null || true)"
            case "$private_mode" in
                700|0700) ;;
                *)
                    echo "[link.sh] error: refusing non-private backup directory (mode ${private_mode:-unknown}): $private_root" >&2
                    return 1
                    ;;
            esac
        fi
        return 0
    fi
    (umask 077; mkdir -p "$private_root") || {
        echo "[link.sh] error: failed to create private backup directory: $private_root" >&2
        return 1
    }
    if is_windows; then
        if ! has_windows_tools || ! windows_initialize_private_backup_acl "$private_root" || ! windows_private_backup_acl "$private_root"; then
            echo "[link.sh] error: created backup directory is not private (Windows ACL): $private_root" >&2
            return 1
        fi
    fi
    return 0
}

backup_existing_target() {
    backup_target="$1"
    backup_root="$(link_backup_root)"

    # The root and each transaction directory are private. The old target is
    # moved, rather than copied, so directories and dangling links are retained
    # exactly and no destructive remove is needed before replacement.
    ensure_private_backup_root "$backup_root" || return 1

    backup_dir="$(mktemp -d "$backup_root/.link-backup.XXXXXX")" || {
        echo "[link.sh] error: failed to allocate private backup directory: $backup_root" >&2
        return 1
    }
    backup_path="$backup_dir/$(basename "$backup_target")"
    if ! mv "$backup_target" "$backup_path"; then
        rmdir "$backup_dir" 2>/dev/null || true
        echo "[link.sh] error: failed to preserve existing target: $backup_target" >&2
        return 1
    fi

    DOTFILES_LAST_BACKUP_PATH="$backup_path"
    echo "[link.sh] preserved existing target '$backup_target' at '$backup_path'" >&2
    return 0
}

restore_existing_target() {
    restore_path="$1"
    restore_target="$2"
    if [ ! -e "$restore_path" ] && [ ! -L "$restore_path" ]; then
        echo "[link.sh] error: private backup is missing: $restore_path" >&2
        return 1
    fi
    if target_exists "$restore_target"; then
        echo "[link.sh] error: cannot restore backup because target appeared: $restore_target" >&2
        return 1
    fi
    if ! mv "$restore_path" "$restore_target"; then
        echo "[link.sh] error: failed to restore existing target: $restore_target (backup: $restore_path)" >&2
        return 1
    fi
    rmdir "$(dirname "$restore_path")" 2>/dev/null || true
    return 0
}

remove_link() {
    remove_target="$1"
    if has_windows_tools; then
        windows_local_path="$(windows_path_literal "$remove_target")" || return 1
        powershell.exe -NoProfile -NonInteractive -Command \
            "Remove-Item -LiteralPath '$windows_local_path' -Force -EA Stop" \
            >/dev/null 2>&1
    else
        rm -f "$remove_target"
    fi
}

remove_link_if_points_to_source() {
    remove_source="$1"
    remove_target="$2"
    [ -L "$remove_target" ] || return 0

    remove_raw="$(readlink "$remove_target" 2>/dev/null)" || return 0
    case "$remove_raw" in
        /*) remove_candidate="$remove_raw" ;;
        *) remove_candidate="$(dirname "$remove_target")/$remove_raw" ;;
    esac
    remove_source_parent="$(CDPATH= cd -P "$(dirname "$remove_source")" 2>/dev/null && pwd -P)" || return 0
    remove_candidate_parent="$(CDPATH= cd -P "$(dirname "$remove_candidate")" 2>/dev/null && pwd -P)" || return 0
    remove_source="$remove_source_parent/$(basename "$remove_source")"
    remove_candidate="$remove_candidate_parent/$(basename "$remove_candidate")"
    [ "$remove_candidate" = "$remove_source" ] || return 0

    if ! remove_link "$remove_target"; then
        echo "[link.sh] error: failed to remove obsolete managed link: $remove_target" >&2
        return 1
    fi
    echo "[link.sh] removed obsolete managed link '$remove_target'"
}

create_file_link() {
    create_source="$1"
    create_target="$2"
    if is_windows; then
        # New-Item -ItemType SymbolicLink (WinPS 5.1) requires elevation even
        # with Developer Mode ON. MSYS native ln -s honors the unprivileged
        # create flag, so it works non-elevated. Directories use Junction.
        MSYS=winsymlinks:nativestrict ln -s "$create_source" "$create_target"
    else
        ln -s "$create_source" "$create_target"
    fi
}

create_dir_link() {
    create_source="$1"
    create_target="$2"
    if is_windows; then
        if ! has_windows_tools; then
            echo "[link.sh] error: PowerShell/cygpath are required for Windows directory links" >&2
            return 1
        fi
        create_target_path="$(windows_path_literal "$create_target")" || return 1
        create_source_path="$(windows_path_literal "$create_source")" || return 1
        powershell.exe -NoProfile -NonInteractive -Command \
            "New-Item -ItemType Junction -Path '$create_target_path' -Target '$create_source_path' -EA Stop | Out-Null" \
            >/dev/null 2>&1
    else
        ln -s "$create_source" "$create_target"
    fi
}

deploy_link() {
    deploy_source="$1"
    deploy_target="$2"
    deploy_kind="$3"
    deploy_label="$4"
    deploy_backup=""

    if ! target_exists "$deploy_source"; then
        echo "[link.sh] error: managed source is missing: $deploy_source ($deploy_label)" >&2
        return 1
    fi
    if target_matches "$deploy_target" "$deploy_source"; then
        echo "[link.sh] unchanged '$deploy_target' -> '$deploy_source'"
        return 0
    fi

    deploy_parent="$(dirname "$deploy_target")"
    if ! mkdir -p "$deploy_parent"; then
        echo "[link.sh] error: failed to create destination directory: $deploy_parent" >&2
        return 1
    fi

    if target_exists "$deploy_target"; then
        if ! backup_existing_target "$deploy_target"; then
            return 1
        fi
        deploy_backup="$DOTFILES_LAST_BACKUP_PATH"
    fi

    deploy_create_status=0
    if [ "$deploy_kind" = file ]; then
        create_file_link "$deploy_source" "$deploy_target" || deploy_create_status=$?
    else
        create_dir_link "$deploy_source" "$deploy_target" || deploy_create_status=$?
    fi

    if [ "$deploy_create_status" -ne 0 ] || ! target_matches "$deploy_target" "$deploy_source"; then
        # Only remove a link created by this transaction. Unexpected foreign
        # content that appeared concurrently is left untouched for safety.
        if target_matches "$deploy_target" "$deploy_source"; then
            remove_link "$deploy_target" || true
        fi
        if [ -n "$deploy_backup" ]; then
            if restore_existing_target "$deploy_backup" "$deploy_target"; then
                echo "[link.sh] restored existing target after failed deployment: $deploy_target" >&2
            else
                echo "[link.sh] error: existing target remains in private backup: $deploy_backup" >&2
            fi
        fi
        echo "[link.sh] error: failed to deploy link: $deploy_target -> $deploy_source ($deploy_label)" >&2
        return 1
    fi

    echo "'$deploy_target' -> '$deploy_source'"
    return 0
}

link_file() {
    link_file_source="$1"
    link_file_target="$2"
    deploy_link "$link_file_source" "$link_file_target" file file
}

link_dir() {
    link_dir_source="$1"
    link_dir_target="$2"

    if ! target_exists "$link_dir_source" || [ ! -d "$link_dir_source" ]; then
        echo "[link.sh] error: managed directory source is missing: $link_dir_source" >&2
        return 1
    fi

    if target_exists "$link_dir_target" && [ "$link_dir_target" -ef "$link_dir_source" ]; then
        return 0
    fi

    if ! is_windows && [ -d "$link_dir_target" ] && [ ! -L "$link_dir_target" ]; then
        # `ln -snf src dir` creates dir/basename(src) instead of replacing a
        # real directory. Preserve the environment-owned directory on macOS
        # and Unix rather than nesting a link or clobbering its contents.
        echo "[link.sh] warn: '$link_dir_target' is a real directory; skipping symlink to '$link_dir_source' (would nest/clobber)"
        return 0
    fi

    deploy_link "$link_dir_source" "$link_dir_target" dir dir
}

ensure_real_directory() {
    real_target="$1"
    real_backup=""

    if target_exists "$real_target"; then
        if [ -d "$real_target" ] && ! is_link "$real_target"; then
            return 0
        fi
        if ! backup_existing_target "$real_target"; then
            return 1
        fi
        real_backup="$DOTFILES_LAST_BACKUP_PATH"
    fi

    if ! mkdir -p "$real_target"; then
        if [ -n "$real_backup" ]; then
            restore_existing_target "$real_backup" "$real_target" || true
        fi
        echo "[link.sh] error: failed to create real directory: $real_target" >&2
        return 1
    fi
    if [ -L "$real_target" ] || [ ! -d "$real_target" ]; then
        if [ -n "$real_backup" ]; then
            rmdir "$real_target" 2>/dev/null || true
            restore_existing_target "$real_backup" "$real_target" || true
        fi
        echo "[link.sh] error: expected a real directory: $real_target" >&2
        return 1
    fi
    return 0
}

# Cursor: never replace a real file/dir (protect user state / skills-cursor).
# Only create or refresh symlinks that already point at (or will point at) dotfiles.
# Exception: skills are materialized as real directories (Cursor does not discover
# symlinked ~/.cursor/skills/*). SSOT remains dotfiles/.cursor/skills.
link_cursor_file() {
    cursor_file_source="$1"
    cursor_file_target="$2"
    if target_exists "$cursor_file_target" && ! is_link "$cursor_file_target"; then
        echo "[link.sh] warn: refusing to replace non-symlink $cursor_file_target (Cursor)"
        return 0
    fi
    link_file "$cursor_file_source" "$cursor_file_target"
}

link_cursor_dir() {
    cursor_dir_source="$1"
    cursor_dir_target="$2"
    if target_exists "$cursor_dir_target" && ! is_link "$cursor_dir_target"; then
        echo "[link.sh] warn: refusing to replace non-symlink dir $cursor_dir_target (Cursor)"
        return 0
    fi
    link_dir "$cursor_dir_source" "$cursor_dir_target"
}

cursor_tree_matches() {
    cursor_tree_source="$1"
    cursor_tree_target="$2"
    [ -d "$cursor_tree_target" ] || return 1
    is_link "$cursor_tree_target" && return 1
    diff -qr "$cursor_tree_source" "$cursor_tree_target" >/dev/null 2>&1
}

# Materialize one skill dir into ~/.cursor/skills/<name> as a real directory.
# Existing trees are moved to a private backup before replacement. An exact
# content match is left alone so repeated deployments do not create backups.
materialize_cursor_skill() {
    materialize_source="$1"
    materialize_target="$2"
    materialize_name="$(basename "$materialize_source")"
    materialize_backup=""

    if [ "$materialize_name" = "skills-cursor" ]; then
        echo "[link.sh] warn: refusing to materialize skills-cursor"
        return 0
    fi
    if [ ! -d "$materialize_source" ]; then
        echo "[link.sh] warn: missing skill src $materialize_source"
        return 0
    fi
    if cursor_tree_matches "$materialize_source" "$materialize_target"; then
        if [ -f "$materialize_target/SKILL.md" ]; then
            chmod a+r "$materialize_target/SKILL.md" 2>/dev/null || true
        fi
        echo "[link.sh] unchanged materialized '$materialize_target'"
        return 0
    fi

    materialize_parent="$(dirname "$materialize_target")"
    if ! mkdir -p "$materialize_parent"; then
        echo "[link.sh] error: failed to create Cursor skill directory: $materialize_parent" >&2
        return 1
    fi
    if target_exists "$materialize_target"; then
        if ! backup_existing_target "$materialize_target"; then
            return 1
        fi
        materialize_backup="$DOTFILES_LAST_BACKUP_PATH"
    fi

    materialize_stage="$(mktemp -d "${materialize_target}.tmp.XXXXXX")" || {
        if [ -n "$materialize_backup" ]; then
            restore_existing_target "$materialize_backup" "$materialize_target" || true
        fi
        echo "[link.sh] error: failed to allocate Cursor skill staging directory: $materialize_target" >&2
        return 1
    }

    materialize_copy_status=0
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete "$materialize_source"/ "$materialize_stage"/ || materialize_copy_status=$?
    else
        cp -a "$materialize_source"/. "$materialize_stage"/ || materialize_copy_status=$?
    fi
    if [ "$materialize_copy_status" -ne 0 ]; then
        rm -rf "$materialize_stage"
        if [ -n "$materialize_backup" ]; then
            restore_existing_target "$materialize_backup" "$materialize_target" || true
        fi
        echo "[link.sh] error: failed to materialize Cursor skill: $materialize_target" >&2
        return 1
    fi

    if [ -f "$materialize_stage/SKILL.md" ]; then
        chmod a+r "$materialize_stage/SKILL.md" 2>/dev/null || true
    fi
    if ! mv "$materialize_stage" "$materialize_target"; then
        rm -rf "$materialize_stage"
        if [ -n "$materialize_backup" ]; then
            restore_existing_target "$materialize_backup" "$materialize_target" || true
        fi
        echo "[link.sh] error: failed to replace Cursor skill: $materialize_target" >&2
        return 1
    fi

    echo "[link.sh] materialized '$materialize_target' from '$materialize_source'"
    return 0
}

# Copy one managed file and preserve any prior target through the same private
# backup mechanism used by links. WSL-owned Windows rules and CODEX_HOME AGENTS
# must be ordinary files so their Windows-native readers do not follow WSL paths.
materialize_managed_file() {
    local materialize_source="$1"
    local materialize_target="$2"
    local materialize_label="${3:-managed file}"
    local materialize_backup=""
    local materialize_parent materialize_stage

    if [ ! -f "$materialize_source" ]; then
        echo "[link.sh] error: $materialize_label source is missing: $materialize_source" >&2
        return 1
    fi
    if [ -f "$materialize_target" ] && [ ! -L "$materialize_target" ] \
        && cmp -s "$materialize_source" "$materialize_target"; then
        echo "[link.sh] unchanged copied $materialize_label '$materialize_target'"
        return 0
    fi

    materialize_parent="$(dirname "$materialize_target")"
    if ! mkdir -p "$materialize_parent"; then
        echo "[link.sh] error: failed to create $materialize_label directory: $materialize_parent" >&2
        return 1
    fi
    if target_exists "$materialize_target"; then
        if ! backup_existing_target "$materialize_target"; then
            return 1
        fi
        materialize_backup="$DOTFILES_LAST_BACKUP_PATH"
    fi

    materialize_stage="$(mktemp "${materialize_target}.tmp.XXXXXX")" || {
        if [ -n "$materialize_backup" ]; then
            restore_existing_target "$materialize_backup" "$materialize_target" || true
        fi
        echo "[link.sh] error: failed to allocate $materialize_label staging file: $materialize_target" >&2
        return 1
    }
    if ! cp -p "$materialize_source" "$materialize_stage"; then
        rm -f "$materialize_stage"
        if [ -n "$materialize_backup" ]; then
            restore_existing_target "$materialize_backup" "$materialize_target" || true
        fi
        echo "[link.sh] error: failed to copy $materialize_label: $materialize_target" >&2
        return 1
    fi
    if ! mv -f "$materialize_stage" "$materialize_target"; then
        rm -f "$materialize_stage"
        if [ -n "$materialize_backup" ]; then
            restore_existing_target "$materialize_backup" "$materialize_target" || true
        fi
        echo "[link.sh] error: failed to publish $materialize_label: $materialize_target" >&2
        return 1
    fi
    echo "[link.sh] copied $materialize_label '$materialize_target' from '$materialize_source'"
    return 0
}

# Deploy already acquired private sources only; acquisition belongs to bootstrap.
# Keep adapters outside the public checkout and reuse the backup-aware installer.
deploy_private_skills() (
    private_source="${PRIVATE_SKILLS_DIR:-$(dirname "$DOT_DIRECTORY")/private-skills}"
    if [ ! -d "$private_source/skills" ]; then
        echo "[link.sh] private skills unavailable: $private_source (public deployment continues)"
        return 0
    fi
    private_stage="$(mktemp -d "${TMPDIR:-/tmp}/private-skills.XXXXXX")" || return 1
    trap 'rm -rf "$private_stage"' EXIT HUP INT TERM
    python3 - "$private_source/skills" "$private_stage" "$DOT_DIRECTORY" "$@" <<'PY_PRIVATE' || return 1
from pathlib import Path
import re
import shutil
import sys
source, stage, public = map(Path, sys.argv[1:4])
public = public.resolve()
for target in [stage, *map(Path, sys.argv[4:])]:
    resolved = target.resolve()
    if resolved == public or public in resolved.parents:
        raise ValueError(f'private deployment target resolves into public checkout: {target}')
for skill in sorted(source.iterdir()):
    if not skill.is_dir() or not (skill / 'SKILL.md').is_file():
        continue
    name = 'private-' + skill.name
    dest = stage / name
    shutil.copytree(skill, dest)
    path = dest / 'SKILL.md'
    body = path.read_bytes()
    # Limit metadata editing to the leading frontmatter, never the body.
    header = re.match(rb'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)', body, re.S)
    if header is None:
        raise ValueError(f'missing frontmatter: {skill.name}')
    metadata = header.group(1)
    names = re.findall(rb'(?m)^name:[ \t]*([^\r\n]*)', metadata)
    if len(names) != 1 or names[0].strip().strip(b'\"\'') != skill.name.encode():
        raise ValueError(f'frontmatter name does not match folder: {skill.name}')
    metadata = re.sub(rb'(?m)^name:[^\r\n]*', ('name: ' + name).encode(), metadata, count=1)
    body = body[:header.start(1)] + metadata + body[header.end(1):]
    path.write_bytes(body)
PY_PRIVATE
    for private_target in "$@"; do
        for private_skill in "$private_stage"/*; do
            [ -d "$private_skill" ] || continue
            materialize_cursor_skill "$private_skill" "$private_target/$(basename "$private_skill")" || return 1
        done
    done
)

deploy_codex_runtime() {
    if ! bash "$DOT_DIRECTORY/etc/sync-codex.sh"; then
        echo "[link.sh] error: sync-codex.sh failed; refusing to continue Codex deployment" >&2
        return 1
    fi

    if ! bash "$DOT_DIRECTORY/etc/link-codex-runtime.sh" --write; then
        echo "[link.sh] error: Codex runtime link deployment failed" >&2
        return 1
    fi
    deploy_private_skills "$HOME/.codex/skills" || return 1
    if [ -n "${CODEX_HOME:-}" ] && [ "$CODEX_HOME" != "$HOME/.codex" ]; then
        deploy_private_skills "$CODEX_HOME/skills" || return 1
        python3 "$DOT_DIRECTORY/jev-hooks/codex-hook.py" --install-codex-hook "$CODEX_HOME" || return 1
    fi
}

deploy_cursor_runtime() {
    if ! bash "$DOT_DIRECTORY/etc/sync-cursor.sh"; then
        echo "[link.sh] error: sync-cursor.sh failed; refusing to continue Cursor deployment" >&2
        return 1
    fi

    if ! mkdir -p "$HOME/.cursor"; then
        echo "[link.sh] error: failed to create Cursor directory: $HOME/.cursor" >&2
        return 1
    fi
    if [ -d "$DOT_DIRECTORY/.cursor/agents" ]; then
        if ! link_cursor_dir "$DOT_DIRECTORY/.cursor/agents" "$HOME/.cursor/agents"; then
            echo "[link.sh] error: Cursor agents deployment failed" >&2
            return 1
        fi
    fi
    if [ -d "$DOT_DIRECTORY/.cursor/skills" ]; then
        if ! mkdir -p "$HOME/.cursor/skills"; then
            echo "[link.sh] error: failed to create Cursor skills directory: $HOME/.cursor/skills" >&2
            return 1
        fi
        for cursor_skill in "$DOT_DIRECTORY"/.cursor/skills/*; do
            [ -d "$cursor_skill" ] || continue
            if ! materialize_cursor_skill "$cursor_skill" "$HOME/.cursor/skills/$(basename "$cursor_skill")"; then
                echo "[link.sh] error: Cursor skill deployment failed: $cursor_skill" >&2
                return 1
            fi
        done
    fi
    if [ -d "$DOT_DIRECTORY/.cursor/rules" ]; then
        if ! mkdir -p "$HOME/.cursor/rules"; then
            echo "[link.sh] error: failed to create Cursor rules directory: $HOME/.cursor/rules" >&2
            return 1
        fi
        for cursor_rule in "$DOT_DIRECTORY"/.cursor/rules/*; do
            [ -f "$cursor_rule" ] || continue
            if ! link_cursor_file "$cursor_rule" "$HOME/.cursor/rules/$(basename "$cursor_rule")"; then
                echo "[link.sh] error: Cursor rule deployment failed: $cursor_rule" >&2
                return 1
            fi
        done
    fi
    if is_wsl; then
        windows_profile="$(windows_userprofile_path)" || {
            echo "[link.sh] error: cannot resolve Windows UserProfile for Cursor rules" >&2
            return 1
        }
        if ! deploy_windows_cursor_rules "$windows_profile"; then
            echo "[link.sh] error: Windows Cursor rules deployment failed" >&2
            return 1
        fi
    fi
    if [ -f "$DOT_DIRECTORY/.cursor/mcp.json" ]; then
        if ! link_cursor_file "$DOT_DIRECTORY/.cursor/mcp.json" "$HOME/.cursor/mcp.json"; then
            echo "[link.sh] error: Cursor MCP deployment failed" >&2
            return 1
        fi
    fi
    deploy_private_skills "$HOME/.cursor/skills" || return 1
    return 0
}

is_wsl() {
    [ -n "${WSL_DISTRO_NAME:-}" ] && return 0
    [ -r /proc/sys/kernel/osrelease ] && grep -qi 'microsoft' /proc/sys/kernel/osrelease
}

windows_userprofile_path() {
    local win_profile
    if [ -n "${WINDOWS_USERPROFILE:-}" ]; then
        win_profile="$WINDOWS_USERPROFILE"
    elif [ -n "${USERPROFILE:-}" ]; then
        win_profile="$USERPROFILE"
    elif command -v powershell.exe >/dev/null 2>&1; then
        win_profile="$(powershell.exe -NoProfile -NonInteractive -Command '[Environment]::GetFolderPath("UserProfile")' 2>/dev/null | tr -d '\r')" || return 1
    else
        return 1
    fi

    case "$win_profile" in
        /*) printf '%s' "$win_profile" ;;
        *)
            if command -v cygpath >/dev/null 2>&1; then
                cygpath -u "$win_profile"
            elif command -v wslpath >/dev/null 2>&1; then
                wslpath -u "$win_profile"
            else
                return 1
            fi
            ;;
    esac
}

deploy_windows_cursor_rules() {
    local windows_profile="$1" windows_rules rule
    windows_rules="$windows_profile/.cursor/rules"
    if ! mkdir -p "$windows_rules"; then
        echo "[link.sh] error: failed to create Windows Cursor rules directory: $windows_rules" >&2
        return 1
    fi
    for rule in shared-agents.mdc skill-procedure.mdc; do
        if [ ! -f "$DOT_DIRECTORY/.cursor/rules/$rule" ]; then
            echo "[link.sh] error: managed Cursor rule is missing: $DOT_DIRECTORY/.cursor/rules/$rule" >&2
            return 1
        fi
        if ! materialize_managed_file "$DOT_DIRECTORY/.cursor/rules/$rule" "$windows_rules/$rule" "Windows Cursor rule"; then
            return 1
        fi
    done
}

deploy_windows_claude_instructions() {
    local windows_profile="$1" windows_claude_dir windows_agents_dir
    windows_claude_dir="$windows_profile/.claude"
    windows_agents_dir="$windows_profile/.agents"
    if ! mkdir -p "$windows_claude_dir" "$windows_agents_dir"; then
        echo "[link.sh] error: failed to create Windows Claude instruction directories under: $windows_profile" >&2
        return 1
    fi
    if ! materialize_managed_file "$DOT_DIRECTORY/.claude/CLAUDE.md" "$windows_claude_dir/CLAUDE.md" "Windows Claude global entry"; then
        return 1
    fi
    if ! materialize_managed_file "$DOT_DIRECTORY/.agents/global-instructions.md" "$windows_agents_dir/AGENTS.md" "Windows shared global instructions"; then
        return 1
    fi
    if ! deploy_windows_shared_skills "$windows_profile"; then
        echo "[link.sh] error: Windows shared skills deployment failed" >&2
        return 1
    fi
}

deploy_windows_shared_skills() {
    local windows_profile="$1" windows_skills_dir package source
    windows_skills_dir="$windows_profile/.agents/skills"
    if ! mkdir -p "$windows_skills_dir"; then
        echo "[link.sh] error: failed to create Windows shared skills directory: $windows_skills_dir" >&2
        return 1
    fi

    # Install the complete packages directly named by the common instructions
    # or Windows Claude entry. Copy each package so its referenced files remain
    # reachable; leave profile-only skill packages untouched.
    for package in pir2 reviewer code-review-guidance instruction-refactor ai-ltm field-notes research codex; do
        source="$DOT_DIRECTORY/.agents/skills/$package"
        if [ ! -f "$source/SKILL.md" ]; then
            echo "[link.sh] error: required shared skill source is missing: $source/SKILL.md" >&2
            return 1
        fi
        if ! materialize_cursor_skill "$source" "$windows_skills_dir/$package"; then
            return 1
        fi
    done
    return 0
}

deploy_grok_runtime() {
    # Grok native rules: preserve real user files; link only owned rule entries.
    if [ -d "$DOT_DIRECTORY/.grok/rules" ]; then
        grok_rules_ready=true
        grok_setup_failed=false
        for grok_parent in "$HOME/.grok" "$HOME/.grok/rules"; do
            if [ -e "$grok_parent" ] || [ -L "$grok_parent" ]; then
                if [ ! -d "$grok_parent" ] || [ -L "$grok_parent" ]; then
                    echo "[link.sh] warn: preserving non-directory or symlink Grok root $grok_parent"
                    grok_rules_ready=false
                    break
                fi
            else
                if ! (umask 077; mkdir "$grok_parent"); then
                    grok_rules_ready=false
                    grok_setup_failed=true
                    break
                fi
            fi
        done
        if [ "$grok_rules_ready" = true ]; then
            for grok_rule in "$DOT_DIRECTORY"/.grok/rules/*.md; do
                [ -f "$grok_rule" ] || continue
                grok_dest="$HOME/.grok/rules/$(basename "$grok_rule")"
                if target_matches "$grok_dest" "$grok_rule"; then
                    continue
                fi
                if target_exists "$grok_dest"; then
                    echo "[link.sh] warn: preserving existing Grok rule $grok_dest"
                    continue
                fi
                if ! ln -s "$grok_rule" "$grok_dest"; then
                    echo "[link.sh] error: failed to deploy Grok rule: $grok_dest" >&2
                    return 1
                fi
            done
        elif [ "$grok_setup_failed" = true ]; then
            echo "[link.sh] error: failed to prepare Grok rules directory" >&2
            return 1
        fi
    fi
    if ! python3 "$DOT_DIRECTORY/jev-hooks/install.py" grok; then
        echo "[link.sh] error: Grok Jev hooks deployment failed" >&2
        return 1
    fi
    if ! python3 "$DOT_DIRECTORY/etc/install-session-sync-hook.py" grok; then
        echo "[link.sh] error: Grok session-sync hook deployment failed" >&2
        return 1
    fi
    return 0
}

deploy_shared_runtime() {
    shared_agents_dir="$HOME/.agents"
    if ! ensure_real_directory "$shared_agents_dir"; then
        echo "[link.sh] error: failed to prepare shared agents directory: $shared_agents_dir" >&2
        return 1
    fi
    if ! link_file "$DOT_DIRECTORY/.agents/global-instructions.md" "$shared_agents_dir/AGENTS.md"; then
        echo "[link.sh] error: shared global instructions deployment failed" >&2
        return 1
    fi
    if [ -d "$DOT_DIRECTORY/.agents/skills" ]; then
        if ! link_dir "$DOT_DIRECTORY/.agents/skills" "$shared_agents_dir/skills"; then
            echo "[link.sh] error: shared skills deployment failed" >&2
            return 1
        fi
    fi
    return 0
}

deploy_grok_global_rule() {
    local source="$DOT_DIRECTORY/.grok/rules/runtime.md"
    local target="$HOME/.grok/rules/runtime.md"
    [ -f "$source" ] || {
        echo "[link.sh] error: Grok global rule is missing: $source" >&2
        return 1
    }
    link_file "$source" "$target"
}

deploy_global_instructions() {
    local common_source="$DOT_DIRECTORY/.agents/global-instructions.md"
    local codex_runtime_dir="${CODEX_HOME:-$HOME/.codex}"
    local cursor_rules_dir="$HOME/.cursor/rules"
    local rule windows_profile devin_config_dir dsh_home

    [ -f "$common_source" ] || {
        echo "[link.sh] error: shared global instructions are missing: $common_source" >&2
        return 1
    }

    if ! deploy_shared_runtime; then
        return 1
    fi
    if ! mkdir -p "$HOME/.claude" || ! link_file "$DOT_DIRECTORY/.claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"; then
        echo "[link.sh] error: Claude global entry deployment failed" >&2
        return 1
    fi
    if ! remove_link_if_points_to_source "$DOT_DIRECTORY/.claude/format.md" "$HOME/.claude/format.md"; then
        return 1
    fi

    if ! bash "$DOT_DIRECTORY/etc/sync-codex.sh"; then
        echo "[link.sh] error: sync-codex.sh failed; refusing to deploy global instructions" >&2
        return 1
    fi
    if is_windows && [ -n "${CODEX_HOME:-}" ] && command -v cygpath >/dev/null 2>&1; then
        codex_runtime_dir="$(cygpath -u "$CODEX_HOME" 2>/dev/null || printf '%s' "$CODEX_HOME")"
    fi
    codex_agents_target="$codex_runtime_dir/AGENTS.md"
    if is_wsl && [ -n "${CODEX_HOME:-}" ] && [ "$CODEX_HOME" != "$HOME/.codex" ]; then
        if ! materialize_managed_file "$DOT_DIRECTORY/.codex/AGENTS.md" "$codex_agents_target" "Codex global instructions"; then
            echo "[link.sh] error: Codex global instructions deployment failed" >&2
            return 1
        fi
    elif ! link_file "$DOT_DIRECTORY/.codex/AGENTS.md" "$codex_agents_target"; then
        echo "[link.sh] error: Codex global instructions deployment failed" >&2
        return 1
    fi
    if ! CODEX_HOME="$codex_runtime_dir" bash "$DOT_DIRECTORY/etc/link-codex-runtime.sh" --write-file AGENTS.md; then
        echo "[link.sh] error: Codex global instructions are not in the runtime allowlist" >&2
        return 1
    fi

    if ! bash "$DOT_DIRECTORY/etc/sync-cursor.sh"; then
        echo "[link.sh] error: sync-cursor.sh failed; refusing to deploy global instructions" >&2
        return 1
    fi
    if ! mkdir -p "$cursor_rules_dir"; then
        echo "[link.sh] error: failed to create Cursor rules directory: $cursor_rules_dir" >&2
        return 1
    fi
    for rule in shared-agents.mdc skill-procedure.mdc; do
        if ! link_file "$DOT_DIRECTORY/.cursor/rules/$rule" "$cursor_rules_dir/$rule"; then
            echo "[link.sh] error: Cursor rule deployment failed: $rule" >&2
            return 1
        fi
    done
    if is_wsl; then
        windows_profile="$(windows_userprofile_path)" || {
            echo "[link.sh] error: cannot resolve Windows UserProfile for Cursor rules" >&2
            return 1
        }
        if ! deploy_windows_cursor_rules "$windows_profile"; then
            return 1
        fi
        if ! deploy_windows_claude_instructions "$windows_profile"; then
            echo "[link.sh] error: Windows Claude global instructions deployment failed" >&2
            return 1
        fi
    fi

    if ! bash "$DOT_DIRECTORY/etc/sync-opencode.sh" --agents-only; then
        echo "[link.sh] error: OpenCode global instructions generation failed" >&2
        return 1
    fi

    if ! bash "$DOT_DIRECTORY/etc/sync-antigravity.sh"; then
        echo "[link.sh] error: sync-antigravity.sh failed; refusing to deploy global instructions" >&2
        return 1
    fi
    if ! link_file "$DOT_DIRECTORY/.gemini/config/rules/shared-agents.md" "$HOME/.gemini/config/rules/shared-agents.md"; then
        echo "[link.sh] error: Antigravity global instructions deployment failed" >&2
        return 1
    fi

    if ! deploy_grok_global_rule; then
        return 1
    fi

    devin_config_dir="$HOME/.config/devin"
    if is_windows && command -v cygpath >/dev/null 2>&1 && [ -n "${APPDATA:-}" ]; then
        devin_config_dir="$(cygpath -u "$APPDATA")/devin"
    fi
    if ! link_file "$common_source" "$devin_config_dir/AGENTS.md"; then
        echo "[link.sh] error: Devin global instructions deployment failed" >&2
        return 1
    fi

    dsh_home="${DSH_HOME:-$HOME/.dsh}"
    if ! link_file "$common_source" "$dsh_home/AGENTS.md"; then
        echo "[link.sh] error: DeepSeek Harness global instructions deployment failed" >&2
        return 1
    fi
}

deploy_devin_runtime() {
    if ! bash "$DOT_DIRECTORY/etc/sync-devin.sh"; then
        echo "[link.sh] error: sync-devin.sh failed; refusing to continue Devin deployment" >&2
        return 1
    fi

    # Devin reads ~/.config/devin/AGENTS.md (%APPDATA%\devin\AGENTS.md on
    # Windows) as global rules; point it at the shared SSOT.
    devin_config_dir="$HOME/.config/devin"
    if is_windows && command -v cygpath >/dev/null 2>&1 && [ -n "${APPDATA:-}" ]; then
        devin_config_dir="$(cygpath -u "$APPDATA")/devin"
    fi
    if ! link_file "$DOT_DIRECTORY/.agents/global-instructions.md" "$devin_config_dir/AGENTS.md"; then
        echo "[link.sh] error: Devin AGENTS.md deployment failed" >&2
        return 1
    fi
    return 0
}

deploy_dsh_runtime() {
    # DeepSeek Harness reads $DSH_HOME/AGENTS.md (default ~/.dsh/AGENTS.md) as
    # its user-global instruction file; point it at the shared SSOT.
    dsh_home="${DSH_HOME:-}"
    if [ -z "$dsh_home" ]; then
        dsh_home="$HOME/.dsh"
    fi
    if ! mkdir -p "$dsh_home"; then
        echo "[link.sh] error: failed to create DeepSeek Harness home: $dsh_home" >&2
        return 1
    fi
    if ! link_file "$DOT_DIRECTORY/.agents/global-instructions.md" "$dsh_home/AGENTS.md"; then
        echo "[link.sh] error: DeepSeek Harness AGENTS.md deployment failed" >&2
        return 1
    fi
    return 0
}

deploy_gemini_runtime() {
    if ! bash "$DOT_DIRECTORY/etc/sync-antigravity.sh"; then
        echo "[link.sh] error: sync-antigravity.sh failed; refusing to continue Gemini deployment" >&2
        return 1
    fi

    if ! mkdir -p "$HOME/.gemini/config"; then
        echo "[link.sh] error: failed to create Gemini config directory: $HOME/.gemini/config" >&2
        return 1
    fi
    if [ -d "$DOT_DIRECTORY/.gemini/config/rules" ]; then
        if ! mkdir -p "$HOME/.gemini/config/rules"; then
            echo "[link.sh] error: failed to create Gemini rules directory: $HOME/.gemini/config/rules" >&2
            return 1
        fi
        for gemini_rule in "$DOT_DIRECTORY"/.gemini/config/rules/*; do
            [ -f "$gemini_rule" ] || continue
            if ! link_file "$gemini_rule" "$HOME/.gemini/config/rules/$(basename "$gemini_rule")"; then
                echo "[link.sh] error: Gemini rule deployment failed: $gemini_rule" >&2
                return 1
            fi
        done
    fi
    if [ -f "$DOT_DIRECTORY/.gemini/config/mcp_config.json" ]; then
        if ! link_file "$DOT_DIRECTORY/.gemini/config/mcp_config.json" "$HOME/.gemini/config/mcp_config.json"; then
            echo "[link.sh] error: Gemini MCP deployment failed" >&2
            return 1
        fi
    fi
    if [ -f "$DOT_DIRECTORY/.gemini/config/hooks.json" ]; then
        if ! link_file "$DOT_DIRECTORY/.gemini/config/hooks.json" "$HOME/.gemini/config/hooks.json"; then
            echo "[link.sh] error: Gemini hooks deployment failed" >&2
            return 1
        fi
    fi
    if [ -d "$DOT_DIRECTORY/.gemini/config/scripts" ]; then
        if ! link_dir "$DOT_DIRECTORY/.gemini/config/scripts" "$HOME/.gemini/config/scripts"; then
            echo "[link.sh] error: Gemini scripts deployment failed" >&2
            return 1
        fi
    fi
    if [ -d "$HOME/.agents/skills" ]; then
        if ! link_dir "$HOME/.agents/skills" "$HOME/.gemini/config/skills"; then
            echo "[link.sh] error: Gemini shared skills deployment failed" >&2
            return 1
        fi
    fi
    return 0
}

deploy_ai_runtimes() {
    if ! deploy_codex_runtime; then
        return 1
    fi
    if ! deploy_cursor_runtime; then
        return 1
    fi
    if ! deploy_grok_runtime; then
        return 1
    fi
    if ! deploy_shared_runtime; then
        return 1
    fi
    if ! deploy_gemini_runtime; then
        return 1
    fi
    if ! deploy_devin_runtime; then
        return 1
    fi
    if ! deploy_dsh_runtime; then
        return 1
    fi
    return 0
}

if [ "${LINK_SH_LIB_ONLY:-0}" = 1 ]; then
    # `return` succeeds when this file is sourced by a fixture test; the
    # fallback exits when someone invokes the script directly in library mode.
    return 0 2>/dev/null || exit 0
fi

if [ "$LINK_MODE" = ai-runtimes-only ]; then
    if ! deploy_ai_runtimes; then
        echo "[link.sh] error: AI runtime deployment failed" >&2
        exit 1
    fi
    echo "Deploy AI runtimes completed."
    exit 0
fi

if [ "$LINK_MODE" = global-instructions-only ]; then
    if ! deploy_global_instructions; then
        echo "[link.sh] error: global instructions deployment failed" >&2
        exit 1
    fi
    echo "Deploy global instructions completed."
    exit 0
fi

if [ "$LINK_MODE" = codex-cursor-only ]; then
    if ! deploy_codex_runtime; then
        echo "[link.sh] error: Codex runtime deployment failed" >&2
        exit 1
    fi
    if ! deploy_cursor_runtime; then
        echo "[link.sh] error: Cursor runtime deployment failed" >&2
        exit 1
    fi
    if ! deploy_shared_runtime; then
        echo "[link.sh] error: shared runtime deployment failed" >&2
        exit 1
    fi
    echo "Deploy Codex/Cursor runtimes completed."
    exit 0
fi

for f in .??*; do
    [ "$f" = ".git" ] && continue
    [ "$f" = ".gitignore" ] && continue
    [ "$f" = ".DS_Store" ] && continue
    [ "$f" = ".claude" ] && continue
    [ "$f" = ".codex" ] && continue
    [ "$f" = ".cursor" ] && continue
    [ "$f" = ".grok" ] && continue
    [ "$f" = ".gemini" ] && continue
    [ "$f" = ".mcp.json" ] && continue
    [ "$f" = ".opencode" ] && continue
    [ "$f" = ".github" ] && continue
    [ "$f" = ".devcontainer" ] && continue
    [ "$f" = ".gitattributes" ] && continue
    if [ -d "$DOT_DIRECTORY/$f" ]; then
        link_dir "$DOT_DIRECTORY/$f" "$HOME/$f"
    else
        link_file "$DOT_DIRECTORY/$f" "$HOME/$f"
    fi
done

link_file "$DOT_DIRECTORY/.tmux/.tmux.conf" "$HOME/.tmux.conf"
if [ "$(uname)" = "Darwin" ]; then
    link_file "$DOT_DIRECTORY/.tmux/.tmux.conf.mac" "$HOME/.tmux.conf.mac"
fi

mkdir -p "$HOME/.claude"
for claude_file in settings.json CLAUDE.md user-feedback-protocol.md dev-server.md subagent-permissions.md; do
    if [ -f "$DOT_DIRECTORY/.claude/$claude_file" ]; then
        link_file "$DOT_DIRECTORY/.claude/$claude_file" "$HOME/.claude/$claude_file"
    fi
done
if ! remove_link_if_points_to_source "$DOT_DIRECTORY/.claude/format.md" "$HOME/.claude/format.md"; then
    echo "[link.sh] error: obsolete Claude format link cleanup failed" >&2
    exit 1
fi
for claude_dir in skills lib hooks; do
    if [ -d "$DOT_DIRECTORY/.claude/$claude_dir" ]; then
        link_dir "$DOT_DIRECTORY/.claude/$claude_dir" "$HOME/.claude/$claude_dir"
    fi
done

if ! deploy_codex_runtime; then
    echo "[link.sh] error: Codex runtime deployment failed" >&2
    exit 1
fi

# Global pre-commit hook dispatcher: ~/.githooks/pre-commit
# `.githooks/` itself is symlinked by the loop above. We only need to point
# Git at it via `core.hooksPath`. Idempotent: skip if already set.
if command -v git >/dev/null 2>&1; then
    HOOKS_PATH_TARGET="${HOME}/.githooks"
    CURRENT_HOOKS_PATH="$(git config --global --get core.hooksPath 2>/dev/null || true)"
    if [ "$CURRENT_HOOKS_PATH" != "$HOOKS_PATH_TARGET" ]; then
        git config --global core.hooksPath "$HOOKS_PATH_TARGET"
        echo "[link.sh] git config --global core.hooksPath -> $HOOKS_PATH_TARGET"
    else
        echo "[link.sh] git config --global core.hooksPath already $HOOKS_PATH_TARGET"
    fi
fi

# OpenCode sync (SSOT: dotfiles → ~/.config/opencode/)
if ! bash "$DOT_DIRECTORY/etc/sync-opencode.sh"; then
    echo "[link.sh] error: sync-opencode.sh failed; refusing to complete deployment" >&2
    exit 1
fi

if ! deploy_cursor_runtime; then
    echo "[link.sh] error: Cursor runtime deployment failed" >&2
    exit 1
fi
if ! deploy_grok_runtime; then
    echo "[link.sh] error: Grok runtime deployment failed" >&2
    exit 1
fi
if ! deploy_shared_runtime; then
    echo "[link.sh] error: shared runtime deployment failed" >&2
    exit 1
fi
if ! deploy_gemini_runtime; then
    echo "[link.sh] error: Gemini runtime deployment failed" >&2
    exit 1
fi
if ! deploy_devin_runtime; then
    echo "[link.sh] error: Devin runtime deployment failed" >&2
    exit 1
fi
if ! deploy_dsh_runtime; then
    echo "[link.sh] error: DeepSeek Harness runtime deployment failed" >&2
    exit 1
fi

echo 'Deploy dotfiles completed.'
