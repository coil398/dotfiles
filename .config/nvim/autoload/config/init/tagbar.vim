function! config#init#tagbar#hook_add() abort
    let g:tagbar_width=40
    nmap <Space>z :TagbarToggle<CR>
endfunction

function! config#init#tagbar#hook_source() abort
    let g:tagbar_type_go = {
	\ 'ctagstype' : 'go',
	\ 'kinds'     : [
		\ 'p:package',
		\ 'i:imports:1',
		\ 'c:constants',
		\ 'v:variables',
		\ 't:types',
		\ 'n:interfaces',
		\ 'w:fields',
		\ 'e:embedded',
		\ 'm:methods',
		\ 'r:constructor',
		\ 'f:functions'
	\ ],
	\ 'sro' : '.',
	\ 'kind2scope' : {
		\ 't' : 'ctype',
		\ 'n' : 'ntype'
	\ },
	\ 'scope2kind' : {
		\ 'ctype' : 't',
		\ 'ntype' : 'n'
	\ },
	\ 'ctagsbin'  : 'gotags',
	\ 'ctagsargs' : '-sort -silent'
    \ }
    let g:tagbar_type_typescript = {                                                  
      \ 'ctagsbin' : 'ctags',                                                        
      \ 'kinds': [                                                                     
        \ 'e:enums:0:1',                                                               
        \ 'f:function:0:1',                                                            
        \ 't:typealias:0:1',                                                           
        \ 'M:Module:0:1',                                                              
        \ 'I:import:0:1',                                                              
        \ 'i:interface:0:1',                                                           
        \ 'C:class:0:1',                                                               
        \ 'm:method:0:1',                                                              
        \ 'p:property:0:1',                                                            
        \ 'v:variable:0:1',                                                            
        \ 'c:const:0:1',                                                              
      \ ],                                                                            
      \ 'sort' : 0                                                                    
    \ }                   
endfunction
