#!/bin/sh

SCRIPT_DIR=`dirname $0`
OS=`uname`
cd $SCRIPT_DIR

. "../../util.sh"

if has "brew"; then
    echo "brew already installed."
fi

case "${OS}" in
    Darwin*)
        ./mac.sh
        ;;
    Linux*)
        ./linux.sh
        ;;
esac

./brew_install.sh
