local mason = require("mason")
local mason_lspconfig = require("mason-lspconfig")
local lspconfig = require("lspconfig")
local cmp = require("cmp")
local lspkind = require("lspkind")

-- Mason setup
mason.setup({})

-- Install servers
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
local codelens_group = vim.api.nvim_create_augroup('LspCodeLensRefresh', { clear = false })
local reference_hint_group = vim.api.nvim_create_augroup('LspReferenceHint', { clear = false })
local reference_hint_ns = vim.api.nvim_create_namespace('lsp_reference_hint')

local function refresh_codelens(bufnr)
  pcall(vim.lsp.codelens.refresh, { bufnr = bufnr })
end

local function clear_reference_hint(bufnr)
  if vim.api.nvim_buf_is_valid(bufnr) then
    vim.api.nvim_buf_clear_namespace(bufnr, reference_hint_ns, 0, -1)
  end
end

local function refresh_reference_hint(bufnr)
  if not vim.api.nvim_buf_is_valid(bufnr) then
    return
  end

  local cursor = vim.api.nvim_win_get_cursor(0)
  local request_line = cursor[1] - 1
  local request_col = cursor[2]

  local params = vim.lsp.util.make_position_params(0, "utf-16")
  params.context = { includeDeclaration = false }

  vim.lsp.buf_request_all(bufnr, "textDocument/references", params, function(results)
    if not vim.api.nvim_buf_is_valid(bufnr) then
      return
    end

    local current_cursor = vim.api.nvim_win_get_cursor(0)
    if current_cursor[1] - 1 ~= request_line or current_cursor[2] ~= request_col then
      return
    end

    local count = 0
    local seen = {}

    for _, response in pairs(results or {}) do
      for _, location in ipairs(response.result or {}) do
        local uri = location.uri or location.targetUri
        local range = location.range or location.targetSelectionRange
        if uri and range and range.start then
          local key = table.concat({
            uri,
            tostring(range.start.line),
            tostring(range.start.character),
          }, ":")
          if not seen[key] then
            seen[key] = true
            count = count + 1
          end
        end
      end
    end

    clear_reference_hint(bufnr)
    vim.api.nvim_buf_set_extmark(bufnr, reference_hint_ns, request_line, 0, {
      virt_text = { { (" %d refs"):format(count), "Comment" } },
      virt_text_pos = "eol",
      hl_mode = "combine",
    })
  end)
end

local function maybe_refresh_reference_hint(bufnr)
  local now = vim.loop.now()
  local last = vim.b[bufnr].last_reference_hint_refresh or 0
  if now - last < 500 then
    return
  end
  vim.b[bufnr].last_reference_hint_refresh = now
  refresh_reference_hint(bufnr)
end

