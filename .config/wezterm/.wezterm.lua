local wezterm = require 'wezterm'

return {
  font = wezterm.font 'Cica',
  font_size = 11.0,
  color_scheme = 'iceberg-dark',

  enable_tab_bar = false,

  default_domain = 'WSL:Arch',
  wsl_domains = {
    {
      name = 'WSL:Arch',
      distribution = 'Arch',
      username = 'coil398',
      default_cwd = '/home/coil398'
    }
  },

  keys = {
    { key = 'Tab',   mods = 'SHIFT', action = wezterm.action { SendString = '\x1b[Z' } },
    { key = '[',     mods = 'ALT',   action = wezterm.action { SendString = '\x1b[' } },
    { key = ']',     mods = 'ALT',   action = wezterm.action { SendString = '\x1b]' } },
    { key = 'Enter', mods = 'ALT',   action = wezterm.action { SendString = '\x1b\x0d' } },
  }
}
