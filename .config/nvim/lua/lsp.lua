local mason = require("mason")
local mason_lspconfig = require("mason-lspconfig")
local lspconfig = require("lspconfig")
local cmp = require("cmp")
local lspkind = require("lspkind")

-- Mason setup
mason.setup({})

-- Install servers (REMOVE metals from here as nvim-metals handles it)
local servers = {
  "hls",          -- Haskell
  "gopls",        -- Go
  "rust_analyzer",-- Rust
  "ts_ls",        -- TypeScript
  "pyright",      -- Python
  "ruff",         -- Python linting/formatting
  "terraformls",  -- Terraform
  "yamlls",       -- YAML
  "elixirls",     -- Elixir
  "efm",          -- General
  "lua_ls",       -- Lua
}

-- Capabilities for cmp
local capabilities = require('cmp_nvim_lsp').default_capabilities()

-- Force signcolumn to always show to prevent shifting
vim.opt.signcolumn = "yes"

-- Telescope Integration for LSP
local telescope_builtin = require('telescope.builtin')

-- LSP Keymappings
local on_attach = function(client, bufnr)
  local opts = { noremap = true, silent = true, buffer = bufnr }

  -- GoTo code navigation (using Telescope for better UI)
  vim.keymap.set('n', 'gd', telescope_builtin.lsp_definitions, opts)
  vim.keymap.set('n', 'gy', telescope_builtin.lsp_type_definitions, opts)
  vim.keymap.set('n', 'gi', telescope_builtin.lsp_implementations, opts)
  vim.keymap.set('n', 'gr', telescope_builtin.lsp_references, opts)
  
  -- Symbols (Telescope)
  vim.keymap.set('n', '<leader>s', telescope_builtin.lsp_dynamic_workspace_symbols, opts)
  vim.keymap.set('n', '<leader>o', telescope_builtin.lsp_document_symbols, opts)

  -- Documentation
  vim.keymap.set('n', 'K', vim.lsp.buf.hover, opts)

  -- Rename
  vim.keymap.set('n', '<leader>rn', vim.lsp.buf.rename, opts)

  -- Code Actions
  vim.keymap.set({ 'n', 'v' }, '<leader>a', vim.lsp.buf.code_action, opts)
  vim.keymap.set('n', '<leader>ac', vim.lsp.buf.code_action, opts) -- cursor
  vim.keymap.set('n', '<leader>as', vim.lsp.buf.code_action, opts) -- source (same as normal)
  vim.keymap.set('n', '<leader>qf', vim.lsp.buf.code_action, opts) -- quickfix

  -- Diagnostics
  vim.keymap.set('n', '[g', vim.diagnostic.goto_prev, opts)
  vim.keymap.set('n', ']g', vim.diagnostic.goto_next, opts)
  vim.keymap.set('n', '<leader>fa', telescope_builtin.diagnostics, opts) -- Telescope diagnostics

  -- Formatting
  vim.api.nvim_buf_create_user_command(bufnr, "Format", function()
    vim.lsp.buf.format({ async = true })
  end, {})
  
  -- Highlight symbol on cursor hold
  if client.server_capabilities.documentHighlightProvider then
    vim.api.nvim_create_autocmd("CursorHold", {
      buffer = bufnr,
      callback = function()
        vim.lsp.buf.document_highlight()
      end,
    })
    vim.api.nvim_create_autocmd("CursorMoved", {
      buffer = bufnr,
      callback = function()
        vim.lsp.buf.clear_references()
      end,
    })
  end
end

mason_lspconfig.setup({
  ensure_installed = servers,
  automatic_installation = true,
  handlers = {
    function(server_name)
      local opts = {
        capabilities = capabilities,
        on_attach = on_attach,
      }
      
      -- Lua specific settings
      if server_name == "lua_ls" then
        opts.settings = {
          Lua = {
            diagnostics = { globals = { 'vim' } },
            workspace = { library = vim.api.nvim_get_runtime_file("", true) },
          }
        }
      end

      lspconfig[server_name].setup(opts)
    end,
  }
})

-- nvim-metals setup
local metals_config = require("metals").bare_config()

-- Example of settings
metals_config.settings = {
  showImplicitArguments = true,
  excludedPackages = { "akka.actor.typed.javadsl", "com.github.swagger.akka.javadsl" },
}

-- *READ THIS*
-- I *highly* recommend setting statusBarProvider to true, however if you do,
-- you *have* to have a setting to display this in your statusline or else
-- you'll not see any messages from metals. There is more info in the help
-- docs about this
metals_config.init_options.statusBarProvider = "on"

-- Debug settings if you're using nvim-dap
metals_config.capabilities = capabilities
metals_config.on_attach = on_attach

-- Autocmd that will actually be in charge of starting the whole thing
local nvim_metals_group = vim.api.nvim_create_augroup("nvim-metals", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  pattern = { "scala", "sbt", "java" },
  callback = function()
    require("metals").initialize_or_attach(metals_config)
  end,
  group = nvim_metals_group,
})


-- nvim-cmp setup
local luasnip = require('luasnip')
require("luasnip.loaders.from_vscode").lazy_load()

-- Set up cmp-git
require("cmp_git").setup()

cmp.setup({
  snippet = {
    expand = function(args)
      luasnip.lsp_expand(args.body)
    end,
  },
  mapping = cmp.mapping.preset.insert({
    ['<C-b>'] = cmp.mapping.scroll_docs(-4),
    ['<C-f>'] = cmp.mapping.scroll_docs(4),
    ['<C-Space>'] = cmp.mapping.complete(),
    ['<C-e>'] = cmp.mapping.abort(),
    ['<CR>'] = cmp.mapping.confirm({ select = true }), 
    ['<Tab>'] = cmp.mapping(function(fallback)
      if cmp.visible() then
        cmp.select_next_item()
      elseif luasnip.expand_or_jumpable() then
        luasnip.expand_or_jump()
      else
        fallback()
      end
    end, { 'i', 's' }),
    ['<S-Tab>'] = cmp.mapping(function(fallback)
      if cmp.visible() then
        cmp.select_prev_item()
      elseif luasnip.jumpable(-1) then
        luasnip.jump(-1)
      else
        fallback()
      end
    end, { 'i', 's' }),
  }),
  sources = cmp.config.sources({
    { name = 'nvim_lsp' },
    { name = 'luasnip' },
    { name = 'path' },
    { name = "git" }, 
  }, {
    { name = 'buffer' },
  }),
  formatting = {
    format = lspkind.cmp_format({
      mode = 'symbol',
      maxwidth = 50,
      ellipsis_char = '...',
      symbol_map = { Git = "" } 
    })
  }
})

-- Set configuration for specific filetype.
cmp.setup.filetype('gitcommit', {
  sources = cmp.config.sources({
    { name = 'git' }, 
  }, {
    { name = 'buffer' },
  })
})

-- Use buffer source for `/`
cmp.setup.cmdline('/', {
  mapping = cmp.mapping.preset.cmdline(),
  sources = {
    { name = 'buffer' }
  }
})

-- Use cmdline & path source for ':'
cmp.setup.cmdline(':', {
  mapping = cmp.mapping.preset.cmdline(),
  sources = cmp.config.sources({
    { name = 'path' }
  }, {
    { name = 'cmdline' }
  })
})