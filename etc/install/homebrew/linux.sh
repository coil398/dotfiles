#!/bin/bash

SCRIPT_DIR=`dirname $0`
cd $SCRIPT_DIR
. '../../util.sh'

if has 'sudo'; then
    sudo apt -y update && sudo apt -y upgrade
    sudo apt -y install build-essential file git python-setuptools ruby
    sudo apt -y install linuxbrew-wrapper
else
    apt -y update && sudo apt -y upgrade
    apt -y install build-essential file git python-setuptools ruby
    apt -y install linuxbrew-wrapper
fi
