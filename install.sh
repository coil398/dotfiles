#!/bin/bash

set -eu

# This script is for codespaces

# Update and install necessary packages
echo "Updating and installing necessary packages"
sudo apt update
sudo apt install -y curl git
echo "Updated and installed necessary packages"

# Install neovim for the backend of vs code
echo "Installing neovim"
git clone https://github.com/neovim/neovim.git
cd neovim
make CMAKE_BUILD_TYPE=Release
sudo make install
mkdir -p ~/.config/nvim
cp /workspaces/.codespaces/.persistedshare/dotfiles/.config/nvim/init.lua ~/.config/nvim/init.lua
cp /workspaces/.codespaces/.persistedshare/dotfiles/.config/nvim/linux.vim ~/.config/nvim/linux.vim
echo "Neovim installed"
