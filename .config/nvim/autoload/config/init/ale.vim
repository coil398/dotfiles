function! config#init#ale#hook_add() abort
    highlight clear ALEError
    highlight clear ALEWarning
    let g:ale_lint_on_enter = 0
    let g:ale_sign_column_always = 1
    let g:ale_set_loclist = 0
    let g:ale_set_quickfix = 1
    "let g:ale_open_list = 1
    "let g:ale_keep_list_window_open = 1
    if has('mac')
        let s:header_path = '-I/Library/Developer/CommandLineTools/SDKs/MacOSX10.15.sdk/usr/include'
        let g:ale_cpp_clang_options = '-std=c++14 -Wall ' . s:header_path
        let g:ale_cpp_gcc_options = '-std=c++14 -Wall ' . s:header_path
    endif
    let g:ale_linters = {
                \ 'c': ['clangd'],
                \ 'cpp' : ['clangd']
                \ }
endfunction
