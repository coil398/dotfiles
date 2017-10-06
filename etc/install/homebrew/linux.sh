#!/bin/bash

SCRIPT_DIR=`dirname $0`
cd $SCRIPT_DIR
. '../../util.sh'

sudo apt -y update && sudo apt -y upgrade
sudo apt -y install build-essential file git python-setuptools ruby
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install)"
echo 'export PATH="$HOME/.linuxbrew/bin:$PATH"' >> ${HOME}/.bash_profile
echo 'export MANPATH="$HOME/.linuxbrew/share/man:$MANPATH"' >> ${HOME}/.bash_profile
echo 'export INFOPATH="$HOME/.linuxbrew/share/info:$INFOPATH"' >> ${HOME}/.bash_profile
source ${HOME}/.bash_profile
