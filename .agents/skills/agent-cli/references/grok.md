# Grok CLI (`grok`)

**このマシンでは未インストール**（2026-09 時点、`command -v grok` なし）。
過去セッションから分かっている範囲のメモ。

## 分かっているコマンド

```bash
grok -p 'task'                    # print モード
grok login                        # 認証 → ~/.grok/auth.json
grok inspect --json               # discovery 確認（model task を起動しない）
grok sessions list --json         # cloud セッション一覧
```

- 認証情報は `~/.grok/auth.json`
- セッションは `~/.grok/sessions` 配下にも残る

## 使うとき

- インストールされているか `command -v grok` で先に確認
- `--help` を実測してから使う（上記以外のフラグは未検証）
