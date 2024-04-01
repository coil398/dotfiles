local wezterm = require 'wezterm'

return {
  font = wezterm.font 'Cica',
  font_size = 10.0,
  default_domain = 'WSL:Arch',
  wsl_domains = {
    {
      name = 'WSL:Arch',
      distribution = 'Arch',
      username = 'coil398',
      default_cwd = '/home/coil398'
    }
  },
  enable_tab_bar = false,
}
