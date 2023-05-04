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

  use { 'vim-denops/denops.vim', opt = true }

  use { 'tomasiser/vim-code-dark' }

  use { 'luochen1990/rainbow', config = function() vim.fn['config#rainbow#init']() end, opt = true }

  use {
    'zbirenbaum/copilot.lua',
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
    end,
    opt = true,
    cmd = { 'Copilot' },
    event = 'InsertEnter'
  }

  use {
    'nvim-telescope/telescope.nvim',
    tag = '0.1.1',
    config = function()
      local builtin = require('telescope.builtin')
      vim.keymap.set('n', '<leader>ff', builtin.find_files, {})
      vim.keymap.set('n', '<leader>fg', builtin.live_grep, {})
      vim.keymap.set('n', '<leader>fb', builtin.buffers, {})
      vim.keymap.set('n', '<leader>fn', builtin.help_tags, {})

      local telescope = require('telescope')

      local actions = require 'telescope.actions'
      local fb_actions = require 'telescope._extensions.file_browser.actions'

      telescope.setup {
        defaults = {
          file_ignore_patterns = {
            '^.git/',
            '^node_modules/'
          },
          winblend = 4,
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
          },
          coc = {
            prefer_locations = true
          }
        }
      }

      telescope.load_extension('file_browser')
      telescope.load_extension('coc')
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
    'fannheyward/telescope-coc.nvim',
    config = function()
      vim.keymap.set('n', 'gd', '<cmd>Telescope coc definitions<CR>', { silent = true })
      vim.keymap.set('n', 'gy', '<cmd>Telescope coc type_definitions<CR>', { silent = true })
      vim.keymap.set('n', 'gi', '<cmd>Telescope coc implementations<CR>', { silent = true })
      vim.keymap.set('n', 'gr', '<cmd>Telescope coc references<CR>', { silent = true })
      vim.keymap.set('n', '<space>a', '<cmd>Telescope coc diagnostics<CR>', { silent = true })
      vim.keymap.set('n', '<space>c', '<cmd>Telescope coc commands<CR>', { silent = true })
      vim.keymap.set('n', '<space>s', '<cmd>Telescope coc workspace_symbols<CR>', { silent = true })
    end,
    requires = { 'nvim-telescope/telescope.nvim' }
  }

  use {
    'akinsho/bufferline.nvim',
    config = function()
      vim.opt.termguicolors = true
      require('bufferline').setup {}
    end,
    requires = { 'nvim-tree/nvim-web-devicons' }
  }

  use {
    'nvim-lua/plenary.nvim'
  }

  use {
    'TimUntersberger/neogit',
    requires = { 'nvim-lua/plenary.nvim' },
    opt = true,
    cmd = { 'Neogit' }
  }

  use {
    'lewis6991/gitsigns.nvim',
    config = function()
      require('gitsigns').setup()
    end,
    opt = true
  }

  use {
    'folke/noice.nvim',
    config = function()
      require('noice').setup({
        lsp = {
          override = {
            ["vim.lsp.util.convert_input_to_markdown_lines"] = true,
            ["vim.lsp.util.stylize_markdown"] = true,
            ["cmp.entry.get_documentation"] = true,
          },
        },
        presets = {
          bottom_search = true,
          command_palette = false,
          long_message_to_split = true,
          inc_rename = false,
          lsp_doc_border = false
        }
      })
    end,
    requires = { 'MunifTanjim/nui.nvim', 'rcarriga/nvim-notify' }
  }

  use {
    'stevearc/aerial.nvim',
    requires = { 'nvim-tree/nvim-web-devicons' },
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

  use { 'rust-lang/rust.vim', opt = true, ft = { 'rust' } }

  use { 'vimjas/vim-python-pep8-indent', opt = true, ft = { 'python' } }

  use { 'fatih/vim-go', opt = true, ft = { 'go' } }

  use { 'neovimhaskell/haskell-vim', opt = true, ft = { 'haskell' } }
end

local plugins = setmetatable({}, {
  __index = function(_, key)
    init()
    return packer[key]
  end
})

return plugins
