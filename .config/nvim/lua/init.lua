vim.api.nvim_create_user_command("PackerInstall", [[packadd packer.nvim | lua require("packers").install()]], { bang = true })
vim.api.nvim_create_user_command("PackerUpdate", [[packadd packer.nvim | lua require("packers").update()]], { bang = true })
vim.api.nvim_create_user_command("PackerSync", [[packadd packer.nvim | lua require("packers").sync()]], { bang = true })
vim.api.nvim_create_user_command("PackerClean", [[packadd packer.nvim | lua require("packers").clean()]], { bang = true })
vim.api.nvim_create_user_command("PackerCompile", [[packadd packer.nvim | lua require("packers").compile()]], { bang = true })
vim.api.nvim_create_autocmd("BufWritePost", {
  pattern = { "plugins.lua" },
  command = "PackerCompile",
})

vim.opt.termguicolors = true
