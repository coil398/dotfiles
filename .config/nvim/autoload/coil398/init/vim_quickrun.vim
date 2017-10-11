function! coil398#init#vim_quickrun#hook_add() abort
    let g:quickrun_config = {
        \ '_' : {
            \ 'runner' : 'vimproc',
            \ 'runner/vimproc/updatetime' : 40,
            \ 'outputter' : 'error',
            \ 'outputter/error/success' : 'buffer',
            \ 'outputter/error/error'   : 'quickfix',
            \ 'outputter/buffer/split' : ':botright 8sp',
        \ }
    \}

    " 実行時に前回の表示内容をクローズ&保存してから実行
    let g:quickrun_no_default_key_mappings = 1
    nmap <Space>q :cclose<CR>:write<CR>:QuickRun -mode n<CR>
endfunction
