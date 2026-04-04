#!/bin/sh

SCRIPT_DIR=$(dirname "$0")
OS=$(uname)

case "${OS}" in
    Darwin)
        ;;
    Linux)
        # デスクトップ環境向けオプションツール（失敗しても続行）
        "$SCRIPT_DIR/install/apt/install.sh" || true
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

# Neovim プラグインをヘッドレスインストール
if command -v nvim > /dev/null 2>&1; then
    nvim --headless "+Lazy! sync" +qa 2>/dev/null || true
fi
