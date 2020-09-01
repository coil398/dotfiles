function! config#init#fern#hook_add() abort
    nnoremap <silent> <Space>v :<C-u>Fern . -drawer -width=35<CR>
endfunction

function! config#init#fern#hook_source() abort
    let g:fern#renderer = "nerdfont"
endfunction
