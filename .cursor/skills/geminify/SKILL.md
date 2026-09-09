---
name: geminify
description: "読みにくい日本語（とくに Grok など別モデルの出力）を Gemini 3.8 Flash に渡し、人間が分かる日本語へ書き直す。/geminify、geminify、日本語が読みにくい、Geminiで読みやすく、で使う。"
argument-hint: "[読みにくい日本語。空なら直前の出力]"
disable-model-invocation: true
---

# Geminify — Cursor

**対象文**: `$ARGUMENTS`

Grok など別モデルが書いた日本語を、Gemini 3.8 Flash に渡して人間向けに書き直す。親はその場で言い換えない。書き直しプロンプトとモデル指定は [scripts/geminify.py](scripts/geminify.py) が正本。

## 手順

1. この `SKILL.md` の実体ディレクトリを `SKILL_DIR` として確定する。
2. 対象文を決める。`$ARGUMENTS` が本文ならそれを使う。空、または「直前を直して」だけの指定なら、直前のアシスタント出力を使う。会話全体は送らない。
3. 対象文に秘密・資格情報があるなら送らず停止する。
4. 対象文を UTF-8 base64 にし、シェルへ生日本語を埋め込まない。

```bash
python3 "$SKILL_DIR/scripts/geminify.py" --text-b64 "<BASE64>"
```

5. 標準出力を、前置き・要約・再言い換えなしでユーザーへ返す。失敗したら親が言い換えず、終了コードと stderr を報告する。

## 認証

`GEMINI_API_KEY`（なければ `GOOGLE_API_KEY`）。未設定なら `~/.zsh_secret` の同名行を読む。キーが無いときは取得方法だけ伝え、親が本文を書き直さない。
