-- For go lang
local go_group = vim.api.nvim_create_augroup("go", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = go_group,
  pattern = "go",
  callback = function()
    vim.cmd("highlight goErr cterm=bold ctermfg=214")
    vim.cmd("match goErr /\\<err\\>/")
  end
})
-- For python
local python_group = vim.api.nvim_create_augroup("python", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = python_group,
  pattern = "python",
  callback = function()
    vim.cmd("syn match pythonOperator \"\\(+\\|=\\|-\\|\\^\\|\\*\\)\"")
    vim.cmd("syn match pythonDelimiter \"\\(,\\|\\.\\|:\\)\"")
    vim.cmd("syn keyword self self")
    vim.cmd("hi link pythonOperator Statement")
    vim.cmd("hi link pythonDelimiter Special")
    vim.cmd("hi link self Type")
  end
})

-- For c
local c_group = vim.api.nvim_create_augroup("c", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = c_group,
  pattern = "c",
  callback = function()
    vim.cmd("highlight ccoloncolon cterm=bold ctermfg=214")
    vim.cmd("match ccoloncolon /\\:\\:/")
  end
})

-- For c++
local cpp_group = vim.api.nvim_create_augroup("cpp", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = cpp_group,
  pattern = "cpp",
  callback = function()
    vim.cmd("highlight cppcoloncolon cterm=bold ctermfg=214")
    vim.cmd("match cppcoloncolon /\\:\\:/")
  end
})

-- For cuda
local cuda_group = vim.api.nvim_create_augroup("cuda", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = cuda_group,
  pattern = "cuda",
  callback = function()
    vim.cmd("highlight cudacoloncolon cterm=bold ctermfg=214")
    vim.cmd("match cudacoloncolon /\\:\\:/")
  end
})

-- For javascript
local js_group = vim.api.nvim_create_augroup("javascript", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = js_group,
  pattern = "javascript",
  callback = function()
    vim.cmd("syn match Operator \"\\(|\\|+\\|=\\|-\\|\\^\\|\\*\\)\"")
    vim.cmd("syn match Delimiter \"\\(\\.\\|:\\)\"")
    vim.cmd("hi link Operator Statement")
    vim.cmd("hi link Delimiter Special")
  end
})

-- For typescript
local ts_group = vim.api.nvim_create_augroup("typescript", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = ts_group,
  pattern = "typescript",
  callback = function()
    vim.cmd("syn match Operator \"\\(|\\|+\\|=\\|-\\|\\^\\|\\*\\)\"")
    vim.cmd("syn match Delimiter \"\\(\\.\\|:\\)\"")
    vim.cmd("hi link Operator Statement")
    vim.cmd("hi link Delimiter Special")
  end
})

-- For typescriptreact
local tsx_group = vim.api.nvim_create_augroup("typescriptreact", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = tsx_group,
  pattern = "typescriptreact",
  callback = function()
    vim.cmd("syn match Operator \"\\(|\\|+\\|=\\|-\\|\\^\\|\\*\\)\"")
    vim.cmd("syn match Delimiter \"\\(\\.\\|:\\)\"")
    vim.cmd("hi link Operator Statement")
    vim.cmd("hi link Delimiter Special")
  end
})

-- For vue
local vue_group = vim.api.nvim_create_augroup("vue", { clear = true })
vim.api.nvim_create_autocmd({"BufNewFile", "BufRead"}, {
  group = vue_group,
  pattern = "*.vue",
  callback = function()
    vim.bo.filetype = "vue"
  end
})
vim.api.nvim_create_autocmd("FileType", {
  group = vue_group,
  pattern = "vue",
  callback = function()
    vim.cmd("syn match Operator \"\\(|\\|+\\|=\\|-\\|\\^\\|\\*\\)\"")
    vim.cmd("syn match Delimiter \"\\(\\.\\|:\\)\"")
    vim.cmd("hi link Operator Statement")
    vim.cmd("hi link Delimiter Special")
  end
})

-- For toml
local toml_group = vim.api.nvim_create_augroup("toml", { clear = true })
vim.api.nvim_create_autocmd({"BufNewFile", "BufRead"}, {
  group = toml_group,
  pattern = "*.toml",
  callback = function()
    vim.bo.filetype = "toml"
  end
})
-- For make
local make_group = vim.api.nvim_create_augroup("make", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = make_group,
  pattern = "make",
  callback = function()
    vim.bo.expandtab = false
  end
})

-- For terminal
local terminal_group = vim.api.nvim_create_augroup("terminal", { clear = true })
vim.api.nvim_create_autocmd("TermOpen", {
  group = terminal_group,
  pattern = "*",
  command = "startinsert"
})

-- Keep last position
local keep_pos_group = vim.api.nvim_create_augroup("KeepLastPosition", { clear = true })
vim.api.nvim_create_autocmd("BufRead", {
  group = keep_pos_group,
  pattern = "*",
  callback = function()
    local line = vim.fn.line("'\"")
    if line > 0 and line <= vim.fn.line("$") then
      vim.cmd("normal g`\"")
    end
  end
})

-- Persistent undo
if vim.fn.has('persistent_undo') == 1 then
  local undo_dir = vim.fn.expand('~/.vimundo')
  if vim.fn.isdirectory(undo_dir) == 0 then
    vim.fn.mkdir(undo_dir, 'p')
  end
  vim.opt.undodir = "./.vimundo," .. undo_dir
  local undo_group = vim.api.nvim_create_augroup("SaveUndoFile", { clear = true })
  vim.api.nvim_create_autocmd("BufReadPre", {
    group = undo_group,
    pattern = "~/*",
    callback = function()
      vim.bo.undofile = true
    end
  })
end

-- Ripgrep integration
if vim.fn.executable('rg') == 1 then
  vim.opt.grepprg = 'rg --vimgrep --hidden'
  vim.opt.grepformat = '%f:%l:%c:%m'
end

-- YAML specific
local yaml_group = vim.api.nvim_create_augroup("yaml", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = yaml_group,
  pattern = "yaml",
  callback = function()
    vim.bo.indentexpr = ""
  end
})

-- Auto-reload files when window enters
local autoread_group = vim.api.nvim_create_augroup("AutoRead", { clear = true })
vim.api.nvim_create_autocmd("WinEnter", {
  group = autoread_group,
  pattern = "*",
  command = "checktime"
})
