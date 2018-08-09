function! coil398#init#ale#hook_add() abort
    highlight clear ALEError
    highlight clear ALEWarning
    let g:ale_lint_on_enter = 0
    let g:ale_sign_column_always = 1
    let g:ale_set_loclist = 0
    let g:ale_set_quickfix = 1
    "let g:ale_open_list = 1
    "let g:ale_keep_list_window_open = 1
endfunction
