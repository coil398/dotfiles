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
