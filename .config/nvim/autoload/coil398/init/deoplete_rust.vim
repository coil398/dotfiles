function coil398#init#deoplete_rust#hook_source() abort
    let g:deoplete#sources#rust#racer_binary='~/.cargo/bin/racer'
    let g:deoplete#sources#rust#rust_source_path='~/.rust/src'
    let g:deoplete#sources#rust#show_duplicates=1
endfunction
