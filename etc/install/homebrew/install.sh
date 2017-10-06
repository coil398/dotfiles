#!/bin/sh

SCRIPT_DIR=`dirname $0`
OS=`uname`
cd $SCRIPT_DIR

. "../../util.sh"

if has "brew"; then
    echo "brew already installed."
else
    case "${OS}" in
        Darwin*)
            ./mac.sh
            ;;
        Linux*)
            ./linux.sh
            ;;
    esac
fi

./brew_install.sh
