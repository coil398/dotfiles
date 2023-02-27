function! config#copilot#init() abort
    imap <silent><script><expr> <C-J> copilot#Accept("\<CR>")
    let g:copilot_no_tab_map = v:true
endfunction
