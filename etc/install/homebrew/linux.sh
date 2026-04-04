#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"
. '../../util.sh'

echo 'Installing prerequisites and Homebrew for Linux'

if has 'sudo'; then
    sudo apt-get update -q
    sudo apt-get install -y -q --no-install-recommends \
        build-essential procps curl file git zsh
else
    apt-get update -q
    apt-get install -y -q --no-install-recommends \
        build-essential procps curl file git zsh
fi

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
