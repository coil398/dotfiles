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
        powershell.exe -NoProfile -Command "New-Item -ItemType SymbolicLink -Path '$(cygpath -w "$dest")' -Target '$(cygpath -w "$src")' -Force" > /dev/null
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
for claude_file in settings.json .mcp.json CLAUDE.md format.md pir-handoff.md; do
    if [ -f "$DOT_DIRECTORY/.claude/$claude_file" ]; then
        link_file "$DOT_DIRECTORY/.claude/$claude_file" "$HOME/.claude/$claude_file"
    fi
done
for claude_dir in agents skills lib; do
    if [ -d "$DOT_DIRECTORY/.claude/$claude_dir" ]; then
        link_dir "$DOT_DIRECTORY/.claude/$claude_dir" "$HOME/.claude/$claude_dir"
    fi
done
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
echo 'Deploy dotfiles completed.'
