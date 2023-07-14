local status_ok, gl = pcall(require, 'galaxyline')
if not status_ok then
  print("Couldn't load 'galaxyline'")
  return
end

gl.short_line_list = { 'NvimTree', 'Outline', 'Trouble', 'qf' }

local theme        = require 'config.galaxyline.theme'
local colors       = theme.modecolors
local icons        = theme.signs.icons
local separators   = theme.signs.separators

local U            = require 'config.galaxyline.util'
local condition    = require 'galaxyline.condition'

local mode_lookup  = {
  n = colors.normal,
  i = colors.insert,
  v = colors.visual,
  V = colors.visual,
  [''] = colors.visual,
  r = colors.replace,
  R = colors.replace,
  t = colors.terminal,
  c = colors.command,
}

local mode         = colors.normal


U.section('left', {
  VimIcon = {
    provider = function()
      mode = mode_lookup[vim.fn.mode()] or colors.normal
      U.update_colors(mode.bg)
      return icons.vim
    end,
    highlight = {
      function() return mode.bg end,
      function() return mode.primary end,
    },
  }
})
U.section('left', {
  VimSeparator = {
    provider = function() return separators.right end,
    highlight = {

      function() return mode.primary end,
      function() return condition.check_git_workspace() and mode.secondary or mode.bg end,
    },
  }
})

U.section('left', {
  GitBranch = {
    condition = condition.check_git_workspace,
    provider = function()
      local branch = require('galaxyline.provider_vcs').get_git_branch()
      return branch and branch:gsub('detached at ', '') or ''
    end,
    icon = icons.git,

    highlight = {
      function() return mode.primary end,
      function() return mode.secondary end,
    },
  }
})

U.section('left', {
  GitChanges = {
    condition = condition.check_git_workspace,
    provider = function()
      local vcs = require('galaxyline.provider_vcs')
      local changes = (vcs.diff_modified() or 0) + (vcs.diff_add() or 0) + (vcs.diff_remove() or 0)
      return changes > 0 and changes or ''
    end,
    icon = icons.git_changes,
    highlight = {
      function() return mode.bg end,
      function() return mode.secondary end,
    },
  }
})
U.section('left', {
  GitBranchSeparator = {
    condition = condition.check_git_workspace,
    provider = function() return separators.right end,
    highlight = {

      function() return mode.secondary end,
      function() return mode.bg end,
    },
  }
})

U.section('left', {
  FileName = {
    condition = U.buffer_not_empty,
    provider = function() return vim.fn.expand('%:.') .. ' ' end,
    highlight = {
      function() return mode.light end,
      function() return mode.bg end,
    },
  }
})
U.section('left', {
  FileModified = {
    condition = U.buffer_not_empty,
    provider = function() return vim.bo.modified and icons.modified or '' end,
    highlight = {
      function() return '#e2eb0a' end,
      function() return mode.bg end,
    },
  }
})
U.section('left', {
  FileReadOnly = {
    condition = function() return not vim.bo.modifiable end,
    provider = function() return icons.readonly end,

    highlight = {
      function() return '#ee0a02' end,
      function() return mode.bg end,
    },
  }

})

U.section('mid', {
  Diagnostics = {
    condition = function()
      return U.buffer_not_empty() and vim.bo.buftype ~= 'terminal'
    end,
    provider = function()
      if next(vim.lsp.buf_get_clients()) == nil then return '' end
      local all = vim.diagnostic.get(0)
      local errs = vim.tbl_filter(function(d)
        return d.severity == vim.diagnostic.severity.ERROR
      end, all)
      local warns = vim.tbl_filter(function(d)
        return d.severity == vim.diagnostic.severity.WARN
      end, all)
      return theme.signs.diagnostics.error .. #errs .. ' ' .. theme.signs.diagnostics.warn .. #warns
    end,
    highlight = {
      function() return mode.secondary end,
      function() return mode.bg end,
    },
  }
})

U.section('right', {
  Indentation = {
    condition = function()
      return U.buffer_not_empty() and vim.bo.buftype ~= 'terminal'
    end,
    provider = function()
      return (vim.bo.expandtab and icons.space or icons.tab) .. vim.bo.shiftwidth .. ' '
    end,
    highlight = {
      function() return mode.secondary end,

      function() return mode.bg end,
    },
  }
})
U.section('right', {
  RightSectionSeparator = {
    provider = function() return separators.left end,
    highlight = {
      function() return mode.dark end,
      function() return mode.bg end,
    },
  }
})
U.section('right', {
  FileFormat = {
    provider = function() return icons[vim.bo.fileformat] end,
    highlight = {
      function() return mode.primary end,
      function() return mode.dark end,
    },
  }

})
U.section('right', {
  FileTypeSeparator = {
    condition = function()
      return U.buffer_not_empty() and vim.bo.buftype ~= 'terminal'
    end,
    provider = function() return separators.left_thin .. ' ' end,
    highlight = {
      function() return mode.bg end,
      function() return mode.dark end,
    },
  }

})
U.section('right', {
  FileType = {
    condition = function()
      return U.buffer_not_empty() and vim.bo.buftype ~= 'terminal'
    end,
    provider = function()
      local ft = vim.bo.filetype
      if ft == 'typescriptreact' then
        ft = 'tsx'
      elseif ft == 'javascriptreact' then
        ft = 'jsx'
      end
      return ' ' .. ft .. ' '
    end,
    highlight = {

      function() return mode.primary end,
      function() return mode.dark end,
      function() return 'italic' end,
    },
  }

})
U.section('right', {
  LinePosSeparator = {
    provider = function() return separators.left_thin .. ' ' end,
    highlight = {
      function() return mode.primary end,

      function() return mode.dark end,
      function() return 'bold' end,
    },
  }
})
U.section('right', {
  LinePosition = {
    provider = function()
      return icons.line .. vim.fn.line('.') .. ':' .. vim.fn.col('.') .. ' '
    end,
    highlight = {
      function() return mode.primary end,
      function() return mode.dark end,
      function() return 'bold' end,
    },
  }
})

U.section('short_line_left', {
  ShortBufferLabel = {
    condition = U.buffer_not_empty,
    provider = function()
      return vim.bo.buftype == 'nofile' and vim.bo.filetype or vim.fn.expand('%:.')
    end,
    highlight = {
      function() return "black" end,
      function() return colors.normal.dark end,
      function() return 'bold,italic' end,
    },
    separator = separators.right,
    separator_highlight = {
      colors.normal.dark,
      "black",
    },
  }

})
