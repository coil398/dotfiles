#!/bin/bash
# Codespaces dotfiles セットアップスクリプト
# https://docs.github.com/ja/codespaces/setting-your-user-preferences/personalizing-github-codespaces-for-your-account

set -euo pipefail

DOT_DIRECTORY="${HOME}/dotfiles"
ARCH="$(uname -m)"  # x86_64 or aarch64

# ── helpers ───────────────────────────────────────────────────────────────
log()  { printf '\033[1;34m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m ✔ %s\033[0m\n' "$*"; }
skip() { printf '\033[1;33m -- %s (スキップ)\033[0m\n' "$*"; }
has()  { command -v "$1" >/dev/null 2>&1; }

# ── 1. apt パッケージ ─────────────────────────────────────────────────────
log "apt パッケージのインストール"
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -q
sudo apt-get install -y -q --no-install-recommends \
    zsh tmux \
    ripgrep fd-find bat colordiff tig fzf \
    unzip curl wget jq

# Ubuntu では batcat / fdfind という名前でインストールされるため symlink を作成
has bat || sudo ln -sf "$(which batcat)" /usr/local/bin/bat 2>/dev/null || true
has fd  || sudo ln -sf "$(which fdfind)"  /usr/local/bin/fd  2>/dev/null || true
ok "apt 完了"

# ── 2. Neovim (prebuilt binary) ───────────────────────────────────────────
log "Neovim のインストール"
if has nvim; then
    skip "Neovim は既にインストール済み: $(nvim --version | head -1)"
else
    if [ "$ARCH" = "aarch64" ]; then
        NVIM_ASSET="nvim-linux-arm64.tar.gz"
        NVIM_DIR="nvim-linux-arm64"
    else
        NVIM_ASSET="nvim-linux-x86_64.tar.gz"
        NVIM_DIR="nvim-linux-x86_64"
    fi
    NVIM_TMP="$(mktemp -d)"
    curl -fsSL -o "${NVIM_TMP}/${NVIM_ASSET}" \
        "https://github.com/neovim/neovim/releases/latest/download/${NVIM_ASSET}"
    tar -xzf "${NVIM_TMP}/${NVIM_ASSET}" -C "${NVIM_TMP}"
    sudo rm -rf /opt/nvim
    sudo mv "${NVIM_TMP}/${NVIM_DIR}" /opt/nvim
    sudo ln -sf /opt/nvim/bin/nvim /usr/local/bin/nvim
    rm -rf "${NVIM_TMP}"
    ok "Neovim $(nvim --version | head -1)"
fi

# ── 3. eza (モダンな ls) ──────────────────────────────────────────────────
log "eza のインストール"
if has eza; then
    skip "eza は既にインストール済み"
else
    EZA_ASSET="eza_${ARCH}-unknown-linux-gnu.tar.gz"
    EZA_TMP="$(mktemp -d)"
    curl -fsSL -o "${EZA_TMP}/${EZA_ASSET}" \
        "https://github.com/eza-community/eza/releases/latest/download/${EZA_ASSET}"
    tar -xzf "${EZA_TMP}/${EZA_ASSET}" -C "${EZA_TMP}"
    sudo install -m755 "${EZA_TMP}/eza" /usr/local/bin/eza
    rm -rf "${EZA_TMP}"
    ok "eza $(eza --version | head -1)"
fi

# ── 4. procs (モダンな ps) ────────────────────────────────────────────────
log "procs のインストール"
if has procs; then
    skip "procs は既にインストール済み"
