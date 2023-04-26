local packer = nil
local function init()
  if packer == nil then
    packer = require('packer')
    packer.init {
      display = {
        open_fn = require("packer.util").float,
      },
    }
  end

  local use = packer.use
  packer.reset()

  use { 'wbthomason/packer.nvim' }
  use { 'neoclide/coc.nvim', branch = 'release', config = function() vim.fn['config#coc#init']() end }
  use { 'itchyny/lightline.vim', config = function() vim.fn['config#lightline#init']() end }
  use { 'itchyny/vim-gitbranch' }

  use { 'ctrlpvim/ctrlp.vim', config = function() vim.fn['config#ctrlp#init']() end }

  use { 'nvim-treesitter/nvim-treesitter', run = ':TSUpdate', config = function() vim.fn['config#nvim_treesitter#init']() end }

  use { 'vim-denops/denops.vim' }

  -- use { 'github/copilot.vim', config = function() vim.fn['config#copilot#init']() end }

  use { 'tomasiser/vim-code-dark' }

  use { 'luochen1990/rainbow', config = function() vim.fn['config#rainbow#init']() end }

  use {
    'zbirenbaum/copilot.lua',
    cmd = 'Copilot',
    event = 'InsertEnter',
    config = function()
      require('copilot').setup({
        panel = {
          auto_refresh = true,
        },
        suggestion = {
          auto_trigger = true,
          keymap = {
            accept = "<C-J>"
          },
        },
        filetypes = {},
      })
    end
  }

  use { "rust-lang/rust.vim" }

end

local plugins = setmetatable({}, {
  __index = function(_, key)
    init()
    return packer[key]
  end
})

return plugins
