function! coil398#init#vimshell#hook_add() abort

    " keymappings
    " start vimshell
    nnoremap <silent> [vimshell]s :VimShell<CR>
    nnoremap <silent> [vimshell]v :VimShellPop -toggle<CR>

endfunction
