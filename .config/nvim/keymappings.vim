" set <Leader> to <Space>
let mapleader = "\<Space>"

" mappings for plugins
nmap [denite] <Nop>
map <Space>u [denite]
nmap [gtags] <Nop>
map <Space>t [gtags]

" mappings for the quickfix window
nnoremap <Space>n :cn<CR>
nnoremap <Space>p :cp<CR>
nnoremap <Space>e :ccl<CR>
nnoremap <Space>w :botright cwindow<CR>

nnoremap <Space><Space> i<Space><Esc>

nnoremap <Space>s :SrcExplToggle

" mapping for ctags
nnoremap <C-]> g<C-]>

" mapping to launch deoplete for temporary
" nnoremap <Space>c :call deoplete#enable()<CR>
"
" mapping for gen_tags
nnoremap <silent> <Space>x :call coil398#init#functions#gen_tags()<CR>
