function! coil398#init#vimfiler#hook_add() abort
    " nnoremap <silent> <Space>v :<C-u>VimFiler -invisible<CR>
    nnoremap <silent> <Space>v :<C-u>VimFiler -simple -split -winwidth=30 -no-quit<CR>
endfunction

function! coil398#init#vimfiler#hook_source() abort
    let g:vimfiler_as_default_explorer=1
    let g:vimfiler_safe_mode_by_default=0
endfunction
