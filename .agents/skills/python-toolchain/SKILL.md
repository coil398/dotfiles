---
name: python-toolchain
description: Python のスクリプト作成・依存管理・環境構築を行うときに使う。uv 優先の実行方法、PEP 723 インライン依存、uv add / uv run --with の使い分けを定める。
---

# Python toolchain

Python の実行・依存管理は `uv` を使う。`python -m venv` + `pip` を直接叩かない。

- 既存プロジェクトに `pyproject.toml` / `uv.lock` があればそれに従う
- 単体スクリプトは PEP 723 インライン依存（`# /// script` ブロックに `dependencies`）を書いて `uv run script.py` で実行する
- 一時依存は `uv run --with <pkg>`、プロジェクト依存は `uv add`
