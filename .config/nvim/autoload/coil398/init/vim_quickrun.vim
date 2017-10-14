function! coil398#init#vim_quickrun#hook_add() abort
    let g:quickrun_config = {
        \ '_' : {
            \ 'runner' : 'vimproc',
            \ 'runner/vimproc/updatetime' : 40,
            \ 'outputter' : 'error',
            \ 'outputter/error/success' : 'buffer',
            \ 'hook/close_buffer/enable_failure': 1,
            \ 'outputter/error/error'   : 'quickfix',
            \ 'outputter/close_quickfix/enable_success': 1,
            \ 'outputter/buffer/split' : ':botright 8sp',
            \ 'outputter/buffer/close_on_empty': 1,
        \ }
    \}

    " 実行時に前回の表示内容をクローズ&保存してから実行
    let g:quickrun_no_default_key_mappings = 1
    nmap <Space>q :<C-u>cclose<CR>:write<CR>:QuickRun -mode n<CR>
endfunction
