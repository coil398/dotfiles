augroup MyAutoCmd
autocmd!
augroup END

if has("syntax")
    syntax on
    set synmaxcol=200
endif

set number
set title
set ambiwidth=double
set tabstop=4
set expandtab
set shiftwidth=4
set smartindent
set list
set listchars=tab:»-,trail:-,eol:↲,extends:»,precedes:«,nbsp:%
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
set showmatch
set laststatus=2
set wrapscan
set modeline
set background=light
set smartcase
set autowrite

" spelling check

" set spell

" search system
set ignorecase
set infercase
set smartcase
set hlsearch
set incsearch

set display=lastline

set matchpairs& matchpairs+=<:>

set matchtime=1
set showtabline=2
set clipboard=unnamed
set wildmode=list:full
set wildignore=*.o,*.obj,*.pyc,*.so,*.dll
set mouse=a
set ttymouse=xterm2
set nocompatible
filetype plugin on
packadd! matchit

" foldmethod
set foldmethod=marker
set foldlevel=0
set foldcolumn=1
" save the fold settings.
autocmd BufWritePost * if expand('%') != '' && &buftype !~ 'nofile' | mkview | endif
autocmd BufRead * if expand('%') != '' && &buftype !~ 'nofile' | silent loadview | endif
" Don't save options.
set viewoptions-=options
" set the color.
hi Folded ctermbg=0 ctermfg=2
hi FoldColumn ctermbg=8 ctermfg=2

source $HOME/.vimplugrc

" <Leader>を<Space>に設定
let mapleader = "\<Space>"

" タブキー補完の順番を変更
let g:SuperTabContextDefaultCompletionType = "context"
let g:SuperTabDefaultCompletionType = "<C-n>"

" Load *.ejs files
au BufNewFile,BufRead *.ejs setf html
" Load .json files
au BufNewFile,BufRead *.json setf js
" Load .xml files
au BufNewFile,BufRead *.goml setf xml
" Load .py files
au BufNewFile,BufRead *.py set filetype=python


" settings for jedi-vim
let g:jedi#auto_vim_configuration = 0
let g:jedi#popup_select_first = 0


autocmd BufNewFile,BufRead *.py nnoremap [command]w :!python %
autocmd BufNewFile,BufRead *.pl nnoremap [command]w :!perl %
"autocmd BufNewFile,BufRead *.hs nnoremap <C-w> :!

nnoremap j gj
nnoremap k gk

" for two or more tags found, display the tags as default
nnoremap <C-]> g<C-]>

nnoremap [q :cprevious<CR>
nnoremap ]q :cnext<CR>
nnoremap [Q :<C-u>cfirst<CR>
nnoremap ]Q :<C-u>clast<CR>
nnoremap <Leader>w :cwindow<CR>

" nnoremap <Tab> <C-w>

nnoremap <Space>h ^
nnoremap <Space>l $

vnoremap v $h

" nnoremap <Tab> %
" vnoremap <Tab> %

" mappings for command mode to scroll histories
" cnoremap <C-p> <Up>
" cnoremap <C-n> <Down>

" mapping to expand directory of the active file in command mode
cnoremap <expr> %% getcmdtype() == ':' ? expand('%:h').'/' : '%%'

"nnoremap :q :qa
"nnoremap :wq :wqa

" T + ? で各種設定をトグル
" nnoremap [toggle] <Nop>
"nmap T [toggle]
" nnoremap <silent> [toggle]p :set paste!<CR>:set paste?<CR>

" toggle for paste
set pastetoggle=<f5>

function! Preserve(command)
    " Save the last search.
    let search = @/
    " Save the current cursor position.
    let cursor_position = getpos('.')
    " Save the current window position.
    normal! H
    let window_position = getpos('.')
    call setpos('.', cursor_position)
    " Execute the command.
    execute a:command
    " Restore the last search.
    let @/ = search
    " Restore the previous window position.
    call setpos('.', window_position)
    normal! zt
    " Restore the previous cursor position.
    call setpos('.', cursor_position)
endfunction

function! Autopep8()
    call Preserve(':silent %!autopep8 -')
endfunction

function! s:clang_format()
  let now_line = line(".")
  exec ":%! clang-format"
  exec ":" . now_line
endfunction

if executable('clang-format')
  augroup cpp_clang_format
    autocmd!
    autocmd BufWrite,FileWritePre,FileAppendPre *.[ch]pp call s:clang_format()
  augroup END
endif

" Shift + F で自動修正
autocmd FileType python nnoremap <Space>f :call Autopep8()<CR>

" Insert space in normal mode
nnoremap <Space><Space> i<Space><ESC>l

