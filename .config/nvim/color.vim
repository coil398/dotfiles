set background=dark
set t_8f=^[[38;2;%lu;%lu;%lum
set t_8b=^[[48;2;%lu;%lu;%lum
colorscheme default

" syntax highlight
if has('syntax')
    syntax enable
endif

" hi fold'
hi Folded ctermbg=0 ctermfg=2
hi FoldColumn ctermbg=8 ctermfg=2

" hi popup 
hi Pmenu ctermfg=15 ctermbg=0
hi PmenuSel ctermfg=0 ctermbg=15
hi PMenuSbar ctermfg=15 ctermbg=0
