" dein Scripts-----------------------------
if &compatible
    set nocompatible               " Be iMproved
endif

let s:vim_plug_dir = $XDG_CACHE_HOME . '/vim-plug'
if !isdirectory(s:vim_plug_dir)
    call system('curl -fLo ' . s:vim_plug_dir . '/plug.vim --create-dir https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim')
endif

" Required:
set runtimepath+=$XDG_CACHE_HOME/vim-plug/plug.vim

