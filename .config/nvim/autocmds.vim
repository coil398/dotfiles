" function Gen2Tags()
"     execute(":GenCtags")
"     execute(":GenGTAGS")
" endfunction
" 
" augroup tags
"     autocmd!
"     autocmd BufWritePost * call Gen2Tags()
" augroup END
