local M = {}

-- Stores buffer IDs in MRU order (index 1 is most recent)
local mru_list = {}

-- Helper to remove a value from a list
local function remove_value(list, value)
  for i, v in ipairs(list) do
    if v == value then
      table.remove(list, i)
      return
    end
  end
end

-- Autocommand to update the MRU list when a buffer is entered
vim.api.nvim_create_autocmd("BufEnter", {
  group = vim.api.nvim_create_augroup("MruBufferSorter", { clear = true }),
  callback = function()
    local bufnr = vim.api.nvim_get_current_buf()
    -- Remove if exists, then insert at the beginning
    remove_value(mru_list, bufnr)
    table.insert(mru_list, 1, bufnr)
  end,
})

-- Autocommand to remove buffer from list when deleted
vim.api.nvim_create_autocmd("BufDelete", {
  group = vim.api.nvim_create_augroup("MruBufferSorterCleanup", { clear = true }),
  callback = function(args)
    remove_value(mru_list, args.buf)
  end,
})

-- Custom compare function for bufferline.nvim
M.sort = function(buffer_a, buffer_b)
  local idx_a = -1
  local idx_b = -1

  -- Find index in MRU list
  for i, bufnr in ipairs(mru_list) do
    if bufnr == buffer_a.id then idx_a = i end
    if bufnr == buffer_b.id then idx_b = i end
  end

  -- If both are in the list, sort by index (smaller index = more recent = first)
  if idx_a ~= -1 and idx_b ~= -1 then
    return idx_a < idx_b
  end

  -- If one is not in the list (e.g. startup), prioritize the one in the list
  if idx_a ~= -1 then return true end
  if idx_b ~= -1 then return false end

  -- Fallback to default ID sort
  return buffer_a.id < buffer_b.id
end

return M