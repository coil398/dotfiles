" settings for mac and unix
if has('mac')
    " settings for mac
    source $HOME/.config/nvim/mac.vim
    " settings for linux
else
    source $HOME/.config/nvim/linux.vim
endif

" load dein.vim
source $XDG_CONFIG_HOME/nvim/dein.vim

" color scheme
source $XDG_CONFIG_HOME/nvim/color.vim

" load other setting files
" key mappings
source $HOME/.config/nvim/keymappings.vim

" settings for each filetypes
source $HOME/.config/nvim/types.vim

" launch commands
" source $HOME/.config/nvim/commands.vim

" autocommands
source $HOME/.config/nvim/autocmds.vim

" functions
" source $HOME/.config/nvim/func.vim

set number
set title
set ambiwidth=double
set tabstop=4
set expandtab
set shiftwidth=4
set smartindent
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

set pumblend=10
