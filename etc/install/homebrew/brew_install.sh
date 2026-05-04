#!/bin/sh

brew update && brew upgrade
brew install git
brew install neovim
brew install zsh
brew install zsh-completions
brew install zplug
brew install tmux
brew install tmux-mem-cpu-load
brew install gitui
brew install ripgrep
brew install eza
brew install bat
brew install procs
brew install fd
brew install fzf
brew install zoxide
brew install direnv
brew install colordiff
brew install tig
brew install gh
brew install mise
brew install gitleaks

# macOS 専用
if [ "$(uname)" = "Darwin" ]; then
    brew install reattach-to-user-namespace
fi
