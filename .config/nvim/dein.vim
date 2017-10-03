" dein Scripts-----------------------------
if &compatible
    set nocompatible               " Be iMproved
endif

" Required:
set runtimepath+=/Users/kawasetakumi/.cache/dein/repos/github.com/Shougo/dein.vim

let s:dein_cache_dir = $XDG_CACHE_HOME . '/dein'
let s:dein_config_dir = $XDG_CONFIG_HOME . '/nvim'

" Required:
if dein#load_state(s:dein_cache_dir)
    call dein#begin(s:dein_cache_dir)

    let s:toml = s:dein_config_dir . '/dein.toml'
    let s:toml_lazy = s:dein_config_dir . '/dein_lazy.toml'
    let s:toml_deoplete = s:dein_config_dir . '/dein_deoplete.toml'
    let s:toml_depend = s:dein_config_dir . '/dein_depend.toml'

    call dein#load_toml(s:toml, {'lazy': 0})
    call dein#load_toml(s:toml_lazy, {'lazy': 1})
    call dein#load_toml(s:toml_deoplete, {})
    call dein#load_toml(s:toml_depend, {'lazy': 1})

    call dein#end()
    call dein#save_state()

    " Let dein manage dein
    " Required:
    " call dein#add('/Users/kawasetakumi/.cache/dein/repos/github.com/Shougo/dein.vim')

    " Add or remove your plugins here:
    " call dein#add('Shougo/neosnippet.vim')
    " call dein#add('Shougo/neosnippet-snippets')

    " You can specify revision/branch/tag.
    " call dein#add('Shougo/vimshell', { 'rev': '3787e5' })

    " Required:
    " call dein#end()
    " call dein#save_state()
endif
    
" Required:
filetype plugin indent on

" if dein#check_install(['vimproc'])
"     call dein#install(['vimproc'])
" endif

" If you want to install not installed plugins on startup.
if dein#check_install()
    call dein#install()
endif

" End dein Scripts-------------------------
