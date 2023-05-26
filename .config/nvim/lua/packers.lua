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

  use { 'folke/tokyonight.nvim' }

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
      -- vim.keymap.set('n', '<leader>fb', builtin.buffers, {})
      vim.keymap.set('n', '<leader>fn', builtin.help_tags, {})
      vim.keymap.set('n', '<leader>t', ':Telescope ', {})

      local actions = require 'telescope.actions'
      local fb_actions = require 'telescope._extensions.file_browser.actions'

      require('telescope').setup {
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
          },
          media_files = {
            find_cmd = 'rg'
          },
          command_palette = {
            { "File",
              { "entire selection (C-a)",  ':call feedkeys("GVgg")' },
              { "save current file (C-s)", ':w' },
              { "save all files (C-A-s)",  ':wa' },
              { "quit (C-q)",              ':qa' },
              { "file browser (C-i)",      ":lua require'telescope'.extensions.file_browser.file_browser()", 1 },
              { "search word (A-w)",       ":lua require('telescope.builtin').live_grep()",                  1 },
              { "git files (A-f)",         ":lua require('telescope.builtin').git_files()",                  1 },
              { "files (C-f)",             ":lua require('telescope.builtin').find_files()",                 1 },
            },
            { "Help",
              { "tips",            ":help tips" },
              { "cheatsheet",      ":help index" },
              { "tutorial",        ":help tutor" },
              { "summary",         ":help summary" },
              { "quick reference", ":help quickref" },
              { "search help(F1)", ":lua require('telescope.builtin').help_tags()", 1 },
            },
            { "Vim",
              { "reload vimrc",              ":source $MYVIMRC" },
              { 'check health',              ":checkhealth" },
              { "jumps (Alt-j)",             ":lua require('telescope.builtin').jumplist()" },
              { "commands",                  ":lua require('telescope.builtin').commands()" },
              { "command history",           ":lua require('telescope.builtin').command_history()" },
              { "registers (A-e)",           ":lua require('telescope.builtin').registers()" },
              { "colorshceme",               ":lua require('telescope.builtin').colorscheme()",    1 },
              { "vim options",               ":lua require('telescope.builtin').vim_options()" },
              { "keymaps",                   ":lua require('telescope.builtin').keymaps()" },
              { "buffers",                   ":Telescope buffers" },
              { "search history (C-h)",      ":lua require('telescope.builtin').search_history()" },
              { "paste mode",                ':set paste!' },
              { 'cursor line',               ':set cursorline!' },
              { 'cursor column',             ':set cursorcolumn!' },
              { "spell checker",             ':set spell!' },
              { "relative number",           ':set relativenumber!' },
              { "search highlighting (F12)", ':set hlsearch!' },
            }
          }
        }
      }
    end,
    requires = { 'nvim-lua/plenary.nvim', 'nvim-tree/nvim-web-devicons' },
  }

  use {
    'nvim-telescope/telescope-file-browser.nvim',
    config = function()
      require('telescope').load_extension('file_browser')
      vim.keymap.set('n', '<leader>fb', ':Telescope file_browser<CR>', { noremap = true })
    end,
    requires = { 'nvim-telescope/telescope.nvim', 'nvim-lua/plenary.nvim', 'nvim-tree/nvim-web-devicons' }
  }

  use {
    'fannheyward/telescope-coc.nvim',
    config = function()
      require('telescope').load_extension('coc')
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
    'nvim-telescope/telescope-frecency.nvim',
    config = function()
      require('telescope').load_extension('frecency')
      vim.keymap.set('n', '<leader><leader>', '<cmd>Telescope frecency<CR>', { silent = true })
    end,
    requires = { 'nvim-telescope/telescope.nvim', 'kkharji/sqlite.lua' }
  }

  use {
    'nvim-telescope/telescope-github.nvim',
    config = function()
      require('telescope').load_extension('gh')
    end,
    require = { 'nvim-lua/plenary.nvim', 'nvim-telescope/telescope.nvim' }
  }

  use {
    'nvim-telescope/telescope-media-files.nvim',
    config = function()
      require('telescope').load_extension('media_files')
    end,
    requires = { 'nvim-lua/popup.nvim', 'nvim-lua/plenary.nvim', 'nvim-telescope/telescope.nvim' }
  }

  use {
    'LinArcX/telescope-command-palette.nvim',
    config = function()
      require('telescope').load_extension('command_palette')
      vim.keymap.set('n', '<space>fc', '<cmd>Telescope command_palette<CR>', { silent = true })
    end,
    requires = { 'nvim-telescope/telescope.nvim' }
  }

  use {
    'AckslD/nvim-neoclip.lua',
    config = function()
      require('neoclip').setup()
      require('telescope').load_extension('neoclip')
    end,
    requires = { 'kkharji/sqlite.lua', module = 'sqlite' }
  }

  use {
    'pwntester/octo.nvim',
    requires = {
      'nvim-lua/plenary.nvim',
      'nvim-telescope/telescope.nvim',
      'kyazdani42/nvim-web-devicons',
    },
    config = function()
      require "octo".setup()
    end
  }

  use {
    'petertriho/nvim-scrollbar',
    config = function()
      require('scrollbar').setup()
    end
  }

  use {
    'kevinhwang91/nvim-hlslens',
    config = function()
      require('hlslens').setup()

      local kopts = { noremap = true, silent = true }

      vim.api.nvim_set_keymap('n', 'n',
        [[<Cmd>execute('normal! ' . v:count1 . 'n')<CR><Cmd>lua require('hlslens').start()<CR>]],
        kopts)
      vim.api.nvim_set_keymap('n', 'N',
        [[<Cmd>execute('normal! ' . v:count1 . 'N')<CR><Cmd>lua require('hlslens').start()<CR>]],
        kopts)
      vim.api.nvim_set_keymap('n', '*', [[*<Cmd>lua require('hlslens').start()<CR>]], kopts)
      vim.api.nvim_set_keymap('n', '#', [[#<Cmd>lua require('hlslens').start()<CR>]], kopts)
      vim.api.nvim_set_keymap('n', 'g*', [[g*<Cmd>lua require('hlslens').start()<CR>]], kopts)
      vim.api.nvim_set_keymap('n', 'g#', [[g#<Cmd>lua require('hlslens').start()<CR>]], kopts)

      vim.api.nvim_set_keymap('n', '<Leader>l', '<Cmd>noh<CR>', kopts)
    end
  }

  use {
    'tversteeg/registers.nvim',
    config = function()
      require('registers').setup()
    end
  }

  use {
    'famiu/bufdelete.nvim'
  }

  use {
    'yutkat/confirm-quit.nvim'
  }

  use {
    'segeljakt/vim-silicon'
  }

  use {
    'Shougo/vinarise.vim'
  }

  use {
    'tyru/open-browser.vim'
  }

  use {
    'tyru/open-browser-github.vim',
    requires = { 'tyru/open-browser.vim' }
  }

  use {
    'andymass/vim-matchup'
  }

  use {
    'sindrets/diffview.nvim',
    requires = { 'nvim-lua/plenary.nvim', 'nvim-tree/nvim-web-devicons' },
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
    'akinsho/git-conflict.nvim',
    config = function()
      require('git-conflict').setup()
    end
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

  use {
    'itmecho/neoterm.nvim',
    config = function()
      vim.keymap.set('n', '<space>n', '<cmd>NeotermToggle<CR>', { noremap = true })
      require('neoterm').setup {
        mode = 'fullscreen',
        noinsert = false
      }
    end
  }

  use {
    'hrsh7th/nvim-cmp',
    config = function()
      local cmp = require('cmp')
      cmp.setup.cmdline({ '/', '?' }, {
        mapping = cmp.mapping.preset.cmdline(),
        sources = {
          { name = 'buffer' }
        }
      })
      cmp.setup.cmdline(':', {
        mapping = cmp.mapping.preset.cmdline(),
        sources = cmp.config.sources({
          { name = 'path' }
        }, {
          { name = 'cmdline' }
        })
      })
    end
  }

  use {
    'hrsh7th/cmp-cmdline'
  }

  use {
    'hrsh7th/cmp-path'
  }

  use {
    'hrsh7th/cmp-buffer'
  }

  use {
    'echasnovski/mini.indentscope',
    config = function()
      require('mini.indentscope').setup({
        symbol = '|'
      })
    end
  }

  use {
    'norcalli/nvim-colorizer.lua'
  }

  use {
    'kylechui/nvim-surround'
  }

  use { 'rust-lang/rust.vim', opt = true, ft = { 'rust' } }

  use { 'vimjas/vim-python-pep8-indent', opt = true, ft = { 'python' } }

  use {
    'fatih/vim-go',
    opt = true,
    config = function()
      vim.g.go_doc_popup_window = 1
    end,
    ft = { 'go' } }

  use {
    'neovimhaskell/haskell-vim',
    opt = true,
    ft = { 'haskell' }
  }

  use {
    'luc-tielen/telescope_hoogle',
    config = function()
      require('telescope').load_extension('hoogle')
    end,
    requres = { 'nvim-telescope/telescope.nvim' }
  }
end

local plugins = setmetatable({}, {
  __index = function(_, key)
    init()
    return packer[key]
  end
})

return plugins
