function! coil398#init#denite#hook_add() abort
    " Prefix for denite
    nmap [denite] <Nop>
    map <Space>u [denite]

    " settings for grep
    nnoremap <silent> [denite]g :Denite grep -buffer-name=search-buffer-denite<CR>
    nnoremap <silent> [denite]r :Denite -resume -buffer-name=search-buffer-denite<CR>
    nnoremap <silent> [denite]n :Dnite -resume -buffer-name=search-buffer-denite -select=+1 -immediately<CR>
    nnoremap <silent> [denite]p :Dnite -resume -buffer-name=search-buffer-denite -select=-1 -immediately<CR>
endfunction

function! coil398#init#denite#hook_post_source() abort
    call denite#custom#var('file_rec', 'command', ['ag', '--follow', '--nocolor', '--nogroup', '-g', ''])
    call denite#custom#var('grep', 'command', ['ag'])
    call denite#custom#var('grep', 'recursive_opt', [])
    call denite#custom#var('grep', 'pattern_opt' [])
    call denite#custom#var('grep', 'default_opts', ['--follow', '--no-group', '--no-color'])
endfunction
