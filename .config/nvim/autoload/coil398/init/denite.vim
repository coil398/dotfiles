function! coil398#init#denite#hook_add() abort
    " defined in keymappings.vim
    " Prefix for denite
    " nmap [denite] <Nop>
    " map <Space>u [denite]

    " key mappings for Denite and sources
    nnoremap <silent> [denite]y :<C-u>Denite neoyank<CR>
    nnoremap <silent> [denite]u :<C-u>Denite buffer file_rec<CR>
    nnoremap <silent> [denite]f :<C-u>Denite file_rec<CR>
    nnoremap <silent> [denite]b :<C-u>Denite buffer<CR>
    nnoremap <silent> [denite]m :<C-u>Denite file_mru<CR>
    nnoremap <silent> [denite]a :<C-u>Denite -resume<CR>

    " settings for grep
    nnoremap <silent> [denite]g :<C-u>Denite grep -buffer-name=search-buffer-denite<CR>
    nnoremap <silent> [denite]w :<C-u>DeniteCursorWord grep -buffer-name=search-buffer-denite<CR>
    nnoremap <silent> [denite]r :<C-u>Denite -resume -buffer-name=search-buffer-denite<CR>
    nnoremap <silent> [denite]n :<C-u>Denite -resume -buffer-name=search-buffer-denite -select=+1 -immediately<CR>
    nnoremap <silent> [denite]p :<C-u>Denite -resume -buffer-name=search-buffer-denite -select=-1 -immediately<CR>
endfunction

function! coil398#init#denite#hook_post_source() abort
    " Change the prompt
    call denite#custom#option('default', 'prompt', '>')

    " Add action keybinds
    call denite#custom#map('insert', '<C-v>', '<denite:do_action:vsplit>')
    call denite#custom#map('insert', '<C-s>', '<denite:do_action:split>')
    call denite#custom#map('normal', '<C-v>', '<denite:do_action:vsplit>')
    call denite#custom#map('normal', '<C-s>', '<denite:do_action:split>')

    call denite#custom#map('insert', '<C-n>', '<denite:move_to_next_line>')
    call denite#custom#map('insert', '<C-p>', '<denite:move_to_previous_line>')
    call denite#custom#map('normal', '<C-n>', '<denite:move_to_next_line>')
    call denite#custom#map('normal', '<C-p>', '<denite:move_to_previous_line>')

    " Variables
    "grepでagを使用するように設定
    call denite#custom#var('grep', 'command', ['ag'])
    "カレントディレクトリ内の検索もagを使用する
    call denite#custom#var('file_rec', 'command', ['ag', '--follow', '--nocolor', '--nogroup', '-g', ''])
    "その他のgrepの設定
    call denite#custom#var('grep', 'default_opts',['-i', '--vimgrep'])
    call denite#custom#var('grep', 'recursive_opts', [])
    call denite#custom#var('grep', 'pattern_opt', [])
    call denite#custom#var('grep', 'separator', ['--'])
    call denite#custom#var('grep', 'final_opts', [])
endfunction
