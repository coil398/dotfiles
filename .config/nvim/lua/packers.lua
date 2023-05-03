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
          auto_trigger = true,
          keymap = {
            accept = "<C-J>"
          },
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

      local actions = require 'telescope.actions'
      local fb_actions = require 'telescope._extensions.file_browser.actions'

      require('telescope').setup {
        defaults = {
          initial_mode = 'normal',
          mappings = {
            i = {
              ["<C-j>"] = actions.move_selection_next,
              ["<C-k>"] = actions.move_selection_previous,
              ["<Tab>"] = actions.toggle_selection + actions.move_selection_better,
              ["<S-Tab>"] = actions.toggle_selection + actions.move_selection_worse
            }
          }
        },
        extensions = {
          file_browser = {
            hijack_netrw = true
          }
        }
      }

      require('telescope').load_extension 'file_browser'
    end,
    requires = { 'nvim-lua/plenary.nvim', 'nvim-tree/nvim-web-devicons' },
  }

  use {
    'nvim-telescope/telescope-file-browser.nvim',
    config = function()
      vim.keymap.set('n', '<C-p>', ':Telescope file_browser path=%:p:h select_buffer=true<CR>',
        { noremap = true })
    end,
    requires = { 'nvim-telescope/telescope.nvim', 'nvim-lua/plenary.nvim', 'nvim-tree/nvim-web-devicons' }
  }

  use {
    'akinsho/bufferline.nvim',
    config = function()
      vim.opt.termguicolors = true
      require('bufferline').setup {}
    end,
    requires = { { 'nvim-tree/nvim-web-devicons' } }
  }

  use {
    'lewis6991/gitsigns.nvim',
    config = function()
      require('gitsigns').setup()
    end
  }

  use {
    'stevearc/aerial.nvim',
    requires = { { 'nvim-tree/nvim-web-devicons' } },
    config = function()
      vim.keymap.set('n', '<space>o', '<cmd>AerialToggle!<CR>', { noremap = true })
      require('aerial').setup({
        nerd_font = 'auto',
        show_guides = true,
        layout = {
          default_direction = 'float',
          placement = 'edge'
        },
        float = {
          border = 'rounded',
          relative = 'win',
          max_height = 0.9,
          height = nil,
          min_height = { 8, 0.1 },
          override = function(conf, source_winid)
            conf.anchor = 'NE'
            conf.row = 0
            conf.col = vim.fn.winwidth(source_winid)
            return conf
          end
        }
      })
    end
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