" delete the hilighting
nnoremap <silent> <ESC><ESC> :noh<CR>

" resolve the ambiguous command :E
command E Ex

" The prefix key.
nnoremap    [unite]   <Nop>
nmap    <Space>u [unite]

" unite.vim keymap
let g:unite_enable_start_insert = 1
let g:unite_source_history_yank_enable =1
nnoremap <silent> [unite]u :<C-u>Unite<Space>file<CR>
nnoremap <silent> [unite]n :<C-u>Unite<Space>file/new<CR>
nnoremap <silent> [unite]g :<C-u>Unite<Space>grep<CR>
nnoremap <silent> [unite]f :<C-u>Unite<Space>buffer<CR>
nnoremap <silent> [unite]b :<C-u>Unite<Space>bookmark<CR>
nnoremap <silent> [unite]a :<C-u>UniteBookmarkAdd<CR>
nnoremap <silent> [unite]m :<C-u>Unite<Space>file_mru<CR>
nnoremap <silent> [unite]h :<C-u>Unite<Space>history/yank<CR>
nnoremap <silent> [unite]r :<C-u>Unite -buffer-name=register register<CR>
nnoremap <silent> [unite]c :<C-u>UniteWithBufferDir -buffer-name=files file<CR>
nnoremap <silent> [unite]o :<C-u>Unite<Space>outline<CR>
nnoremap <silent> [unite]vr :UniteResume<CR>
" vinarise
let g:vinarise_enable_auto_detect = 1 
" unite-build map
nnoremap <silent> [unite]vb :Unite build<CR>
nnoremap <silent> [unite]vcb :Unite build:!<CR>
nnoremap <silent> [unite]vch :UniteBuildClearHighlight<CR>

let g:unite_source_grep_command = 'ag'
let g:unite_source_grep_default_opts = '--nocolor --nogroup'
let g:unite_source_grep_max_candidates = 200
let g:unite_source_grep_recursive_opt = ''

" unite-grepの便利キーマップ
vnoremap [unite]g y:Unite grep::-iRn:<C-R>=escape(@", '\\.*$^[]')<CR><CR>

" giti
    nmap <Space>gd <SID>(git-diff-cached)
    nmap <Space>gD <SID>(git-diff)
    nmap <Space>gf <SID>(git-fetch-now)
    nmap <Space>gF <SID>(git-fetch)
    nmap <Space>gp <SID>(git-push-now)
    nmap <Space>gP <SID>(git-pull-now)
    nmap <Space>gl <SID>(git-log-line)
    nmap <Space>gL <SID>(git-log)

    " unite prefix key
    " nnoremap [unite] <Nop>
    " nmap <Leader>. [unite]

    nmap [unite]gg    <SID>(giti-sources)
    nmap [unite]gst   <SID>(git-status)
    nmap [unite]gb    <SID>(git-branch)
    nmap [unite]gB    <SID>(git-branch_all)
    nmap [unite]gc    <SID>(git-config)
    nmap [unite]gl    <SID>(git-log)
    nmap [unite]gL    <SID>(git-log-this-file)

    " giti {{{
    if globpath(&rtp, 'plugin/giti.vim') != ''
		let g:giti_log_default_line_count = 100
		nnoremap <expr><silent> <SID>(git-diff)        ':<C-u>GitiDiff ' . expand('%:p') . '<CR>'
		nnoremap <expr><silent> <SID>(git-diff-cached) ':<C-u>GitiDiffCached ' . expand('%:p') .  '<CR>'
		nnoremap       <silent> <SID>(git-fetch-now)    :<C-u>GitiFetch<CR>
		nnoremap       <silent> <SID>(git-fetch)        :<C-u>GitiFetch 
		nnoremap <expr><silent> <SID>(git-push-now)    ':<C-u>GitiPushWithSettingUpstream origin ' . giti#branch#current_name() . '<CR>'
		nnoremap       <silent> <SID>(git-push)         :<C-u>GitiPush 
		nnoremap       <silent> <SID>(git-pull-now)     :<C-u>GitiPull<CR>
		nnoremap       <silent> <SID>(git-pull)         :<C-u>GitiPull 
		nnoremap       <silent> <SID>(git-log-line)     :<C-u>GitiLogLine ' . expand('%:p') . '<CR>'
		nnoremap       <silent> <SID>(git-log)          :<C-u>GitiLog ' . expand('%:p') . '<CR>'

		nnoremap <silent> <SID>(giti-sources)   :<C-u>Unite giti<CR>
		nnoremap <silent> <SID>(git-status)     :<C-u>Unite giti/status<CR>
		nnoremap <silent> <SID>(git-branch)     :<C-u>Unite giti/branch<CR>
		nnoremap <silent> <SID>(git-branch_all) :<C-u>Unite giti/branch_all<CR>
		nnoremap <silent> <SID>(git-config)     :<C-u>Unite giti/config<CR>
		nnoremap <silent> <SID>(git-log)        :<C-u>Unite giti/log<CR>

nnoremap <silent><expr> <SID>(git-log-this-file) ':<C-u>Unite giti/log:' . expand('%:p') . '<CR>'
    endif
    " }}}

" VimFiler settings
let g:vimfiler_as_default_explorer=1
let g:vimfiler_safe_mode_by_default=0
nnoremap <silent> [unite]e :<C-u>VimFiler -split -simple -winwidth=40 -no-quit<CR>

" smartinput
call smartinput#map_to_trigger('i', '<Plug>(smartinput_BS)', '<BS>', '<BS>')
call smartinput#map_to_trigger('i', '<Plug>(smartinput_C-h)', '<BS>', '<C-h>')
call smartinput#map_to_trigger('i', '<Plug>(smartinput_CR)', '<Enter>', '<Enter>')

" neocompletion
"Note: This option must be set in .vimrc(_vimrc).  NOT IN .gvimrc(_gvimrc)!
" Disable AutoComplPop.
let g:acp_enableAtStartup = 0
" Use neocomplete.
let g:neocomplete#enable_at_startup = 1
" Use smartcase.
let g:neocomplete#enable_smart_case = 1
" Set minimum syntax keyword length.
let g:neocomplete#sources#syntax#min_keyword_length = 3
let g:neocomplete#lock_buffer_name_pattern = '\*ku\*'

" Define dictionary.
let g:neocomplete#sources#dictionary#dictionaries = {
    \ 'default' : '',
    \ 'vimshell' : $HOME.'/.vimshell_hist',
    \ 'scheme' : $HOME.'/.gosh_completions'
        \ }

