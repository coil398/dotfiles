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
