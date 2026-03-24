#!/bin/sh

set -eu

DOT_DIRECTORY="${HOME}/dotfiles"
cd "$DOT_DIRECTORY"

is_windows() {
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
        *) return 1 ;;
    esac
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
    ln -snfv "$DOT_DIRECTORY/$f" "$HOME/$f"
done

ln -snfv "$DOT_DIRECTORY/.tmux/.tmux.conf" "$HOME/.tmux.conf"
if [ "$(uname)" = "Darwin" ]; then
    ln -snfv "$DOT_DIRECTORY/.tmux/.tmux.conf.mac" "$HOME/.tmux.conf.mac"
fi

mkdir -p "$HOME/.claude"
for claude_file in settings.json .mcp.json CLAUDE.md statusline-command.sh; do
    if [ -f "$DOT_DIRECTORY/.claude/$claude_file" ]; then
        ln -snfv "$DOT_DIRECTORY/.claude/$claude_file" "$HOME/.claude/$claude_file"
    fi
done
for claude_dir in agents skills; do
    if [ -d "$DOT_DIRECTORY/.claude/$claude_dir" ]; then
        link_dir "$DOT_DIRECTORY/.claude/$claude_dir" "$HOME/.claude/$claude_dir"
    fi
done
echo 'Deploy dotfiles completed.'
