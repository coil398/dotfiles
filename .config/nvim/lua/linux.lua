-- Linux clipboard integration
vim.opt.clipboard:append("unnamedplus")

if vim.fn.has("wsl") == 1 then
  local win32yank = "/mnt/c/Windows/System32/win32yank.exe"
  if vim.fn.executable(win32yank) == 1 then
    vim.g.clipboard = {
      name = "win32yank-wsl",
      copy = {
        ["+"] = { win32yank, "-i", "--crlf" },
        ["*"] = { win32yank, "-i", "--crlf" },
      },
      paste = {
        ["+"] = { win32yank, "-o", "--lf" },
        ["*"] = { win32yank, "-o", "--lf" },
      },
      cache_enabled = 0,
    }
  end
end
