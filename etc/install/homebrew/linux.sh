#!/bin/bash

SCRIPT_DIR=`dirname $0`
cd $SCRIPT_DIR
. '../../util.sh'

sudo apt -y update && sudo apt -y upgrade
sudo apt -y install build-essential file git python-setuptools ruby
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install)"
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
export MANPATH="/home/linuxbrew/.linuxbrew/share/man:$MANPATH"
export INFOPATH="/home/linuxbrew/.linuxbrew/share/info:$INFOPATH"
