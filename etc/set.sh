#!/bin/sh

OS=`uname`

case "${OS}" in
    Darwin)
        ;;
    Linux)
        curl https://raw.githubusercontent.com/seebi/dircolors-solarized/master/dircolors.256dark -o $HOME/.zsh/dircolors-solarized/dircolors.256dark
        sudo apt -y install lm-sensors
        mv $HOME/.linuxbrew $HOME/dotfiles/.linuxbrew
        ;;
esac

mv $HOME/.enhancd $HOME/dotfiles/.enhancd
mv $HOME/.pyenv $HOME/dotfiles/.pyenv
mv $HOME/.nodenv $HOME/dotfiles/.nodenv
mv $HOME/.rbenv $HOME/dotfiles/.rbenv
mv $HOME/.cache $HOME/dotfiles/.cache