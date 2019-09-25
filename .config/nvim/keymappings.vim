" set <Leader> to <Space>
let mapleader = "\<Space>"

" mappings for plugins
nmap [denite] <Nop>
map <Space>u [denite]

" mappings for the quickfix window
nnoremap <Space>n :cn<CR>
nnoremap <Space>p :cp<CR>
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

nnoremap <C-6> :b #

" change the terminal mode to the normal mode.
tnoremap <silent> <ESC> <C-\><C-n>

autocmd FileType go nmap [vim-go] <Nop>
autocmd FileType go nmap <leader>g [vim-go]

autocmd FileType go nmap [vim-go]t <Plug>(go-test)

function! s:build_go_files()
    let l:file = expand('%')
    if l:file =~# '^\f\+_test\.go$'
        call go#test#Test(0, 1)
    elseif l:file =~# '^\f\+\.go$'
        call go#cmd#Build(0)
    endif
endfunction

autocmd FileType go nmap [vim-go]b :<C-u>call <SID>build_go_files()<CR>

autocmd FileType go nmap [vim-go]c <Plug>(go-coverage-toggle)
