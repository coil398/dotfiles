#!/bin/sh

SCRIPT_DIR=`dirname $0`
cd $SCRIPT_DIR

sudo -- sh -c 'echo '/usr/local/bin/zsh' >> /etc/shells'
chsh -s /usr/local/bin/zsh
