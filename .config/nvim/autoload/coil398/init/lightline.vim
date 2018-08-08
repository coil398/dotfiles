function! coil398#init#lightline#hook_add() abort
    let g:lightline = {
      \ 'colorscheme': 'wombat',
      \ 'active': {
      \     'left': [['mode', 'paste'],
      \              ['gitbranch', 'readonly', 'filename', 'modified', 'linter_checking', 'linter_errors', 'linter_warnings', 'linter_ok']]
      \ },
      \ 'component_function': {
      \     'gitbranch': 'fugitive#head',
      \     'mode': 'LightlineMode'
      \ },
      \ }
    let g:lightline.component_expand = {
      \ 'linter_checking' : 'lightline#ale#checking',
      \ 'linter_warnings' : 'lightline#ale#warnings',
      \ 'linter_errors' : 'lightline#ale#errors',
      \ 'linter_ok' : 'lightline#ale#ok',
      \ }
    let g:lightline.component_type = {
      \ 'linter_checking' : 'left',
      \ 'linter_warnings' : 'warning',
      \ 'linter_errors' : 'error',
      \ 'linter_ok' : 'left',
      \ }
endfunction

function! LightlineMode()
    return &ft == 'denite' ? 'Denite' :
      \    &ft == 'vimfiler' ? 'VimFiler' :
      \    winwidth(0) > 60 ? lightline#mode() : ''
endfunction
