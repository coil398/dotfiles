function! coil398#init#vim_lsp#hook_source() abort
    if executable('gopls')
        au User lsp_setup call lsp#register_server({
            \ 'name': 'gopls',
            \ 'cmd': {server_info->['gopls', '-mode', 'stdio']},
            \ 'whitelist': ['go'],
            \ })
    endif
    if executable('pyls')
        au User lsp_setup call lsp#register_server({
            \ 'name': 'pyls',
            \ 'cmd': {server_info->['pyls']},
            \ 'whitelist': ['python'],
            \ })
    endif
    if executable('pyls')
        au User lsp_setup call lsp#register_server({
            \ 'name': 'pyls',
            \ 'cmd': {server_info->['pyls']},
            \ 'whitelist': ['python'],
            \ })
    endif
    if executable('clangd')
        au User lsp_setup call lsp#register_server({
            \ 'name': 'clangd',
            \ 'cmd': {server_info->['clangd', '-background-index']},
            \ 'whitelist': ['c', 'cpp', 'objc', 'objcpp'],
            \ })
    endif
endfunction
