#!/bin/sh

set -eu

is_windows() {
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
        *) return 1 ;;
    esac
}

if is_windows; then
    HOME="$(cygpath -u "$USERPROFILE")"
fi

DOT_DIRECTORY="${HOME}/dotfiles"
cd "$DOT_DIRECTORY"

link_file() {
    src="$1"
    dest="$2"
    if is_windows; then
        rm -f "$dest"
        # New-Item -ItemType SymbolicLink (WinPS 5.1) requires elevation even with
        # Developer Mode ON. MSYS native ln -s honors the unprivileged-create flag,
        # so it works non-elevated. Directories still use Junction (link_dir).
        MSYS=winsymlinks:nativestrict ln -s "$src" "$dest"
        echo "'$dest' -> '$src'"
    else
        ln -snfv "$src" "$dest"
    fi
}

link_dir() {
    src="$1"
    dest="$2"
    if is_windows; then
        rm -rf "$dest"
        powershell.exe -NoProfile -Command "New-Item -ItemType Junction -Path '$(cygpath -w "$dest")' -Target '$(cygpath -w "$src")'" > /dev/null
        echo "'$dest' -> '$src'"
    else
        ln -snfv "$src" "$dest"
    fi
}

for f in .??*; do
    [ "$f" = ".git" ] && continue
    [ "$f" = ".gitignore" ] && continue
    [ "$f" = ".DS_Store" ] && continue
    [ "$f" = ".claude" ] && continue
    [ "$f" = ".codex" ] && continue
    [ "$f" = ".cursor" ] && continue
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

if command -v jq >/dev/null 2>&1; then
    bash "$DOT_DIRECTORY/etc/sync-codex.sh" || echo "[link.sh] warn: sync-codex.sh failed (non-fatal)"
else
    echo "[link.sh] info: jq not found, skipping Codex sync"
fi

mkdir -p "$HOME/.codex" "$HOME/.codex/skills"
for codex_file in config.toml AGENTS.md format.md pir-handoff.md user-feedback-protocol.md agent-delegation.md pir2-protocol.md dev-server.md subagent-permissions.md; do
    if [ -f "$DOT_DIRECTORY/.codex/$codex_file" ]; then
        link_file "$DOT_DIRECTORY/.codex/$codex_file" "$HOME/.codex/$codex_file"
    fi
done
if [ -d "$DOT_DIRECTORY/.codex/agents" ]; then
    link_dir "$DOT_DIRECTORY/.codex/agents" "$HOME/.codex/agents"
fi
if [ -d "$DOT_DIRECTORY/.codex/skills" ]; then
    for codex_skill in "$DOT_DIRECTORY"/.codex/skills/*; do
        [ -d "$codex_skill" ] || continue
        link_dir "$codex_skill" "$HOME/.codex/skills/$(basename "$codex_skill")"
    done
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
if command -v jq >/dev/null 2>&1; then
    bash "$DOT_DIRECTORY/etc/sync-opencode.sh" || echo "[link.sh] warn: sync-opencode.sh failed (non-fatal)"
else
    echo "[link.sh] info: jq not found, skipping OpenCode sync"
fi

# Cursor sync (SSOT: dotfiles → dotfiles/.cursor/ generated + link to ~/.cursor/)
if command -v jq >/dev/null 2>&1; then
    bash "$DOT_DIRECTORY/etc/sync-cursor.sh" || echo "[link.sh] warn: sync-cursor.sh failed (non-fatal)"
else
    echo "[link.sh] info: jq not found, skipping Cursor sync"
fi

# Cursor: never replace a real file/dir (protect user state / skills-cursor).
# Only create or refresh symlinks that already point at (or will point at) dotfiles.
# Exception: skills are materialized as real directories (Cursor does not discover
# symlinked ~/.cursor/skills/* — forum #149693). SSOT remains dotfiles/.cursor/skills.
link_cursor_file() {
    src="$1"
    dest="$2"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        if [ ! -L "$dest" ]; then
            echo "[link.sh] warn: refusing to replace non-symlink $dest (Cursor)"
            return 0
        fi
    fi
    link_file "$src" "$dest"
}

link_cursor_dir() {
    src="$1"
    dest="$2"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        if [ ! -L "$dest" ]; then
            echo "[link.sh] warn: refusing to replace non-symlink dir $dest (Cursor)"
            return 0
        fi
    fi
    link_dir "$src" "$dest"
}

# Materialize one skill dir into ~/.cursor/skills/<name> as a real directory.
# Replaces prior symlink or stale copy. Never touches skills-cursor.
materialize_cursor_skill() {
    src="$1"
    dest="$2"
    name="$(basename "$src")"
    if [ "$name" = "skills-cursor" ]; then
        echo "[link.sh] warn: refusing to materialize skills-cursor"
        return 0
    fi
    if [ ! -d "$src" ]; then
        echo "[link.sh] warn: missing skill src $src"
        return 0
    fi
    mkdir -p "$(dirname "$dest")"
    # Drop symlink or previous tree so rsync/cp always lands a real dir.
    if [ -L "$dest" ] || [ -e "$dest" ]; then
        rm -rf "$dest"
    fi
    mkdir -p "$dest"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete "$src"/ "$dest"/
    else
        # portable fallback: wipe already done; copy contents
        cp -a "$src"/. "$dest"/
    fi
    # Ensure SKILL.md is world-readable enough for Cursor indexing (overlay often 600).
    if [ -f "$dest/SKILL.md" ]; then
        chmod a+r "$dest/SKILL.md" 2>/dev/null || true
    fi
    echo "[link.sh] materialized '$dest' from '$src'"
}

mkdir -p "$HOME/.cursor"
if [ -d "$DOT_DIRECTORY/.cursor/agents" ]; then
    link_cursor_dir "$DOT_DIRECTORY/.cursor/agents" "$HOME/.cursor/agents"
fi
if [ -d "$DOT_DIRECTORY/.cursor/skills" ]; then
    mkdir -p "$HOME/.cursor/skills"
    for cursor_skill in "$DOT_DIRECTORY"/.cursor/skills/*; do
        [ -d "$cursor_skill" ] || continue
        materialize_cursor_skill "$cursor_skill" "$HOME/.cursor/skills/$(basename "$cursor_skill")"
    done
fi
if [ -d "$DOT_DIRECTORY/.cursor/rules" ]; then
    mkdir -p "$HOME/.cursor/rules"
    for cursor_rule in "$DOT_DIRECTORY"/.cursor/rules/*; do
        [ -f "$cursor_rule" ] || continue
        link_cursor_file "$cursor_rule" "$HOME/.cursor/rules/$(basename "$cursor_rule")"
    done
fi
if [ -f "$DOT_DIRECTORY/.cursor/mcp.json" ]; then
    link_cursor_file "$DOT_DIRECTORY/.cursor/mcp.json" "$HOME/.cursor/mcp.json"
fi

echo 'Deploy dotfiles completed.'
