#!/bin/sh

set -eu

DOT_DIRECTORY="${HOME}/dotfiles"
cd "$DOT_DIRECTORY"

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
for claude_file in settings.json .mcp.json CLAUDE.md; do
    if [ -f "$DOT_DIRECTORY/.claude/$claude_file" ]; then
        ln -snfv "$DOT_DIRECTORY/.claude/$claude_file" "$HOME/.claude/$claude_file"
    fi
done
for claude_dir in agents skills; do
    if [ -d "$DOT_DIRECTORY/.claude/$claude_dir" ]; then
        ln -snfv "$DOT_DIRECTORY/.claude/$claude_dir" "$HOME/.claude/$claude_dir"
    fi
done
echo 'Deploy dotfiles completed.'
