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

nnoremap j gj
nnoremap k gk
nnoremap <Down> gj
nnoremap <Up> gk
nnoremap gj j
nnoremap gk k

" change the terminal mode to the normal mode.
tnoremap <silent> <ESC> <C-\><C-n>
