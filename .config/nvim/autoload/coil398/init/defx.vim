function! coil398#init#defx#hook_add() abort
    nnoremap <silent> <Space>v :<C-u>Defx -split=vertical -winwidth=35 -direction=topleft<CR>
endfunction

function! coil398#init#defx#hook_source() abort
    " function! Root(path) abort
    "     return fnamemodify(a:path, ':t')
    " endfunction

    " call defx#custom#source('file', {
    "         \ 'root': 'Root',
    "         \ })
    " call defx#custom#column('mark', {
    "         \ 'readonly_icon': '✗',
    "         \ 'selected_icon': '✓',
    "         \ })
    " call defx#custom#column('icon', {
    "         \ 'directory_icon': '▸',
    "         \ 'opened_icon': '▾',
    "         \ 'root_icon': ' ',
    "         \ })
    call defx#custom#option('_', {
            \ 'columns': 'icons:indent:filename:type',
            \ })

    let g:defx_icons_enable_syntax_highlight = 1
    let g:defx_icons_column_length = 2
    let g:defx_icons_directory_icon = ''
    let g:defx_icons_mark_icon = '*'
    let g:defx_icons_parent_icon = ''
    let g:defx_icons_default_icon = ''
    let g:defx_icons_directory_symlink_icon = ''
    " Options below are applicable only when using "tree" feature
    " let g:defx_icons_root_opened_tree_icon = ''
    " let g:defx_icons_nested_opened_tree_icon = ''
    " let g:defx_icons_nested_closed_tree_icon = ''
endfunction
