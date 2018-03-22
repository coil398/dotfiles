function Gen2Tags() abort
    GenCtags
    GenGTAGS
endfunction

augroup tags
    autocmd!
    autocmd BufWritePost * call Gen2Tags()
augroup END
