local wezterm = require 'wezterm'

local config = {
  font = wezterm.font 'Cica',
  font_size = 10.0,
  color_scheme = 'iceberg-dark',

  enable_tab_bar = false,

  keys = {
    { key = 'Tab',   mods = 'SHIFT', action = wezterm.action { SendString = '\x1b[Z' } },
    { key = '[',     mods = 'ALT',   action = wezterm.action { SendString = '\x1b[' } },
    { key = ']',     mods = 'ALT',   action = wezterm.action { SendString = '\x1b]' } },
    { key = 'Enter', mods = 'ALT',   action = wezterm.action { SendString = '\x1b\x0d' } },
  }
}

if wezterm.target_triple == 'aarch64-apple-darwin' or wezterm.target_triple == 'x64_64-apple-darwin' then
  config.font_size = 13.0
end

config.color_scheme = 'Vs Code Dark+ (Gogh)'
config.window_close_confirmation = 'NeverPrompt'

return config