else
    PROCS_TAG="$(curl -fsSL https://api.github.com/repos/dalance/procs/releases/latest | grep -oP '"tag_name":\s*"\K[^"]+')"
    PROCS_ASSET="procs-${PROCS_TAG}-${ARCH}-linux.zip"
    PROCS_TMP="$(mktemp -d)"
    curl -fsSL -o "${PROCS_TMP}/procs.zip" \
        "https://github.com/dalance/procs/releases/download/${PROCS_TAG}/${PROCS_ASSET}"
    unzip -q "${PROCS_TMP}/procs.zip" -d "${PROCS_TMP}"
    sudo install -m755 "${PROCS_TMP}/procs" /usr/local/bin/procs
    rm -rf "${PROCS_TMP}"
    ok "procs $(procs --version)"
fi

# ── 5. 追加ツール (zoxide, direnv, gh, tmux-mem-cpu-load) ────────────────
log "追加ツールのインストール"
if ! has zoxide; then
    curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh | sh
    ok "zoxide"
else
    skip "zoxide は既にインストール済み"
fi

if ! has direnv; then
    curl -sfL https://direnv.net/install.sh | bash
    ok "direnv"
else
    skip "direnv は既にインストール済み"
fi

if ! has gh; then
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update -q && sudo apt-get install -y -q gh
    ok "gh"
else
    skip "gh は既にインストール済み"
fi

# gitleaks (pre-commit secret scan; required by ~/.githooks/pre-commit)
if has gitleaks; then
    skip "gitleaks は既にインストール済み: $(gitleaks version 2>/dev/null || echo unknown)"
else
    case "$ARCH" in
        x86_64)  GITLEAKS_PLATFORM="linux_x64"   ;;
        aarch64) GITLEAKS_PLATFORM="linux_arm64" ;;
        *)       GITLEAKS_PLATFORM="linux_x64"   ;;
    esac
    GITLEAKS_TAG="$(curl -fsSL https://api.github.com/repos/gitleaks/gitleaks/releases/latest | grep -oP '"tag_name":\s*"\K[^"]+')"
    GITLEAKS_VERSION="${GITLEAKS_TAG#v}"
    GITLEAKS_ASSET="gitleaks_${GITLEAKS_VERSION}_${GITLEAKS_PLATFORM}.tar.gz"
    GITLEAKS_TMP="$(mktemp -d)"
    curl -fsSL -o "${GITLEAKS_TMP}/gitleaks.tar.gz" \
        "https://github.com/gitleaks/gitleaks/releases/download/${GITLEAKS_TAG}/${GITLEAKS_ASSET}"
    tar -xzf "${GITLEAKS_TMP}/gitleaks.tar.gz" -C "${GITLEAKS_TMP}"
    sudo install -m755 "${GITLEAKS_TMP}/gitleaks" /usr/local/bin/gitleaks
    rm -rf "${GITLEAKS_TMP}"
    ok "gitleaks $(gitleaks version)"
fi

# ── 6. mise (runtime version manager) ────────────────────────────────────
log "mise のインストール"
if has mise; then
    skip "mise は既にインストール済み: $(mise --version)"
else
    curl https://mise.jdx.dev/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    ok "mise $(mise --version)"
fi

# ── 7. zplug ─────────────────────────────────────────────────────────────
log "zplug のインストール"
if [ -d "${HOME}/.zplug" ]; then
    skip "zplug は既にインストール済み"
else
    curl -sL --proto-redir -all,https \
        https://raw.githubusercontent.com/zplug/installer/master/installer.zsh | zsh
    ok "zplug インストール完了"
fi

# ── 8. dotfiles をリンク ──────────────────────────────────────────────────
log "dotfiles をリンク"
sh "${DOT_DIRECTORY}/etc/link.sh"
ok "dotfiles リンク完了"

# ── 9. デフォルトシェルを zsh に変更 ─────────────────────────────────────
log "デフォルトシェルを zsh に変更"
ZSH_PATH="$(which zsh)"
if [ "$(getent passwd "${USER}" | cut -d: -f7)" = "${ZSH_PATH}" ]; then
    skip "既に zsh がデフォルトシェル"
else
    sudo chsh -s "${ZSH_PATH}" "${USER}"
    ok "デフォルトシェルを zsh に変更"
fi

# ── 10. Neovim プラグイン (ヘッドレス) ───────────────────────────────────
log "Neovim プラグインのインストール"
nvim --headless "+Lazy! sync" +qa 2>/dev/null || true
ok "Neovim プラグインインストール完了"

# ── 11. Claude Code MCP サーバー (user scope) ────────────────────────────
log "Claude Code MCP サーバーの sync"
bash "${DOT_DIRECTORY}/etc/sync-mcp.sh" || true
ok "MCP sync 完了"

# ── 完了 ─────────────────────────────────────────────────────────────────
echo ""
log "セットアップ完了！ターミナルを再起動するか 'exec zsh' を実行してください"
