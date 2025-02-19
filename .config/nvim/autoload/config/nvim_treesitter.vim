function! config#nvim_treesitter#init() abort

lua <<EOF
require'nvim-treesitter.configs'.setup {
  ensure_installed = 'all',

  highlight = {
    enable = true,
    additional_vim_regex_highlighting = false,
  },
}
EOF

endfunction
