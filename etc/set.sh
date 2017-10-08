#!/bin/sh

OS=`uname`

case "${OS}" in
    Darwin)
        ;;
    Linux)
        git clone git://github.com/sigurdga/gnome-terminal-colors-solarized.git
        cd gnome-terminal-colors-solarized
        ./install.sh
        sudo apt -y install lm-sensors
        mv $HOME/.linuxbrew $HOME/dotfiles/.linuxbrew
        ;;
esac

mv $HOME/.enhancd $HOME/dotfiles/.enhancd
mv $HOME/.pyenv $HOME/dotfiles/.pyenv
mv $HOME/.nodenv $HOME/dotfiles/.nodenv
mv $HOME/.rbenv $HOME/dotfiles/.rbenv
mv $HOME/.cache $HOME/dotfiles/.cache