" Define keyword.
if !exists('g:neocomplete#keyword_patterns')
    let g:neocomplete#keyword_patterns = {}
endif
let g:neocomplete#keyword_patterns['default'] = '\h\w*'

" Plugin key-mappings.
inoremap <expr><C-g>     neocomplete#undo_completion()
inoremap <expr><C-l>     neocomplete#complete_common_string()

" Recommended key-mappings.
" <CR>: close popup and save indent.
" inoremap <silent> <CR> <C-r>=<SID>my_cr_function()<CR>
" function! s:my_cr_function()
  " return (pumvisible() ? "\<C-y>" : "" ) . "\<CR>"
  " For no inserting <CR> key.
  " return pumvisible() ? "\<C-y>" : "\<CR>"
" endfunction
" <TAB>: completion.
inoremap <expr><TAB> pumvisible() ? "\<C-n>" : "\<TAB>"
" <C-h>, <BS>: close popup and delete backword char.
inoremap <expr><C-h> neocomplete#smart_close_popup()."\<C-h>"
inoremap <expr><BS> neocomplete#smart_close_popup()."\<C-h>"
" Close popup by <Space>.
"inoremap <expr><Space> pumvisible() ? "\<C-y>" : "\<Space>"

" AutoComplPop like behavior.
"let g:neocomplete#enable_auto_select = 1

" Shell like behavior(not recommended).
"set completeopt+=longest
"let g:neocomplete#enable_auto_select = 1
"let g:neocomplete#disable_auto_complete = 1
"inoremap <expr><TAB>  pumvisible() ? "\<Down>" : "\<C-x>\<C-u>"

" change the trigger TAB to Ctrl + k to expand ultisnips.
" let g:UltiSnipsExpandTrigger="<C-k>"

" settings for neosnippet
" Plugin key-mappings.
imap <C-k>     <Plug>(neosnippet_expand_or_jump)
smap <C-k>     <Plug>(neosnippet_expand_or_jump)
xmap <C-k>     <Plug>(neosnippet_expand_target)
" SuperTab like snippets behavior.
imap <expr><TAB> neosnippet#expandable_or_jumpable() ?
\ "\<Plug>(neosnippet_expand_or_jump)"
\: pumvisible() ? "\<C-n>" : "\<TAB>"
smap <expr><TAB> neosnippet#expandable_or_jumpable() ?
\ "\<Plug>(neosnippet_expand_or_jump)"
\: "\<TAB>"

" For snippet_complete marker.
if has('conceal')
  set conceallevel=2 concealcursor=i
  endif


" Popup color.
hi Pmenu ctermfg=15 ctermbg=0
hi PmenuSel ctermfg=0 ctermbg=15
hi PMenuSbar ctermfg=15 ctermbg=0

