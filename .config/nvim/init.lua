vim.cmd('filetype indent off')

vim.opt.compatible = false

if vim.fn.has('mac') == 1 then
  vim.cmd('source $HOME/.config/nvim/mac.vim')
else
  vim.cmd('source $HOME/.config/nvim/linux.vim')
end

if vim.g.vscode then
  print('VSCode detected, disabling plugins')
else
  require('init')
end

vim.cmd('source $HOME/.config/nvim/color.vim')

vim.cmd('source $HOME/.config/nvim/keymappings.vim')

vim.cmd('source $HOME/.config/nvim/auto.vim')

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
vim.opt.backupdir = '~/.vim/backup'
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

vim.opt.completeopt:remove('preview')

if vim.fn.has('nvim') == 1 then
  vim.opt.pumblend = 50
  vim.opt.winblend = 50
end

vim.cmd('filetype indent on')
