#!/usr/bin/env python3
"""Rewrite Japanese through Gemini 3.8 Flash. Prompt and model live here."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "gemini-3.8-flash"
THINKING_LEVEL = "low"
ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent"
)
SECRET_FILE = Path.home() / ".zsh_secret"
SYSTEM_INSTRUCTION = """\
あなたは日本語の編集者です。与えられた文章を、人間が読んで自然に理解できる日本語に書き直してください。

守ること:
- 意味・事実・数値・固有名詞・コード・パス・URL・コマンドは変えない
- 情報を足さない。読みにくさの原因になる冗長な接続やメタ説明だけ整える
- AI翻訳調・硬すぎる文体・不自然な体言止めの連続を避ける
- 前置き・後書き・解説は出さない。書き直した本文だけを返す
"""


def load_api_key() -> str:
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    if SECRET_FILE.is_file():
        for raw in SECRET_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("export "):
                line = line[len("export ") :]
            for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                prefix = f"{name}="
                if line.startswith(prefix):
                    value = line[len(prefix) :].strip().strip("'\"")
                    if value:
                        return value
    raise SystemExit(
        "GEMINI_API_KEY がありません。Google AI Studio のキーを "
        "GEMINI_API_KEY に設定するか、~/.zsh_secret に同名の行を書いてください。"
    )


def read_source(args: argparse.Namespace) -> str:
    if args.text_b64:
        return base64.b64decode(args.text_b64).decode("utf-8")
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("対象文が空です。--text-b64、--file、または stdin を渡してください。")


def build_payload(source: str) -> dict[str, object]:
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"role": "user", "parts": [{"text": source}]}],
        "generationConfig": {
            "thinkingConfig": {"thinkingLevel": THINKING_LEVEL},
        },
    }


def extract_text(body: dict[str, object]) -> str:
    candidates = body.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise SystemExit(f"Gemini 応答に candidates がありません: {json.dumps(body, ensure_ascii=False)}")
    content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        raise SystemExit(f"Gemini 応答に text parts がありません: {json.dumps(body, ensure_ascii=False)}")
    chunks: list[str] = []
    for part in parts:
        if not isinstance(part, dict) or part.get("thought"):
            continue
        text = part.get("text")
        if isinstance(text, str) and text:
            chunks.append(text)
    rewritten = "".join(chunks).strip()
    if not rewritten:
        raise SystemExit("Gemini 応答から本文を取り出せませんでした。")
    return rewritten


def request_rewrite(api_key: str, payload: dict[str, object]) -> dict[str, object]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Gemini API HTTP {exc.code}: {detail}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite Japanese with Gemini 3.8 Flash")
    parser.add_argument("--text-b64", help="UTF-8 source text, standard base64")
    parser.add_argument("--file", help="Path to a UTF-8 source file")
    args = parser.parse_args()

    source = read_source(args).strip()
    if not source:
        raise SystemExit("対象文が空です。")

    body = request_rewrite(load_api_key(), build_payload(source))
    rewritten = extract_text(body)
    sys.stdout.write(rewritten if rewritten.endswith("\n") else rewritten + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)