" Enable omni completion.
autocmd FileType css setlocal omnifunc=csscomplete#CompleteCSS
autocmd FileType html,markdown setlocal omnifunc=htmlcomplete#CompleteTags
autocmd FileType javascript setlocal omnifunc=javascriptcomplete#CompleteJS
"autocmd FileType python setlocal omnifunc=pythoncomplete#Complete
autocmd FileType python setlocal omnifunc=jedi#completions
autocmd FileType python setlocal completeopt-=preview
autocmd FileType xml setlocal omnifunc=xmlcomplete#CompleteTags

" Enable heavy omni completion.
if !exists('g:neocomplete#sources#omni#input_patterns')
  let g:neocomplete#sources#omni#input_patterns = {}
endif

"let g:neocomplete#sources#omni#input_patterns.php = '[^. \t]->\h\w*\|\h\w*::'
"let g:neocomplete#sources#omni#input_patterns.c = '[^.[:digit:] *\t]\%(\.\|->\)'
"let g:neocomplete#sources#omni#input_patterns.cpp = '[^.[:digit:] *\t]\%(\.\|->\)\|\h\w*::'

let g:syntastic_check_on_open=0
let g:syntastic_check_on_wq=0
" python
let g:syntastic_python_checkers = ['flake8']
" C
let g:syntastic_c_check_header = 1
" C++
let g:syntastic_cpp_compiler = 'clang++'
let g:syntastic_cpp_check_header = 1

if has('path_extra')
    set tags+=tags;
endif


nnoremap [command] <Nop>
nmap <Space>c [command]
let g:tagbar_width=30
nnoremap <silent> [command]t :TagbarToggle<CR>

let g:SrcExpl_RefreshTime = 1000
" Is update tags when SrcExpl is opened
let g:SrcExpl_isUpdateTags = 0
" Tag update command
let g:SrcExpl_updateTagsCmd = 'ctags --sort=foldcase %'
" Update all tags
function! g:SrcExpl_UpdateAllTags()
let g:SrcExpl_updateTagsCmd = 'ctags --sort=foldcase -R .'
call g:SrcExpl_UpdateTags()
let g:SrcExpl_updateTagsCmd = 'ctags --sort=foldcase %'
endfunction
" Source Explorer Window Height
let g:SrcExpl_winHeight = 14
" Mappings
nnoremap <silent> [command]e :SrcExplToggle<CR>
nnoremap <silent> [command]u :call g:SrcExpl_UpdateTags()<CR>
nnoremap <silent> [command]a :call g:SrcExpl_UpdateAllTags()<CR>
nnoremap <silent> [command]n :call g:SrcExpl_NextDef()<CR>
nnoremap <silent> [command]p :call g:SrcExpl_PrevDef()<CR>
nnoremap <silent> [command]A :SrcExplToggle<CR>:set autochdir!<CR>:<C-u>VimFiler -split -simple -winwidth=40 -no-quit<CR>:TagbarToggle<CR>
nnoremap <silent> [command]h :GhcModType<CR>
let $PATH = $PATH . ':' . expand('~/.local/bin')

" 隣接した{}で改行したらインデント
function! IndentBraces()
    let nowletter = getline(".")[col(".")-1]    " 今いるカーソルの文字
    let beforeletter = getline(".")[col(".")-2] " 1つ前の文字

    " カーソルの位置の括弧が隣接している場合
    if nowletter == "}" && beforeletter == "{"
        return "\n\n\<UP>\t"
    else
        return "\n"
    endif
endfunction
" Enterに割り当て
inoremap <silent> <expr> <CR> IndentBraces() 

" settings for marching
" 非同期ではなくて同期処理で補完する
let g:marching_backend = "sync_clang_command"

" オプションの設定
" これは clang のコマンドに渡される
let g:marching_clang_command_option="-std=c++1y"


" neocomplete.vim と併用して使用する場合
" neocomplete.vim を使用すれば自動補完になる
let g:marching_enable_neocomplete = 1

"auto-ctags
let g:auto_ctags = 1

" For haskell
" Disable haskell-vim omnifunc
let g:haskellmode_completion_ghc = 0
autocmd FileType haskell setlocal omnifunc=necoghc#omnifunc

" extend search
xnoremap * :<C-u>call <SID>VSetSearch()<CR>/<C-R>=@/<CR><CR>
xnoremap # :<C-u>call <SID>VSetSearch()<CR>?<C-R>=@/<CR><CR>

function! s:VSetSearch()
  let temp = @s
  norm! gv"sy
  let @/ = '\V' . substitute(escape(@s, '/\'), '\n', '\\n', 'g')
  let @s = temp
endfunction

" & command contains && flag
nnoremap & :&&<CR>
xnoremap & :&&<CR>
