" set <Leader> to <Space>
let mapleader = "\<Space>"

" mappings for plugins
nmap [denite] <Nop>
map <Space>u [denite]
nmap [gtags] <Nop>
map <Space>t [gtags]
nmap [vimshell] <Nop>
map <Space>s [vimshell]

" mappings for the quickfix window
nnoremap <Space>n :cn<CR>
nnoremap <Space>p :cp<CR>
nnoremap <Space>e :ccl<CR>
