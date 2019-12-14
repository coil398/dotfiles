function! config#init#lightline#hook_add() abort
    let g:lightline = {
      \ 'colorscheme': 'wombat',
      \ 'active': {
      \     'left': [['mode', 'paste'],
      \              ['gitbranch', 'readonly', 'filename', 'modified']],
      \     'right': [['lineinfo'], ['percent'], ['fileformat', 'fileencoding', 'filetype'],
      \              ['cocstatus', 'currentfunction']]
      \ },
      \ 'component_function': {
      \     'gitbranch': 'gina#component#repo#branch',
      \     'mode': 'LightlineMode',
      \     'cocstatus': 'coc#status',
      \     'currentfunction': 'CocCurrentFunction'
      \ }
      \ }
endfunction

function! LightlineMode()
    return &ft == 'denite' ? 'Denite' :
      \    &ft == 'vimfiler' ? 'VimFiler' :
      \    winwidth(0) > 60 ? lightline#mode() : ''
endfunction

function! CocCurrentFunction()
    return get(b:, 'coc_current_function', '')
endfunction
