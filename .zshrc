# Load utilities
. $HOME/dotfiles/etc/load.sh
. $HOME/.zsh_alias

# 日本語を使用
export LANG=ja_JP.UTF-8

# パスを追加したい場合
export PATH="$HOME/bin:$PATH"
export PATH="$HOME/.tmux/plugins:$PATH"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_LOCAL_HOME="$HOME/.local"

# for built libraries
export PATH="$HOME/opt/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/opt/include:$LD_LIBRARY_PATH"

# cargo
export PATH="$HOME/.cargo/bin:$PATH"

export PATH="$HOME/.bin:$PATH"

# krew
export PATH="${KWER_ROOT:-$HOME/.krew}/bin:$PATH"

fpath=($HOME/.zsh/completion $fpath)

# anyenv
export PATH="$HOME/.anyenv/bin:$PATH"
eval "$(anyenv init -)"

export GOPATH="$HOME/go"
export PATH="$PATH:$GOPATH/bin"

# os type
OS=`uname`

# macOS と linux の場合分け
case "${OS}" in
    Darwin*)
        # for clang on macOS
        export PATH="/usr/local/opt/llvm/bin:$PATH"
        export PATH="/usr/local/sbin:$PATH"
        fpath=(/usr/local/share/zsh-completions $fpath)

        export  PATH=/usr/local/opt/coreutils/libexec/gnubin:${PATH}
        export  MANPATH=/usr/local/opt/coreutils/libexec/gnuman:${MANPATH}
        export  PATH=/usr/local/opt/ed/libexec/gnubin:${PATH}
        export  MANPATH=/usr/local/opt/ed/libexec/gnuman:${MANPATH}
        export  PATH=/usr/local/opt/findutils/libexec/gnubin:${PATH}
        export  MANPATH=/usr/local/opt/findutils/libexec/gnuman:${MANPATH}
        export  PATH=/usr/local/opt/gnu-sed/libexec/gnubin:${PATH}
        export  MANPATH=/usr/local/opt/gnu-sed/libexec/gnuman:${MANPATH}
        export  PATH=/usr/local/opt/gnu-tar/libexec/gnubin:${PATH}
        export  MANPATH=/usr/local/opt/gnu-tar/libexec/gnuman:${MANPATH}
        export  PATH=/usr/local/opt/grep/libexec/gnubin:${PATH}
        export  MANPATH=/usr/local/opt/grep/libexec/gnuman:${MANPATH}
    ;;
    Linux*)
        # for lib64
        export LD_LIBRARY_PATH="/usr/local/lib64:$LD_LIBRARY_PATH"

        # for cuda 9.0
        export PATH="/opt/cuda-9.0//bin:$PATH"
        export LD_LIBRARY_PATH="/opt/cuda-9.0//lib64:$LD_LIBRARY_PATH"

        # for cuda
        export PATH="/opt/cuda/bin:$PATH"
        export LD_LIBRARY_PATH="/opt/cuda/lib64:$LD_LIBRARY_PATH"

        # for cuda for 2 GPUs
        export TF_MIN_GPU_MULTIPROCESSOR_COUNT=6

        # anyenv for linux
        export PATH="$HOME/.anyenv/bin:$PATH"

        ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE='fg=4'

        export DENO_INSTALL="/home/coil398/.deno"
        export PATH="$DENO_INSTALL/bin:$PATH"
    ;;
esac

# Launch tmux
$HOME/dotfiles/bin/tmuxx

# 色を使用
autoload -Uz colors
colors
zstyle ':completion:*' list-colors "${LS_COLORS}"

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

# backspace,deleteキーを使えるように
stty erase "^?"

# cdの後にlsを実行
chpwd() { ls }
# chpwd() { ls -tr -G }

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
    export ZPLUG_HOME="$HOME/.zplug"
fi
. $ZPLUG_HOME/init.zsh
. $HOME/.zplugrc

export DOT_REPO="https://github.com/coil_msp123/dotfiles.git"
export DOT_DIR="$HOME/dotfiles"

# Path for haskell stack
export PATH="$PATH:$XDG_LOCAL_HOME/bin"

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

bindkey "^[[3~" delete-char

export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

source ~/.optional.zsh

move() {
    cd "$(ghq root)/$(ghq list | fzf)"
}

gopen() {
    cat ~/repos.txt | fzf | xargs -I URL open URL
}

eval "$(direnv hook zsh)"

# The next line updates PATH for the Google Cloud SDK.
if [ -f "$HOME/opt/bin/google-cloud-sdk/path.zsh.inc" ]; then . "$HOME/opt/bin/google-cloud-sdk/path.zsh.inc"; fi

# The next line enables shell command completion for gcloud.
if [ -f "$HOME/opt/bin/google-cloud-sdk/completion.zsh.inc" ]; then . "$HOME/opt/bin/google-cloud-sdk/completion.zsh.inc"; fi
