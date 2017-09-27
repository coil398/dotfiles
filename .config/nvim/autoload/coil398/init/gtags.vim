function! coil398#init#gtags#hook_add() abort
    nnoremap <silent> <Space>f :Gtags -f %<CR>
    nnoremap <silent> <Space>j :GtagsCursor<CR>
    nnoremap <silent> <Space>d :<C-u>exe('Gtags '.expand('<cword>'))<CR>
    nnoremap <silent> <Space>r :<C-u>exe('Gtags -r '.expand('<cword>'))<CR>
endfunction
