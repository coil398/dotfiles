#!/bin/sh

set -eu

if !(type brew > /dev/null 2>&1); then
  echo "Home brew does not exist"
  exit 1
fi

(
  brew install coreutils diffutils ed findutils gawk gnu-sed gnu-tar grep gzip
)
