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

  use {
    'nvim-lualine/lualine.nvim',
    requires = { 'nvim-tree/nvim-web-devicons' },
    config = function()
      require('lualine').setup({
        options = {
          theme = 'codedark'
        }
      })
    end
  }

  use { 'ctrlpvim/ctrlp.vim', config = function() vim.fn['config#ctrlp#init']() end }

  use { 'nvim-treesitter/nvim-treesitter', run = ':TSUpdate', config = function() vim.fn['config#nvim_treesitter#init']() end }

  use { 'vim-denops/denops.vim' }

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
          layout = {
            position = "right",
            ratio = 0.4
          }
        },
        suggestion = {
          auto_trigger = true
        },
        filetypes = {},
      })
    end
  }

  use { 'nvim-lua/plenary.nvim' }

  use {
    'nvim-telescope/telescope.nvim',
    tag = '0.1.1',
    config = function()
      local builtin = require('telescope.builtin')
      vim.keymap.set('n', '<leader>ff', builtin.find_files, {})
      vim.keymap.set('n', '<leader>fg', builtin.live_grep, {})
      vim.keymap.set('n', '<leader>fb', builtin.buffers, {})
      vim.keymap.set('n', '<leader>fn', builtin.help_tags, {})
    end,
    requires = { { 'nvim-lua/plenary.nvim' } },
  }

  use {
    'akinsho/bufferline.nvim',
    requires = { { 'nvim-tree/nvim-web-devicons' } }
  }

  use { 'rust-lang/rust.vim', ft = { 'rust' } }

  use { 'vimjas/vim-python-pep8-indent', ft = { 'python' } }

  use { 'fatih/vim-go', ft = { 'go' } }

  use { 'neovimhaskell/haskell-vim', ft = { 'haskell' } }
end

local plugins = setmetatable({}, {
  __index = function(_, key)
    init()
    return packer[key]
  end
})

return plugins
