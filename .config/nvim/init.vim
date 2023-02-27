set nocompatible

" settings for mac and unix
if has('mac')
    " settings for mac
    source $HOME/.config/nvim/mac.vim
    " settings for linux
else
    source $HOME/.config/nvim/linux.vim
endif

" load plugins
lua require('init')

" color scheme
source $XDG_CONFIG_HOME/nvim/color.vim

" load other setting files
" key mappings
source $HOME/.config/nvim/keymappings.vim

" augroup, autocommands
source $HOME/.config/nvim/auto.vim

set tabstop=4
set expandtab
set shiftwidth=4

set number
set title
set ambiwidth=double
set list
set listchars=tab:»-,trail:-,extends:»,precedes:«,nbsp:%
set nrformats-=octal
set hidden
set history=200
set virtualedit=block
set whichwrap=b,s,h,l,[,],<,>
set backspace=indent,eol,start
set wildmenu
set fenc=utf-8
set nobackup
set noswapfile
set autoread
set showcmd
set cursorline
set visualbell
set laststatus=2
set wrapscan
set modeline
set autowrite
set display=lastline
set matchpairs& matchpairs+=<:>
set matchtime=1
set showtabline=2
set wildmenu
set wildignore=*.o,*.obj,*.pyc,*.so,*.dll
set mouse=a
set updatetime=100

" search system
set showmatch
set smartcase
set ignorecase
set infercase
set hlsearch
set incsearch

" foldmethod
set foldmethod=marker
set foldlevel=0
set foldcolumn=1

" disable the preview window
set completeopt-=preview

if has('nvim')
    set pumblend=5
endif

filetype indent off
