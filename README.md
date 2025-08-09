My best dotfiles.

- Install: `curl -fsSL https://raw.githubusercontent.com/coil398/dotfiles/master/etc/init.sh | sh`

## Prerequisites

For optimal Neovim experience with telescope-github.nvim:

- **GitHub CLI (gh)**: Required for GitHub integration features
  - macOS: `brew install gh`
  - Ubuntu/Debian: `sudo apt install gh` or `sudo snap install gh`
  - Other: See [GitHub CLI installation guide](https://cli.github.com/)

Notes
- Do not commit absolute, machine-specific symlinks in the repo (e.g., `nvim -> /Users/...`).
- To link Neovim config on your machine, run one of:
  - `sh etc/link.sh` (links dotfiles, including `.config` contents)
  - `ln -snfv "$PWD/.config/nvim" "$HOME/.config/nvim"`

Baseline
- Target Ubuntu for Linux instructions; prefer apt-based tooling.
