" settings for mac and unix
if has('mac')
    " settings for mac
    source $HOME/.config/nvim/mac.vim
    " settings for unix
elseif has('unix')
    source $HOME/.config/nvim/unix.vim
else
    echo 'neither mac nor unix'
endif

set number
