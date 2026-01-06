vim.cmd('filetype indent off')

vim.opt.compatible = false

if vim.fn.has('mac') == 1 then
  require('mac')
else
  require('linux')
end

if vim.g.vscode then
  print('VSCode detected, disabling plugins')
else
  require('init')
end

require('color')

require('keymappings')

require('auto')

vim.opt.tabstop = 4
vim.opt.expandtab = true
vim.opt.shiftwidth = 4

vim.opt.number = true
vim.opt.title = true
vim.opt.ambiwidth = 'double'
vim.opt.list = true
vim.opt.listchars = 'tab:»-,trail:-,extends:»,precedes:«,nbsp:%'
vim.opt.nrformats:remove('octal')
vim.opt.hidden = true
vim.opt.history = 200
vim.opt.virtualedit = 'block'
vim.opt.whichwrap:append('b,s,h,l,[,],<,>')
vim.opt.backspace = { 'indent', 'eol', 'start' }
vim.opt.wildmenu = true
vim.opt.backup = false
local backup_dir = vim.fn.expand('~/.vim/backup')
if vim.fn.isdirectory(backup_dir) == 0 then
  vim.fn.mkdir(backup_dir, 'p')
end
vim.opt.backupdir = backup_dir
vim.opt.swapfile = false
vim.opt.autoread = true
vim.opt.showcmd = true
vim.opt.cursorline = true
vim.opt.visualbell = true
vim.opt.laststatus = 3
vim.opt.wrapscan = true
vim.opt.modeline = true
vim.opt.autowrite = true
vim.opt.display = 'lastline'
vim.opt.matchpairs:append('<:>')
vim.opt.matchtime = 1
vim.opt.showtabline = 2
vim.opt.wildmenu = true
vim.opt.wildignore = '*.o,*.obj,*.pyc,*.so,*.dll'
vim.opt.mouse = 'a'
vim.opt.updatetime = 100

vim.opt.showmatch = true
vim.opt.smartcase = true
vim.opt.ignorecase = true
vim.opt.infercase = true
vim.opt.hlsearch = true
vim.opt.incsearch = true

vim.opt.foldmethod = 'marker'
vim.opt.foldlevel = 0
vim.opt.foldcolumn = '1'

vim.opt.termguicolors = true
vim.opt.signcolumn = 'yes'

vim.opt.completeopt:remove('preview')

vim.opt.ambiwidth = "single"

if vim.fn.has('nvim') == 1 then
  vim.opt.pumblend = 10
  vim.opt.winblend = 10
end

vim.cmd('filetype indent on')
