-- Performance optimization: Enable Lua module caching
vim.loader.enable()

-- Set leader early so all mappings can use <leader>
vim.g.mapleader = ' '

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
          lualine_b = { 'branch', 'diff' },
          lualine_c = { { 'filename', path = 1 } },
          lualine_x = { { 'diagnostics', sources = { 'coc', 'nvim_diagnostic' } }, 'encoding', 'fileformat', 'filetype' }
        }
      })
    end
  },
  {
    'nvim-treesitter/nvim-treesitter',
    branch = 'main',
    lazy = false,
    build = ':TSUpdate',
    config = function()
      local nvim_treesitter = require('nvim-treesitter')
      nvim_treesitter.setup({
        install_dir = vim.fs.joinpath(vim.fn.stdpath('data'), 'site')
      })
      nvim_treesitter.install(
        {
          'all'
        },
        {
          force = false,
          generate = true,
          max_jobs = 4,
          summary = false
        }
      )
    end,
  },
  {
    'HiPhish/rainbow-delimiters.nvim',
    config = function()
      require('rainbow-delimiters.setup').setup({
        strategy = {
          [''] = 'rainbow-delimiters.strategy.global',
          vim = 'rainbow-delimiters.strategy.local',
        },
        query = {
          [''] = 'rainbow-delimiters',
          lua = 'rainbow-blocks',
        },
        priority = {
          [''] = 110,
          lua = 210,
        },
        highlight = {
          'RainbowDelimiterRed',
          'RainbowDelimiterYellow',
          'RainbowDelimiterBlue',
          'RainbowDelimiterOrange',
          'RainbowDelimiterGreen',
          'RainbowDelimiterViolet',
          'RainbowDelimiterCyan',
        },
      })
    end
  },
  {
    'Mofiqul/vscode.nvim'
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
        -- Enable Copilot for most filetypes, but disable on prompts/docs
        filetypes = {
          ['*'] = true,
          TelescopePrompt = false,
          markdown = false,
        },
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
      vim.keymap.set('n', '<leader>ff', builtin.find_files, {})
      vim.keymap.set('n', '<leader>fg', builtin.live_grep, {})
      -- vim.keymap.set('n', '<leader>fb', builtin.buffers, {})
      vim.keymap.set('n', '<leader>fn', builtin.help_tags, {})
      vim.keymap.set('n', '<leader>fr', builtin.resume, {})
      vim.keymap.set('n', '<leader>t', ':Telescope ', {})

      local actions = require 'telescope.actions'
      -- local fb_actions = require 'telescope._extensions.file_browser.actions'

      require('telescope').setup {
        defaults = {
          file_ignore_patterns = {
            '^%.git/',
            '^node_modules/',
            '^%.cache/',
          },
          winblend = 50,
          initial_mode = 'insert',
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
      vim.keymap.set('n', '<leader>fb', ':Telescope file_browser<CR>', { noremap = true })
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
      vim.keymap.set('n', '<leader>fa', '<cmd>Telescope coc diagnostics<CR>', { silent = true })
      vim.keymap.set('n', '<leader>c', '<cmd>Telescope coc commands<CR>', { silent = true })
      vim.keymap.set('n', '<leader>s', '<cmd>Telescope coc workspace_symbols<CR>', { silent = true })
      vim.keymap.set('n', '<leader>o', '<cmd>Telescope coc document_symbols<CR>', { silent = true })
    end,
    dependencies = { 'nvim-telescope/telescope.nvim' }
  },
  {
    'smartpde/telescope-recent-files',
    config = function()
      require('telescope').load_extension('recent_files')
      vim.keymap.set('n', '<leader>fe', "<cmd>lua require('telescope').extensions.recent_files.pick()<CR>",
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
      vim.keymap.set('n', '<leader>fc', '<cmd>Telescope command_palette<CR>', { silent = true })
    end,
    dependencies = { 'nvim-telescope/telescope.nvim' }
  },
  {
    'petertriho/nvim-scrollbar',
    event = 'VeryLazy',
    config = function()
      require('scrollbar').setup()
    end
  },
  {
    'lewis6991/gitsigns.nvim',
    event = 'BufReadPre',
    config = function()
      require('gitsigns').setup()
      -- Hunk navigation
      vim.keymap.set('n', ']c', require('gitsigns').next_hunk, { desc = 'Next Hunk' })
      vim.keymap.set('n', '[c', require('gitsigns').prev_hunk, { desc = 'Prev Hunk' })
      -- Common actions
      vim.keymap.set('n', '<leader>hs', require('gitsigns').stage_hunk, { desc = 'Stage Hunk' })
      vim.keymap.set('n', '<leader>hr', require('gitsigns').reset_hunk, { desc = 'Reset Hunk' })
      vim.keymap.set('n', '<leader>hp', require('gitsigns').preview_hunk, { desc = 'Preview Hunk' })
    end
  },
  {
    'folke/which-key.nvim',
    event = "VeryLazy",
    config = function()
      local wk = require('which-key')
      wk.setup({
        plugins = {
          marks = true,
          registers = true,
          spelling = {
            enabled = true,
            suggestions = 20,
          },
        },
      })

      -- Register key mappings with descriptions
      wk.add({
        -- Find/Files
        { "<leader>f",  group = "Find/Files" },
        { "<leader>ff", desc = "Find Files" },
        { "<leader>fg", desc = "Live Grep" },
        { "<leader>fn", desc = "Help Tags" },
        { "<leader>fr", desc = "Resume Last Search" },
        { "<leader>fb", desc = "File Browser" },
        { "<leader>fc", desc = "Command Palette" },
        { "<leader>fe", desc = "Recent Files" },
        { "<leader>fa", desc = "Diagnostics (Telescope)" },

        -- Git Hunks
        { "<leader>h",  group = "Git Hunks" },
        { "<leader>hs", desc = "Stage Hunk" },
        { "<leader>hr", desc = "Reset Hunk" },
        { "<leader>hp", desc = "Preview Hunk" },

        -- Code Actions
        {
          group = "Code Actions",
          { "<leader>a",  desc = "Code Action (selected)" },
          { "<leader>ac", desc = "Code Action (cursor)" },
          { "<leader>as", desc = "Code Action (source)" },
          { "<leader>ao", desc = "Aerial Toggle" },
        },

        -- Refactor/Rename
        {
          group = "Refactor/Rename",
          { "<leader>r",  desc = "Refactor Selected" },
          { "<leader>rn", desc = "Rename Symbol" },
          { "<leader>re", desc = "Refactor Action" },
        },

        { "<leader>c",   desc = "CocList Commands" },
        { "<leader>s",   desc = "Workspace Symbols" },
        { "<leader>o",   desc = "Document Symbols" },
        { "<leader>n",   desc = "Terminal Toggle" },
        { "<leader>t",   desc = "Telescope Prompt" },
        { "<leader>qf",  desc = "Quick Fix" },
        { "<leader>cl",  desc = "Code Lens Action" },
        { "<leader>fmt", desc = "Format File" },
      })
    end
  },
  {
    'TimUntersberger/neogit',
    dependencies = { 'nvim-lua/plenary.nvim', 'nvim-telescope/telescope.nvim', 'sindrets/diffview.nvim' },
    lazy = true,
    config = function()
      require('neogit').setup {
        integrations = {
          telescope = true,
          diffview = true
        },
      }
    end,
    cmd = { 'Neogit' }
  },
  {
    'stevearc/aerial.nvim',
    cmd = { 'AerialToggle', 'AerialOpen', 'AerialClose' },
    keys = { '<leader>ao' },
    dependencies = { 'nvim-tree/nvim-web-devicons' },
    config = function()
      vim.keymap.set('n', '<leader>ao', '<cmd>AerialToggle!<CR>', { noremap = true })
      require('aerial').setup({
        nerd_font = 'auto',
        show_guides = true,
        update_events = 'TextChanged,InsertLeave',
        close_on_select = false,
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
        },
        open_automatic = function(_)
          return true
        end,
      })
    end
  },
  {
    'itmecho/neoterm.nvim',
    keys = { '<leader>n' },
    config = function()
      vim.keymap.set('n', '<leader>n', '<cmd>NeotermToggle<CR>', { noremap = true })
      require('neoterm').setup {
        position = 'fullscreen',
        noinsert = false
      }
    end
  },
  {
    "folke/noice.nvim",
    event = "VeryLazy",
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
        command_palette = true,
        long_message_to_split = true,
        inc_rename = false,
        lsp_doc_border = false,
      },
      views = {
        cmdline_popup = {
          position = { row = "50%", col = "50%" },
          size = { width = 60, height = "auto" }
        }
      }
    },
    dependencies = {
      "MunifTanjim/nui.nvim",
      "rcarriga/nvim-notify",
    }
  },
  {
    'hrsh7th/nvim-cmp',
    event = 'CmdlineEnter',
    dependencies = {
      'hrsh7th/cmp-cmdline',
      'hrsh7th/cmp-path',
      'hrsh7th/cmp-buffer',
    },
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
