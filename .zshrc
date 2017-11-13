# Load utilities
. $HOME/dotfiles/etc/load.sh

# 日本語を使用
export LANG=ja_JP.UTF-8

# パスを追加したい場合
export PATH="$HOME/bin:$PATH"
export PATH="$HOME/.tmux/plugins:$PATH"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_LOCAL_HOME="$HOME/.local"

fpath=($HOME/.zsh/completion $fpath)

# os type
OS=`uname`

# macOS と linux の場合分け
case "${OS}" in
    Darwin*)
    # do something
        ;;
    Linux*)
        export PATH="$HOME/.linuxbrew/bin:$PATH"
        export MANPATH="$HOME/.linuxbrew/share/man:$MANPATH"
        export INFOPATH="$HOME/.linuxbrew/share/info:$INFOPATH"
        export LD_LIBRARY_PATH="$HOME/.linuxbrew/lib:$LD_LIBRARY_PATH"
        eval `dircolors $HOME/.zsh/dircolors-solarized/dircolors.256dark`
        # for built libraries
        export PATH="$HOME/opt/bin:$PATH"
        export LD_LIBRARY_PATH="$HOME/opt/include:$LD_LIBRARY_PATH"

        # for gnu global
        export GTAGSCONF="$HOME/.globalrc"
        export GTAGSLABEL=pygments

        # for lib64
        export LD_LIBRARY_PATH="/usr/local/lib64:$LD_LIBRARY_PATH"

        # for cuda for 2 GPUs
        export TF_MIN_GPU_MULTIPROCESSOR_COUNT=6
	;;
esac

# Launch tmux
$HOME/dotfiles/bin/tmuxx

# 色を使用
autoload -Uz colors
colors

# ctrl-s で新しいコマンド履歴に移動
# stty stop undef

# 補完
autoload -Uz compinit && compinit -i
compinit

# 他のターミナルとヒストリーを共有
setopt share_history

# ヒストリーに重複を表示しない
setopt histignorealldups

HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000

# cdコマンドを省略して、ディレクトリ名のみの入力で移動
setopt auto_cd

# 自動でpushdを実行
setopt auto_pushd

# pushdから重複を削除
setopt pushd_ignore_dups

# コマンドミスを修正
setopt correct

# Ctrl+sのロック, Ctrl+qのロック解除を無効にする
setopt no_flow_control

# no beep
setopt no_beep

# グローバルエイリアス
alias -g L='| less'
alias -g H='| head'
alias -g G='| grep'
alias -g GI='| grep -ri'


# エイリアス
case "${OSTYPE}" in
    darwin*)
        alias lst='ls -tr -G'
        alias l='ls -tr -G'
        alias ls='ls -tr -G'
        alias la='ls -a -G'
        alias ll='ls -l -G'
        alias lla='ls -la -G'
        alias lal='ls -al -G'
        ;;
    linux*)
        alias lst='ls -tr --color'
        alias l='ls -tr --color'
        alias ls='ls -tr --color'
        alias la='ls -a --color'
        alias ll='ls -l --color'
        alias lla='ls -la --color'
        alias lal='ls -al --color'
esac

alias so='source'
alias v='nvim'
alias vi='nvim'
alias vim='nvim'
alias vz='nvim ~/.zshrc'
alias nv='nvim'
alias c='cdr'
alias soz='source ~/.zshrc'
alias fzft='fzf-tmux'
# historyに日付を表示
alias h='fc -lt '%F %T' 1'
alias cp='cp -i'
alias rm='rm -i'
alias mkdir='mkdir -p'
alias ..='c ../'
alias back='pushd'
alias diff='diff -U1'
alias ctags='/usr/local/bin/ctags'

# backspace,deleteキーを使えるように
stty erase "^?"

# cdの後にlsを実行
chpwd() { ls -tr -G }

# どこからでも参照できるディレクトリパス
cdpath=(~)

# 区切り文字の設定
autoload -Uz select-word-style
select-word-style default
zstyle ':zle:*' word-chars "_-./;@"
zstyle ':zle:*' word-style unspecified

