#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    SUDO=""
fi

# デスクトップ環境向けのオプションツール
$SUDO apt-get install -y -q --no-install-recommends \
    xsel \
    lm-sensors \
    imwheel 2>/dev/null || true
