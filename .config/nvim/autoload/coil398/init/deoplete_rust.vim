" function coil398#init#deoplete_rust#hook_add() abort
"     let g:deoplete#sources#rust#racer_binary='/Users/takumi/.cargo/bin/racer'
"     let g:deoplete#sources#rust#rust_source_path='/Users/takumi/.rust/src'
"     let g:deoplete#sources#rust#show_duplicates=0
" endfunction

function coil398#init#deoplete_rust#hook_source() abort
    let l:home_dir = expand('~/')
    let g:deoplete#sources#rust#racer_binary=l:home_dir . '.cargo/bin/racer'
    let g:deoplete#sources#rust#rust_source_path=l:home_dir . '.rust/src'
    let g:deoplete#sources#rust#show_duplicates=0
endfunction
