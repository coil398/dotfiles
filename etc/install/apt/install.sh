#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

if command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    SUDO=""
fi

# デスクトップ環境向けのオプションツール
$SUDO apt-get install -y -q --no-install-recommends \
    xsel \
    lm-sensors \
    imwheel 2>/dev/null || true

# gitleaks (pre-commit secret scan; required by ~/.githooks/pre-commit dispatcher)
# apt 公式リポジトリには無いので GitHub Releases から prebuilt binary を取得する
if ! command -v gitleaks >/dev/null 2>&1; then
    install_gitleaks() {
        local arch asset_arch tag version asset tmp
        arch="$(uname -m)"
        case "$arch" in
            x86_64)  asset_arch="linux_x64"   ;;
            aarch64) asset_arch="linux_arm64" ;;
            *)       asset_arch="linux_x64"   ;;
        esac
        tag="$(curl -fsSL https://api.github.com/repos/gitleaks/gitleaks/releases/latest 2>/dev/null \
            | grep -oP '"tag_name":\s*"\K[^"]+')" || return 1
        [ -n "$tag" ] || return 1
        version="${tag#v}"
        asset="gitleaks_${version}_${asset_arch}.tar.gz"
        tmp="$(mktemp -d)" || return 1
        if ! curl -fsSL -o "${tmp}/gitleaks.tar.gz" \
            "https://github.com/gitleaks/gitleaks/releases/download/${tag}/${asset}" 2>/dev/null; then
            rm -rf "$tmp"
            return 1
        fi
        tar -xzf "${tmp}/gitleaks.tar.gz" -C "${tmp}" || { rm -rf "$tmp"; return 1; }
        $SUDO install -m755 "${tmp}/gitleaks" /usr/local/bin/gitleaks || { rm -rf "$tmp"; return 1; }
        rm -rf "$tmp"
        return 0
    }
    install_gitleaks || echo "[apt/install.sh] warn: gitleaks install failed (non-fatal)" >&2
fi
