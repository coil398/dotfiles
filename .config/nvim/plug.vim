if &compatible
    set nocompatible
endif

let s:vim_plug_dir = $XDG_CACHE_HOME . '/vim-plug'
if !isdirectory(s:vim_plug_dir)
    call system('curl -fLo ' . s:vim_plug_dir . '/plug.vim --create-dir https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim')
endif

source $XDG_CACHE_HOME/vim-plug/plug.vim
source $XDG_CONFIG_HOME/nvim/config.vim

call config#lightline#init()

call plug#begin()

Plug 'neoclide/coc.nvim', {'branch': 'release'}
Plug 'lambdalisue/gina.vim'
Plug 'itchyny/lightline.vim'
Plug 'itchyny/vim-gitbranch'
Plug 'luochen1990/rainbow'
Plug 'tomasiser/vim-code-dark'
Plug 'ctrlpvim/ctrlp.vim'
Plug 'nvim-treesitter/nvim-treesitter', {'do': ':TSUpdate'}

call plug#end()

let g:rainbow_active = 1
call config#coc#init()
call config#ctrlp#init()
call config#nvim_treesitter#init()