# プロンプトを2行で表示、時刻を表示
PROMPT="%(?.%{${fg[green]}%}.%{${fg[red]}%})%n${reset_color}@${fg[blue]}%m${reset_color}(%*%) %~
%# "

# 補完後、メニュー選択モードになり左右キーで移動が出来る
zstyle ':completion:*:default' menu select=2

# 補完で大文字にもマッチ
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

# Ctrl+rでヒストリーのインクリメンタルサーチ、Ctrl+sで逆順
bindkey '^r' history-incremental-pattern-search-backward
bindkey '^s' history-incremental-pattern-search-forward

# コマンドを途中まで入力後、historyから絞り込み
# 例 ls まで打ってCtrl+pでlsコマンドをさかのぼる、Ctrl+bで逆順
autoload -Uz history-search-end
zle -N history-beginning-search-backward-end history-search-end
zle -N history-beginning-search-forward-end history-search-end
bindkey "^p" history-beginning-search-backward-end
bindkey "^b" history-beginning-search-forward-end

# vim keybind
# bindkey -v

# cdrコマンドを有効 ログアウトしても有効なディレクトリ履歴
# cdr タブでリストを表示
autoload -Uz add-zsh-hook
autoload -Uz chpwd_recent_dirs cdr
add-zsh-hook chpwd chpwd_recent_dirs
# cdrコマンドで履歴にないディレクトリにも移動可能に
zstyle ":chpwd:*" recent-dirs-default true

# 複数ファイルのmv 例　zmv *.txt *.txt.bk
autoload -Uz zmv
alias zmv='noglob zmv -W'

# mkdirとcdを同時実行
function mkcd() {
      if [[ -d $1 ]]; then
          echo "$1 already exists!"
          cd $1
      else
          mkdir -p $1 && cd $1
      fi
}

## PROMPT
CURRENT_DIR="%{${fg[blue]}%}[%~]%{${reset_color}%}"

autoload -Uz vcs_info
setopt PROMPT_SUBST
zstyle ':vcs_info:git:*' check-for-changes true
zstyle ':vcs_info:git:*' stagedstr "%F{yellow}!"
zstyle ':vcs_info:git:*' unstagedstr "%F{red}+"
zstyle ':vcs_info:*' formats "%F{green}%c%u[%b]%f"
zstyle ':vcs_info:*' actionformats '[%b|%a]'

function _update_vcs_info_msg() {
    LANG=en_US.UTF-8 vcs_info
    VCS_INFO=" ${vcs_info_msg_0_}"
    RPROMPT=$CURRENT_DIR$VCS_INFO
}

add-zsh-hook precmd _update_vcs_info_msg

# RPROMPT=$RPROMPT"${vcs_info_msg_0_}"

# zplugを読み込み
if [ "$(uname -s)" = 'Darwin' ]; then
    export ZPLUG_HOME=/usr/local/opt/zplug
elif [ "$(uname -s)" = 'Linux' ]; then
    export ZPLUG_HOME=$HOME/.linuxbrew/opt/zplug
fi

source $ZPLUG_HOME/init.zsh
source $HOME/.zplugrc

export DOT_REPO="https://github.com/coil_msp123/dotfiles.git"
export DOT_DIR="$HOME/dotfiles"

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

export NODENV_ROOT="$HOME/.nodenv"
export PATH="$NODENV_ROOT/bin:$PATH"
eval "$(nodenv init -)"

export RBENV_ROOT="$HOME/.rbenv"
export PATH="$RBENV_ROOT/bin:$PATH"
eval "$(rbenv init -)"

# Path for go lang
export GOPATH="$HOME/.go"
export PATH="$HOME/.go/bin:$PATH"

# yarn
export PATH="$PATH:`yarn global bin`"

# Path for haskell stack
export PATH="$PATH:$XDG_LOCAL_HOME/bin"

# if [[ -s $HOME/.nvm/nvm.sh ]] ; then source $HOME/.nvm/nvm.sh; fi

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

# エイリアス
alias diff='colordiff'
alias tig='tig --all'

# haskell
alias ghc='stack ghc --'
alias ghci='stack ghci --'
alias runhaskell='stack runhaskell --'

alias relogin='exec $SHELL -l'
