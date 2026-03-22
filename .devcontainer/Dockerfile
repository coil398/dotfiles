FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG TARGETARCH
# TARGETARCH は docker buildx が設定: amd64 or arm64

# ── apt パッケージ ─────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    zsh tmux \
    ripgrep fd-find bat colordiff tig fzf \
    unzip curl wget \
    && ln -sf /usr/bin/batcat /usr/local/bin/bat \
    && ln -sf /usr/bin/fdfind /usr/local/bin/fd \
    && rm -rf /var/lib/apt/lists/*

# ── Neovim (prebuilt binary) ───────────────────────────────────────────────
RUN set -e; \
    if [ "$TARGETARCH" = "arm64" ]; then \
        NVIM_ASSET="nvim-linux-arm64.tar.gz"; \
        NVIM_DIR="nvim-linux-arm64"; \
    else \
        NVIM_ASSET="nvim-linux64.tar.gz"; \
        NVIM_DIR="nvim-linux64"; \
    fi; \
    curl -fsSL -o /tmp/${NVIM_ASSET} \
        "https://github.com/neovim/neovim/releases/latest/download/${NVIM_ASSET}"; \
    tar -xzf /tmp/${NVIM_ASSET} -C /tmp; \
    mv /tmp/${NVIM_DIR} /opt/nvim; \
    ln -sf /opt/nvim/bin/nvim /usr/local/bin/nvim; \
    rm /tmp/${NVIM_ASSET}

# ── eza (モダンな ls) ──────────────────────────────────────────────────────
RUN set -e; \
    if [ "$TARGETARCH" = "arm64" ]; then EZA_ARCH="aarch64"; else EZA_ARCH="x86_64"; fi; \
    curl -fsSL -o /tmp/eza.tar.gz \
        "https://github.com/eza-community/eza/releases/latest/download/eza_${EZA_ARCH}-unknown-linux-gnu.tar.gz"; \
    tar -xzf /tmp/eza.tar.gz -C /tmp; \
    install -m755 /tmp/eza /usr/local/bin/eza; \
    rm /tmp/eza.tar.gz /tmp/eza

# ── procs (モダンな ps) ───────────────────────────────────────────────────
RUN set -e; \
    if [ "$TARGETARCH" = "arm64" ]; then PROCS_ARCH="aarch64"; else PROCS_ARCH="x86_64"; fi; \
    curl -fsSL -o /tmp/procs.zip \
        "https://github.com/dalance/procs/releases/latest/download/procs-${PROCS_ARCH}-linux.zip"; \
    unzip -q /tmp/procs.zip procs -d /tmp; \
    install -m755 /tmp/procs /usr/local/bin/procs; \
    rm /tmp/procs.zip /tmp/procs
