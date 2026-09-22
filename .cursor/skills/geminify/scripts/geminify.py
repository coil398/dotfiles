#!/usr/bin/env python3
"""Rewrite Japanese through Gemini 3.8 Flash, then check the rewrite for misunderstanding."""

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
REVIEW_INSTRUCTION = """\
あなたは原文と書き直しを照合する。見るのは、書き直しが原文を誤解していないかだけ。

誤解にあたるもの:
- 主張、結論、話者、対象の取り違え
- 条件、否定、因果の逆転
- 数値、固有名詞、コード、パス、URL、コマンドのすり替え
- 原文にない断定を足して、意味を変えること

誤解にあたらないもの:
- 読みやすくするための言い換え
- 意味が同じまま短くした接続やメタ説明
- 意味が変わらない細部の省略

JSON だけを返す。説明は付けない。
誤解がなければ {"misunderstanding": false}
誤解があれば {"misunderstanding": true, "points": ["原文の意味と、書き直しがどう取り違えているか"]}
"""
REPAIR_INSTRUCTION = """\
書き直しが原文を誤解している。指摘された誤解だけを直し、読みやすい日本語は保つ。
意味を変える情報は足さない。前置きと解説は出さず、直した本文だけを返す。
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


def build_payload(system: str, user: str) -> dict[str, object]:
    return {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "thinkingConfig": {"thinkingLevel": THINKING_LEVEL},
        },
    }


def review_user(source: str, rewritten: str) -> str:
    return f"原文:\n{source}\n\n書き直し:\n{rewritten}"


def repair_user(source: str, rewritten: str, points: list[str]) -> str:
    listed = "\n".join(f"- {point}" for point in points)
    return f"原文:\n{source}\n\n書き直し:\n{rewritten}\n\n誤解:\n{listed}"


def parse_review(text: str) -> tuple[bool, list[str]]:
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("review JSON must be an object")
    misunderstood = bool(data.get("misunderstanding"))
    points_raw = data.get("points")
    points: list[str] = []
    if isinstance(points_raw, list):
        points = [item.strip() for item in points_raw if isinstance(item, str) and item.strip()]
    if misunderstood and not points:
        raise ValueError("misunderstanding requires points")
    return misunderstood, points


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

    api_key = load_api_key()
    rewritten = extract_text(request_rewrite(api_key, build_payload(SYSTEM_INSTRUCTION, source)))
    try:
        misunderstood, points = parse_review(
            extract_text(request_rewrite(api_key, build_payload(REVIEW_INSTRUCTION, review_user(source, rewritten))))
        )
    except (json.JSONDecodeError, ValueError) as exc:
        sys.stdout.write(rewritten if rewritten.endswith("\n") else rewritten + "\n")
        sys.stdout.write(f"\n照合: 判定できなかった ({exc})\n")
        return 0

    if misunderstood:
        rewritten = extract_text(
            request_rewrite(api_key, build_payload(REPAIR_INSTRUCTION, repair_user(source, rewritten, points)))
        )
        try:
            still, remaining = parse_review(
                extract_text(
                    request_rewrite(api_key, build_payload(REVIEW_INSTRUCTION, review_user(source, rewritten)))
                )
            )
        except (json.JSONDecodeError, ValueError) as exc:
            still, remaining = True, [f"再照合できなかった ({exc})"]
        label = "まだ誤解がある" if still else "誤解を直した"
        noted = remaining if still else points
    else:
        label = "誤解はない"
        noted = []

    sys.stdout.write(rewritten if rewritten.endswith("\n") else rewritten + "\n")
    sys.stdout.write(f"\n照合: {label}\n")
    for point in noted:
        sys.stdout.write(f"- {point}\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)
