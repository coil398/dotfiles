local M = {}

local gl = package.loaded.galaxyline


M.buffer_not_empty = function()
  return #vim.fn.bufname('%') > 0
end

local sections = { left = 0, mid = 0, right = 0, short_line_left = 0, short_line_right = 0 }


--- Declares a section of Galaxyline dynamically, so code can be moved around easily
---@param pos string Which part of Galaxyline this section belongs to
---@param tbl table The section's properties
M.section = function(pos, tbl)
  sections[pos] = sections[pos] + 1
  gl.section[pos][sections[pos]] = tbl
end


M.update_colors = function(statusline)
  vim.api.nvim_command('hi StatusLine guibg=' .. statusline .. ' gui=nocombine')
  for pos, _ in pairs(sections) do
    for i = 1, #gl.section[pos] do
      for k, v in pairs(gl.section[pos][i]) do
        local function none() return 'NONE' end
        local fg = v.highlight[1] or none
        local bg = v.highlight[2] or none
        local style = v.highlight[3] or none
        local cmd = 'hi! Galaxy' .. k
            .. ' gui=' .. style()
            .. ' guifg=' .. fg()
            .. ' guibg=' .. bg()
        vim.api.nvim_command(cmd)
      end
    end
  end
end

return M
