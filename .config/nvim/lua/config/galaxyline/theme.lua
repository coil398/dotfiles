local M = {}

--- Defines primary, secondary, foreground and background colors for a Vim mode
---@class ModeTheme
---@field primary string
---@field secondary string
---@field bg string
---@field light string
---@field dark string

--- Defines color palletes for all vim modes
---@class VimModeColors

---@field normal ModeTheme

---@field visual ModeTheme

---@field insert ModeTheme

---@field replace ModeTheme
---@field terminal ModeTheme
---@field command ModeTheme
---@field none ModeTheme

M.signs = {
  icons = {
    vim         = '  ',
    git         = '  ',
    git_changes = '±',
    line        = '  ',
    unix        = ' ',
    dos         = ' ',

    space       = '•',
    tab         = 'ﬀ ',
    modified    = 'פֿ',
    readonly    = '',
  },
  separators = {
    right = ' ',
    right_thin = ' ',
    left = '',
    left_thin = '',
  },
  diagnostics = {

    lsp = ' ',

    error = ' ',
    warn = ' ',
  },
}

M.modecolors = { ---@type VimModeColors
  command = {
    primary   = "#f8e087",
    secondary = "#5f5044",
    bg        = "#201010",
    light     = "#fcf0dc",
    dark      = "#453a22",
  },

  visual = {
    primary   = "#77c0ff",
    secondary = "#354fed",
    bg        = "#112060",
    light     = "#afe8ff",
    dark      = "#2040a0",
  },
  insert = {
    primary   = "#2bff9a",
    secondary = "#277e40",
    bg        = "#003322",
    light     = "#aaffdd",
    dark      = "#005010",
  },

  replace = {

    primary   = "#f76842",
    secondary = "#893401",
    bg        = "#201000",
    light     = "#ffdda0",

    dark      = "#43200a",
  },
  terminal = {
    primary   = "#8f4466",
    secondary = "#50302e",
    bg        = "#2a180b",
    light     = "#ffddee",
    dark      = "#4f0a05",
  },
  normal = {
    primary   = "#cbcbcb",

    secondary = "#535353",
    bg        = "#1e1e1e",
    light     = "#f0f0f0",
    dark      = "#343434",

  },
  none = {
    primary   = "#2b3c66",
    secondary = "#203044",
    bg        = "#0a0a1c",
    light     = "#a0b0c0",
    dark      = "#3a405b",
  },
}

return M
