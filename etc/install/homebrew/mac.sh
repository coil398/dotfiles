#!/bin/sh

set -eu
echo 'Installing Homebrew (official script)'
xcode-select --install || true
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
