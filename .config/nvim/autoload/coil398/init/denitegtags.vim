function! coil398#init#denitegtags#hook_add() abort
    nnoremap [gtags]a :DeniteCursorWord -buffer-name=gtags_context gtags_context<cr>
    nnoremap [gtags]d :DeniteCursorWord -buffer-name=gtags_def gtags_def<cr>
    nnoremap [gtags]r :DeniteCursorWord -buffer-name=gtags_ref gtags_ref<cr>
    nnoremap [gtags]g :DeniteCursorWord -buffer-name=gtags_grep gtags_grep<cr>
    nnoremap [gtags]t :Denite -buffer-name=gtags_completion gtags_completion<cr>
    nnoremap [gtags]f :Denite -buffer-name=gtags_file gtags_file<cr>
    nnoremap [gtags]p :Denite -buffer-name=gtags_path gtags_path<cr>
endfunction
