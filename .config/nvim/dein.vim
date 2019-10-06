" dein Scripts-----------------------------
if &compatible
    set nocompatible               " Be iMproved
endif

" set cache and config dirs
let s:dein_cache_dir = $XDG_CACHE_HOME . '/dein'
let s:dein_config_dir = $XDG_CONFIG_HOME . '/nvim'

" Required:
set runtimepath+=$XDG_CACHE_HOME/dein/repos/github.com/Shougo/dein.vim

let s:dein_dir = s:dein_cache_dir . '/repos/github.com/Shougo/dein.vim'
if !isdirectory(s:dein_dir)
    call system('git clone https://github.com/Shougo/dein.vim ' . shellescape(s:dein_dir))
endif

" Required:
if dein#load_state(s:dein_cache_dir)
    call dein#begin(s:dein_cache_dir)

    let s:toml = s:dein_config_dir . '/dein.toml'
    let s:toml_lazy = s:dein_config_dir . '/dein_lazy.toml'
    " let s:toml_lsp = s:dein_config_dir . '/dein_lsp.toml'
    " let s:toml_lsp = s:dein_config_dir . '/async_vim_lsp.toml'
    let s:toml_coc = s:dein_config_dir . '/coc.toml'
    let s:toml_lang = s:dein_config_dir . '/dein_lang.toml'

    let s:toml_plugin = s:dein_config_dir . '/dein_plugin.toml'

    call dein#load_toml(s:toml, {'lazy': 0})
    call dein#load_toml(s:toml_lazy, {'lazy': 1})

    " call dein#load_toml(s:toml_lsp, {})
    " call dein#load_toml(s:toml_deoplete, {})
    call dein#load_toml(s:toml_coc, {'lazy': 1})
    call dein#load_toml(s:toml_lang, {'lazy': 1})

    call dein#load_toml(s:toml_plugin, {'lazy': 0})

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
