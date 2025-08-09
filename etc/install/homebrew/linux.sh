#!/bin/sh

# Prefer apt-based installs on Linux; do not install linuxbrew-wrapper.
# Install basic build tools commonly needed by other steps.
set -eu

if command -v sudo >/dev/null 2>&1; then
  sudo apt -y update && sudo apt -y upgrade
  sudo apt -y install build-essential file git curl
else
  apt -y update && apt -y upgrade
  apt -y install build-essential file git curl
fi

echo "Skipped Homebrew install on Linux. Use apt-based installers instead."