-- Global LSP Keymappings (Safe to define globally or via LspAttach)
-- Using LspAttach autocmd is the modern way to set keymaps only when LSP is active,
-- but ensures they are set reliably.
vim.api.nvim_create_autocmd('LspAttach', {
  group = vim.api.nvim_create_augroup('UserLspConfig', {}),
  callback = function(ev)
    local opts = { buffer = ev.buf, silent = true }

    -- GoTo code navigation
    vim.keymap.set('n', 'gd', telescope_builtin.lsp_definitions, opts)
    vim.keymap.set('n', 'gy', telescope_builtin.lsp_type_definitions, opts)
    vim.keymap.set('n', 'gi', telescope_builtin.lsp_implementations, opts)
    vim.keymap.set('n', 'gr', telescope_builtin.lsp_references, opts)
    
    -- Symbols
    vim.keymap.set('n', '<leader>s', telescope_builtin.lsp_dynamic_workspace_symbols, opts)
    vim.keymap.set('n', '<leader>o', telescope_builtin.lsp_document_symbols, opts)

    -- Documentation
    vim.keymap.set('n', 'K', vim.lsp.buf.hover, opts)

    -- Rename
    vim.keymap.set('n', '<leader>rn', vim.lsp.buf.rename, opts)

    -- Code Actions
    vim.keymap.set({ 'n', 'v' }, '<leader>a', vim.lsp.buf.code_action, opts)

    -- Diagnostics
    vim.keymap.set('n', '[g', vim.diagnostic.goto_prev, opts)
    vim.keymap.set('n', ']g', vim.diagnostic.goto_next, opts)
    vim.keymap.set('n', '<leader>fa', telescope_builtin.diagnostics, opts)

    -- Formatting
    vim.api.nvim_buf_create_user_command(ev.buf, "Format", function()
      vim.lsp.buf.format({ async = true })
    end, {})

    -- Highlight symbol on cursor hold
    local client = vim.lsp.get_client_by_id(ev.data.client_id)
    if client and client.server_capabilities.documentHighlightProvider then
      vim.api.nvim_create_autocmd("CursorHold", {
        buffer = ev.buf,
        callback = function()
          vim.lsp.buf.document_highlight()
        end,
      })
      vim.api.nvim_create_autocmd("CursorMoved", {
        buffer = ev.buf,
        callback = function()
          vim.lsp.buf.clear_references()
        end,
      })
    end

    -- Attach navic
    if client.server_capabilities.documentSymbolProvider then
        require("nvim-navic").attach(client, ev.buf)
    end

    if client.server_capabilities.referencesProvider then
      if not vim.b[ev.buf].lsp_reference_hint_enabled then
        vim.b[ev.buf].lsp_reference_hint_enabled = true
        vim.api.nvim_create_autocmd({ 'BufEnter', 'CursorHold', 'CursorMoved', 'InsertLeave' }, {
          group = reference_hint_group,
          buffer = ev.buf,
          callback = function()
            maybe_refresh_reference_hint(ev.buf)
          end,
        })
        vim.api.nvim_create_autocmd('InsertEnter', {
          group = reference_hint_group,
          buffer = ev.buf,
          callback = function()
            clear_reference_hint(ev.buf)
          end,
        })
      end

      refresh_reference_hint(ev.buf)
    end

    if client.server_capabilities.codeLensProvider then
      vim.keymap.set('n', '<leader>lr', function()
        refresh_codelens(ev.buf)
      end, opts)
      vim.keymap.set('n', '<leader>ll', vim.lsp.codelens.run, opts)

      if not vim.b[ev.buf].lsp_codelens_refresh_enabled then
        vim.b[ev.buf].lsp_codelens_refresh_enabled = true
        vim.api.nvim_create_autocmd({ 'BufEnter', 'CursorHold', 'InsertLeave' }, {
          group = codelens_group,
          buffer = ev.buf,
          callback = function()
            refresh_codelens(ev.buf)
          end,
        })
      end

      refresh_codelens(ev.buf)
    end
  end,
})

mason_lspconfig.setup({
  ensure_installed = servers,
  automatic_installation = true,
  handlers = {
    function(server_name)
      local opts = {
        capabilities = capabilities,
        -- on_attach is no longer needed here as we use LspAttach autocmd
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

      if server_name == "yamlls" then
        opts.settings = {
          yaml = {
            schemaStore = {
              enable = true,
              url = "https://www.schemastore.org/api/json/catalog.json",
            },
            validate = true,
            completion = true,
            hover = true,
            format = { enable = true },
            schemas = {
              ["https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.0/schema.json"] = {
                "openapi.yaml",
                "openapi.yml",
                "swagger.yaml",
                "swagger.yml",
                "**/*openapi*.yaml",
                "**/*openapi*.yml",
                "**/*swagger*.yaml",
                "**/*swagger*.yml",
                "**/openapi/**/*.yaml",
                "**/openapi/**/*.yml",
                "**/paths/**/*.yaml",
                "**/paths/**/*.yml",
                "**/components/**/*.yaml",
                "**/components/**/*.yml",
                "**/schemas/**/*.yaml",
                "**/schemas/**/*.yml",
              },
            },
          },
        }
      end

      lspconfig[server_name].setup(opts)
    end,
  }
})

-- nvim-metals setup
local metals_config = require("metals").bare_config()

metals_config.settings = {
  showImplicitArguments = true,
  excludedPackages = { "akka.actor.typed.javadsl", "com.github.swagger.akka.javadsl" },
}
metals_config.init_options.statusBarProvider = "on"
metals_config.capabilities = capabilities
-- metals_config.on_attach = on_attach -- Not needed, LspAttach handles it globally

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

require("cmp_git").setup()

local cmp_autopairs = require('nvim-autopairs.completion.cmp')
cmp.event:on(
  'confirm_done',
  cmp_autopairs.on_confirm_done()
)

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
    ['<CR>'] = cmp.mapping.confirm({ select = false }), 
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
  preselect = cmp.PreselectMode.None,
  completion = {
    completeopt = "menu,menuone,noinsert,noselect",
  },
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

cmp.setup.cmdline('/', {
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
