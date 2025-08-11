local wezterm = require 'wezterm'

local config = {}

config.font = wezterm.font 'Cica'
config.font_size = 10.0
config.enable_tab_bar = false
config.use_ime = true
config.ime_preedit_rendering = 'Builtin'

local triple = wezterm.target_triple
local is_macos = triple:find('apple%-darwin') ~= nil
local is_windows = triple:find('windows') ~= nil

if is_windows then
	config.default_domain = 'WSL:Arch'
	config.wsl_domains = {
		{
			name = 'WSL:Arch',
			distribution = 'Arch',
			username = 'coil398',
			default_cwd = '/home/coil398',
		},
	}
end

if is_macos then
	config.macos_forward_to_ime_modifier_mask = 'SHIFT'
end

return config
