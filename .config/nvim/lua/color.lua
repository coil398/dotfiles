-- True color support
vim.opt.termguicolors = true

-- Try to set colorscheme
local ok, _ = pcall(vim.cmd, 'colorscheme vscode')
if not ok then
  vim.cmd('colorscheme default')
end

-- Highlight configurations
vim.cmd([[
  hi Folded ctermbg=0 ctermfg=2
  hi FoldColumn ctermbg=8 ctermfg=2

  hi Pmenu ctermfg=15 ctermbg=0
  hi PmenuSel ctermfg=0 ctermbg=15
  hi PMenuSbar ctermfg=15 ctermbg=0

  hi Search ctermbg=lightyellow
  hi Search ctermfg=black
  hi CursorColumn ctermbg=lightyellow
  hi CursorColumn ctermfg=black
  hi SpellBad ctermfg=black
  hi SpellRare ctermfg=black
  highlight CopilotSuggestion ctermfg=15
]])

vim.api.nvim_create_autocmd('FileType', {
  pattern = '*',
  callback = function(args)
    local ft = vim.bo[args.buf].filetype
    if vim.treesitter.language.add(ft) then
      vim.treesitter.start(args.buf, ft)
      vim.bo[args.buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
    end
  end,
})
