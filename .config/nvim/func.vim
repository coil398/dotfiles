" automatic indent for inside ()
function! IndentForRoundBracket()
    let cursorChar = getline(",")[col(".")-1]
    let leftCursorChar = getline(".")[col(".")-2]

    if cursorChar == ")" && leftCursorChar == "("
        return "\n\t\n\<UP>\<RIGHT>"
    else
        return "\n"
    endif
endfunction


inoremap <silent> <expr> <CR> IndentForRoundBracket()
