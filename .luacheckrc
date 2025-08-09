std = 'lua54'

globals = {
  -- Neovim API
  'vim',
}

codes = {
  -- allow long lines and unused args/vars in config snippets
  -- (we run luacheck mainly for syntax/scope problems)
  ignore = {
    '631', -- line is too long
  }
}

