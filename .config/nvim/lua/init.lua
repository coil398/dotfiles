local lazypath = vim.fn.stdpath('data') .. '/lazy/lazy.nvim'
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    'git',
    'clone',
    '--filter=blob:none',
    'https://github.com/folke/lazy.nvim.git',
    '--branch=stable',
    lazypath
  })
end
vim.opt.rtp:prepend(lazypath)

require('lazy').setup({
  {
    'neoclide/coc.nvim',
    branch = 'release',
    config = function() require('coc').init() end
  },
  {
    'nvim-lualine/lualine.nvim',
    dependencies = { 'nvim-tree/nvim-web-devicons' },
    config = function()
      require('lualine').setup({
        options = {
          theme = 'auto',
          globalstatus = true
        },
        sections = {
          lualine_c = { { 'filename', path = 1 } }
        }
      })
    end
  },
  {
    'nvim-treesitter/nvim-treesitter',
    config = function() vim.fn['config#nvim_treesitter#init']() end,
    event = { 'BufNewFile', 'BufRead' }
  },
  {
    'tomasiser/vim-code-dark'
  },
  {
    'folke/tokyonight.nvim'
  },
  {
    'luochen1990/rainbow',
    config = function() vim.g.rainbow_active = 1 end
  },
  {
    'zbirenbaum/copilot.lua',
    config = function()
      require('copilot').setup({
        panel = {
          auto_refresh = true,
          keymap = {
            open = "<C-CR>"
          },
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
    lazy = true,
    cmd = { 'Copilot' },
    event = 'InsertEnter'
  },
  {
    'nvim-telescope/telescope.nvim',
    config = function()
      local builtin = require('telescope.builtin')
      vim.keymap.set('n', '<Space>ff', builtin.find_files, {})
      vim.keymap.set('n', '<Space>fg', builtin.live_grep, {})
      -- vim.keymap.set('n', '<leader>fb', builtin.buffers, {})
      vim.keymap.set('n', '<Space>fn', builtin.help_tags, {})
      vim.keymap.set('n', '<Space>fr', builtin.resume, {})
      vim.keymap.set('n', '<Space>t', ':Telescope ', {})

      local actions = require 'telescope.actions'
      -- local fb_actions = require 'telescope._extensions.file_browser.actions'

      require('telescope').setup {
        defaults = {
          file_ignore_patterns = {
            '^.git/',
            '^node_modules/'
          },
          winblend = 50,
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
    dependencies = { 'nvim-lua/plenary.nvim', 'nvim-tree/nvim-web-devicons' },
  },
  {
    'nvim-telescope/telescope-file-browser.nvim',
    config = function()
      require('telescope').load_extension('file_browser')
      vim.keymap.set('n', '<Space>fb', ':Telescope file_browser<CR>', { noremap = true })
    end,
    dependencies = { 'nvim-telescope/telescope.nvim', 'nvim-lua/plenary.nvim', 'nvim-tree/nvim-web-devicons' }
  },
  {
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
    dependencies = { 'nvim-telescope/telescope.nvim' }
  },
  {
    'smartpde/telescope-recent-files',
    config = function()
      require('telescope').load_extension('recent_files')
      vim.keymap.set('n', '<Space>fe', "<cmd>lua require('telescope').extensions.recent_files.pick()<CR>",
        { noremap = true, silent = true })
    end,
    dependencies = { 'nvim-telescope/telescope.nvim' }
  },
  {
    'nvim-telescope/telescope-github.nvim',
    config = function()
      require('telescope').load_extension('gh')
    end,
    dependencies = { 'nvim-lua/plenary.nvim', 'nvim-telescope/telescope.nvim' }
  },
  {
    'LinArcX/telescope-command-palette.nvim',
    config = function()
      require('telescope').load_extension('command_palette')
      vim.keymap.set('n', '<space>fc', '<cmd>Telescope command_palette<CR>', { silent = true })
    end,
    dependencies = { 'nvim-telescope/telescope.nvim' }
  },
  {
    'petertriho/nvim-scrollbar',
    config = function()
      require('scrollbar').setup()
    end
  },
  {
    'TimUntersberger/neogit',
    requires = { 'nvim-lua/plenary.nvim' },
    lazy = true,
    config = function()
      require('neogit').setup {}
    end,
    cmd = { 'Neogit' }
  },
  {
    'folke/noice.nvim',
    opts = {
      lsp = {
        override = {
          ["vim.lsp.util.convert_input_to_markdown_lines"] = true,
          ["vim.lsp.util.stylize_markdown"] = true,
          ["cmp.entry.get_documentation"] = true,
        },
      },
      presets = {
        bottom_search = false,
        command_palette = false,
        long_message_to_split = true,
        inc_rename = false,
        lsp_doc_border = false
      },
      views = {
        cmdline_popup = { border = { style = 'none' } } }
    },
    dependencies = { 'MunifTanjim/nui.nvim', 'rcarriga/nvim-notify' }
  },
  {
    'stevearc/aerial.nvim',
    dependencies = { 'nvim-tree/nvim-web-devicons' },
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
  },
  {
    'itmecho/neoterm.nvim',
    config = function()
      vim.keymap.set('n', '<space>n', '<cmd>NeotermToggle<CR>', { noremap = true })
      require('neoterm').setup {
        positon = 'fullscreen',
        noinsert = false
      }
    end
  },
  {
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
  },
  {
    'hrsh7th/cmp-cmdline'
  },
  {
    'hrsh7th/cmp-path'
  },
  {
    'hrsh7th/cmp-buffer'
  },
  { 'rust-lang/rust.vim',            lazy = true, ft = { 'rust' } },
  { 'vimjas/vim-python-pep8-indent', lazy = true, ft = { 'python' } },
  {
    'fatih/vim-go',
    lazy = true,
    config = function()
      vim.g.go_doc_popup_window = 1
    end,
    ft = { 'go' }
  },
  {
    'neovimhaskell/haskell-vim',
    lazy = true,
    ft = { 'haskell' }
  },
  {
    'luc-tielen/telescope_hoogle',
    config = function()
      require('telescope').load_extension('hoogle')
    end,
    dependencies = { 'nvim-telescope/telescope.nvim' }
  },
  {
    'rafcamlet/coc-nvim-lua',
    dependencies = { 'neoclide/coc.nvim' }
  }
})
