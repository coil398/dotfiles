My best dotfiles.

- Install: `curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/init.sh | sh`

Notes
- Do not commit absolute, machine-specific symlinks in the repo (e.g., `nvim -> /Users/...`).
- To link Neovim config on your machine, run one of:
  - `sh etc/link.sh` (links dotfiles, including `.config` contents)
  - `ln -snfv "$PWD/.config/nvim" "$HOME/.config/nvim"`

Baseline
- Linux baseline is Ubuntu; prefer apt-based tooling.
- Avoid hardcoding WSL distributions or user-specific settings in config files.
