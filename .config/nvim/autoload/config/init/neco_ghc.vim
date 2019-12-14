function config#init#neco_ghc#hook_add() abort
    " Disable haskell-vim omnifunc
    let g:haskellmode_completion_ghc = 0
    autocmd FileType haskell setlocal omnifunc=necoghc#omnifunc
endfunction
