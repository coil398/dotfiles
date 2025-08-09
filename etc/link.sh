#!/bin/sh

set -eu

DOT_DIRECTORY="${HOME}/dotfiles"
cd "$DOT_DIRECTORY"

for f in .??*; do
    [ "$f" = ".git" ] && continue
    [ "$f" = ".gitignore" ] && continue
    [ "$f" = ".DS_Store" ] && continue
    ln -snfv "$DOT_DIRECTORY/$f" "$HOME/$f"
done

ln -snfv "$DOT_DIRECTORY/.tmux/.tmux.conf" "$HOME/.tmux.conf"
if [ "$(uname)" = "Darwin" ]; then
    ln -snfv "$DOT_DIRECTORY/.tmux/.tmux.conf.mac" "$HOME/.tmux.conf.mac"
fi
echo 'Deploy dotfiles completed.'
