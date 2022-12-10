" push quickfix window always to the bottom
autocmd FileType qf wincmd J

" for go lang
augroup go
    autocmd!
    autocmd FileType go :highlight goErr cterm=bold ctermfg=214
    autocmd FileType go :match goErr /\<err\>/
    autocmd BufWritePre *.go :silent call CocAction('runCommand', 'editor.action.organizeImport')
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

" for c
augroup c
    autocmd!
    autocmd FileType c :highlight ccoloncolon cterm=bold ctermfg=214
    autocmd FileType c :match ccoloncolon /\:\:/
    autocmd FileType c :setlocal tabstop=2
    autocmd FileType c :setlocal shiftwidth=2
augroup END

" for c++
augroup cpp
    autocmd!
    autocmd FileType cpp :highlight cppcoloncolon cterm=bold ctermfg=214
    autocmd FileType cpp :match cppcoloncolon /\:\:/
    autocmd FileType cpp :setlocal tabstop=2
    autocmd FileType cpp :setlocal shiftwidth=2
augroup END

augroup html
    autocmd!
    autocmd FileType html :setlocal tabstop=2
    autocmd FileType html :setlocal shiftwidth=2
augroup END

augroup javascript
    autocmd!
    autocmd FileType javascript :syn match Operator "\(|\|+\|=\|-\|\^\|\*\)"
    autocmd FileType javascript :syn match Delimiter "\(\.\|:\)"
    autocmd FileType javascript :hi link Operator Statement
    autocmd FileType javascript :hi link Delimiter Special
    autocmd FileType javascript :setlocal tabstop=2
    autocmd FileType javascript :setlocal shiftwidth=2
augroup END

augroup typescript
    autocmd!
    autocmd FileType typescript :syn match Operator "\(|\|+\|=\|-\|\^\|\*\)"
    autocmd FileType typescript :syn match Delimiter "\(\.\|:\)"
    autocmd FileType typescript :hi link Operator Statement
    autocmd FileType typescript :hi link Delimiter Special
    autocmd FileType typescript :setlocal tabstop=2
    autocmd FileType typescript :setlocal shiftwidth=2
augroup END

augroup typescriptreact
    autocmd!
    autocmd FileType typescriptreact :syn match Operator "\(|\|+\|=\|-\|\^\|\*\)"
    autocmd FileType typescriptreact :syn match Delimiter "\(\.\|:\)"
    autocmd FileType typescriptreact :hi link Operator Statement
    autocmd FileType typescriptreact :hi link Delimiter Special
    autocmd FileType typescriptreact :setlocal tabstop=2
    autocmd FileType typescriptreact :setlocal shiftwidth=2
augroup END

augroup vue
    autocmd!
    autocmd BufNewFile,BufRead *.vue :set filetype=vue
    autocmd FileType vue :syn match Operator "\(|\|+\|=\|-\|\^\|\*\)"
    autocmd FileType vue :syn match Delimiter "\(\.\|:\)"
    autocmd FileType vue :hi link Operator Statement
    autocmd FileType vue :hi link Delimiter Special
    autocmd FileType vue :setlocal tabstop=2
    autocmd FileType vue :setlocal shiftwidth=2
augroup END

augroup dart
    autocmd!
    autocmd FileType dart :setlocal tabstop=2
    autocmd FileType dart :setlocal shiftwidth=2
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

augroup terraform
    autocmd!
    autocmd FileType terraform :setlocal tabstop=2
    autocmd FileType terraform :setlocal shiftwidth=2
augroup END

augroup lua
    autocmd!
    autocmd FileType lua :setlocal tabstop=2
    autocmd FileType lua :setlocal shiftwidth=2
augroup END

augroup toml
    autocmd!
    autocmd BufNewFile,BufRead *.toml :set filetype=toml
    autocmd FileType toml :setlocal tabstop=2
    autocmd FileType toml :setlocal shiftwidth=2
augroup End

augroup sh
    autocmd!
    autocmd FileType sh :setlocal tabstop=2
    autocmd FileType sh :setlocal shiftwidth=2
augroup End

augroup make
    autocmd!
    autocmd FileType make :setlocal noexpandtab
augroup End

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
