#!/bin/sh

SCRIPT_DIR=`dirname $0`
OS=`uname`

case "${OS}" in
    Darwin)
        ;;
    Linux)
        git clone git://github.com/sigurdga/gnome-terminal-colors-solarized.git
        cd gnome-terminal-colors-solarized
        ./install.sh
        cd $SCRIPT_DIR
        ./install/apt/install.sh
        mv $HOME/.linuxbrew $HOME/dotfiles/.linuxbrew
        ;;
esac

mv "$HOME/.enhancd" "$HOME/dotfiles/.enhancd" 2>/dev/null || true
mv "$HOME/.cache" "$HOME/dotfiles/.cache" 2>/dev/null || true

# Make setup non-destructive: avoid removing the entire ~/.config
# If ~/.config exists and is not a symlink, back it up once with a timestamp
if [ -e "$HOME/.config" ] && [ ! -L "$HOME/.config" ]; then
    backup_dir="$HOME/.config.backup.$(date +%Y%m%d%H%M%S)"
    echo "Backing up ~/.config to ${backup_dir}"
    mv "$HOME/.config" "$backup_dir"
fi

# If this repo provides a ~/.config directory, link it when no link exists
if [ -d "$HOME/dotfiles/.config" ] && [ ! -L "$HOME/.config" ]; then
    ln -s "$HOME/dotfiles/.config" "$HOME/.config"
fi

sh "$HOME/.config/nvim/init.sh"
