#!/bin/sh

set -eu

if [ "${LINK_SH_LIB_ONLY:-0}" = 1 ]; then
    LINK_MODE=library
else
    case "${1:-}" in
        "") LINK_MODE=all ;;
        --codex-motitan-only) LINK_MODE=codex-motitan-only ;;
        # Canonical deployment entry for the AI runtime-owned trees only.
        --ai-runtimes-only) LINK_MODE=ai-runtimes-only ;;
        *) echo "Usage: $0 [--codex-motitan-only|--ai-runtimes-only]" >&2; exit 2 ;;
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
DOT_DIRECTORY="${HOME}/dotfiles"
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
        case "$(uname -s)" in
            Darwin) private_mode="$(stat -f '%Lp' "$private_root" 2>/dev/null || true)" ;;
            *) private_mode="$(stat -c '%a' "$private_root" 2>/dev/null || true)" ;;
        esac
        case "$private_mode" in
            700|0700) ;;
            *)
                echo "[link.sh] error: refusing non-private backup directory (mode ${private_mode:-unknown}): $private_root" >&2
                return 1
                ;;
        esac
        return 0
    fi
    (umask 077; mkdir -p "$private_root") || {
        echo "[link.sh] error: failed to create private backup directory: $private_root" >&2
        return 1
    }
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

    if ! is_windows && [ -d "$link_dir_target" ] && [ ! -L "$link_dir_target" ]; then
        # `ln -snf src dir` creates dir/basename(src) instead of replacing a
        # real directory. Preserve the environment-owned directory on macOS
        # and Unix rather than nesting a link or clobbering its contents.
        echo "[link.sh] warn: '$link_dir_target' is a real directory; skipping symlink to '$link_dir_source' (would nest/clobber)"
        return 0
    fi

    deploy_link "$link_dir_source" "$link_dir_target" dir dir
}

link_motitan_launcher() {
    launcher_source="$1"
    launcher_target="$2"
    launcher_bin_dir="$(dirname "$launcher_target")"

    if [ ! -f "$launcher_source" ]; then
        echo "[link.sh] error: motitan launcher source is missing: $launcher_source" >&2
        return 1
    fi

    if [ -e "$launcher_bin_dir" ] || [ -L "$launcher_bin_dir" ]; then
        if [ ! -d "$launcher_bin_dir" ]; then
            echo "[link.sh] error: refusing to replace non-directory $launcher_bin_dir (motitan launcher)" >&2
            return 1
        fi
    elif ! mkdir -p "$launcher_bin_dir"; then
        echo "[link.sh] error: failed to create launcher directory: $launcher_bin_dir" >&2
        return 1
    fi

    if [ -e "$launcher_target" ] || [ -L "$launcher_target" ]; then
        if [ ! -L "$launcher_target" ]; then
            echo "[link.sh] error: refusing to replace non-symlink $launcher_target (motitan launcher)" >&2
            return 1
        fi
    fi

    link_file "$launcher_source" "$launcher_target"
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

if [ "${LINK_SH_LIB_ONLY:-0}" = 1 ]; then
    # `return` succeeds when this file is sourced by a fixture test; the
    # fallback exits when someone invokes the script directly in library mode.
    return 0 2>/dev/null || exit 0
fi

if [ "$LINK_MODE" = codex-motitan-only ]; then
    if ! bash "$DOT_DIRECTORY/etc/link-codex-runtime.sh" --write-file motitan.config.toml; then
        echo "[link.sh] error: motitan profile deployment failed" >&2
        exit 1
    fi
    if ! link_motitan_launcher "$DOT_DIRECTORY/bin/codex-motitan" "$HOME/bin/codex-motitan"; then
        echo "[link.sh] error: motitan launcher deployment failed" >&2
        exit 1
    fi
    echo "Deploy codex-motitan completed."
    exit 0
fi

deploy_codex_runtime() {
    if ! bash "$DOT_DIRECTORY/etc/sync-codex.sh"; then
        echo "[link.sh] error: sync-codex.sh failed; refusing to continue Codex deployment" >&2
        return 1
    fi

    if ! bash "$DOT_DIRECTORY/etc/link-codex-runtime.sh" --write; then
        echo "[link.sh] error: Codex runtime link deployment failed" >&2
        return 1
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
    if [ -f "$DOT_DIRECTORY/.cursor/mcp.json" ]; then
        if ! link_cursor_file "$DOT_DIRECTORY/.cursor/mcp.json" "$HOME/.cursor/mcp.json"; then
            echo "[link.sh] error: Cursor MCP deployment failed" >&2
            return 1
        fi
    fi
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
    return 0
}

deploy_shared_runtime() {
    if ! mkdir -p "$HOME/.agents"; then
        echo "[link.sh] error: failed to create shared agents directory: $HOME/.agents" >&2
        return 1
    fi
    if [ -d "$DOT_DIRECTORY/.agents/skills" ]; then
        if ! link_dir "$DOT_DIRECTORY/.agents/skills" "$HOME/.agents/skills"; then
            echo "[link.sh] error: shared skills deployment failed" >&2
            return 1
        fi
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
    return 0
}

if [ "$LINK_MODE" = ai-runtimes-only ]; then
    if ! deploy_ai_runtimes; then
        echo "[link.sh] error: AI runtime deployment failed" >&2
        exit 1
    fi
    echo "Deploy AI runtimes completed."
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
    [ "$f" = ".mcp.json" ] && continue
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

if ! link_motitan_launcher "$DOT_DIRECTORY/bin/codex-motitan" "$HOME/bin/codex-motitan"; then
    echo "[link.sh] error: motitan launcher deployment failed" >&2
    exit 1
fi

mkdir -p "$HOME/.claude"
for claude_file in settings.json .mcp.json CLAUDE.md format.md pir-handoff.md user-feedback-protocol.md agent-delegation.md pir2-protocol.md dev-server.md subagent-permissions.md; do
    if [ -f "$DOT_DIRECTORY/.claude/$claude_file" ]; then
        link_file "$DOT_DIRECTORY/.claude/$claude_file" "$HOME/.claude/$claude_file"
    fi
done
for claude_dir in agents skills lib hooks; do
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

echo 'Deploy dotfiles completed.'
