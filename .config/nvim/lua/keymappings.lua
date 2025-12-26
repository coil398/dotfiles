-- Set <Leader> to <Space>
vim.g.mapleader = " "

-- Mappings for the quickfix window
local function toggle_quickfix()
  local qf_exists = false
  for _, win in pairs(vim.fn.getwininfo()) do
    if win.quickfix == 1 then
      qf_exists = true
    end
  end
  if qf_exists then
    vim.cmd('cclose')
  else
    vim.cmd('botright cwindow')
  end
end

vim.keymap.set('n', '<leader>q', toggle_quickfix, { desc = 'Toggle Quickfix' })
vim.keymap.set('n', '[q', ':cprev<CR>', { desc = 'Previous Quickfix Item' })
vim.keymap.set('n', ']q', ':cnext<CR>', { desc = 'Next Quickfix Item' })

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

vim.keymap.set('n', '<leader>fmt', ':Format<CR>', { desc = 'Format File' })

