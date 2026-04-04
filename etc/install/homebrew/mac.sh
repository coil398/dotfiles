#!/bin/bash

echo 'Installing homebrew'
xcode-select --install 2>/dev/null || true
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
