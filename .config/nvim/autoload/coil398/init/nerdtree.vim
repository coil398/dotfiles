function! coil398#init#nerdtree#hook_add() abort
    nnoremap <silent> <Space>v :<C-u>NERDTreeToggle<CR>
endfunction

function! coil398#init#nerdtree#hook_source() abort
    let g:NERDTreeWinSize = 40
    let g:WebDevIconsUnicodeGlyphDoubleWidth = 0
    let g:WebDevIconsNerdTreeBeforeGlyphPadding = ''
    let g:WebDevIconsNerdTreeAfterGlyphPadding = '  '
    let g:WebDevIconsUnicodeDecorateFolderNodes = 0
endfunction
