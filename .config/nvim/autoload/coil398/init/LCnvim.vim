function! coil398#init#LCnvim#hook_source() abort
    let g:LanguageClient_diagnosticsEnable = 0

    let g:LanguageClient_serverCommands = {
    \ 'python' : ['pyls']
    \ }
endfunction
