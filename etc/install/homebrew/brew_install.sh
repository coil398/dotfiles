brew update && brew upgrade
brew install git neovim zsh zsh-completions zplug tmux tig ripgrep go

# macOS-only tools
if [ "$(uname)" = "Darwin" ]; then
  brew install reattach-to-user-namespace osx-cpu-temp
fi

# Tags/tools (no deprecated options)
brew install global ctags pygments || true
