" push quickfix window always to the bottom
autocmd FileType qf wincmd J

" for go lang
augroup go
    autocmd!
    autocmd FileType go :highlight goErr cterm=bold ctermfg=214
    autocmd FileType go :match goErr /\<err\>/
augroup END

" for python
augroup python
    autocmd!
    autocmd FileType python :syn match pythonOperator "\(+\|=\|-\|\^\|\*\)"
    autocmd FileType python :syn match pythonDelimiter "\(,\|\.\|:\)"
    autocmd FileType python :syn keyword self self
    autocmd FileType python :hi link pythonOperator Statement
    autocmd FileType python :hi link pythonDelimiter Special
    autocmd FileType python :hi link self Type
    " autocmd FileType python :highlight self cterm=bold ctermfg=214
    " autocmd FileType python :match self /self/
    " autocmd FileType python :highlight colon cterm=bold ctermfg=214
    " autocmd FileType python :match colon /:/
augroup END

" for c++
augroup cpp
    autocmd!
    autocmd FileType cpp :highlight cppcoloncolon cterm=bold ctermfg=214
    autocmd FileType cpp :match cppcoloncolon /\:\:/
augroup END

augroup html
    autocmd!
    autocmd FileType html :setlocal tabstop=2
    autocmd FileType html :setlocal shiftwidth=2
augroup END

augroup typescript
    autocmd!
    autocmd FileType typescript :syn match Operator "\(|\|+\|=\|-\|\^\|\*\)"
    autocmd FileType typescript :syn match Delimiter "\(\.\|:\)"
    autocmd FileType typescript :hi link Operator Statement
    autocmd FileType typescript :hi link Delimiter Special
augroup END

augroup typescriptreact
    autocmd!
    autocmd BufNewFile,BufRead *.tsx set filetype=typescript.tsx
    autocmd FileType typescript.tsx :syn match Operator "\(|\|+\|=\|-\|\^\|\*\)"
    autocmd FileType typescript.tsx :syn match Delimiter "\(\.\|:\)"
    autocmd FileType typescript.tsx :hi link Operator Statement
    autocmd FileType typescript.tsx :hi link Delimiter Special
    autocmd FileType typescript.tsx :setlocal tabstop=2
    autocmd FileType typescript.tsx :setlocal shiftwidth=2
augroup END

augroup yaml
    autocmd!
    autocmd FileType yaml :setlocal tabstop=2
    autocmd FileType yaml :setlocal shiftwidth=2
augroup END

augroup json
    autocmd!
    autocmd FileType json :setlocal tabstop=2
    autocmd FileType json :setlocal shiftwidth=2
augroup END

augroup denite-windows
    autocmd!
    autocmd FileType denite set winblend=5
    autocmd FileType denite-filter set winblend=5
augroup END

" Define mappings
autocmd FileType denite call s:denite_my_settings()
function! s:denite_my_settings() abort
    nnoremap <silent><buffer><expr> <CR>
    \ denite#do_map('do_action')
    nnoremap <silent><buffer><expr> d
    \ denite#do_map('do_action', 'delete')
    nnoremap <silent><buffer><expr> p
    \ denite#do_map('do_action', 'preview')
    nnoremap <silent><buffer><expr> q
    \ denite#do_map('quit')
    nnoremap <silent><buffer><expr> i
    \ denite#do_map('open_filter_buffer')
    nnoremap <silent><buffer><expr> <Space>
    \ denite#do_map('toggle_select').'j'
endfunction

autocmd FileType denite-filter call s:denite_filter_my_settings()
function! s:denite_filter_my_settings() abort
    imap <silent><buffer> <C-o> <Plug>(denite_filter_quit)

endfunction

augroup KeepLastPosition
    au BufRead * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal g`\"" | endif
augroup END

if has('persistent_undo')
    set undodir=./.vimundo,~/.vimundo
    augroup SaveUndoFile
        autocmd!
        autocmd BufReadPre ~/* setlocal undofile
    augroup END
endif

if executable('rg')
    let &grepprg = 'rg --vimgrep --hidden'
    set grepformat=%f:%l:%c:%m
endif
