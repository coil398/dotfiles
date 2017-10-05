#!/bin/sh

SCRIPT_DIR=`dirname $0`
cd $SCRIPT_DIR

. "../../util.sh"

if has "brew"; then
    echo "brew already installed."
fi

case "${OSTYPE}" in
    darwin*)
        ./mac.sh
        ;;
    linux*)
        ./linux.sh
        ;;
esac

./brew_install.sh
