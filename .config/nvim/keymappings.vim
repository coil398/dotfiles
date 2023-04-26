" set <Leader> to <Space>
let mapleader = "\<Space>"

" mappings for the quickfix window
nnoremap <Space>n :cnext<CR>
nnoremap <Space>p :cprev<CR>
nnoremap <Space>q :ccl<CR>
nnoremap <Space>w :botright cwindow<CR>

nnoremap <Space><Space> i<Space><Esc>

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
