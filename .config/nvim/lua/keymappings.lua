-- Set <Leader> to <Space>
vim.g.mapleader = " "

-- Mappings for the quickfix window
vim.keymap.set('n', '<Space>q', ':ccl<CR>')
vim.keymap.set('n', '<Space>w', ':botright cwindow<CR>')

vim.keymap.set('n', '<Space><Space>', 'i<Space><Esc>')

-- Mapping for ctags
vim.keymap.set('n', '<C-]>', 'g<C-]>')

vim.keymap.set('n', 'j', 'gj')
vim.keymap.set('n', 'k', 'gk')
vim.keymap.set('n', '<Down>', 'gj')
vim.keymap.set('n', '<Up>', 'gk')
vim.keymap.set('n', 'gj', 'j')
vim.keymap.set('n', 'gk', 'k')

-- Change the terminal mode to the normal mode
vim.keymap.set('t', '<ESC>', '<C-\\><C-n>', { silent = true })