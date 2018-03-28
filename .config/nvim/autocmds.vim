augroup tags
    autocmd!
    autocmd BufWritePost * call coil398#init#functions#gen_tags()
augroup END
