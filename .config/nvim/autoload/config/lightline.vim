function! config#lightline#init() abort
    let g:lightline = {
      \ 'colorscheme': 'wombat',
      \ 'active': {
      \     'left': [['mode', 'paste'],
      \              ['gitbranch', 'readonly', 'filename', 'modified']],
      \     'right': [['lineinfo'], ['percent'], ['fileformat', 'fileencoding', 'filetype'],
      \              ['cocstatus', 'currentfunction']]
      \ },
      \ 'component_function': {
      \     'gitbranch': 'gitbranch#name',
      \     'cocstatus': 'coc#status',
      \     'currentfunction': 'CocCurrentFunction'
      \ }
      \ }
endfunction

function! CocCurrentFunction()
    return get(b:, 'coc_current_function', '')
endfunction
