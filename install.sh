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
sudo apt install -y neovim
mkdir -p ~/.config/nvim
cp /workspaces/.codespaces/.persistedshare/dotfiles/.config/nvim/init.lua ~/.config/nvim/init.lua
echo "Neovim installed"
