function! coil398#init#lightline#hook_add() abort
    let g:lightline = {
      \ 'colorscheme': 'wombat',
      \ 'active': {
      \     'left': [['mode', 'paste'],
      \              ['gitbranch', 'readonly', 'filename', 'modified']]
      \ },
      \ 'component_function': {
      \     'gitbranch': 'fugitive#head',
      \     'mode': 'LightlineMode'
      \ }
      \ }
endfunction

function! LightlineMode()
    return &ft == 'denite' ? 'Denite' :
      \    &ft == 'vimfiler' ? 'VimFiler' :
      \    winwidth(0) > 60 ? lightline#mode() : ''
endfunction
